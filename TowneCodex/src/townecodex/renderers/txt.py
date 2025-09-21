# towne_codex/renderers/txt.py
from __future__ import annotations

from typing import Iterable, Optional
from ..dto import CardDTO
from .base import CardRenderer

"""
Plain-text renderer for CardDTOs.

author: Cole McGregor
date: 2025-09-20
version: 0.1.0
"""


def _attunement_text(required: bool, criteria: Optional[str]) -> str:
    return "No" if not required else f"Yes{(' - ' + criteria) if criteria else ''}"


def _format_price(value: Optional[int], value_updated: bool) -> str:
    if value is None:
        return "N/A"
    return f"*{value}" if not value_updated else f"{value}"


class TextCardRenderer(CardRenderer):
    """
    Plain-text renderer (good for CLI output or logs).
    """
    name = "text"

    def render_card(self, c: CardDTO) -> str:
        att = _attunement_text(c.attunement_required, c.attunement_criteria)
        price = _format_price(c.value, c.value_updated)
        lines = [
            "=" * 72,
            f"{c.title}  [id={c.id}]",
            "-" * 72,
            f"Rarity: {c.rarity}",
            f"Attunement: {att}",
            f"Value: {price}",
            f"Type: {c.type}",
            f"Image: {c.image_url or '(none)'}",
            "-" * 72,
            (c.description or "(no description)"),
            "=" * 72,
        ]
        return "\n".join(lines)

    def render_page(self, cards: Iterable[CardDTO], *, page_title: str = "Towne Codex — Items") -> str:
        parts = [f"# {page_title}"]
        emitted = False
        for c in cards:
            parts.append(self.render_card(c))
            emitted = True
        if not emitted:
            parts.append("(no cards)")
        return "\n".join(parts)

    def write_page(self, cards: Iterable[CardDTO], out_path: str, *, page_title: str = "Towne Codex — Items") -> None:
        doc = self.render_page(cards, page_title=page_title)
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(doc)
