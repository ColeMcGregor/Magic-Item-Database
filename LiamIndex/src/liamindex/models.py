from __future__ import annotations
from sqlalchemy import Column, Integer, String, Text, Boolean, ForeignKey
from sqlalchemy.orm import declarative_base, relationship

"""
These are data models for the LiamIndex database.
these are for the entries table and generators table

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
    image_path = Column(String, nullable=True)       # path to image file

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
    # Could later link to a Config or Inventory
