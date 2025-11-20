from __future__ import annotations

from pathlib import Path
import time
from typing import Any

from .parsers.base import choose_parser, RawRow, ParserError
from .scraper import RedditScraper
from .repos import EntryRepository
from .utils import derive_type_info
from .pricing import compute_price


"""
Importer pipeline for Towne Codex.

- Parses a file using the ParserStrategy system (CSV/XLSX/etc).
- For each row, in order:
    1. Read raw fields and link
    2. Scrape (if link present, e.g. Reddit)
    3. Normalize attunement and rarity
    4. Compute price (if not explicitly provided)
    5. Derive type info (general/specific)
    6. Upsert into the Entry table

- Processes entries in batches of N rows, then sleeps for a fixed time
  to avoid hammering external services.

author: Cole McGregor
date: 2025-11-20
version: 0.3.0
"""


# ---------------------------------------------------------------------------
# Attunement normalization helpers
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
    if not v or v.lower() in {"missing", "n/a", "na"}:
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

def import_file(
    path: str | Path,
    *,
    default_image: str | None = None,
    batch_size: int = 10,
    batch_sleep_seconds: float = 5.0,
    progress_every: int = 5,
) -> int:
    """
    Import items from a data file into the database.

    For each row:
      - load raw fields
      - scrape (if link present and supported)
      - normalize attunement and rarity
      - compute price if not explicitly provided
      - derive type info
      - upsert into Entry table

    Processing is paced:
      - every `progress_every` items, we print a progress + ETA line
      - after each `batch_size` items, we sleep `batch_sleep_seconds`
    """
    parser = choose_parser(path)
    rows: list[RawRow] = list(parser.parse(path))

    repo = EntryRepository()
    processed = 0

    # Accumulate type info for catalog tables
    seen_generals: set[str] = set()
    seen_specifics: dict[str, set[str]] = {}

    total_rows = len(rows)
    if total_rows == 0:
        print("[import] no rows found; nothing to do.")
        return 0

    start_time = time.perf_counter()

    for idx, row in enumerate(rows, start=1):
        # --- basic fields ----------------------------------------------------
        name_raw = (row.get("Name") or row.get("Item") or "").strip()
        type_raw = (row.get("Type") or "").strip()
        rarity_raw = (row.get("Rarity") or "").strip()
        link = (row.get("Link") or None) or None
        explicit_value_raw: Any = row.get("Value")

        # CSV attunement → tuple
        att_req, att_crit = _parse_attunement_csv(row.get("Attunement"))

        # --- scrape (if applicable) -----------------------------------------
        scraped: dict[str, Any] = {}
        if link:
            l_low = link.lower()
            if "reddit" in l_low:
                try:
                    scraped = RedditScraper.fetch_post_data(link)
                except Exception as e:
                    print(f"[scrape warn] {name_raw or 'MISSING'}: {e}")
                    scraped = {}
            elif "beyond" in l_low:
                # Placeholder for DNDBeyond scraper
                print(f"[info] DNDBeyond link detected for {name_raw or 'MISSING'}; scraper not implemented yet.")
                scraped = {}
            else:
                scraped = {}

        # --- merge CSV + scraped fields -------------------------------------
        title = (scraped.get("title") or name_raw or "Unknown").strip()
        item_type = type_raw or "Unknown"
        rarity = (scraped.get("rarity") or rarity_raw or "Unknown").strip() or "Unknown"
        desc = scraped.get("description") or None
        image_url = scraped.get("image_url") or None

        # Derive type info
        gen_type, spec_tags = derive_type_info(item_type)
        if gen_type:
            seen_generals.add(gen_type)
            if spec_tags:
                bucket = seen_specifics.setdefault(gen_type, set())
                bucket.update(spec_tags)

        # --- attunement merge policy ----------------------------------------
        s_req, s_crit = _attunement_from_scraper(scraped.get("attunement"))
        att_cell_raw = (row.get("Attunement") or "")
        csv_blank = att_cell_raw.strip() == "" or att_cell_raw.strip().lower() in {"missing", "n/a", "na"}

        if s_req:
            # scraper explicitly says requires attunement → trust it
            att_req = True
            att_crit = s_crit or att_crit
        elif csv_blank:
            # CSV is effectively blank → adopt scraper’s result (even if “None”)
            att_req, att_crit = s_req, s_crit
        elif att_req and not att_crit and s_crit:
            # CSV said "Yes" but no criteria; scraper has more detail
            att_crit = s_crit

        # --- default image ---------------------------------------------------
        if not image_url and default_image:
            image_url = default_image

        # --- price: explicit value wins, otherwise compute -------------------
        value = None
        value_updated = False

        if explicit_value_raw is not None and str(explicit_value_raw).strip() != "":
            try:
                value = int(str(explicit_value_raw).strip())
                value_updated = True   # user-provided override
            except ValueError:
                print(f"[price warn] Could not parse explicit value {explicit_value_raw!r} for {title!r}")

        if value is None:
            # Compute default price from chart
            value = compute_price(
                rarity=rarity,
                type_text=item_type,
                attunement_required=bool(att_req),
            )
            value_updated = False

        data = {
            "name": title,
            "type": item_type,
            "rarity": rarity,
            "attunement_required": att_req,
            "attunement_criteria": att_crit,
            "source_link": link,
            "description": desc,
            "image_url": image_url,
            "general_type": gen_type,
            "specific_type_tags": list(spec_tags) if spec_tags else None,
            "value": value,
            "value_updated": value_updated,
        }

        repo.upsert_entry(data)
        processed += 1

        # --- progress / ETA --------------------------------------------------
        if (processed % progress_every == 0) or (processed == total_rows):
            now = time.perf_counter()
            elapsed = now - start_time
            rate = processed / elapsed if elapsed > 0 else 0.0
            remaining = total_rows - processed
            eta_sec = remaining / rate if rate > 0 else 0.0
            print(
                f"[import] {processed}/{total_rows} entries; "
                f"elapsed={elapsed:.1f}s, ETA≈{eta_sec:.1f}s"
            )

        # --- batch pacing ----------------------------------------------------
        if (processed % batch_size == 0) and (processed < total_rows):
            print(f"[import] processed {processed} entries; sleeping {batch_sleep_seconds:.1f}s…")
            time.sleep(batch_sleep_seconds)

    # Sync the type catalog tables once per import
    if seen_generals:
        repo.sync_type_catalog(seen_generals, seen_specifics)

    return processed
