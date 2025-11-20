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
)
from townecodex.dto import CardDTO, to_card_dto
from townecodex.importer import import_file as tc_import_file
from townecodex.pricing import compute_price
from townecodex.scraper import RedditScraper
from townecodex.generation.generator_engine import run_generator_from_def


@dataclass(frozen=True)
class QueryParams:
    name_contains: Optional[str] = None
    type_contains: Optional[str] = None
    rarity_in: Optional[Sequence[str]] = None
    attunement_required: Optional[bool] = None
    page: int = 1
    size: int = 1000
    sort: str = "name"


@dataclass(frozen=True)
class ListItem:
    id: int
    name: str


class Backend:
    """
    Thin application layer for the GUI:

    - entry listing and detail lookup
    - pricing and scraping utilities
    - generator execution
    - unified import interface
    """

    def __init__(self):
        self.entry_repo = EntryRepository()
        self.gen_repo = GeneratorRepository()

    # ------------------------------------------------------------------ #
    # Listing & detail                                                   #
    # ------------------------------------------------------------------ #

    def list_items(
        self,
        *,
        name_contains: Optional[str] = None,
        type_contains: Optional[str] = None,
        rarities: Optional[Sequence[str]] = None,
        attunement_required: Optional[bool] = None,
        page: int = 1,
        size: int = 500,
    ) -> List[ListItem]:
        name_contains = (name_contains or "").strip() or None
        ef = EntryFilters(
            name_contains=name_contains,
            type_contains=type_contains,  # already normalized by GUI
            rarity_in=[r for r in (rarities or []) if r != "Any"] or None,
            attunement_required=attunement_required,
        )
        entries = self.entry_repo.search(ef, page=page, size=size, sort="name")
        return [ListItem(id=int(e.id), name=e.name or "") for e in entries]


    def get_item(self, entry_id: int) -> Optional[CardDTO]:
        e = self.entry_repo.get_by_id(entry_id)
        return to_card_dto(e) if e else None

    # ------------------------------------------------------------------ #
    # Bulk operations for workers                                       #
    # ------------------------------------------------------------------ #

    def auto_price_missing(self) -> int:
        updated = 0

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
        gens, specs = self.entry_repo.collect_type_terms()
        return gens, specs

    # ------------------------------------------------------------------ #
    # Generators                                                         #
    # ------------------------------------------------------------------ #

    def list_generators(self):
        return self.gen_repo.list_all()

    def get_generator(self, gen_id: int):
        return self.gen_repo.get_by_id(gen_id)

    def run_generator(self, gen_id: int) -> List[CardDTO]:
        gen_def = self.gen_repo.get_by_id(gen_id)
        if not gen_def:
            return []

        entries = run_generator_from_def(self.entry_repo, gen_def)
        return [to_card_dto(e) for e in entries]

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
        Delegate to the importer module. This keeps the GUI ignorant of details.
        """
        return tc_import_file(
            path,
            default_image=default_image,
            batch_size=batch_size,
            batch_sleep_seconds=batch_sleep_seconds,
        )