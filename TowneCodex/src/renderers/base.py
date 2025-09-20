# towne_codex/renderers/base.py
from __future__ import annotations
from typing import Iterable, Protocol
from ..dto import CardDTO

"""
This is the base class for the card renderer.
it is used to render the card to the user.
implementations might include html, text, markdown, pdf, etc

author: Cole McGregor
date: 2025-09-20
version: 0.1.0
"""

class RendererError(Exception):
    pass

class CardRenderer(Protocol):
    """
    Strategy interface: render a list of CardDTOs to a string (HTML, text, etc.)
    Implementations MUST apply the asterisk rule:
      show "*{value}" when value is set and value_updated is False.
    """
    name: str  # stable key, e.g., "html", "text"

    def render_card(self, card: CardDTO) -> str: ...
    def render_page(self, cards: Iterable[CardDTO], *, page_title: str) -> str: ...
    def write_page(self, cards: Iterable[CardDTO], out_path: str, *, page_title: str) -> None: ...
