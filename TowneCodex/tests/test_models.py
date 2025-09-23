# tests/test_models.py
import os
import tempfile
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, clear_mappers

from townecodex.models import Base, Entry, GeneratorDef, Inventory, InventoryItem


@pytest.fixture(scope="function")
def session():
    """Provide a fresh file-based SQLite DB session for each test, cleanup after."""
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)

    engine = create_engine(f"sqlite:///{path}", echo=False, future=True)
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine, future=True)
    sess = Session()
    try:
        yield sess
    finally:
        sess.close()
        engine.dispose()
        if os.path.exists(path):
            os.remove(path)


def test_create_entry(session):
    e = Entry(name="Potion of Healing", type="Potion", rarity="Common", value=50)
    session.add(e)
    session.commit()

    db_entry = session.query(Entry).filter_by(name="Potion of Healing").one()
    assert db_entry.rarity == "Common"
    assert repr(db_entry).startswith("<Entry(")


def test_generatordef_unique_name(session):
    g1 = GeneratorDef(name="Shop-SmallTown", context="shop")
    session.add(g1)
    session.commit()

    g2 = GeneratorDef(name="Shop-SmallTown", context="shop")
    session.add(g2)
    with pytest.raises(Exception):  # uniqueness violation
        session.commit()


def test_inventory_add_entry_and_total(session):
    entry = Entry(name="Sword", type="Weapon", rarity="Uncommon", value=100)
    inv = Inventory(name="Blacksmith Shop")
    session.add_all([entry, inv])
    session.commit()

    inv.add_entry(entry, quantity=2)
    session.commit()

    refreshed = session.get(Inventory, inv.id)
    assert len(refreshed.items) == 1
    item = refreshed.items[0]
    assert item.total_value == 200
    assert refreshed.total_value == 200


def test_inventoryitem_effective_unit_value(session):
    entry1 = Entry(name="Shield", type="Armor", rarity="Rare", value=150)
    entry2 = Entry(name="Helmet", type="Armor", rarity="Uncommon", value=80)
    inv = Inventory(name="Guard Tower")
    session.add_all([entry1, entry2, inv])
    session.commit()

    # Use explicit snapshot
    ii1 = inv.add_entry(entry1, quantity=1, unit_value=120)
    # Use fallback Entry.value
    ii2 = inv.add_entry(entry2, quantity=3)

    session.commit()
    assert ii1.effective_unit_value == 120
    assert ii2.effective_unit_value == 80
    assert ii2.total_value == 240
