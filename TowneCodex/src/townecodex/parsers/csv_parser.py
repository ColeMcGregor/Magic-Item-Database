"""
CSV parser for Towne Codex.

Reads a CSV with columns:
  Name, Type, Rarity, Attunement, Link

- Validates required headers (with a few common aliases).
- Trims whitespace.
- Fills any missing/empty expected fields with a sentinel token (default: "MISSING").
- Ignores blank/comment-only rows.
- Yields RawRow dictionaries, these must be parsed further to separate attunement
  from criteria.

author: Cole McGregor, ChatGPT
date: 2025-09-16
version: 0.2.0

You can change `missing_token` to any string, but it MUST be a string that is not
a valid value for any of the fields.

Usage:
    parser = CSVParser(missing_token="MISSING")
    for row in parser.parse("items.csv"):
        ...
"""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Iterable, List

from .base import RawRow, ParserStrategy, ParserError


# ---------------------------------------------------------------------------
# Header normalization
# ---------------------------------------------------------------------------

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

# Required columns (after normalization)
REQUIRED_HEADERS: List[str] = ["Name", "Type", "Rarity", "Attunement", "Link"]


def _normalize_header(h: str) -> str:
    """Normalize a CSV header to our canonical name (if known)."""
    key = (h or "").strip().lower()
    return HEADER_ALIASES.get(key, None) or (h or "").strip()


def _trim(v) -> str:
    """Convert value to string and strip whitespace; None -> empty string."""
    return "" if v is None else str(v).strip()


# ---------------------------------------------------------------------------
# CSV Parser
# ---------------------------------------------------------------------------

class CSVParser(ParserStrategy):
    """
    Strategy for parsing CSV source files.

    Tries UTF-8 first, then falls back to Windows-1252 (cp1252) for files that
    contain “smart quotes” and similar non-UTF-8 bytes.
    """

    def __init__(self, *, missing_token: str = "MISSING"):
        self.missing_token = missing_token

    def name(self) -> str:
        return "CSVParser"

    def parse(self, path: str | Path) -> Iterable[RawRow]:
        """
        Parse the CSV at `path` and yield RawRow objects.

        - Tries encodings in order: "utf-8-sig", "utf-8", "cp1252".
        - If an encoding fails with UnicodeDecodeError, tries the next.
        - If all fail, raises ParserError with details.
        """
        p = Path(path)
        if not p.exists():
            raise ParserError(f"CSV file not found: {p}")

        encodings = ["utf-8-sig", "utf-8", "cp1252"]
        last_decode_err: UnicodeDecodeError | None = None

        for enc in encodings:
            rows: list[RawRow] = []

            try:
                with p.open("r", encoding=enc, newline="") as f:
                    reader = csv.DictReader(f)

                    # No header row at all
                    if reader.fieldnames is None:
                        raise ParserError("CSV has no header row.")

                    # Normalize headers
                    normalized_fields = [_normalize_header(h) for h in reader.fieldnames]
                    header_map = {
                        orig: norm
                        for orig, norm in zip(reader.fieldnames, normalized_fields)
                    }

                    # Validate required headers exist (after normalization)
                    normalized_set = set(header_map.values())
                    missing = [h for h in REQUIRED_HEADERS if h not in normalized_set]
                    if missing:
                        raise ParserError(
                            f"CSV missing required columns: {', '.join(missing)}"
                        )

                    # Read rows
                    for raw in reader:
                        # Skip completely blank rows
                        if not raw or all((_trim(v) == "" for v in raw.values())):
                            continue

                        # Skip comment rows where the first cell starts with '#'
                        first_val = next(iter(raw.values()))
                        if isinstance(first_val, str) and first_val.strip().startswith("#"):
                            continue

                        # Remap and trim according to normalized header names
                        row: dict[str, str] = {}
                        for orig_key, val in raw.items():
                            norm_key = header_map.get(orig_key, orig_key)
                            row[norm_key] = _trim(val)

                        # Enforce sentinel for each expected field
                        def get_or_missing(key: str) -> str:
                            v = row.get(key, "")
                            return v if v != "" else self.missing_token

                        rows.append(
                            RawRow(
                                Name=get_or_missing("Name"),
                                Type=get_or_missing("Type"),
                                Rarity=get_or_missing("Rarity"),
                                Attunement=get_or_missing("Attunement"),
                                Link=get_or_missing("Link"),
                            )
                        )

            except UnicodeDecodeError as e:
                # Could not decode with this encoding; keep error and try next.
                last_decode_err = e
                continue
            except csv.Error as e:
                # Structural CSV error; retrying with a different encoding won't help.
                raise ParserError(f"CSV parsing error: {e}") from e

            # If we got here, this encoding worked. Yield everything and exit.
            for r in rows:
                yield r
            return

        # All encoding attempts failed
        raise ParserError(
            f"CSV encoding error (tried {', '.join(encodings)}): {last_decode_err}"
        ) from last_decode_err

    # -------------------------------------------------------------------
    # return (list_of_rows, count)
    # -------------------------------------------------------------------
    def parse_with_count(self, path: str | Path):
        """
        Parse the CSV and return (rows, total_count).

        This wraps parse() so callers who need the number of rows up front
        (e.g. for ETA calculations) can get it without changing parse().
        """
        rows = list(self.parse(path))
        return rows, len(rows)
