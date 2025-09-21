from __future__ import annotations
from sqlalchemy import Column, Integer, String, Text, Boolean, ForeignKey, DateTime, func, UniqueConstraint
from sqlalchemy.orm import declarative_base, relationship

"""
These are data models for the Towne Codex database.
these are for the tables in the database.
they include:

- Entry
- GeneratorDef
- Inventory
- InventoryItem


author: Cole McGregor
date: 2025-09-17
version: 0.1.0
"""
# a declarative base is used to create the models.
Base = declarative_base()


class Entry(Base):
    """
    Represents an item/entry (e.g., potion, weapon, armor).
    Parsed from fed files elsewhere
    """
    __tablename__ = "entries"

    id = Column(Integer, primary_key=True, autoincrement=True)

    # Core fields
    name = Column(String, nullable=False, index=True)
    type = Column(String, nullable=False)
    rarity = Column(String, nullable=False)
    value = Column(Integer, nullable=True)

    # Attunement
    attunement_required = Column(Boolean, default=False)
    attunement_criteria = Column(String, nullable=True)

    # Links & description
    source_link = Column(String, nullable=True, unique=True)       # Reddit or external link, shouldnt match any other source link
    description = Column(Text, nullable=True)        # scraped or manual text
    image_url = Column(String, nullable=True)  # scraped direct link


    #flags
    value_updated=Column(Boolean, default=False) #used to track if the value of the item has been updated from original generated value

    # Relationships
    # inventories = relationship("Inventory", back_populates="entry")

    def __repr__(self) -> str:
        return f"<Entry(id={self.id}, name={self.name!r}, rarity={self.rarity!r})>"


class GeneratorDef(Base):
    """
    Defines a generator configuration (e.g., shop, NPC loot, monster drops).
    """
    __tablename__ = "generators"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False, unique=True)   # e.g., "Shop-SmallTown"
    context = Column(String, nullable=False)             # e.g., "shop", "party", "monster"

    # Bounds and rules
    min_items = Column(Integer, nullable=True)
    max_items = Column(Integer, nullable=True)
    budget = Column(Integer, nullable=True)
    rarity_bias = Column(String, nullable=True)          # e.g., "Common+", "Rare+ only"

    # Relationships
    

    # --- Inventory & InventoryItem -------------------------------------------------
# Requires: from sqlalchemy import DateTime, func, UniqueConstraint

class InventoryItem(Base):
    """
    Join table (association object) between Inventory and Entry with extra fields.
    - quantity: how many of this Entry are in the inventory
    - unit_value: optional snapshot of Entry.value taken when added (can be None to use live Entry.value)
    """
    __tablename__ = "inventory_items"
    __table_args__ = (UniqueConstraint("inventory_id", "entry_id", name="uq_inventory_entry"),)

    id = Column(Integer, primary_key=True, autoincrement=True)

    inventory_id = Column(Integer, ForeignKey("inventories.id", ondelete="CASCADE"), index=True, nullable=False)
    entry_id = Column(Integer, ForeignKey("entries.id", ondelete="CASCADE"), index=True, nullable=False)

    quantity = Column(Integer, nullable=False, default=1)
    unit_value = Column(Integer, nullable=True)  # snapshot at add-time; if None, falls back to Entry.value

    # Relationships
    inventory = relationship("Inventory", back_populates="items")
    entry = relationship("Entry", back_populates="inventory_items")

    # --- Computed helpers (not persisted) ---
    @property
    def effective_unit_value(self) -> int:
        """
        The price used for totals:
        - If a snapshot (unit_value) exists, use it.
        - Otherwise, use the Entry.value (0 if missing).
        """
        return self.unit_value if self.unit_value is not None else int(self.entry.value or 0)

    @property
    def total_value(self) -> int:
        return self.quantity * self.effective_unit_value

    def __repr__(self) -> str:
        return f"<InventoryItem(inv_id={self.inventory_id}, entry_id={self.entry_id}, qty={self.quantity})>"


class Inventory(Base):
    """
    A collection of entries (e.g., shop stock, loot table result).
    """
    __tablename__ = "inventories"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False, index=True)        # e.g., "Barovia General Store – Sep 20"
    context = Column(String, nullable=True)                  # e.g., "shop", "loot", "npc"
    budget = Column(Integer, nullable=True)                  # optional planning budget
    created_at = Column(DateTime, server_default=func.now(), nullable=False)

    # Items in this inventory
    items = relationship(
        "InventoryItem",
        back_populates="inventory",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    # --- Helpers ---
    def add_entry(self, entry: "Entry", *, quantity: int = 1, unit_value: int | None = None) -> InventoryItem:
        """
        Append an Entry to this inventory with a quantity and optional unit value snapshot.
        If unit_value is None, the item's current Entry.value will be used for totals at read time.
        """
        ii = InventoryItem(entry=entry, quantity=quantity, unit_value=unit_value)
        self.items.append(ii)
        return ii

    @property
    def total_value(self) -> int:
        """
        Sum of item totals. Uses each item's effective_unit_value (snapshot or live).
        """
        return sum(ii.total_value for ii in self.items)

    def __repr__(self) -> str:
        return f"<Inventory(id={self.id}, name={self.name!r}, items={len(self.items)})>"


# --- Back-populate on Entry (where an item appears) ----------------------------
# If Entry is defined above, we can attach the reverse relationship here.
Entry.inventory_items = relationship(  # type: ignore[attr-defined]
    "InventoryItem",
    back_populates="entry",
    cascade="all, delete-orphan",
    passive_deletes=True,
)

