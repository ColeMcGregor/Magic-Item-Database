from __future__ import annotations

from typing import Iterable, Optional, Callable
import html

from ..dto import CardDTO
from .base import CardRenderer

try:
    import markdown as _md  # optional dependency
except Exception:  # pragma: no cover - markdown not installed
    _md = None  # type: ignore


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _attunement_text(required: bool, criteria: Optional[str]) -> str:
    return "No" if not required else f"Yes{(' - ' + criteria) if criteria else ''}"


def _format_price(value: Optional[int], value_updated: bool) -> str:
    if value is None:
        return "N/A"
    return f"*{value}" if not value_updated else f"{value}"


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


# ---------------------------------------------------------------------------
# HTMLCardRenderer
# ---------------------------------------------------------------------------

class HTMLCardRenderer(CardRenderer):
    """
    Render one or more CardDTOs as a simple, printable HTML page
    of item cards.
    """

    # *** this is what the registry in renderers/__init__.py needs ***
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
        img_html = (
            f'<img src="{html.escape(c.image_url)}" '
            f'alt="{html.escape(title)} image">'
            if c.image_url
            else ""
        )

        return f"""
<article class="card" data-entry-id="{c.id}">
  <h2>{html.escape(title)}</h2>
  <div class="meta">
    Rarity: {html.escape(c.rarity or "Unknown")}<br>
    Attunement: {html.escape(att)}<br>
    Value: {html.escape(price)}<br>
    Type: {html.escape(c.type or "Unknown")}
  </div>
  {img_html}
  <div class="description">{description_html}</div>
</article>
""".strip()

    # ---- page ---------------------------------------------------------

    def render_page(
        self,
        cards: Iterable[CardDTO],
        *,
        page_title: str = "Towne Codex — Items",
    ) -> str:
        cards_markup = (
            "\n\n".join(self.render_card(c) for c in cards)
            or '<div style="color:#fff7ee">No cards to display.</div>'
        )

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
  .wrap {{
    padding:2rem;
    display:grid;
    grid-template-columns:repeat(auto-fit,minmax(320px,1fr));
    gap:1.25rem;
    align-items:start;
  }}
  .card {{
    background:var(--card);
    border:1px solid var(--border);
    border-radius:12px;
    box-shadow:0 2px 6px rgba(0,0,0,.12);
    padding:1.25rem;
  }}
  .card h2 {{
    margin:0 0 .25rem;
    font-size:1.25rem;
  }}
  .meta {{
    font-style:italic;
    color:var(--muted);
    margin-bottom:.75rem;
  }}
  .card img {{
    max-width:50%;
    height:auto;
    display:block;
    border-radius:6px;
    margin:.25rem 0 .75rem;
  }}
  .description p {{
    margin:.5rem 0;
  }}
  @media print {{
    body {{ background:#fff; }}
    .card {{ break-inside:avoid; box-shadow:none; }}
  }}
</style>
</head>
<body>
  <header class="page">{html.escape(page_title)}</header>
  <main class="wrap">
{cards_markup}
  </main>
</body>
</html>"""

    def write_page(
        self,
        cards: Iterable[CardDTO],
        out_path: str,
        *,
        page_title: str = "Towne Codex — Items",
    ) -> None:
        html_doc = self.render_page(cards, page_title=page_title)
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(html_doc)
