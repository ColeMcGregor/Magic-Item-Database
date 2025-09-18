"""
CSV parser for LiamIndex.

Reads a CSV with columns:
  Name, Type, Rarity, Attunement, Link

- Validates required headers (with a few common aliases).
- Trims whitespace.
- Fills any missing/empty expected fields with a sentinel token (default: "MISSING").
- Ignores blank/comment-only rows.
- Yields RawRow dictionaries, these must be parsed further to separate attunemnet from criteria.

author: Cole McGregor, ChatGPT
date: 2025-09-16
version: 0.1.0

can change missing token to any string, but it MUST be a string that is not a valid value for any of the fields.

Usage:
    parser = CSVParser(missing_token="MISSING")
    for row in parser.parse("items.csv"):
        ...
"""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Iterable

from .base import RawRow, ParserStrategy, ParserError

# Header normalization map (supports some common variants)
HEADER_ALIASES = {
    "name": "Name",
    "item": "Name",
    "item name": "Name",

    "type": "Type",
    "category": "Type",

    "rarity": "Rarity",

    "attunement": "Attunement",
    "requires attunement": "Attunement",

    "link": "Link",
    "source": "Link",
    "sourcelink": "Link",
    "url": "Link",
}
# REQUIRED_HEADERS is used to check if the csv file has the required headers.
REQUIRED_HEADERS = ["Name", "Type", "Rarity", "Attunement", "Link"]

# _normalize_header is used to normalize the header of the csv file.
def _normalize_header(h: str) -> str:
    key = (h or "").strip().lower()
    return HEADER_ALIASES.get(key, None) or (h or "").strip()

# _trim is used to trim the value of the cell.
def _trim(v) -> str:
    return "" if v is None else str(v).strip()


class CSVParser(ParserStrategy):
    # init is used as a constructor for the parser, it is used to set the missing token.
    def __init__(self, *, missing_token: str = "MISSING"):
        self.missing_token = missing_token

    # name is used to return the name of the parser.
    def name(self) -> str:
        return "CSVParser"

    # parse is used to parse the csv file.
    # it is used to parse the csv file and return a list of RawRow dictionaries.
    # takes in a path to the csv file.
    def parse(self, path: str | Path) -> Iterable[RawRow]:
        # p is used to get the path to the csv file.
        p = Path(path)
        # if the path does not exist, raise a ParserError.
        if not p.exists():
            raise ParserError(f"CSV file not found: {p}")

        # try to parse the csv file.
        try:
            # open the csv file.
            with p.open("r", encoding="utf-8-sig", newline="") as f:
                # create a csv reader., a dictreader is from the csv module.
                reader = csv.DictReader(f)
                # if the csv file has no header row, raise a ParserError.
                if reader.fieldnames is None:
                    raise ParserError("CSV has no header row.")

                # Normalize headers
                normalized_fields = [_normalize_header(h) for h in reader.fieldnames]
                header_map = {orig: norm for orig, norm in zip(reader.fieldnames, normalized_fields)}

                # Validate required headers exist (after normalization)
                normalized_set = set(header_map.values())
                missing = [h for h in REQUIRED_HEADERS if h not in normalized_set]
                if missing:
                    raise ParserError(f"CSV missing required columns: {', '.join(missing)}")

                for raw in reader:
                    # Skip completely blank rows or comment rows (first cell starts with '#')
                    if not raw or all((_trim(v) == "" for v in raw.values())):
                        continue
                    first_val = next(iter(raw.values()))
                    # Skip comment rows
                    if isinstance(first_val, str) and first_val.strip().startswith("#"):
                        continue

                    # Remap and trim
                    row: dict[str, str] = {}
                    for orig_key, val in raw.items():
                        norm_key = header_map.get(orig_key, orig_key)
                        row[norm_key] = _trim(val)

                    # Enforce sentinel for each expected field
                    def get_or_missing(key: str) -> str:
                        v = row.get(key, "")
                        return v if v != "" else self.missing_token

                    yield RawRow(
                        Name=get_or_missing("Name"),
                        Type=get_or_missing("Type"),
                        Rarity=get_or_missing("Rarity"),
                        Attunement=get_or_missing("Attunement"),
                        Link=get_or_missing("Link"),
                    )
        except UnicodeDecodeError as e:
            raise ParserError(f"CSV encoding error (expected UTF-8): {e}") from e
        except csv.Error as e:
            raise ParserError(f"CSV parsing error: {e}") from e
