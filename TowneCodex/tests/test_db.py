# tests/test_db.py
import os
import tempfile

import pytest
from sqlalchemy import inspect

import townecodex.db as db
from townecodex.models import Entry


@pytest.fixture(scope="function")
def temp_db(monkeypatch):
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)

    url = f"sqlite:///{path}"
    monkeypatch.setattr(db, "DATABASE_URL", url)
    db.engine = db.create_engine(url, echo=False, future=True)
    db.SessionLocal.configure(bind=db.engine)

    yield path

    # Cleanup: close engine/connection pool first
    db.engine.dispose()
    try:
        os.remove(path)
    except FileNotFoundError:
        pass



def test_init_db_creates_tables(temp_db):
    # run the init
    db.init_db()

    inspector = inspect(db.engine)
    tables = inspector.get_table_names()
    assert "entries" in tables
    assert "generators" in tables
    assert "inventories" in tables
    assert "inventory_items" in tables


def test_sessionlocal_add_and_query(temp_db):
    db.init_db()

    # use SessionLocal
    session = db.SessionLocal()
    e = Entry(name="Test Potion", type="Potion", rarity="Common", value=42)
    session.add(e)
    session.commit()

    found = session.query(Entry).filter_by(name="Test Potion").one()
    assert found.value == 42
    assert found.rarity == "Common"

    session.close()
