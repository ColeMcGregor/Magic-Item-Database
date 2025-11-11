# tests/test_importer.py
import os
import tempfile
import pytest
from pathlib import Path
from sqlalchemy import select

import townecodex.db as db
from townecodex.importer import import_file
from townecodex.models import Entry


# in tests/test_importer_integration.py

@pytest.fixture(scope="function")
def temp_db(monkeypatch):
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)

    url = f"sqlite:///{path}"
    monkeypatch.setattr(db, "DATABASE_URL", url, raising=True)
    db.engine = db.create_engine(url, echo=False, future=True)
    db.SessionLocal.configure(bind=db.engine)

    db.init_db()
    yield path

    # ensure all sessions are closed before removing the sqlite file
    try:
        from sqlalchemy.orm import close_all_sessions
        close_all_sessions()
    except Exception:
        pass

    db.engine.dispose()
    try:
        os.remove(path)
    except FileNotFoundError:
        pass



def make_csv(tmp_path: Path, content: str) -> Path:
    p = tmp_path / "items.csv"
    p.write_text(content, encoding="utf-8")
    return p


def test_import_file_basic(tmp_path, temp_db):
    # Prepare a minimal CSV (no scraping)
    content = (
        "Name,Type,Rarity,Attunement,Link\n"
        "Potion of Healing,Potion,Common,No,http://example.com/potion\n"
        "Sword,Weapon,Uncommon,Yes - Str 15,http://example.com/sword\n"
    )
    path = make_csv(tmp_path, content)

    count = import_file(path, scrape=False)
    assert count == 2

    # Verify in DB
    session = db.SessionLocal()
    entries = list(session.execute(select(Entry)).scalars().all())
    names = {e.name for e in entries}
    assert names == {"Potion of Healing", "Sword"}

    sword = next(e for e in entries if e.name == "Sword")
    assert sword.attunement_required is True
    assert sword.attunement_criteria == "Str 15"
    session.close()


def test_import_scrape_fills_attunement_when_csv_blank(tmp_path, temp_db, monkeypatch):
    # CSV has blank Attunement; scraper provides normalized string
    content = (
        "Name,Type,Rarity,Attunement,Link\n"
        "Relentless Bulwark,Armor (shield),, ,https://reddit.example/bulwark\n"
    )
    path = make_csv(tmp_path, content)

    # Fake scraper response to avoid network
    class FakeScraper:
        @classmethod
        def fetch_post_data(cls, url: str):
            return {
                "title": "Relentless Bulwark | Armor (shield)",
                "rarity": "Uncommon",
                "attunement": "Requires Attunement (Cleric or Paladin)",
                "description": "Body...",
                "image_url": "https://img.example/b.png",
            }

    import townecodex.importer as importer_mod
    monkeypatch.setattr(importer_mod, "RedditScraper", FakeScraper, raising=True)

    count = import_file(path, scrape=True)
    assert count == 1

    session = db.SessionLocal()
    try:
        (e,) = list(session.execute(select(Entry)).scalars().all())
        assert e.name.startswith("Relentless Bulwark")
        assert e.rarity == "Uncommon"
        assert e.attunement_required is True
        assert e.attunement_criteria == "Cleric or Paladin"
    finally:
        session.close()


def test_import_default_image_applied_when_missing(tmp_path, temp_db, monkeypatch):
    # No image from scraper, default_image should be used
    content = (
        "Name,Type,Rarity,Attunement,Link\n"
        "Hat of Osnomnosis,Wondrous Item,Common,,https://reddit.example/hat\n"
    )
    path = make_csv(tmp_path, content)

    class FakeScraperNoImage:
        @classmethod
        def fetch_post_data(cls, url: str):
            return {
                "title": "Hat of Osnomnosis | Wondrous item",
                "rarity": "Common",
                "attunement": "Requires Attunement (Wizard)",
                "description": "Body...",
                "image_url": None,
            }

    import townecodex.importer as importer_mod
    monkeypatch.setattr(importer_mod, "RedditScraper", FakeScraperNoImage, raising=True)

    default_img = "https://static.example/default.png"
    count = import_file(path, scrape=True, default_image=default_img)
    assert count == 1

    session = db.SessionLocal()
    (e,) = list(session.execute(select(Entry)).scalars().all())
    assert e.image_url == default_img
    session.close()
