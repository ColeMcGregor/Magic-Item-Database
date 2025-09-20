# towne_codex/dto.py
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Sequence


"""
This is the data transfer object for the card.
it is used when rendering the card to the user.

author: Cole McGregor
date: 2025-09-20
version: 0.1.0
"""


# --- CardDTO ---------------------------------------------------------------
@dataclass(frozen=True)
class CardDTO:
    """
    Minimal, raw view data for an item card.
    """
    id: int
    title: str
    type: str
    rarity: str
    attunement_required: bool
    attunement_criteria: Optional[str]
    value: Optional[int]
    value_updated: bool
    description: Optional[str]    # unformatted (raw/markdown/plain)
    image_url: Optional[str]      # URL only

# --- to_card_dto ------------------------------------------------------------
def to_card_dto(entry) -> CardDTO:
    """
    Convert an Entry ORM object to CardDTO (expects Entry.image_url to exist).
    """
    return CardDTO(
        id=int(entry.id),
        title=(entry.name or "Name Unknown"),
        type=(entry.type or "Type Unknown"),
        rarity=(entry.rarity or "Rarity Unknown"),
        attunement_required=bool(entry.attunement_required),
        attunement_criteria=getattr(entry, "attunement_criteria", None),
        value=getattr(entry, "value", None),
        value_updated=bool(getattr(entry, "value_updated", False)),
        description=getattr(entry, "description", None),
        image_url=getattr(entry, "image_url", None),
    )


# --- to_card_dtos ------------------------------------------------------------
def to_card_dtos(entries: Sequence) -> list[CardDTO]:
    return [to_card_dto(e) for e in entries]


__all__ = ["CardDTO", "to_card_dto", "to_card_dtos"]
