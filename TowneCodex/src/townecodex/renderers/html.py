# towne_codex/renderers/html.py
from __future__ import annotations

from typing import Iterable, Optional, Callable, Union
import html

from ..dto import CardDTO
from .base import CardRenderer, ExportLayout

try:
    import markdown as _md  # optional dependency
except Exception:  # pragma: no cover - markdown not installed
    _md = None  # type: ignore


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _attunement_text(required: bool, criteria: Optional[str]) -> str:
    return "No" if not required else f"Yes{(' - ' + criteria) if criteria else ''}"


def _format_price(value: Optional[Union[int, str]], value_updated: bool) -> str:
    if value is None:
        return "N/A"

    # Normalize to string and strip whitespace
    raw = str(value).strip()

    # Detect and strip leading asterisk if present
    has_asterisk = raw.startswith("*")
    if has_asterisk:
        raw = raw[1:].strip()

    # Convert to int (fail loudly if invalid)
    try:
        numeric = int(raw)
    except ValueError:
        return "N/A"

    formatted = f"{numeric:,}"

    # Apply asterisk rule:
    # show "*" when value is set and value_updated is False
    # if not value_updated:
    #     return f"*{formatted}"

    return formatted


def _render_description(
    md_text: Optional[str],
    enable_markdown: bool,
    md_renderer: Optional[Callable[[str], str]],
) -> str:
    if not md_text:
        return ""
    if enable_markdown:
        # custom renderer (if provided)
        if md_renderer:
            try:
                return md_renderer(md_text) or ""
            except Exception:
                pass
        # fallback to python-markdown if available
        if _md:
            try:
                return _md.markdown(md_text)
            except Exception:
                pass
    # final fallback: escape as plain text
    return html.escape(md_text)


def _chunk(cards: list[CardDTO], page_size: int) -> list[list[CardDTO]]:
    """
    Group cards into pages of `page_size`. The last page may contain fewer cards.
    """
    if page_size <= 0:
        raise ValueError(f"page_size must be > 0 (got {page_size})")
    pages: list[list[CardDTO]] = []
    i = 0
    n = len(cards)
    while i < n:
        pages.append(cards[i : i + page_size])
        i += page_size
    return pages


# ---------------------------------------------------------------------------
# HTMLCardRenderer
# ---------------------------------------------------------------------------

class HTMLCardRenderer(CardRenderer):
    """
    Render CardDTOs as a printable HTML page of item cards.

    Card layout:
      - Optional thumbnail floats left
      - Text flows to the right until it passes the image height,
        then continues full width underneath (classic float wrap).
    """

    name = "html"

    def __init__(
        self,
        *,
        enable_markdown: bool = True,
        markdown_renderer: Optional[Callable[[str], str]] = None,
    ) -> None:
        self.enable_markdown = enable_markdown
        self.markdown_renderer = markdown_renderer

    # ---- per-card -----------------------------------------------------

    def render_card(self, c: CardDTO) -> str:
        att = _attunement_text(c.attunement_required, c.attunement_criteria)
        price = _format_price(c.value, c.value_updated)
        description_html = _render_description(
            c.description,
            self.enable_markdown,
            self.markdown_renderer,
        )

        title = c.title or "Unknown Item"

        # IMPORTANT: image first + floated via CSS => wrap behavior
        thumb_html = (
            f'<img class="thumb" src="{html.escape(c.image_url)}" '
            f'alt="{html.escape(title)} image">'
            if c.image_url
            else ""
        )

        return f"""
<article class="card" data-entry-id="{c.id}">
  {thumb_html}
  <h2>{html.escape(title)}</h2>

  <div class="meta">
    <div><span class="k">Rarity: </span><span class="v">{html.escape(c.rarity or "Unknown")}</span></div>
    <div><span class="k">Attunement: </span><span class="v">{html.escape(att)}</span></div>
    <div><span class="k">Value: </span><span class="v">{html.escape(price)} gp</span></div>
    <div><span class="k">Type: </span><span class="v">{html.escape(c.type or "Unknown")}</span></div>
  </div>

  <div class="description">{description_html}</div>
</article>
""".strip()

    # ---- page ---------------------------------------------------------

    def render_page(
        self,
        cards: Iterable[CardDTO],
        *,
        page_title: str = "Your Items",
        layout: ExportLayout = ExportLayout.ONE_PER_PAGE,
    ) -> str:
        cards_list = list(cards)

        match layout:
            case ExportLayout.ONE_PER_PAGE:
                pages_markup = self._render_pages_one_per_page(cards_list)
            case ExportLayout.TWO_PER_PAGE_VERTICAL:
                pages_markup = self._render_pages_n_per_page(
                    cards_list,
                    page_size=2,
                    container_class="page-two-vertical",
                )
            case ExportLayout.TWO_PER_PAGE_HORIZONTAL:
                pages_markup = self._render_pages_n_per_page(
                    cards_list,
                    page_size=2,
                    container_class="page-two-horizontal",
                )
            case _:
                raise ValueError(f"Unsupported export layout: {layout!r}")

        return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>{html.escape(page_title)}</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
<style>
  :root {{
    --bg:#582f0e;
    --card:#fdf0d5;
    --ink:#222;
    --muted:#555;
    --border:#d9c2a3;
  }}

  body {{
    margin:0;
    font-family:system-ui,-apple-system,"Segoe UI",Roboto,Arial,sans-serif;
    background:var(--bg);
    color:var(--ink);
    line-height:1.45;
  }}

  header.page {{
    padding:1.5rem 2rem .5rem;
    color:#fff7ee;
    font-weight:600;
    font-size:1.4rem;
  }}

  /* "Book" wrapper (screen) */
  .book {{
    padding: 2rem;
    display: grid;
    gap: 1.25rem;
    align-items: start;
  }}

  /* A "printed page" wrapper */
  .print-page {{
    background: transparent;
  }}

  /* Layout containers inside each page */
  .page-one {{
    display: grid;
    grid-template-columns: 1fr;
    gap: 1.25rem;
  }}

  .page-two-vertical {{
    display: grid;
    grid-template-rows: 1fr 1fr;
    gap: 1.25rem;
  }}

  .page-two-horizontal {{
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 1.25rem;
  }}

  .card {{
    background:var(--card);
    border:1px solid var(--border);
    border-radius:12px;
    box-shadow:0 2px 6px rgba(0,0,0,.12);
    padding:1.25rem;
  }}

  /* Clear floats so the card background wraps the thumbnail */
  .card::after {{
    content:"";
    display:block;
    clear:both;
  }}

  .card h2 {{
    margin:0 0 .35rem;
    font-size:1.25rem;
  }}

  /* Thumbnail: float-left = wrapped text that then becomes full width below */
  .card .thumb {{
    float:left;
    width:140px;
    height:140px;
    object-fit:cover;
    border-radius:10px;
    border:1px solid var(--border);
    margin:0 1rem .75rem 0;
    display:block;
    background:#fff;
  }}

  /* Layout-driven thumbnail sizes (optional, but makes 2-up layouts breathe) */
  .page-one .card .thumb {{
    width:22vw;
    height:22vw;
  }}
  .page-two-vertical .card .thumb {{
    width:18vw;
    height:18vw;
  }}
  .page-two-horizontal .card .thumb {{
    width:22vw;
    height:22vw;
  }}

  .meta {{
    color:var(--muted);
    margin-bottom:.75rem;
  }}
  .meta .k {{
    display:inline-block;
    min-width: 95px;
    font-style: italic;
  }}
  .meta .v {{
    font-weight: 600;
    color: var(--ink);
  }}

  .description p {{
    margin:.5rem 0;
  }}

  @media print {{
    body {{
      background:#fff;
      margin: 0;
    }}

    header.page {{
      color: #000;
      padding: 0.25in 0.25in 0;
      font-size: 14pt;
    }}

    .book {{
      padding: 0.25in;
      gap: 0.25in;
    }}

    .card {{
      box-shadow:none;
      break-inside: avoid;
    }}

    /* hard page breaks */
    .print-page {{
      break-after: page;
      page-break-after: always;
    }}

    /* tighten gaps for print */
    .page-one,
    .page-two-vertical,
    .page-two-horizontal {{
      gap: 0.25in;
    }}
  }}
</style>
</head>
<body>
  <header class="page">{html.escape(page_title)}</header>
  <main class="book">
{pages_markup}
  </main>
</body>
</html>"""

    def write_page(
        self,
        cards: Iterable[CardDTO],
        out_path: str,
        *,
        page_title: str = "Your Items",
        layout: ExportLayout = ExportLayout.ONE_PER_PAGE,
    ) -> None:
        html_doc = self.render_page(cards, page_title=page_title, layout=layout)
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(html_doc)

    # ---- layout strategies --------------------------------------------

    def _render_pages_one_per_page(self, cards: list[CardDTO]) -> str:
        if not cards:
            return '<div style="color:#fff7ee">No cards to display.</div>'
        return "\n".join(
            f"""<section class="print-page">
  <div class="page-one">
    {self.render_card(c)}
  </div>
</section>"""
            for c in cards
        )

    def _render_pages_n_per_page(
        self,
        cards: list[CardDTO],
        *,
        page_size: int,
        container_class: str,
    ) -> str:
        if not cards:
            return '<div style="color:#fff7ee">No cards to display.</div>'

        pages = _chunk(cards, page_size)
        out: list[str] = []
        for page_cards in pages:
            inner = "\n".join(self.render_card(c) for c in page_cards)
            out.append(
                f"""<section class="print-page">
  <div class="{container_class}">
    {inner}
  </div>
</section>"""
            )
        return "\n".join(out)
