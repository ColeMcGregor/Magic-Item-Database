# tests/test_cli.py
from __future__ import annotations

import os
import tempfile
from pathlib import Path

import pytest
from sqlalchemy import select

import townecodex.db as db
from townecodex.ui.cli import main
from townecodex.repos import EntryRepository
from townecodex.models import Entry


# ---------- test DB fixture ----------

@pytest.fixture(scope="function")
def temp_db(monkeypatch):
    # Create a temp sqlite file-backed DB (works on Windows)
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)

    url = f"sqlite:///{path}"
    # Rebind module-level engine/session to this DB
    monkeypatch.setattr(db, "DATABASE_URL", url, raising=True)
    db.engine = db.create_engine(url, echo=False, future=True)
    db.SessionLocal.configure(bind=db.engine)
    db.init_db()

    yield path

    # Teardown: close and delete the file
    try:
        # close all pooled connections to avoid Windows file lock
        db.engine.dispose()
    finally:
        try:
            os.remove(path)
        except FileNotFoundError:
            pass


# ---------- helpers ----------

def make_csv(tmp_path: Path, content: str) -> Path:
    p = tmp_path / "items.csv"
    p.write_text(content, encoding="utf-8")
    return p


def seed_entries(repo: EntryRepository) -> list[int]:
    ids = []
    for data in [
        {
            "name": "Hat of Osnomnosis",
            "type": "Wondrous Item",
            "rarity": "Common",
            "source_link": "https://example/items/hat",
            "description": "Wizard hat",
        },
        {
            "name": "Bloodmage Dagger",
            "type": "Weapon (dagger)",
            "rarity": "Very Rare",
            "source_link": "https://example/items/bloodmage-dagger",
            "description": "Arcane blade",
        },
        {
            "name": "Sun and Moon Shield",
            "type": "Armor (shield)",
            "rarity": "Common",
            "source_link": "https://example/items/sun-moon",
            "description": "Radiant shield",
        },
    ]:
        ids.append(repo.upsert_entry(data).id)  # noqa: SLF001
    return ids


# ---------- tests ----------

def test_import_file_command(tmp_path, temp_db, capsys):
    content = (
        "Name,Type,Rarity,Attunement,Link\n"
        "Potion of Healing,Potion,Common,No,http://example.com/potion\n"
        "Sword,Weapon,Uncommon,Yes - Str 15,http://example.com/sword\n"
    )
    csv_path = make_csv(tmp_path, content)

    rc = main(["import-file", str(csv_path)])
    assert rc == 0

    # Check stdout and DB
    out = capsys.readouterr().out
    assert "Imported 2" in out

    session = db.SessionLocal()
    try:
        rows = list(session.execute(select(Entry)).scalars().all())
        assert len(rows) == 2
        names = {e.name for e in rows}
        assert names == {"Potion of Healing", "Sword"}
    finally:
        session.close()


def test_list_and_show_commands(temp_db, capsys):
    repo = EntryRepository()
    ids = seed_entries(repo)

    # list
    rc = main(["list", "--page", "1", "--size", "10", "--sort", "name"])
    assert rc == 0
    out = capsys.readouterr().out
    # Expect at least one seeded item visible
    assert "Hat of Osnomnosis" in out
    assert "Bloodmage Dagger" in out

    # show (text to stdout)
    rc = main(["show", str(ids[0])])
    assert rc == 0
    out = capsys.readouterr().out
    assert f"[{ids[0]}]" in out
    assert "Type:" in out
    assert "Rarity:" in out

    # show (HTML to file)
    html_out = Path(tempfile.gettempdir()) / "townecodex_show_test.html"
    try:
        if html_out.exists():
            html_out.unlink()
        rc = main(["show", str(ids[0]), "--out", str(html_out), "--title", "One Item"])
        assert rc == 0
        assert html_out.exists()
        text = html_out.read_text(encoding="utf-8")
        assert "<!DOCTYPE html" in text or "<html" in text
        assert "One Item" in text
    finally:
        try:
            html_out.unlink()
        except FileNotFoundError:
            pass


def test_export_command(temp_db):
    repo = EntryRepository()
    seed_entries(repo)

    out_file = Path(tempfile.gettempdir()) / "townecodex_export_test.html"
    try:
        if out_file.exists():
            out_file.unlink()

        rc = main([
            "export",
            "--out", str(out_file),
            "--title", "All Items",
            "--limit", "10",
            "--sort", "name",
        ])
        assert rc == 0
        assert out_file.exists()
        text = out_file.read_text(encoding="utf-8")
        assert "All Items" in text
        # Expect at least one known title rendered
        assert "Hat of Osnomnosis" in text or "Bloodmage Dagger" in text
    finally:
        try:
            out_file.unlink()
        except FileNotFoundError:
            pass


def test_update_price_and_search_commands(temp_db, capsys):
    repo = EntryRepository()
    ids = seed_entries(repo)

    # update-price
    rc = main(["update-price", str(ids[1]), "1234"])
    assert rc == 0

    # Verify DB state changed
    session = db.SessionLocal()
    try:
        e = session.get(Entry, ids[1])
        assert e.value == 1234
        assert e.value_updated is True
    finally:
        session.close()

    # search by name substring and text
    rc = main(["search", "--name-contains", "Dagger", "--page", "1", "--size", "10"])
    assert rc == 0
    out = capsys.readouterr().out
    assert "Bloodmage Dagger" in out

    rc = main(["search", "--text", "Arcane", "--page", "1", "--size", "10"])
    assert rc == 0
    out = capsys.readouterr().out
    # Should print a result row containing the blade
    assert "Bloodmage Dagger" in out
