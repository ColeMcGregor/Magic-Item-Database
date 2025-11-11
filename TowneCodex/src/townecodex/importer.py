# townecodex/importer.py
from __future__ import annotations

from pathlib import Path

from .parsers.base import choose_parser, RawRow, ParserError
from .scraper import RedditScraper
from .repos import EntryRepository

"""
Importer pipeline for Towne Codex.

- Parses a CSV/XLSX file using the ParserStrategy system.
- Normalizes attunement:
    CSV:  "No" / "Yes" / "Yes - Wizard" / free-text criteria
    Scraper: "None" / "Requires Attunement" / "Requires Attunement (Wizard)"
- Writes entries via EntryRepository (idempotent upsert by source_link, else (name,type)).

author: Cole McGregor
date: 2025-09-17
version: 0.2.1
"""


# ---------------------------------------------------------------------------
# Attunement normalization
# ---------------------------------------------------------------------------

def _parse_attunement_csv(value: str | None) -> tuple[bool, str | None]:
    """
    Convert CSV cell to (required, criteria).
      "No"            -> (False, None)
      "Yes"           -> (True, None)
      "Yes - Wizard"  -> (True, "Wizard")
      "Dex 15"        -> (True, "Dex 15")         # any free text means required with criteria
      "", "missing"   -> (False, None)
    """
    if not value:
        return (False, None)
    v = value.strip()
    if not v or v.lower() in {"missing", "n/a"}:
        return (False, None)

    lv = v.lower()
    if lv.startswith("no"):
        return (False, None)
    if lv.startswith("yes"):
        parts = v.split("-", 1)
        return (True, parts[1].strip() if len(parts) == 2 else None)

    # Fallback: any non-empty free-text implies required with criteria
    return (True, v)


def _attunement_from_scraper(att: str | None) -> tuple[bool, str | None]:
    """
    Convert scraper string to (required, criteria).
      "None"                                 -> (False, None)
      "Requires Attunement"                  -> (True, None)
      "Requires Attunement (Wizard)"         -> (True, "Wizard")
      any other non-empty text               -> (True, text)
    """
    if not att:
        return (False, None)
    s = att.strip()
    if not s:
        return (False, None)

    ls = s.lower()
    if ls in {"none", "no"}:
        return (False, None)
    if ls.startswith("requires attunement"):
        i, j = s.find("("), s.rfind(")")
        if i != -1 and j != -1 and j > i + 1:
            crit = s[i + 1 : j].strip()
            return (True, crit or None)
        return (True, None)

    # Fallback: treat provided text as criteria
    return (True, s)


# ---------------------------------------------------------------------------
# Import
# ---------------------------------------------------------------------------

def import_file(path: str | Path, *, scrape: bool = False, default_image: str | None = None) -> int:
    """
    Import items from a CSV/XLSX file into the database.

    Args:
        path: file path to parse
        scrape: whether to fetch Reddit descriptions/images
        default_image: image URL/path to assign if none found

    Returns:
        count of rows processed (created+updated; upsert is idempotent)
    """
    parser = choose_parser(path)
    rows: list[RawRow] = list(parser.parse(path))

    repo = EntryRepository()
    processed = 0

    for row in rows:
        name_csv = (row.get("Name") or row.get("Item") or "").strip()
        type_csv = (row.get("Type") or "").strip()
        rarity_csv = (row.get("Rarity") or "").strip()
        link = (row.get("Link") or None) or None

        # CSV attunement → tuple
        att_req, att_crit = _parse_attunement_csv(row.get("Attunement"))

        scraped: dict = {}
        if scrape and link and "reddit" in link.lower():
            try:
                scraped = RedditScraper.fetch_post_data(link)
            except Exception as e:
                # Non-fatal: keep importing CSV values
                print(f"[scrape warn] {name_csv or 'MISSING'}: {e}")
                scraped = {}

        # Prefer scraped fields where present
        title = (scraped.get("title") or name_csv or "Unknown").strip()
        item_type = type_csv or "Unknown"
        rarity = (scraped.get("rarity") or rarity_csv or "Unknown").strip()
        desc = scraped.get("description") or None
        image_url = scraped.get("image_url") or None

        # --- Robust attunement merge policy ---
        # If the scraper explicitly says "Requires Attunement ...", trust it.
        # Else, if CSV attunement cell is blank/placeholder, adopt scraper's values.
        # Else, if CSV says required but lacks criteria and scraper has one, fill it.
        att_cell_raw = (row.get("Attunement") or "")
        csv_blank = att_cell_raw.strip() == "" or att_cell_raw.strip().lower() in {"missing", "n/a", "na"}
        s_req, s_crit = _attunement_from_scraper(scraped.get("attunement"))

        if s_req:
            att_req = True
            att_crit = s_crit or att_crit
        elif csv_blank:
            att_req, att_crit = s_req, s_crit
        elif att_req and not att_crit and s_crit:
            att_crit = s_crit
        # --------------------------------------

        # Apply default image if none found
        if not image_url and default_image:
            image_url = default_image

        data = {
            "name": title,
            "type": item_type,
            "rarity": rarity,
            "attunement_required": att_req,
            "attunement_criteria": att_crit,
            "source_link": link,
            "description": desc,
            "image_url": image_url,
        }

        # Centralized write policy (trim, non-empty overwrite, upsert by link/(name,type))
        repo.upsert_entry(data)
        processed += 1

    return processed
