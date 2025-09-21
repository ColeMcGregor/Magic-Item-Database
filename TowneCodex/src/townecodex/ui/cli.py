# towne_codex/cli.py
from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Optional, Sequence

from .importer import import_file
from .repo import EntryRepository
from .dto import to_card_dto, to_card_dtos

# Renderer registry (strategy-based)
from .renderers import get as get_renderer, available as available_renderers


# ---------------------------- implemented commands -----------------------------


def cmd_import(args) -> int:
    count = import_file(
        args.path,
        scrape=bool(args.scrape),
        default_image=args.default_image,
    )
    print(f"Imported {count} entr{'y' if count == 1 else 'ies'}.")
    return 0


def cmd_show(args) -> int:
    """
    Show a single entry as text or HTML.
    - If --out is provided, writes a full page via renderer.write_page().
    - If not, prints a single card via renderer.render_card() to stdout.
    """
    repo = EntryRepository()
    entry = repo.get_by_id(int(args.id))
    if not entry:
        print(f"Entry {args.id} not found.", file=sys.stderr)
        return 1

    renderer = get_renderer(args.renderer)
    card = to_card_dto(entry)

    if args.out:
        renderer.write_page([card], args.out, page_title=args.title)
        print(f"Wrote {args.renderer} page to {args.out}")
    else:
        # Print a single card to stdout (text renderer is ideal; html will output markup)
        print(renderer.render_card(card))
    return 0


def cmd_export(args) -> int:
    """
    Export a page of entries using the chosen renderer.
    """
    repo = EntryRepository()
    entries = repo.list(page=1, size=args.limit, sort=args.sort)
    cards = to_card_dtos(entries)

    if not cards:
        print("No entries to export.")
        return 0

    renderer = get_renderer(args.renderer)
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    renderer.write_page(cards, str(out_path), page_title=args.title)
    print(f"Wrote {args.renderer} page to {out_path}")
    return 0


def cmd_update_price(args) -> int:
    repo = EntryRepository()
    repo.update_price(int(args.id), int(args.value))
    print(f"Updated price of entry {args.id} to {args.value} (value_updated=True).")
    return 0


def cmd_list(args) -> int:
    """
    Lightweight listing (id, name, rarity). Not the full query layer.
    """
    repo = EntryRepository()
    entries = repo.list(page=args.page, size=args.size, sort=args.sort)
    if not entries:
        print("No entries.")
        return 0
    for e in entries:
        print(f"[{e.id}] {e.name}  |  {e.rarity}  |  type={e.type}")
    return 0


# ------------------------------- TODO stubs ------------------------------------
# Intentionally left unimplemented until query/generator layers are added.


def cmd_search(_args) -> int:
    """
    TODO: implement search via a dedicated QueryService (query.py).
    For now, use 'list' with filters or add a minimal repo-backed search if needed.
    """
    print("TODO: 'search' is not implemented yet. Add QueryService in query.py.", file=sys.stderr)
    return 2


def cmd_suggest(_args) -> int:
    """
    TODO: implement prefix suggestions via SearchService + Trie.
    """
    print("TODO: 'suggest' is not implemented yet. Wire SearchService/Trie.", file=sys.stderr)
    return 2


def cmd_run_generator(_args) -> int:
    """
    TODO: run a generator and produce an Inventory. Requires generator engine & repo.
    """
    print("TODO: 'run-generator' is not implemented yet. Add generator engine.", file=sys.stderr)
    return 2


def cmd_list_generators(_args) -> int:
    """
    TODO: list saved generators via GeneratorRepository.
    """
    print("TODO: 'list-generators' is not implemented yet. Add GeneratorRepository.", file=sys.stderr)
    return 2


def cmd_create_generator(_args) -> int:
    """
    TODO: create/save a generator definition.
    """
    print("TODO: 'create-generator' is not implemented yet. Add generator creation.", file=sys.stderr)
    return 2


# ---------------------------- argparse wiring ----------------------------------


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="towne-codex",
        description="Towne Codex CLI — import and render D&D item cards."
    )
    sub = p.add_subparsers(dest="command", required=True)

    # import-file
    sp = sub.add_parser("import-file", help="Import entries from CSV/XLSX.")
    sp.add_argument("path", help="Path to CSV/XLSX file.")
    sp.add_argument("--scrape", action="store_true", help="Fetch Reddit descriptions/images where available.")
    sp.add_argument("--default-image", help="Fallback image URL when none found (optional).", default=None)
    sp.set_defaults(func=cmd_import)

    # show
    sp = sub.add_parser("show", help="Show a single entry as text or HTML.")
    sp.add_argument("id", help="Entry id.")
    sp.add_argument("--renderer", default="text", choices=available_renderers(), help="Output renderer.")
    sp.add_argument("--out", help="Write to file (if omitted, prints to stdout).")
    sp.add_argument("--title", default="Towne Codex — Item", help="Page title when writing to file.")
    sp.set_defaults(func=cmd_show)

    # export
    sp = sub.add_parser("export", help="Export a page of entries using a renderer.")
    sp.add_argument("--renderer", default="html", choices=available_renderers(), help="Output renderer.")
    sp.add_argument("--out", required=True, help="Output file path.")
    sp.add_argument("--title", default="Towne Codex — Items", help="Page title.")
    sp.add_argument("--limit", type=int, default=24, help="Max entries to include.")
    sp.add_argument("--sort", default="name", help='Sort by "name", "-name", "rarity", "value", etc.')
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
    sp.add_argument("--sort", default="name", help='Sort by "name", "-name", "rarity", "value", etc.')
    sp.set_defaults(func=cmd_list)

    # --- stubs to keep CLI shape stable ---
    sub.add_parser("search", help="(TODO) Search via query layer.").set_defaults(func=cmd_search)
    sub.add_parser("suggest", help="(TODO) Autocomplete via trie.").set_defaults(func=cmd_suggest)
    sub.add_parser("run-generator", help="(TODO) Run a generator to build an inventory.").set_defaults(func=cmd_run_generator)
    sub.add_parser("list-generators", help="(TODO) List saved generators.").set_defaults(func=cmd_list_generators)
    sub.add_parser("create-generator", help="(TODO) Create/save a generator.").set_defaults(func=cmd_create_generator)

    return p


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
