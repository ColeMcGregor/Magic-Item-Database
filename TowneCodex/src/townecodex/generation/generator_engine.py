from __future__ import annotations

import random
from typing import List, Iterable, Tuple, Optional, Set

from townecodex.models import Entry, GeneratorDef
from townecodex.repos import EntryRepository, EntryFilters
from townecodex.generation.schema import (
    GeneratorConfig,
    BucketConfig,
    config_from_json,
)


# ---------------------------------------------------------------------------
# Errors
# ---------------------------------------------------------------------------

class GeneratorError(Exception):
    """Raised when a generator config cannot be satisfied by the available data/caps."""
    pass


# ---------------------------------------------------------------------------
# Core engine
# ---------------------------------------------------------------------------

def run_generator(
    repo: EntryRepository,
    config: GeneratorConfig,
) -> List[Entry]:
    """
    Generate a list of Entries according to the given GeneratorConfig.

    Contract (strict):
      - Bucket min_count / max_count are enforced.
      - Target count per bucket is random within [min_count, max_count] (or available feasibility).
      - If constraints make a bucket impossible (data too sparse, global caps too tight), raises GeneratorError.
      - Global caps (max_items, max_total_value) are enforced during selection; we do NOT silently trim.
    """
    if config.random_seed is not None:
        random.seed(config.random_seed)

    results: List[Entry] = []
    used_ids: Set[int] = set()

    for bucket in config.buckets:
        picked = _generate_bucket(repo, bucket, config, used_ids, results)
        results.extend(picked)

    # Final strict validation (fail loud, don't mutate)
    count, total_value = _current_totals(results)

    if config.max_items is not None and count > config.max_items:
        raise GeneratorError(
            f"Global max_items violated after generation: {count} > {config.max_items}"
        )

    if config.max_total_value is not None and total_value > config.max_total_value:
        raise GeneratorError(
            f"Global max_total_value violated after generation: {total_value} > {config.max_total_value}"
        )

    if config.min_items is not None and count < config.min_items:
        raise GeneratorError(
            f"Global min_items not met: {count} < {config.min_items}"
        )

    if config.min_total_value is not None and total_value < config.min_total_value:
        raise GeneratorError(
            f"Global min_total_value not met: {total_value} < {config.min_total_value}"
        )

    return results


def _current_totals(entries: Iterable[Entry]) -> Tuple[int, int]:
    count = 0
    value_sum = 0
    for e in entries:
        count += 1
        value_sum += int(e.value or 0)
    return count, value_sum


# ---------------------------------------------------------------------------
# Per-bucket logic
# ---------------------------------------------------------------------------

def _generate_bucket(
    repo: EntryRepository,
    bucket: BucketConfig,
    config: GeneratorConfig,
    used_ids: Set[int],
    current_results: List[Entry],
) -> List[Entry]:
    """
    Generate entries for a single bucket.

    Strict enforcement:
      - Randomly chooses a target_count in [min_count, feasible_max]
      - Ensures target_count is achievable given:
          * bucket filters
          * uniqueness preferences
          * global caps (remaining item slots, remaining budget)
      - If not achievable, raises GeneratorError
    """
    # ---- bucket range -------------------------------------------------
    min_count = max(0, int(bucket.min_count or 0))

    # Interpret max_count <= 0 as "no explicit upper bound"
    raw_max = bucket.max_count
    max_count: Optional[int]
    if raw_max is None or int(raw_max) <= 0:
        max_count = None
    else:
        max_count = int(raw_max)

    # ---- global caps remaining ---------------------------------------
    current_count, current_value = _current_totals(current_results)

    remaining_item_slots: Optional[int] = None
    if config.max_items is not None:
        remaining_item_slots = max(0, int(config.max_items) - current_count)

    remaining_budget: Optional[int] = None
    if config.max_total_value is not None:
        remaining_budget = max(0, int(config.max_total_value) - current_value)

    # ---- step 1: coarse DB query -------------------------------------
    filters = EntryFilters(
        name_contains=None,
        type_equals=None,  # we do type substring filtering in Python
        rarity_in=bucket.allowed_rarities,
        attunement_required=bucket.attunement_required,
        text=None,
    )

    candidates: List[Entry] = repo.search(filters, page=1, size=500, sort="name")

    # ---- step 2: refine in Python ------------------------------------
    def matches_bucket(e: Entry) -> bool:
        # Type substring filters
        if bucket.type_contains_any:
            etype = (e.type or "").lower()
            if not any(sub.lower() in etype for sub in bucket.type_contains_any):
                return False

        # Value bounds
        v = e.value
        if v is None:
            # If min/max value is specified, skip entries with unknown value
            if bucket.min_value is not None or bucket.max_value is not None:
                return False
        else:
            if bucket.min_value is not None and v < bucket.min_value:
                return False
            if bucket.max_value is not None and v > bucket.max_value:
                return False

        return True

    filtered: List[Entry] = [e for e in candidates if matches_bucket(e)]

    # ---- step 3: enforce uniqueness (if either global or bucket wants it) ----
    if config.global_prefer_unique or bucket.prefer_unique:
        filtered = [e for e in filtered if int(e.id) not in used_ids]

    if not filtered:
        if min_count > 0:
            raise GeneratorError(
                f"Bucket '{bucket.name}' requires at least {min_count}, but 0 candidates match filters."
            )
        return []

    # ---- step 4: compute feasibility for picking counts ----------------
    available = len(filtered)

    feasible_max = available
    if max_count is not None:
        feasible_max = min(feasible_max, max_count)

    if remaining_item_slots is not None:
        feasible_max = min(feasible_max, remaining_item_slots)

    # Budget feasibility: compute the maximum number of items we could possibly
    # take within remaining_budget by taking the cheapest candidates.
    budget_cap = None
    if remaining_budget is not None:
        cheapest_values = sorted(int(e.value or 0) for e in filtered)
        running = 0
        can_take = 0
        for v in cheapest_values:
            if running + v > remaining_budget:
                break
            running += v
            can_take += 1
        budget_cap = can_take
        feasible_max = min(feasible_max, budget_cap)

    if feasible_max < min_count:
        msg = (
            f"Bucket '{bucket.name}' cannot meet min_count={min_count}. "
            f"Feasible max is {feasible_max} after filters"
        )
        if remaining_item_slots is not None:
            msg += f", remaining_item_slots={remaining_item_slots}"
        if remaining_budget is not None:
            msg += f", remaining_budget={remaining_budget}"
        msg += "."
        raise GeneratorError(msg)

    # Random variability: pick target_count uniformly from feasible range
    target_count = random.randint(min_count, feasible_max)

    if target_count == 0:
        return []

    # ---- step 5: pick exactly target_count while respecting remaining_budget ----
    # If no budget cap, a simple random.sample is sufficient and matches your intent.
    if remaining_budget is None:
        chosen = random.sample(filtered, k=target_count) if target_count < available else list(filtered)
        for e in chosen:
            used_ids.add(int(e.id))
        return chosen

    # Budgeted selection:
    # 1) start with a random sample of size k
    # 2) if over budget, swap out expensive picks for cheap non-picked entries until within budget
    k = target_count
    if k >= available:
        initial = list(filtered)
    else:
        initial = random.sample(filtered, k=k)

    selected_ids = {int(e.id) for e in initial}
    selected = list(initial)

    # Build list of remaining candidates (not selected)
    remaining = [e for e in filtered if int(e.id) not in selected_ids]

    # Quick sums
    def val(e: Entry) -> int:
        return int(e.value or 0)

    total = sum(val(e) for e in selected)
    budget = remaining_budget

    if total > budget:
        # Sort remaining by value asc (cheapest first) for swaps
        remaining.sort(key=val)

        # We'll repeatedly replace the most expensive selected item with the cheapest remaining
        # if it reduces total.
        while total > budget:
            if not remaining:
                raise GeneratorError(
                    f"Bucket '{bucket.name}' cannot pick {k} items within remaining_budget={budget}."
                )

            # Most expensive currently selected
            sel_max = max(selected, key=val)
            sel_max_v = val(sel_max)

            # Cheapest remaining candidate
            rem_min = remaining[0]
            rem_min_v = val(rem_min)

            # If we can't reduce the total, it's impossible
            if rem_min_v >= sel_max_v:
                raise GeneratorError(
                    f"Bucket '{bucket.name}' cannot pick {k} items within remaining_budget={budget} "
                    f"(cannot reduce selection cost further)."
                )

            # Perform swap
            selected.remove(sel_max)
            selected_ids.remove(int(sel_max.id))

            selected.append(rem_min)
            selected_ids.add(int(rem_min.id))

            total = total - sel_max_v + rem_min_v

            # Remove rem_min from remaining, add sel_max back (keep remaining sorted-ish)
            remaining.pop(0)
            remaining.append(sel_max)
            remaining.sort(key=val)

    # At this point we have exactly k items within budget
    for e in selected:
        used_ids.add(int(e.id))

    return selected


# ---------------------------------------------------------------------------
# Convenience: run from a GeneratorDef row
# ---------------------------------------------------------------------------

def run_generator_from_def(
    repo: EntryRepository,
    gen_def: GeneratorDef,
) -> List[Entry]:
    """
    Convenience helper: parse config_json from a GeneratorDef row and run the generator.
    """
    cfg = config_from_json(gen_def.config_json)
    return run_generator(repo, cfg)
