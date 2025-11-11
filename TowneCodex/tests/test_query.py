# tests/test_query_service.py
from __future__ import annotations

import os
import tempfile
from pathlib import Path

import pytest
from sqlalchemy import select

import townecodex.db as db
from townecodex.repos import EntryRepository
from townecodex.query import QueryService
from townecodex.models import Entry


# --- Temp DB fixture (isolated per test) --------------------------------------
@pytest.fixture(scope="function")
def temp_db(monkeypatch):
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    url = f"sqlite:///{path}"

    # Rebind module-level engine/session to this temp DB
    monkeypatch.setattr(db, "DATABASE_URL", url, raising=True)
    db.engine = db.create_engine(url, echo=False, future=True)
    db.SessionLocal.configure(bind=db.engine)

    db.init_db()
    yield path

    # Teardown: close sessions, dispose engine, remove file
    try:
        # SQLAlchemy deprecation suggests using close_all_sessions()
        from sqlalchemy.orm import close_all_sessions
        close_all_sessions()
    except Exception:
        pass

    db.engine.dispose()
    try:
        os.remove(path)
    except FileNotFoundError:
        pass


# --- Helpers ------------------------------------------------------------------
def seed(repo: EntryRepository):
    """Seed a small set of entries with varied fields."""
    repo.bulk_upsert(
        [
            {
                "name": "Potion of Healing",
                "type": "Potion",
                "rarity": "Common",
                "description": "Restores hit points",
                "attunement_required": False,
                "source_link": "https://example/items/potion-healing",
                "value": 50,
                "value_updated": False,
            },
            {
                "name": "Cloak of Stillness",
                "type": "Wondrous Item",
                "rarity": "Uncommon",
                "description": "Quiet as night",
                "attunement_required": True,
                "attunement_criteria": "Rogue",
                "source_link": "https://example/items/cloak-stillness",
                "value": 200,
                "value_updated": True,
            },
            {
                "name": "Bloodmage Dagger",
                "type": "Weapon (dagger)",
                "rarity": "Very Rare",
                "description": "Arcane rituals and blood",
                "attunement_required": True,
                "attunement_criteria": "Spellcaster",
                "source_link": "https://example/items/bloodmage-dagger",
                "value": 5000,
                "value_updated": False,
            },
            {
                "name": "Sun and Moon Shield",
                "type": "Armor (shield)",
                "rarity": "Common",
                "description": "Radiant and lunar motifs",
                "attunement_required": False,
                "source_link": "https://example/items/sun-moon-shield",
                "value": 150,
                "value_updated": False,
            },
        ]
    )


# --- Tests --------------------------------------------------------------------

def test_search_basic_filters(temp_db):
    repo = EntryRepository()
    seed(repo)

    svc = QueryService(repo)

    # name_contains
    out = svc.search(name_contains="of")
    titles = {c.title for c in out}
    assert "Potion of Healing" in titles
    assert "Cloak of Stillness" in titles
    # should not inadvertently filter out others unless "of" present
    assert "Sun and Moon Shield" not in titles

    # type_equals (case-insensitive match is implemented in repo)
    out2 = svc.search(type_equals="wondrous item")
    assert [c.title for c in out2] == ["Cloak of Stillness"]

    # rarity_in
    out3 = svc.search(rarity_in=["Common", "Uncommon"])
    got = {c.title for c in out3}
    assert got == {"Potion of Healing", "Cloak of Stillness", "Sun and Moon Shield"}

    # attunement_required
    out4 = svc.search(attunement_required=True)
    assert {c.title for c in out4} == {"Cloak of Stillness", "Bloodmage Dagger"}

    # text search (name or description)
    out5 = svc.search(text="arcane")
    assert [c.title for c in out5] == ["Bloodmage Dagger"]


def test_pagination_and_sort(temp_db):
    repo = EntryRepository()
    seed(repo)
    svc = QueryService(repo)

    # Sort by name ascending, page size 2 -> page 1
    pg1 = svc.search(sort="name", page=1, size=2)
    assert [c.title for c in pg1] == ["Bloodmage Dagger", "Cloak of Stillness"]

    # Page 2
    pg2 = svc.search(sort="name", page=2, size=2)
    assert [c.title for c in pg2] == ["Potion of Healing", "Sun and Moon Shield"]

    # Desc by name, first page of size 3
    pgd = svc.search(sort="-name", page=1, size=3)
    assert [c.title for c in pgd] == ["Sun and Moon Shield", "Potion of Healing", "Cloak of Stillness"]


def test_get_entry_card(temp_db):
    repo = EntryRepository()
    seed(repo)
    svc = QueryService(repo)

    # Fetch the id of a known row to test detail path
    session = db.SessionLocal()
    try:
        row = session.execute(
            select(Entry).where(Entry.source_link == "https://example/items/bloodmage-dagger")
        ).scalar_one()
        entry_id = row.id
    finally:
        session.close()

    card = svc.get_entry_card(entry_id)
    assert card is not None
    assert card.id == entry_id
    assert card.title == "Bloodmage Dagger"
    assert card.type == "Weapon (dagger)"
    assert card.rarity == "Very Rare"
    assert card.attunement_required is True
    assert card.attunement_criteria == "Spellcaster"
    assert card.value == 5000
    # Pass-through of raw/markdown/plain description and URL only image_url
    assert isinstance(card.description, str) and "Arcane" in card.description
