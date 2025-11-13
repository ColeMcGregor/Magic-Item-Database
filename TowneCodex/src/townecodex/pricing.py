# townecodex/pricing.py
from __future__ import annotations
from typing import Optional

# Normalized rarity labels
_RARITY_KEY = {
    "common": "Common",
    "uncommon": "Uncommon",
    "rare": "Rare",
    "very rare": "Very Rare",
    "very-rare": "Very Rare",
    "very_rare": "Very Rare",
    "legendary": "Legendary",
    "artifact": "Artifact",
}

def _normalize_rarity(rarity: str | None) -> Optional[str]:
    if not rarity:
        return None
    key = " ".join(rarity.split()).lower()
    return _RARITY_KEY.get(key)

def _is_consumable(type_text: str | None) -> bool:
    """
    Treat ammunition, potions, and scrolls as the 'consumable' branch.
    """
    if not type_text:
        return False
    t = type_text.lower()
    return (
        "ammunition" in t
        or "ammo" in t
        or "potion" in t
        or "scroll" in t
        or "bolt" in t
    )

# (rarity, category, attune_required) → gp value
# category: "consumable" or "other"
_PRICE_TABLE: dict[tuple[str, str, Optional[bool]], int] = {
    # Common
    ("Common", "consumable", None): 50,
    ("Common", "other", True): 150,
    ("Common", "other", False): 100,

    # Uncommon
    ("Uncommon", "consumable", None): 250,
    ("Uncommon", "other", True): 1_000,
    ("Uncommon", "other", False): 500,

    # Rare
    ("Rare", "consumable", None): 1_000,
    ("Rare", "other", True): 4_000,
    ("Rare", "other", False): 2_000,

    # Very Rare
    ("Very Rare", "consumable", None): 3_000,
    ("Very Rare", "other", True): 15_000,
    ("Very Rare", "other", False): 10_000,

    # Legendary
    ("Legendary", "consumable", None): 5_000,
    ("Legendary", "other", True): 50_000,
    ("Legendary", "other", False): 30_000,

    # Artifact
    ("Artifact", "consumable", None): 20_000,
    ("Artifact", "other", True): 200_000,
    ("Artifact", "other", False): 100_000,
}


def compute_price(
    *,
    rarity: str | None,
    type_text: str | None,
    attunement_required: Optional[bool],
) -> Optional[int]:
    """
    Return the chart price for a given entry, or None if we can't map it.
    """
    r = _normalize_rarity(rarity)
    if not r:
        return None

    category = "consumable" if _is_consumable(type_text) else "other"

    # For consumables, attunement doesn't matter
    if category == "consumable":
        return _PRICE_TABLE.get((r, category, None))

    # For non-consumables, attunement matters. Treat None as False.
    att = bool(attunement_required)
    return _PRICE_TABLE.get((r, category, att))
