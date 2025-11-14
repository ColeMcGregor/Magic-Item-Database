from __future__ import annotations

import random
from typing import List, Iterable, Tuple, Optional

from townecodex.models import Entry, GeneratorDef
from townecodex.repos import EntryRepository, EntryFilters
from townecodex.generation.schema import (
    GeneratorConfig,
    BucketConfig,
    config_from_json,
)



# ---------------------------------------------------------------------------
# Core engine
# ---------------------------------------------------------------------------

def run_generator(
    repo: EntryRepository,
    config: GeneratorConfig,
) -> List[Entry]:
    """
    Generate a list of Entries according to the given GeneratorConfig.

    Notes:
      - Uses EntryRepository.search for rough filtering, then refines in Python.
      - Enforces global max_items / max_total_value as best as possible.
      - If constraints are tight or DB is sparse, you may get fewer items
        than requested.
    """
    if config.random_seed is not None:
        random.seed(config.random_seed)

    results: List[Entry] = []
    used_ids: set[int] = set()

    # Helper to compute current totals
    def current_totals(entries: Iterable[Entry]) -> Tuple[int, int]:
        count = 0
        value_sum = 0
        for e in entries:
            count += 1
            value_sum += int(e.value or 0)
        return count, value_sum

    for bucket in config.buckets:
        bucket_entries = _generate_bucket(repo, bucket, config, used_ids, results)
        results.extend(bucket_entries)

    # Final sanity pass for global caps (if any)
    count, total_value = current_totals(results)

    if config.max_items is not None and count > config.max_items:
        # Trim from the end; a more sophisticated strategy could be added later.
        results = results[: config.max_items]
        count, total_value = current_totals(results)

    if config.max_total_value is not None and total_value > config.max_total_value:
        # Greedy trim from the end until under budget.
        trimmed: List[Entry] = []
        running_value = 0
        for e in results:
            v = int(e.value or 0)
            if running_value + v > config.max_total_value:
                continue
            trimmed.append(e)
            running_value += v
        results = trimmed

    return results


# ---------------------------------------------------------------------------
# Per-bucket logic
# ---------------------------------------------------------------------------

def _generate_bucket(
    repo: EntryRepository,
    bucket: BucketConfig,
    config: GeneratorConfig,
    used_ids: set[int],
    current_results: List[Entry],
) -> List[Entry]:
    """
    Generate entries for a single bucket.

    Respects:
      - bucket rarity / type / value / attunement filters
      - bucket min_count / max_count
      - global_prefer_unique + bucket.prefer_unique
      - global max_items / max_total_value where feasible
    """
    # Step 1: coarse DB query by rarity + attunement
    filters = EntryFilters(
        name_contains=None,
        type_equals=None,           # we do type substring filtering in Python
        rarity_in=bucket.allowed_rarities,
        attunement_required=bucket.attunement_required,
        text=None,
    )

    # Fetch a reasonably large candidate pool; tune size as needed.
    candidates: List[Entry] = repo.search(filters, page=1, size=500, sort="name")

    # Step 2: refine in Python for type + value range + uniqueness preferences
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

    # Enforce uniqueness preferences
    prefer_unique_global = config.global_prefer_unique
    prefer_unique_bucket = bucket.prefer_unique

    if prefer_unique_global or prefer_unique_bucket:
        filtered = [e for e in filtered if e.id not in used_ids]

    if not filtered:
        return []

    # Step 3: decide how many items we *want* from this bucket
    # Interpret max_count <= 0 as "no explicit upper bound" (use min_count as target).
    min_count = max(0, bucket.min_count)
    max_count = bucket.max_count if bucket.max_count and bucket.max_count > 0 else None

    # Cap by available candidates
    if max_count is not None:
        target_max = min(max_count, len(filtered))
    else:
        target_max = len(filtered)

    if target_max <= 0:
        return []

    # Simple strategy: aim for target_max (try to fill as much as allowed)
    target_count = target_max

    # Step 4: sample from filtered candidates
    # Use random.sample for uniqueness; if we ever allow duplicates, this is where
    # we'd change strategy.
    if target_count >= len(filtered):
        chosen = list(filtered)
    else:
        chosen = random.sample(filtered, k=target_count)

    # Step 5: enforce global caps as we go (max_items / max_total_value)
    selected: List[Entry] = []
    current_count = len(current_results)
    current_value = sum(int(e.value or 0) for e in current_results)

    for e in chosen:
        # Check global max_items
        if config.max_items is not None and (current_count + len(selected) + 1) > config.max_items:
            break

        # Check global max_total_value
        v = int(e.value or 0)
        if config.max_total_value is not None and (current_value + sum(int(x.value or 0) for x in selected) + v) > config.max_total_value:
            # Skip this one; try next
            continue

        selected.append(e)
        used_ids.add(int(e.id))

    # We *try* to hit min_count, but might not if constraints are too tight.
    if len(selected) < min_count:
        # You could log or warn here in a non-UI context.
        # For now, just return what we managed to pick.
        return selected

    return selected


# ---------------------------------------------------------------------------
# Convenience: run from a GeneratorDef row
# ---------------------------------------------------------------------------

def run_generator_from_def(
    repo: EntryRepository,
    gen_def: GeneratorDef,
) -> List[Entry]:
    """
    Convenience helper: parse config_json from a GeneratorDef row
    and run the generator.
    """
    cfg = config_from_json(gen_def.config_json)
    return run_generator(repo, cfg)
