# townecodex/ui/backend.py
from __future__ import annotations
from dataclasses import dataclass
from typing import Optional, Sequence, Dict, Any, List

from townecodex.repos import EntryRepository, EntryFilters
from townecodex.dto import to_card_dtos, CardDTO
from townecodex.importer import import_file as tc_import_file

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
    def __init__(self):
        self.repo = EntryRepository()

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
        # keep sort stable
        entries = self.repo.search(ef, page=page, size=size, sort="name")
        return [ListItem(id=int(e.id), name=e.name or "") for e in entries]

    def get_item(self, entry_id: int) -> Optional[Dict[str, Any]]:
        e = self.repo.get_by_id(entry_id)
        if not e:
            return None
        return {
            "id": int(e.id),
            "name": e.name or "",
            "type": e.type or "",
            "rarity": e.rarity or "",
            "attunement_required": bool(e.attunement_required),
            "attunement_criteria": e.attunement_criteria or "",
            "value": e.value if e.value is not None else "",
            "image_url": e.image_url or "",
            "description": e.description or "",
            "source_link": e.source_link or "",
        }

    def import_file(self, path: str, *, scrape: bool, default_image: str | None) -> int:
        return tc_import_file(path, scrape=scrape, default_image=default_image)
