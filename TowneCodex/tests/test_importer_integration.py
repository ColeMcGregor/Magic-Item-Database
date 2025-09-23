import os
import tempfile
import pytest
from pathlib import Path

import townecodex.db as db
from townecodex.importer import import_file
from townecodex.models import Entry


@pytest.fixture(scope="function")
def temp_db(monkeypatch):
    # Make a temporary sqlite file
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)

    url = f"sqlite:///{path}"
    monkeypatch.setattr(db, "DATABASE_URL", url)
    db.engine = db.create_engine(url, echo=False, future=True)
    db.SessionLocal.configure(bind=db.engine)

    db.init_db()
    yield path

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
    # Prepare a minimal CSV
    content = (
        "Name,Type,Rarity,Attunement,Link\n"
        "Potion of Healing,Potion,Common,No,http://example.com/potion\n"
        "Sword,Weapon,Uncommon,Yes - Str 15,http://example.com/sword\n"
    )
    path = make_csv(tmp_path, content)

    count = import_file(path)
    assert count == 2

    # Verify in DB
    session = db.SessionLocal()
    entries = session.query(Entry).all()
    names = {e.name for e in entries}
    assert names == {"Potion of Healing", "Sword"}
    sword = next(e for e in entries if e.name == "Sword")
    assert sword.attunement_required is True
    assert sword.attunement_criteria == "Str 15"
    session.close()
