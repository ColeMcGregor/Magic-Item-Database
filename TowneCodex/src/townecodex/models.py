from __future__ import annotations
from sqlalchemy import String, Text, Boolean, ForeignKey, DateTime, func, UniqueConstraint, Integer
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

"""
These are data models for the Towne Codex database.
they are for the tables in the database.
they include:

- Entry
- GeneratorDef
- Inventory
- InventoryItem

author: Cole McGregor
date: 2025-09-17
version: 0.1.0
"""


# Declarative base for SQLAlchemy 2.x
class Base(DeclarativeBase):
    pass


class Entry(Base):
    """
    Represents an item/entry (e.g., potion, weapon, armor).
    Parsed from fed files elsewhere
    """
    __tablename__ = "entries"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    # Core fields
    name: Mapped[str] = mapped_column(String, nullable=False, index=True)
    type: Mapped[str] = mapped_column(String, nullable=False)
    rarity: Mapped[str] = mapped_column(String, nullable=False)
    value: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Attunement
    attunement_required: Mapped[bool] = mapped_column(Boolean, default=False)
    attunement_criteria: Mapped[str | None] = mapped_column(String, nullable=True)

    # Links & description
    source_link: Mapped[str | None] = mapped_column(String, nullable=True, unique=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    image_url: Mapped[str | None] = mapped_column(String, nullable=True)

    # Flags
    value_updated: Mapped[bool] = mapped_column(Boolean, default=False)

    # Relationships
    inventory_items: Mapped[list["InventoryItem"]] = relationship(
        back_populates="entry",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    def __repr__(self) -> str:
        return f"<Entry(id={self.id}, name={self.name!r}, rarity={self.rarity!r})>"


class GeneratorDef(Base):
    """
    Defines a generator configuration (e.g., shop, NPC loot, monster drops).
    """
    __tablename__ = "generators"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String, nullable=False, unique=True)
    context: Mapped[str] = mapped_column(String, nullable=False)

    # Bounds and rules
    min_items: Mapped[int | None] = mapped_column(Integer, nullable=True)
    max_items: Mapped[int | None] = mapped_column(Integer, nullable=True)
    budget: Mapped[int | None] = mapped_column(Integer, nullable=True)
    rarity_bias: Mapped[str | None] = mapped_column(String, nullable=True)


class InventoryItem(Base):
    """
    Join table (association object) between Inventory and Entry with extra fields.
    """
    __tablename__ = "inventory_items"
    __table_args__ = (UniqueConstraint("inventory_id", "entry_id", name="uq_inventory_entry"),)

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    inventory_id: Mapped[int] = mapped_column(ForeignKey("inventories.id", ondelete="CASCADE"), index=True, nullable=False)
    entry_id: Mapped[int] = mapped_column(ForeignKey("entries.id", ondelete="CASCADE"), index=True, nullable=False)

    quantity: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    unit_value: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Relationships
    inventory: Mapped["Inventory"] = relationship(back_populates="items")
    entry: Mapped["Entry"] = relationship(back_populates="inventory_items")

    # Computed helpers
    @property
    def effective_unit_value(self) -> int:
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

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String, nullable=False, index=True)
    context: Mapped[str | None] = mapped_column(String, nullable=True)
    budget: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[str] = mapped_column(DateTime, server_default=func.now(), nullable=False)

    # Relationships
    items: Mapped[list["InventoryItem"]] = relationship(
        back_populates="inventory",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    def add_entry(self, entry: "Entry", *, quantity: int = 1, unit_value: int | None = None) -> InventoryItem:
        ii = InventoryItem(entry=entry, quantity=quantity, unit_value=unit_value)
        self.items.append(ii)
        return ii

    @property
    def total_value(self) -> int:
        return sum(ii.total_value for ii in self.items)

    def __repr__(self) -> str:
        return f"<Inventory(id={self.id}, name={self.name!r}, items={len(self.items)})>"
