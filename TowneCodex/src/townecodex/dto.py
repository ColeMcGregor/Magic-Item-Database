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


# -------------------------------------------------------------------------------
#                   Inventory
#--------------------------------------------------------------------------------


# --- InventoryItemDTO -------------------------------------------------------
@dataclass(frozen=True)
class InventoryItemDTO:
    """
    Snapshot of a single InventoryItem row, enriched for UI display.
    """
    id: int
    entry_id: int
    name: str
    rarity: str
    type: str
    quantity: int
    unit_value: Optional[int]
    total_value: int

def to_inventory_item_dto(ii) -> InventoryItemDTO:
    e = ii.entry
    return InventoryItemDTO(
        id=int(ii.id),
        entry_id=int(e.id),
        name=e.name or "Unknown",
        rarity=e.rarity or "Unknown",
        type=e.type or "Unknown",
        quantity=int(ii.quantity),
        unit_value=ii.unit_value,
        total_value=int(ii.total_value),
    )


# --- InventoryDTO ------------------------------------------------------------
@dataclass(frozen=True)
class InventoryDTO:
    """
    Snapshot of an Inventory and all of its items.
    """
    id: int
    name: str
    purpose: Optional[str]
    budget: Optional[int]
    created_at: str
    total_value: int
    items: list[InventoryItemDTO]


def to_inventory_dto(inv) -> InventoryDTO:
    items = [to_inventory_item_dto(ii) for ii in inv.items]

    return InventoryDTO(
        id=int(inv.id),
        name=inv.name or "Unnamed Inventory",
        purpose=inv.purpose,
        budget=inv.budget,
        created_at=inv.created_at.isoformat() if hasattr(inv, "created_at") else "",
        total_value=sum(ii.total_value for ii in inv.items),
        items=items,
    )



__all__ = [
    "CardDTO", 
    "to_card_dto", 
    "to_card_dtos", 
    "InventoryItemDTO", 
    "to_inventory_item_dto",
    "InventoryDTO", 
    "to_inventory_dto"
    ]
