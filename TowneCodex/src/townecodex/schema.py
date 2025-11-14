from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Optional, List, Dict, Any
import json


"""
This is the schema for the generator configuration.
It is used to store the generator configuration in the database.
It is also used to convert the generator configuration to and from JSON.4

The schema is as follows:
    BucketConfig is a single bucket within a generator.
    GeneratorConfig is the full configuration for a generator: global constraints + buckets.

    config_to_dict is used to convert GeneratorConfig to a plain dict, safe for JSON.
    config_from_dict is used to convert a plain dict to a GeneratorConfig (with BucketConfig objects).
    config_to_json is used to serialize GeneratorConfig to a JSON string.
    config_from_json is used to deserialize GeneratorConfig from a JSON string.

author: Cole McGregor
date: 2025-11-13
version: 0.1.0

"""

# ---------------------------------------------------------------------------
# BucketConfig
# ---------------------------------------------------------------------------

@dataclass
class BucketConfig:
    """
    A single bucket within a generator.

    Examples:
      - "2–4 common consumables"
      - "1 rare weapon (non-attuned)"
      - "1 legendary item, any type, must require attunement"
    """

    # Human-facing name, e.g. "Consumables" or "Main Weapon"
    name: str

    # How many items this bucket should try to contribute
    min_count: int = 0
    max_count: int = -1  # -1 can mean "no upper bound" if you want

    # Rarity filter: if empty/None, do not filter by rarity
    allowed_rarities: Optional[List[str]] = None

    # Type filter: case-insensitive substring match against Entry.type
    # e.g. ["weapon"], ["armor"], ["potion", "scroll"]
    type_contains_any: Optional[List[str]] = None

    # Value/price bounds (inclusive). None == no bound.
    min_value: Optional[int] = None
    max_value: Optional[int] = None

    # Attunement constraint:
    #   None  -> ignore attunement
    #   True  -> only entries that require attunement
    #   False -> only entries that do NOT require attunement
    attunement_required: Optional[bool] = None

    # Whether the engine should try to avoid duplicates in this bucket
    prefer_unique: bool = True

    # Future-proof catch-all for extra options (weighting, tags, etc.)
    extra: Dict[str, Any] = field(default_factory=dict)


# ---------------------------------------------------------------------------
# GeneratorConfig
# ---------------------------------------------------------------------------

@dataclass
class GeneratorConfig:
    """
    Full configuration for a generator: global constraints + buckets.

    This is what gets serialized into GeneratorDef.config_json.
    """

    # Optional short description/label inside the config itself
    label: Optional[str] = None

    # Global item count bounds (across all buckets)
    min_items: Optional[int] = None
    max_items: Optional[int] = None

    # Global value bounds (across all buckets)
    min_total_value: Optional[int] = None
    max_total_value: Optional[int] = None

    # If True, engine will try harder to avoid duplicate entries overall
    global_prefer_unique: bool = True

    # Optional fixed RNG seed for reproducible runs
    random_seed: Optional[int] = None

    # Per-bucket rules
    buckets: List[BucketConfig] = field(default_factory=list)

    # Free-form notes for DM / user
    notes: Optional[str] = None

    # Future-proof catch-all
    extra: Dict[str, Any] = field(default_factory=dict)


# ---------------------------------------------------------------------------
# JSON helpers for storing in GeneratorDef.config_json
# ---------------------------------------------------------------------------

def config_to_dict(cfg: GeneratorConfig) -> Dict[str, Any]:
    """Convert GeneratorConfig -> plain dict, safe for JSON."""
    return asdict(cfg)


def config_from_dict(data: Dict[str, Any]) -> GeneratorConfig:
    """Convert plain dict -> GeneratorConfig (with BucketConfig objects)."""
    buckets_data = data.get("buckets") or []
    buckets: List[BucketConfig] = []
    for b in buckets_data:
        buckets.append(
            BucketConfig(
                name=b.get("name", ""),
                min_count=b.get("min_count", 0),
                max_count=b.get("max_count", 0),
                allowed_rarities=b.get("allowed_rarities"),
                type_contains_any=b.get("type_contains_any"),
                min_value=b.get("min_value"),
                max_value=b.get("max_value"),
                attunement_required=b.get("attunement_required"),
                prefer_unique=b.get("prefer_unique", True),
                extra=b.get("extra") or {},
            )
        )

    return GeneratorConfig(
        label=data.get("label"),
        min_items=data.get("min_items"),
        max_items=data.get("max_items"),
        min_total_value=data.get("min_total_value"),
        max_total_value=data.get("max_total_value"),
        global_prefer_unique=data.get("global_prefer_unique", True),
        random_seed=data.get("random_seed"),
        buckets=buckets,
        notes=data.get("notes"),
        extra=data.get("extra") or {},
    )


def config_to_json(cfg: GeneratorConfig) -> str:
    """Serialize GeneratorConfig to a JSON string."""
    return json.dumps(config_to_dict(cfg), separators=(",", ":"), sort_keys=True)


def config_from_json(raw: str) -> GeneratorConfig:
    """Deserialize GeneratorConfig from a JSON string."""
    data = json.loads(raw)
    if not isinstance(data, dict):
        raise ValueError("GeneratorConfig JSON must decode to an object")
    return config_from_dict(data)
