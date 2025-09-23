# towne_codex/renderers/__init__.py
from __future__ import annotations
from typing import Dict
from .base import CardRenderer, RendererError
from .html import HTMLCardRenderer
from .txt import TextCardRenderer

"""
This is the registry for the renderers.
it is used to register the renderers and get the renderers.
"""

_REGISTRY: Dict[str, CardRenderer] = {}

# register the renderer
def register(renderer: CardRenderer) -> None:
    _REGISTRY[renderer.name.lower().strip()] = renderer

# get the renderer
def get(name: str) -> CardRenderer:
    key = name.lower().strip()
    try:
        return _REGISTRY[key]
    except KeyError:
        raise RendererError(f"Unknown renderer: {name!r}. Available: {', '.join(sorted(_REGISTRY))}")

# get the available renderers
def available() -> list[str]:
    return sorted(_REGISTRY.keys())


# Pre-register built-ins
register(HTMLCardRenderer())
register(TextCardRenderer())
