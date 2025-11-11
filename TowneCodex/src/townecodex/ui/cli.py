# src/townecodex/cli.py
from __future__ import annotations

"""
Towne Codex CLI

Commands:
  import-file     Parse CSV/XLSX and (optionally) scrape, then upsert into DB.
  show            Show a single entry (plain text to stdout or HTML file).
  export          Export a page of entries to an HTML document.
  update-price    Update an entry's price (marks value_updated=True).
  list            List entries (simple, repo-backed).
  search          QueryService-backed search with filters & pagination.

Stubs (future):
  suggest         Trie-based autocomplete.
  run-generator   Build an inventory using generator engine.
  list-generators List saved generator definitions.
  create-generatorCreate/save a generator definition.

author: Cole McGregor
date: 2025-09-20
version: 0.2.0
"""

import argparse
import sys
from pathlib import Path
from typing import Optional, Sequence

# Ensure DB engine/session are initialized
from . import db  # noqa: F401

from .importer import import_file
from .repos import EntryRepository
from .dto import to_card_dto, to_card_dtos
from .query import QueryService
from .renderers.html import HTMLCardRenderer


# ------------------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------------------

def _print_text_card(entry) -> None:
    """Readable one-card summary for terminals."""
    c = to_card_dto(entry)
    att = "Yes" if c.attunement_required else "No"
    if c.attunement_required and c.attunement_criteria:
        att += f" - {c.attunement_criteria}"
    val = "N/A" if c.value is None else (f"*{c.value}" if not c.value_updated else f"{c.value}")
    print(f"[{c.id}] {c.title}")
    print(f"  Type:       {c.type}")
    print(f"  Rarity:     {c.rarity}")
    print(f"  Attunement: {att}")
    print(f"  Value:      {val}")
    if c.image_url:
        print(f"  Image:      {c.image_url}")
    if c.description:
        snippet = " ".join(c.description.split())
        print(f"  Desc:       {snippet[:239] + '…' if len(snippet) > 240 else snippet}")
    print()


def _print_text_rows(entries) -> None:
    """Compact table-like output for lists/search results."""
    if not entries:
        print("No entries.")
        return
    for e in entries:
        # Avoid lazy-load after session close; repos return usable instances
        name = getattr(e, "name", "")
        rarity = getattr(e, "rarity", "")
        typ = getattr(e, "type", "")
        print(f"[{e.id}] {name}  |  {rarity}  |  type={typ}")


# ------------------------------------------------------------------------------
# Command implementations
# ------------------------------------------------------------------------------

def cmd_import(args) -> int:
    """Import entries from a file."""
    count = import_file(
        args.path,
        scrape=bool(args.scrape),
        default_image=args.default_image,
    )
    print(f"Imported {count} entr{'y' if count == 1 else 'ies'}.")
    return 0


def cmd_show(args) -> int:
    """
    Show a single entry.
    - If --out is provided, writes an HTML page (card) to that file.
    - Otherwise prints a compact text summary to stdout.
    """
    repo = EntryRepository()
    entry = repo.get_by_id(int(args.id))
    if not entry:
        print(f"Entry {args.id} not found.", file=sys.stderr)
        return 1

    if args.out:
        renderer = HTMLCardRenderer(enable_markdown=True)
        renderer.write_page([to_card_dto(entry)], args.out, page_title=args.title)
        print(f"Wrote HTML page to {args.out}")
    else:
        _print_text_card(entry)
    return 0


def cmd_export(args) -> int:
    """Export a page of entries to HTML."""
    repo = EntryRepository()
    entries = repo.list(page=1, size=args.limit, sort=args.sort)
    if not entries:
        print("No entries to export.")
        return 0

    cards = to_card_dtos(entries)
    renderer = HTMLCardRenderer(enable_markdown=True)
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    renderer.write_page(cards, str(out_path), page_title=args.title)
    print(f"Wrote HTML page to {out_path}")
    return 0


def cmd_update_price(args) -> int:
    """Update the price of an entry and mark it as user-updated."""
    repo = EntryRepository()
    repo.update_price(int(args.id), int(args.value))
    print(f"Updated price of entry {args.id} to {args.value} (value_updated=True).")
    return 0


def cmd_list(args) -> int:
    """List entries (simple; repo-backed)."""
    repo = EntryRepository()
    entries = repo.list(page=args.page, size=args.size, sort=args.sort)
    _print_text_rows(entries)
    return 0


def cmd_search(args) -> int:
    """
    Search via QueryService (repo-backed).
    Supported filters: name_contains, type, rarity (multi), require_attunement, text
    Pagination & sort included.
    """
    repo = EntryRepository()
    svc = QueryService(repo)

    # Build filter kwargs for QueryService.search
    kwargs = dict(
        name_contains=args.name_contains,
        type_equals=args.type_equals,
        rarity_in=args.rarity if args.rarity else None,
        attunement_required=args.require_attunement,
        text=args.text,
        page=args.page,
        size=args.size,
        sort=args.sort,
    )
    # Trim Nones that the service can accept either way, but harmless:
    results = svc.search(**kwargs)

    # Print a compact list
    for c in results:
        att = "Yes" if c.attunement_required else "No"
        if c.attunement_required and c.attunement_criteria:
            att += f" ({c.attunement_criteria})"
        val = "N/A" if c.value is None else (f"*{c.value}" if not c.value_updated else f"{c.value}")
        print(f"[{c.id}] {c.title}  |  {c.rarity}  |  {c.type}  |  attun={att}  |  value={val}")
    if not results:
        print("No results.")
    return 0


# --- stubs to keep CLI shape stable (future wiring) ---

def cmd_suggest(_args) -> int:
    print("TODO: 'suggest' is not implemented yet. Wire SearchService/Trie.", file=sys.stderr)
    return 2


def cmd_run_generator(_args) -> int:
    print("TODO: 'run-generator' is not implemented yet. Add generator engine.", file=sys.stderr)
    return 2


def cmd_list_generators(_args) -> int:
    print("TODO: 'list-generators' is not implemented yet. Add GeneratorRepository.", file=sys.stderr)
    return 2


def cmd_create_generator(_args) -> int:
    print("TODO: 'create-generator' is not implemented yet. Add generator creation.", file=sys.stderr)
    return 2


# ------------------------------------------------------------------------------
# argparse wiring
# ------------------------------------------------------------------------------

def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="townecodex",
        description="Towne Codex CLI — import and render D&D item cards."
    )
    sub = p.add_subparsers(dest="command", required=True)

    # import-file
    sp = sub.add_parser("import-file", help="Import entries from CSV/XLSX.")
    sp.add_argument("path", help="Path to CSV/XLSX file.")
    sp.add_argument("--scrape", action="store_true",
                    help="Fetch Reddit descriptions/images where available.")
    sp.add_argument("--default-image",
                    help="Fallback image URL when none found (optional).",
                    default=None)
    sp.set_defaults(func=cmd_import)

    # show
    sp = sub.add_parser("show", help="Show a single entry (text to stdout or HTML to file).")
    sp.add_argument("id", help="Entry id.")
    sp.add_argument("--out", help="Write HTML to file (if omitted, prints a text summary).")
    sp.add_argument("--title", default="Towne Codex — Item", help="Page title when writing to file.")
    sp.set_defaults(func=cmd_show)

    # export
    sp = sub.add_parser("export", help="Export a page of entries to HTML.")
    sp.add_argument("--out", required=True, help="Output file path.")
    sp.add_argument("--title", default="Towne Codex — Items", help="Page title.")
    sp.add_argument("--limit", type=int, default=24, help="Max entries to include.")
    sp.add_argument("--sort", default="name",
                    help='Sort by "name", "-name", "rarity", "value", etc.')
    sp.set_defaults(func=cmd_export)

    # update-price
    sp = sub.add_parser("update-price", help="Update price and mark it as user-updated.")
    sp.add_argument("id", help="Entry id.")
    sp.add_argument("value", help="New integer price.")
    sp.set_defaults(func=cmd_update_price)

    # list (simple)
    sp = sub.add_parser("list", help="List entries (simple; not full query).")
    sp.add_argument("--page", type=int, default=1)
    sp.add_argument("--size", type=int, default=50)
    sp.add_argument("--sort", default="name",
                    help='Sort by "name", "-name", "rarity", "value", etc.')
    sp.set_defaults(func=cmd_list)

    # search (QueryService)
    sp = sub.add_parser("search", help="Search entries with filters & pagination.")
    sp.add_argument("--name-contains", dest="name_contains", default=None,
                    help="Case-insensitive substring match on name.")
    sp.add_argument("--type", dest="type_equals", default=None,
                    help='Exact (case-insensitive) type match. e.g. "Wondrous Item"')
    sp.add_argument("--rarity", action="append", default=None,
                    help="Allowed rarity (can repeat). e.g. --rarity Common --rarity Uncommon")
    att_group = sp.add_mutually_exclusive_group()
    att_group.add_argument("--require-attunement", dest="require_attunement",
                           action="store_true", help="Only items that require attunement.")
    att_group.add_argument("--no-attunement", dest="require_attunement",
                           action="store_false", help="Only items that do NOT require attunement.")
    sp.set_defaults(require_attunement=None)  # default: ignore attunement filter
    sp.add_argument("--text", default=None,
                    help="Substring over name + description.")
    sp.add_argument("--page", type=int, default=1)
    sp.add_argument("--size", type=int, default=50)
    sp.add_argument("--sort", default="name",
                    help='Sort by "name", "-name", "rarity", "value", etc.')
    sp.set_defaults(func=cmd_search)

    # stubs
    sub.add_parser("suggest", help="(TODO) Autocomplete via trie.").set_defaults(func=cmd_suggest)
    sub.add_parser("run-generator", help="(TODO) Run a generator to build an inventory.")\
       .set_defaults(func=cmd_run_generator)
    sub.add_parser("list-generators", help="(TODO) List saved generators.")\
       .set_defaults(func=cmd_list_generators)
    sub.add_parser("create-generator", help="(TODO) Create/save a generator.")\
       .set_defaults(func=cmd_create_generator)

    return p


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
