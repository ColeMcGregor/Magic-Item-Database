# tests/test_repos.py
from __future__ import annotations

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from townecodex.models import Base, Entry, GeneratorDef
from townecodex.repos import EntryRepository, EntryFilters, GeneratorRepository


# ----------------------------
# Test DB session_factory fixture
# ----------------------------
@pytest.fixture(scope="module")
def session_factory():
    """
    In-memory SQLite for repo tests.
    """
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    Base.metadata.create_all(engine)
    SessionFactory = sessionmaker(
        bind=engine,
        autoflush=False,
        autocommit=False,
        future=True,
        expire_on_commit=False,   # <-- crucial: keep instances usable after commit
    )
    yield SessionFactory
    Base.metadata.drop_all(engine)
    engine.dispose()


# ----------------------------
# EntryRepository tests
# ----------------------------

def test_upsert_insert_and_fetch_by_link(session_factory):
    repo = EntryRepository(session_factory=session_factory)

    # Create via upsert with source_link
    created = repo.upsert_entry({
        "name": "Relentless Bulwark",
        "type": "Armor (shield)",
        "rarity": "Uncommon",
        "attunement_required": True,
        "attunement_criteria": "Cleric or Paladin",
        "source_link": "https://reddit.com/r/x/bulwark",
        "description": "Initial description",
        "image_url": "https://img.example/bulwark.png",
        "value": 500,
        "value_updated": False,
    })
    assert isinstance(created, Entry)
    assert created.id is not None
    assert created.name == "Relentless Bulwark"
    assert created.attunement_required is True
    assert created.attunement_criteria == "Cleric or Paladin"

    # Fetch by link
    fetched = repo.get_by_source_link(" https://reddit.com/r/x/bulwark ")
    assert fetched and fetched.id == created.id

    # Update via upsert; empty strings must NOT clobber, fields should trim
    updated = repo.upsert_entry({
        "source_link": "https://reddit.com/r/x/bulwark",
        "name": "  Relentless Bulwark  ",   # trimmed
        "description": "Updated description",
        "image_url": "",                     # empty → ignored; keeps previous
        "value": 750,
        "value_updated": True,
    })
    assert updated.id == created.id
    assert updated.name == "Relentless Bulwark"
    assert updated.description == "Updated description"
    assert updated.image_url == "https://img.example/bulwark.png"
    assert updated.value == 750
    assert updated.value_updated is True


def test_upsert_without_link_matches_unique_name_type(session_factory):
    repo = EntryRepository(session_factory=session_factory)

    # Insert without source_link
    e1 = repo.upsert_entry({
        "name": "Blade of the Moor",
        "type": "Weapon (longsword)",
        "rarity": "Rare",
        "attunement_required": False,
        "description": "v1",
    })

    # Upsert with same (name,type) should update the single match
    e2 = repo.upsert_entry({
        "name": "Blade of the Moor",
        "type": "Weapon (longsword)",
        "description": "v2",
        "value": 2500,
    })
    assert e1.id == e2.id
    assert e2.description == "v2"
    assert e2.value == 2500


def test_bulk_upsert_counts(session_factory):
    repo = EntryRepository(session_factory=session_factory)

    created, updated = repo.bulk_upsert([
        {
            "name": "Hat of Osnomnosis",
            "type": "Wondrous Item",
            "rarity": "Common",
            "attunement_required": True,
            "attunement_criteria": "Wizard",
            "source_link": "https://reddit.com/r/x/osnomnosis",
        },
        {
            # same link → should update, not create
            "name": "Hat of Osnomnosis",
            "type": "Wondrous Item",
            "description": "With updated description",
            "source_link": "https://reddit.com/r/x/osnomnosis",
        },
        {
            # no link, unique (name,type) → create
            "name": "Sun and Moon Shield",
            "type": "Armor (shield)",
            "rarity": "Common",
        },
    ])
    # One new for hat, then update hat, and one new for shield → (2 created, 1 updated)
    assert created == 2
    assert updated == 1

    # Verify persisted values
    hat = repo.get_by_source_link("https://reddit.com/r/x/osnomnosis")
    assert hat and hat.description == "With updated description"


def test_search_and_search_with_total(session_factory):
    repo = EntryRepository(session_factory=session_factory)

    # Seed a few rows
    repo.bulk_upsert([
        {"name": "Amulet of Wind", "type": "Wondrous Item", "rarity": "Uncommon", "description": "Breeze"},
        {"name": "Cloak of Stillness", "type": "Wondrous Item", "rarity": "Common", "description": "Quiet"},
        {"name": "Bloodmage Dagger", "type": "Weapon (dagger)", "rarity": "Very Rare", "description": "Arcane"},
    ])

    # Basic search by name substring
    out = repo.search(EntryFilters(name_contains="of"))
    names = {e.name for e in out}
    assert "Amulet of Wind" in names and "Cloak of Stillness" in names

    # Filter by type (case-insensitive)
    out2, total2 = repo.search_with_total(
        EntryFilters(type_equals="wondrous item"),
        page=1, size=10, sort="name"
    )
    assert total2 >= 2
    assert all("Wondrous" in e.type for e in out2)

    # Rarity filter
    out3 = repo.search(EntryFilters(rarity_in=["Common", "Uncommon"]))
    assert {e.rarity for e in out3}.issubset({"Common", "Uncommon"})

    # Text search hits description as well
    out4 = repo.search(EntryFilters(text="Arcane"))
    assert len(out4) == 1 and out4[0].name == "Bloodmage Dagger"


def test_update_price_sets_flag(session_factory):
    repo = EntryRepository(session_factory=session_factory)
    e = repo.upsert_entry({
        "name": "Bath Potion",
        "type": "Potion",
        "rarity": "Common",
        "value": 100,
        "value_updated": False,
    })
    repo.update_price(e.id, 125)
    updated = repo.get_by_id(e.id)
    assert updated and updated.value == 125 and updated.value_updated is True


def test_delete_and_clear_all_entries(session_factory):
    repo = EntryRepository(session_factory=session_factory)

    a = repo.upsert_entry({"name": "A", "type": "Wondrous Item", "rarity": "Common"})
    b = repo.upsert_entry({"name": "B", "type": "Wondrous Item", "rarity": "Common"})

    assert repo.delete_by_id(a.id) is True
    assert repo.get_by_id(a.id) is None
    # Clear remaining
    removed = repo.clear_all_entries()
    assert removed >= 1
    assert repo.list() == []


# ----------------------------
# GeneratorRepository tests
# ----------------------------

def test_generator_repo_crud(session_factory):
    grepo = GeneratorRepository(session_factory=session_factory)

    g = GeneratorDef(name="Shop: Northgate", context="Blacksmith", min_items=3, max_items=6, budget=10000)
    saved = grepo.insert(g)
    assert saved.id is not None

    fetched = grepo.get_by_id(saved.id)
    assert fetched and fetched.name == "Shop: Northgate"

    items = grepo.list_all()
    assert any(x.id == saved.id for x in items)

    assert grepo.delete_by_id(saved.id) is True
    assert grepo.get_by_id(saved.id) is None
