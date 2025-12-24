# townecodex/ui/backend.py
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Sequence, List

import time

from townecodex.repos import (
    EntryRepository,
    EntryFilters,
    session_scope,
    GeneratorRepository,
    InventoryRepository,
)
from townecodex.dto import (
    CardDTO,
    to_card_dto,
    InventoryDTO,
    to_inventory_dto,
    to_inventory_item_dto,  # NOTE: kept as-is; used elsewhere in UI flows
)
from townecodex.importer import import_file as tc_import_file
from townecodex.pricing import compute_price
from townecodex.scraper import RedditScraper

# Generator execution lives in the engine. Backend only orchestrates:
#   (load def) -> (run engine) -> (convert Entries to DTOs)
from townecodex.generation.generator_engine import (
    run_generator_from_def,
    run_generator,  # NOTE: needed for "run from current UI config" without saving
)
from townecodex.models import GeneratorDef
from townecodex.generation.schema import (
    GeneratorConfig,
    BucketConfig,      # NOTE: kept as-is; GUI/builders may reference this type
    config_from_json,  # NOTE: not required for running, but useful for debugging/UI
    config_to_json,
)


# ------------------------------------------------------------------------------
# Small UI helper DTOs
# ------------------------------------------------------------------------------

@dataclass(frozen=True)
class QueryParams:
    """
    Snapshot of a list/search query.

    This is mainly a convenience for:
      - passing around query intent in a structured way
      - making it easier to store/restore last query later if desired
    """
    name_contains: Optional[str] = None
    type_contains: Optional[str] = None
    rarity_in: Optional[Sequence[str]] = None
    attunement_required: Optional[bool] = None
    general_type: Optional[str] = None
    specific_tag: Optional[str] = None
    page: int = 1
    size: int = 1000
    sort: str = "name"


@dataclass(frozen=True)
class ListItem:
    """
    Minimal list row structure for list widgets.
    """
    id: int
    name: str


# ------------------------------------------------------------------------------
# Backend façade
# ------------------------------------------------------------------------------

class Backend:
    """
    Thin application layer for the GUI.

    Responsibilities:
      - Provide a clean API for UI + worker threads (QRunnable workers)
      - Convert ORM objects to DTOs before returning to UI layer
      - Orchestrate calls to repositories and domain utilities

    Non-responsibilities:
      - No Qt code here
      - No rendering here
      - No in-memory basket state here
    """

    def __init__(self):
        # Repos store a session_factory, not a live session.
        # Each repo call should open/close its own Session via session_scope.
        self.entry_repo = EntryRepository()
        self.gen_repo = GeneratorRepository()
        self.inv_repo = InventoryRepository()

    # ------------------------------------------------------------------ #
    # Listing & detail                                                   #
    # ------------------------------------------------------------------ #

    def list_items(
        self,
        *,
        name_contains: Optional[str] = None,
        type_contains: Optional[str] = None,  # reserved for free-text type search if needed
        general_type: Optional[str] = None,
        specific_tag: Optional[str] = None,
        rarities: Optional[Sequence[str]] = None,
        attunement_required: Optional[bool] = None,
        page: int = 1,
        size: int = 500,
    ) -> List[ListItem]:
        """
        Return search results as lightweight ListItem objects.

        Notes:
          - This function intentionally returns a minimal representation suitable
            for list widgets (id + name) to keep UI snappy.
          - Full detail is fetched via get_item(entry_id) as needed.
        """
        name_contains = (name_contains or "").strip() or None

        # GUI uses structured general_type + specific_tag. Repo supports these
        # via EntryFilters.general_type_in and EntryFilters.specific_tag.
        general_type_in = [general_type] if general_type else None

        ef = EntryFilters(
            name_contains=name_contains,
            # GUI now uses structured typing; this remains for any future free-text callers.
            type_contains=type_contains,
            rarity_in=[r for r in (rarities or []) if r != "Any"] or None,
            attunement_required=attunement_required,
            general_type_in=general_type_in,
            specific_tag=specific_tag,
        )
        entries = self.entry_repo.search(ef, page=page, size=size, sort="name")
        return [ListItem(id=int(e.id), name=e.name or "") for e in entries]

    def get_item(self, entry_id: int) -> Optional[CardDTO]:
        """
        Return a fully-hydrated CardDTO for a single Entry.

        Important:
          - DTO boundary: UI should not receive ORM objects.
        """
        e = self.entry_repo.get_by_id(entry_id)
        return to_card_dto(e) if e else None

    # ------------------------------------------------------------------ #
    # Entry CRUD for Details tab                                         #
    # ------------------------------------------------------------------ #

    def create_entry(self, data: dict) -> CardDTO:
        """
        Create a brand-new Entry from Details tab data.

        Repo method handles:
          - normalization of form fields
          - creation
          - flush/commit semantics
        """
        e = self.entry_repo.create_from_details(data)
        return to_card_dto(e)

    def update_entry(self, entry_id: int, data: dict) -> CardDTO:
        """
        Update an existing Entry from Details tab data.

        Repo method handles:
          - normalization of form fields
          - overwriting fields explicitly (including clears)
        """
        e = self.entry_repo.update_from_details(entry_id, data)
        return to_card_dto(e)

    def delete_entry(self, entry_id: int) -> bool:
        """
        Delete an Entry by id (used by Details tab).
        """
        return self.entry_repo.delete_by_id(entry_id)

    # ------------------------------------------------------------------ #
    # Bulk operations for workers                                        #
    # ------------------------------------------------------------------ #

    def auto_price_missing(self) -> int:
        """
        Compute and assign default prices to entries missing a value.

        Implementation notes:
          - Runs in a single transaction scope.
          - Uses compute_price(...) chart logic.
          - Marks value_updated=False because this is an automated/default price.
        """
        updated = 0

        # We use the repo's session factory explicitly so this stays consistent
        # with other repo operations and remains thread-safe under workers.
        with session_scope(self.entry_repo._session_factory) as s:  # type: ignore[attr-defined]
            for e in self.entry_repo.iter_missing_price(s):
                price = compute_price(
                    rarity=e.rarity,
                    type_text=e.type,
                    attunement_required=bool(e.attunement_required),
                )
                if price is None:
                    continue

                e.value = price
                e.value_updated = False
                updated += 1

        return updated

    def scrape_existing_missing(self, throttle_seconds: float = 1.0) -> int:
        """
        Scrape external sources to fill missing description/image_url.

        Current policy:
          - only scrapes entries with a reddit source link
          - only fills fields that are currently empty
          - sleeps between items to throttle
        """
        updated = 0

        with session_scope(self.entry_repo._session_factory) as s:  # type: ignore[attr-defined]
            for e in self.entry_repo.iter_needing_scrape(s):
                link = e.source_link or ""
                if not link or "reddit" not in link.lower():
                    continue

                try:
                    data = RedditScraper.fetch_post_data(link)
                except Exception as exc:
                    print(f"[scrape warn] id={e.id} {e.name!r}: {exc}")
                    continue

                changed = False

                desc = data.get("description")
                if desc and not e.description:
                    e.description = desc
                    changed = True

                img = data.get("image_url")
                if img and not e.image_url:
                    e.image_url = img
                    changed = True

                if changed:
                    updated += 1

                if throttle_seconds > 0:
                    time.sleep(throttle_seconds)

        return updated

    def get_type_terms(self) -> tuple[List[str], List[str]]:
        """
        Return:
          (general_types, specific_tags)

        Intended for populating dropdowns.
        """
        gens, specs = self.entry_repo.collect_type_terms()
        return gens, specs

    # ------------------------------------------------------------------ #
    # Generators                                                         #
    # ------------------------------------------------------------------ #

    def create_generator(self, name: str, purpose: str | None, config: GeneratorConfig) -> GeneratorDef:
        """
        Persist a new GeneratorDef.

        Notes:
          - config is stored as JSON (config_to_json)
          - description is currently unused here (left None)
        """
        gen = GeneratorDef(
            name=name,
            purpose=purpose,
            description=None,
            config_json=config_to_json(config),
        )
        return self.gen_repo.insert(gen)

    def update_generator(self, gen_id: int, name: str, purpose: str | None, config: GeneratorConfig) -> GeneratorDef:
        """
        Update an existing GeneratorDef.

        Important:
          - This does NOT run the generator.
          - This only persists definition changes (name/purpose/config_json).
        """
        gen = self.gen_repo.get_by_id(gen_id)
        if not gen:
            raise ValueError("Generator not found")

        gen.name = name
        gen.purpose = purpose
        gen.config_json = config_to_json(config)

        return self.gen_repo.update(gen)

    def delete_generator(self, gen_id: int) -> bool:
        """
        Delete a GeneratorDef by id.
        """
        return self.gen_repo.delete_by_id(gen_id)

    def list_generators(self):
        """
        Return all GeneratorDef rows (ORM objects).

        NOTE:
          This is kept as-is to preserve GUI expectations.
          If you ever want DTO-only here, we can change it later, but do NOT
          change the return type casually because GUI may depend on attributes.
        """
        return self.gen_repo.list_all()

    def get_generator(self, gen_id: int):
        """
        Return GeneratorDef by id (ORM object).
        """
        return self.gen_repo.get_by_id(gen_id)

    def run_generator(self, gen_id: int) -> List[CardDTO]:
        """
        Run a saved GeneratorDef by id and return results as CardDTOs.

        This is the main entry point for:
          - GenerateWorker (QRunnable)
          - any future CLI trigger
          - "Run generator" button in GUI

        Contract guarantees:
          - Raises if the generator doesn't exist (hard failure is better than silently returning [])
          - Does NOT return ORM objects (DTO boundary)
          - Uses engine logic (including strict min/max enforcement + global caps)
        """
        gen_id = int(gen_id)

        gen_def = self.gen_repo.get_by_id(gen_id)
        if not gen_def:
            raise ValueError(f"Generator not found: id={gen_id}")

        # Engine returns Entries (ORM). Backend converts to CardDTO immediately.
        entries = run_generator_from_def(self.entry_repo, gen_def)
        return [to_card_dto(e) for e in entries]

    def run_generator_from_config(self, config: GeneratorConfig) -> List[CardDTO]:
        """
        Run generation directly from an in-memory GeneratorConfig.

        Why this exists:
          - GUI may have "current generator settings loaded" that are edited but not saved.
          - This allows "Run" to reflect *current UI state* without requiring a DB write.

        Contract:
          - Raises GeneratorError (or other exceptions) if constraints are unsatisfiable.
          - Returns DTOs only.
        """
        entries = run_generator(self.entry_repo, config)
        return [to_card_dto(e) for e in entries]

    # ------------------------------------------------------------------ #
    # Inventories                                                        #
    # ------------------------------------------------------------------ #
    #
    # Inventory methods are already implemented in your project (repo + backend + GUI).
    # They are kept here as-is; if you want this file updated further for inventory,
    # paste the remaining portion and I’ll apply the same comment standard.
    # ------------------------------------------------------------------ #

    def list_inventories(self) -> List[ListItem]:
        """
        List all inventories as lightweight list items for selection widgets.
        """
        invs = self.inv_repo.list_all()
        return [ListItem(id=int(i.id), name=i.name or "") for i in invs]

    def get_inventory(self, inv_id: int) -> Optional[InventoryDTO]:
        """
        Return fully-hydrated InventoryDTO (items already sorted via dto.py helper).
        """
        inv = self.inv_repo.get_by_id(inv_id)
        return to_inventory_dto(inv) if inv else None

    def create_inventory(
        self,
        *,
        name: str,
        purpose: str | None,
        items_spec: list[dict],
    ) -> InventoryDTO:
        """
        Create inventory + its InventoryItem rows in one operation.
        """
        inv = self.inv_repo.create_inventory(
            name=name,
            purpose=purpose,
            items_spec=items_spec,
        )
        return to_inventory_dto(inv)

    def update_inventory(
        self,
        inv_id: int,
        *,
        name: str,
        purpose: str | None,
        items_spec: list[dict],
    ) -> InventoryDTO:
        """
        Update inventory header fields and replace items with items_spec.
        """
        inv = self.inv_repo.update_inventory(
            inv_id,
            name=name,
            purpose=purpose,
            items_spec=items_spec,
        )
        return to_inventory_dto(inv)

    def delete_inventory(self, inv_id: int) -> bool:
        """
        Delete inventory by id.
        """
        return self.inv_repo.delete_by_id(inv_id)

    # ------------------------------------------------------------------ #
    # Import                                                             #
    # ------------------------------------------------------------------ #

    def import_file(
        self,
        path: str,
        *,
        default_image: str | None,
        batch_size: int = 10,
        batch_sleep_seconds: float = 5.0,
    ) -> int:
        """
        Unified import entry point for GUI + workers.

        Delegates to importer module, which:
          - parses file
          - normalizes rows
          - uses repo upsert/bulk logic
        """
        return tc_import_file(
            path,
            default_image=default_image,
            batch_size=batch_size,
            batch_sleep_seconds=batch_sleep_seconds,
        )
