from __future__ import annotations

from pathlib import Path
from sqlalchemy.orm import Session

from .db import SessionLocal
from .models import Entry
from .parsers.base import choose_parser, RawRow, ParserError


"""
Importer pipeline for LiamIndex.

- Parses a CSV/XLSX file using the ParserStrategy system.
- Normalizes attunement ("Yes - criteria" -> required + criteria string).
- Writes entries into the database.

author: Cole McGregor
date: 2025-09-17
version: 0.1.0
"""


def _parse_attunement(value: str) -> tuple[bool, str | None]:
    """
    Convert attunement cell into (required, criteria).
    Examples:
      "No"           -> (False, None)
      "Yes"          -> (True, None)
      "Yes - Dex 15" -> (True, "Dex 15")
    """
    if not value or value.strip().lower() == "missing":
        return (False, None)

    val = value.strip()
    if val.lower().startswith("no"):
        return (False, None)
    if val.lower().startswith("yes"):
        parts = val.split("-", 1)
        if len(parts) == 2:
            return (True, parts[1].strip())
        return (True, None)
    # Fallback: treat as "criteria string"
    return (True, val)


def import_file(path: str | Path, *, scrape: bool = False, default_image: str | None = None) -> int:
    """
    Import items from a CSV/XLSX file into the database.

    Args:
        path: file path to parse
        scrape: whether to fetch Reddit descriptions/images (TODO: integrate scraper)
        default_image: image path to assign if none found

    Returns:
        count of entries imported
    """

    # choose the parser based on the file extension
    parser = choose_parser(path)
    # parse the file, getting back a list of RawRow dictionaries
    rows: list[RawRow] = list(parser.parse(path))

    # create a session
    session: Session = SessionLocal()
    # initialize the imported count
    imported_count = 0

    # try to import the entries
    try:
        # iterate through the rows
        for row in rows:
            # parse the attunement, getting back a tuple of (required, criteria)
            attune_required, attune_criteria = _parse_attunement(row["Attunement"])
            # scrape the description
            description = RedditScraper.fetch_description(row["Link"])

            # create the entry
            entry = Entry(
                # fill in the entry
                name=row["Name"] if row["Name"] else "MISSING",
                type=row["Type"] if row["Type"] else "MISSING",
                rarity=row["Rarity"] if row["Rarity"] else "MISSING",
                attunement_required=attune_required,
                attunement_criteria=attune_criteria,
                source_link=row["Link"] or None,
                description=description or None,          #filled by scraper or if none left as none
                image_path=default_image,  # placeholder
            )
            # add the entry to the session
            session.add(entry)
            # increment the imported count
            imported_count += 1

        # commit the session
        session.commit()
    #if an error occurs,
    except Exception:
        # rollback the session
        session.rollback()
        raise
    # finally, close the session
    finally:
        session.close()
    # return the imported count to be used for debug, logging, and iteration purposes
    return imported_count
