# townecodex/ui/backend.py
from __future__ import annotations
from dataclasses import dataclass

from typing import Optional, Sequence, Dict, Any, List
import time

from townecodex.repos import EntryRepository, EntryFilters, session_scope
from townecodex.dto import CardDTO, to_card_dto
from townecodex.importer import import_file as tc_import_file
from townecodex.pricing import compute_price
from townecodex.scraper import RedditScraper


@dataclass(frozen=True)
class QueryParams:
    name_contains: Optional[str] = None
    type_equals: Optional[str] = None
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
    Thin application layer for the GUI.

    - Wraps EntryRepository for basic reads.
    - Owns bulk operations like auto-pricing and scraping.
    """

    def __init__(self):
        self.repo = EntryRepository()

    # ------------------------------------------------------------------ #
    # Listing & detail                                                   #
    # ------------------------------------------------------------------ #

    def list_items(
        self,
        *,
        name_contains: Optional[str] = None,
        type_equals: Optional[str] = None,
        rarities: Optional[Sequence[str]] = None,
        attunement_required: Optional[bool] = None,
        page: int = 1,
        size: int = 500,
    ) -> List[ListItem]:
        name_contains = (name_contains or "").strip() or None
        ef = EntryFilters(
            name_contains=name_contains,
            type_equals=type_equals if (type_equals and type_equals != "Any") else None,
            rarity_in=[r for r in (rarities or []) if r != "Any"] or None,
            attunement_required=attunement_required,
        )
        entries = self.repo.search(ef, page=page, size=size, sort="name")
        return [ListItem(id=int(e.id), name=e.name or "") for e in entries]

    def get_item(self, entry_id: int) -> Optional[CardDTO]:
        e = self.repo.get_by_id(entry_id)
        if not e:
            return None
        return to_card_dto(e)

    # ------------------------------------------------------------------ #
    # Bulk operations for workers                                       #
    # ------------------------------------------------------------------ #

    def auto_price_missing(self) -> int:
        """
        Walk entries with NULL/None value and fill them using the rarity/type/attune chart.
        Returns number of entries updated.
        """
        updated = 0
        # Use the same session factory as the repo
        with session_scope(self.repo._session_factory) as s:  # type: ignore[attr-defined]
            for e in self.repo.iter_missing_price(s):
                print(f"auto-pricing {e.name!r} (id={e.id})")
                price = compute_price(
                    rarity=e.rarity,
                    type_text=e.type,
                    attunement_required=bool(e.attunement_required),
                )
                print(f"price: {price}")
                if price is None:
                    continue
                e.value = price
                # Automatic chart price, not a user override
                e.value_updated = False
                updated += 1

        return updated

    def scrape_existing_missing(self, throttle_seconds: float = 1.0) -> int:
        """
        For existing DB rows that have a source_link but missing description/image,
        hit Reddit and fill them in. Returns count of successfully scraped entries.
        """
        updated = 0

        with session_scope(self.repo._session_factory) as s:  # type: ignore[attr-defined]
            for e in self.repo.iter_needing_scrape(s):
                link = e.source_link or ""
                if not link or "reddit" not in link.lower():
                    continue

                try:
                    data = RedditScraper.fetch_post_data(link)
                except Exception as exc:
                    # For now, just log to stdout; GUI worker will surface a generic error
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

    # ------------------------------------------------------------------ #
    # Import                                                            #
    # ------------------------------------------------------------------ #

    def import_file(self, path: str, *, scrape: bool, default_image: str | None) -> int:
        """
        Delegate to the importer module. This keeps the GUI ignorant of details.
        """
        return tc_import_file(path, scrape=scrape, default_image=default_image)
