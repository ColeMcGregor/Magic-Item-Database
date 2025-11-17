from __future__ import annotations

from datetime import datetime

from sqlalchemy import (
    String,
    Text,
    Boolean,
    ForeignKey,
    DateTime,
    func,
    UniqueConstraint,
    Integer,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

"""
These are data models for the Towne Codex database.
They are for the tables in the database.
They include:

- Entry
- GeneratorDef
- Inventory
- InventoryItem

author: Cole McGregor
date: 2025-11-13
version: 0.2.0
"""


# ---------------------------------------------------------------------------
# Base
# ---------------------------------------------------------------------------

class Base(DeclarativeBase):
    pass


# ---------------------------------------------------------------------------
# Entry
# ---------------------------------------------------------------------------

class Entry(Base):
    """
    Represents an item/entry (e.g., potion, weapon, armor).
    Parsed from fed files elsewhere.
    """
    __tablename__ = "entries"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    # Core fields
    name: Mapped[str] = mapped_column(String, nullable=False, index=True)
    type: Mapped[str] = mapped_column(String, nullable=False)
    rarity: Mapped[str] = mapped_column(String, nullable=False)
    value: Mapped[int | None] = mapped_column(Integer, nullable=True)

    #type information for filtering queries
    general_type: Mapped[str | None] = mapped_column(String, nullable=True, index=True)
    specific_type_tags_json: Mapped[str | None] = mapped_column(Text, nullable=True)

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


# ---------------------------------------------------------------------------
# GeneratorDef
# ---------------------------------------------------------------------------

class GeneratorDef(Base):
    """
    Defines a generator configuration (e.g., shop, NPC loot, monster drops).

    The detailed rules (globals + buckets) are stored as JSON in `config_json`,
    interpreted by the generator engine.
    """
    __tablename__ = "generators"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    # Human-facing identity
    name: Mapped[str] = mapped_column(String, nullable=False, unique=True, index=True)
    context: Mapped[str | None] = mapped_column(
        String,
        nullable=True,
        doc="Optional context hint, e.g. 'shop', 'npc', 'boss_loot'.",
    )
    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        doc="Optional DM-facing notes about this generator.",
    )

    # Serialized configuration (JSON text)
    config_json: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        doc="JSON-encoded GeneratorConfig (globals + buckets).",
    )

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    def __repr__(self) -> str:
        return f"<GeneratorDef(id={self.id}, name={self.name!r})>"


# ---------------------------------------------------------------------------
# InventoryItem
# ---------------------------------------------------------------------------

class InventoryItem(Base):
    """
    Join table (association object) between Inventory and Entry with extra fields.
    """
    __tablename__ = "inventory_items"
    __table_args__ = (
        UniqueConstraint("inventory_id", "entry_id", name="uq_inventory_entry"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    inventory_id: Mapped[int] = mapped_column(
        ForeignKey("inventories.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    entry_id: Mapped[int] = mapped_column(
        ForeignKey("entries.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )

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
        return (
            f"<InventoryItem(inv_id={self.inventory_id}, "
            f"entry_id={self.entry_id}, qty={self.quantity})>"
        )


# ---------------------------------------------------------------------------
# Inventory
# ---------------------------------------------------------------------------

class Inventory(Base):
    """
    A collection of entries (e.g., shop stock, loot table result).
    """
    __tablename__ = "inventories"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String, nullable=False, index=True)
    context: Mapped[str | None] = mapped_column(String, nullable=True)
    budget: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.now(),
        nullable=False,
    )

    # Relationships
    items: Mapped[list["InventoryItem"]] = relationship(
        back_populates="inventory",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    def add_entry(
        self,
        entry: Entry,
        *,
        quantity: int = 1,
        unit_value: int | None = None,
    ) -> InventoryItem:
        ii = InventoryItem(entry=entry, quantity=quantity, unit_value=unit_value)
        self.items.append(ii)
        return ii

    @property
    def total_value(self) -> int:
        return sum(ii.total_value for ii in self.items)

    def __repr__(self) -> str:
        return f"<Inventory(id={self.id}, name={self.name!r}, items={len(self.items)})>"

# ---------------------------------------------------------------------------
# Type Catalog (for filters)
# ---------------------------------------------------------------------------

class GeneralType(Base):
    """
    Catalog of all general item types observed in the data:
    e.g. 'Armor', 'Weapon', 'Potion', etc.
    """
    __tablename__ = "general_types"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String, unique=True, nullable=False, index=True)

    specific_types: Mapped[list["SpecificType"]] = relationship(
        back_populates="general_type",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<GeneralType(id={self.id}, name={self.name!r})>"


class SpecificType(Base):
    """
    Catalog of specific type tags under each GeneralType:
    e.g. ('Armor', 'Leather'), ('Weapon', 'Greataxe'), ('Weapon', 'Special')
    """
    __tablename__ = "specific_types"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String, nullable=False, index=True)

    general_type_id: Mapped[int] = mapped_column(
        ForeignKey("general_types.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    general_type: Mapped["GeneralType"] = relationship(back_populates="specific_types")

    __table_args__ = (
        UniqueConstraint("general_type_id", "name", name="uq_specific_per_general"),
    )

    def __repr__(self) -> str:
        return f"<SpecificType(id={self.id}, general={self.general_type_id}, name={self.name!r})>"

