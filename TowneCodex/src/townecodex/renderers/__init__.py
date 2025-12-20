# towne_codex/renderers/__init__.py
from __future__ import annotations

from typing import Dict

from .base import CardRenderer, RendererError
from .html import HTMLCardRenderer

"""
Renderer registry.

- Registers concrete renderer instances keyed by renderer.name (lowercased/stripped).
- Used by the GUI/export pipeline to select an output format (html, later pdf, etc).
"""

_REGISTRY: Dict[str, CardRenderer] = {}


def register(renderer: CardRenderer) -> None:
    _REGISTRY[renderer.name.lower().strip()] = renderer


def get(name: str) -> CardRenderer:
    key = name.lower().strip()
    try:
        return _REGISTRY[key]
    except KeyError:
        raise RendererError(
            f"Unknown renderer: {name!r}. Available: {', '.join(sorted(_REGISTRY))}"
        )


def available() -> list[str]:
    return sorted(_REGISTRY.keys())


# Pre-register built-ins
register(HTMLCardRenderer())
