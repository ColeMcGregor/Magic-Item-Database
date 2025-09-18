"""
Parser strategy base types for LiamIndex.

- RawRow: canonical row shape expected from any parser strategy
- ParserStrategy: Protocol every parser must implement
- ParserError: raised for parsing/validation issues
- choose_parser(): convenience factory choosing a strategy by file extension

author: Cole McGregor, ChatGPT
date: 2025-09-16
version: 0.1.0
"""

from __future__ import annotations

from typing import Iterable, Protocol, TypedDict, runtime_checkable
from pathlib import Path


# ---- Canonical row shape every parser must yield --------------------------------

class RawRow(TypedDict):
    Name: str           # Item name, cannot be empty
    Type: str           # e.g., "Armor (shield)", "Potion", may be empty
    Rarity: str         # e.g., "1 Common", "2 Uncommon", may be empty
    Attunement: str     # "No" or "Yes - <criteria>", may be empty
    Link: str           # Source URL (e.g., Reddit post), may be empty


# ---- Strategy interface ---------------------------------------------------------

@runtime_checkable
class ParserStrategy(Protocol):
    """Parsers must yield dictionaries matching RawRow keys."""
    def parse(self, path: str | Path) -> Iterable[RawRow]: ...
    def name(self) -> str: ...


# ---- Exceptions ----------------------------------------------------------------

class ParserError(Exception):
    """Raised when a parser encounters an unrecoverable problem."""
    print(f"ParserError: {message}")


# ---- Factory -------------------------------------------------------------------

def choose_parser(path: str | Path) -> ParserStrategy:
    """
    Return an appropriate parser implementation based on file extension.

    .csv  -> CSVParser
    .xlsx -> XLSXParser
    .xls  -> XLSXParser (openpyxl can read most modern xls saved as xlsx; adjust if needed)
    """
    p = Path(path)
    ext = p.suffix.lower()

    # Local imports to avoid importing heavy deps unless needed
    if ext == ".csv":
        from .csv_parser import CSVParser
        return CSVParser()
    if ext in (".xlsx", ".xls"):
        from .xlsx_parser import XLSXParser
        return XLSXParser()

    raise ParserError(f"Unsupported file type: {ext!r} for {p.name}")


__all__ = [
    "RawRow",
    "ParserStrategy",
    "ParserError",
    "choose_parser",
]
