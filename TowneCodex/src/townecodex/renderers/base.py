# towne_codex/renderers/base.py
from __future__ import annotations

from enum import Enum, auto
from typing import Iterable, Protocol

from ..dto import CardDTO

"""
Base protocol for card renderers.

Renderers are responsible for producing a complete "page"
(HTML, PDF, etc.) from a sequence of CardDTOs.

Author: Cole McGregor
Date: 2025-09-20
Version: 0.1.0
"""


# ---------------------------------------------------------------------------
# Export Layout Contract
# ---------------------------------------------------------------------------

class ExportLayout(Enum):
    """
    Defines how cards are laid out per page.

    This enum is a HARD contract: all registered renderers
    must support every value defined here.
    """
    ONE_PER_PAGE = auto()
    TWO_PER_PAGE_VERTICAL = auto()
    TWO_PER_PAGE_HORIZONTAL = auto()


# ---------------------------------------------------------------------------
# Renderer Base
# ---------------------------------------------------------------------------

class RendererError(Exception):
    pass


class CardRenderer(Protocol):
    """
    Strategy interface: render a list of CardDTOs to a string
    (HTML, PDF, etc.).

    Implementations MUST apply the asterisk rule:
      show "*{value}" when value is set and value_updated is False.
    """

    name: str  # stable key, e.g., "html", "pdf"

    def render_card(self, card: CardDTO) -> str: ...

    def render_page(
        self,
        cards: Iterable[CardDTO],
        *,
        page_title: str,
        layout: ExportLayout,
    ) -> str: ...

    def write_page(
        self,
        cards: Iterable[CardDTO],
        out_path: str,
        *,
        page_title: str,
        layout: ExportLayout,
    ) -> None: ...
