# tests/test_csv_parser.py
import io
import csv
import pytest
from pathlib import Path
from townecodex.parsers.csv_parser import CSVParser
from townecodex.parsers.base import ParserError

def make_csv(tmp_path, content: str) -> Path:
    p = tmp_path / "test.csv"
    p.write_text(content, encoding="utf-8")
    return p

def test_basic_parse(tmp_path):
    content = """Name,Type,Rarity,Attunement,Link
Potion,Potion,Common,No,http://example.com
"""
    path = make_csv(tmp_path, content)
    rows = list(CSVParser().parse(path))
    assert len(rows) == 1
    row = rows[0]
    assert row["Name"] == "Potion"
    assert row["Attunement"] == "No"

def test_header_normalization(tmp_path):
    content = """item,category,rarity,requires attunement,source
Sword,Weapon,Uncommon,Yes,http://ex.com
"""
    path = make_csv(tmp_path, content)
    rows = list(CSVParser().parse(path))
    assert rows[0]["Name"] == "Sword"
    assert rows[0]["Type"] == "Weapon"
    assert rows[0]["Attunement"] == "Yes"

def test_missing_required_header(tmp_path):
    content = "Name,Type,Rarity\nSword,Weapon,Uncommon\n"
    path = make_csv(tmp_path, content)
    with pytest.raises(ParserError):
        list(CSVParser().parse(path))

def test_blank_and_comment_rows(tmp_path):
    content = """Name,Type,Rarity,Attunement,Link
#Comment,Potion,Common,No,link
,,,
Sword,Weapon,Uncommon,Yes,link
"""
    path = make_csv(tmp_path, content)
    rows = list(CSVParser().parse(path))
    assert len(rows) == 1
    assert rows[0]["Name"] == "Sword"

def test_missing_values_replaced(tmp_path):
    content = """Name,Type,Rarity,Attunement,Link
Potion,,,,
"""
    path = make_csv(tmp_path, content)
    rows = list(CSVParser().parse(path))
    row = rows[0]
    assert row["Type"] == "MISSING"
    assert row["Link"] == "MISSING"

def test_encoding_error(tmp_path):
    # write latin1 with non-utf8 char
    p = tmp_path / "bad.csv"
    p.write_bytes("Name,Type,Rarity,Attunement,Link\nCafé,Food,Common,No,link\n".encode("latin1"))
    parser = CSVParser()
    with pytest.raises(ParserError):
        list(parser.parse(p))

