# townecodex/pricing.py
from __future__ import annotations
from typing import Optional

# Normalized rarity labels
_RARITY_KEY = {
    "1 Common": "Common",
    "2 Uncommon": "Uncommon",
    "3 Rare": "Rare",
    "4 Very Rare": "Very Rare",
    "5 Legendary": "Legendary",
    "6 Artifact": "Artifact",
    "common": "Common",
    "uncommon": "Uncommon",
    "rare": "Rare",
    "very rare": "Very Rare",
    "legendary": "Legendary",
    "artifact": "Artifact",
    "Common": "Common",
    "Uncommon": "Uncommon",
    "Rare": "Rare",
    "Very Rare": "Very Rare",
    "Legendary": "Legendary",
    "Artifact": "Artifact",
}

def _normalize_rarity(rarity: str | None) -> Optional[str]:
    if not rarity:
        return None
    return _RARITY_KEY.get(rarity)

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
        or "arrow" in t
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
    ("Uncommon", "other", True): 1000,
    ("Uncommon", "other", False): 500,

    # Rare
    ("Rare", "consumable", None): 1000,
    ("Rare", "other", True): 4000,
    ("Rare", "other", False): 2000,

    # Very Rare
    ("Very Rare", "consumable", None): 3000,
    ("Very Rare", "other", True): 15000,
    ("Very Rare", "other", False): 10000,

    # Legendary
    ("Legendary", "consumable", None): 5000,
    ("Legendary", "other", True): 50000,
    ("Legendary", "other", False): 30000,

    # Artifact
    ("Artifact", "consumable", None): 20000,
    ("Artifact", "other", True): 200000,
    ("Artifact", "other", False): 100000,
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

    category = "consumable" if _is_consumable(type_text) else "other"
    r = _normalize_rarity(rarity)
    if not r:
        print(f"no rarity for {type_text}: {r}")
        return None

    # For consumables, attunement doesn't matter
    if category == "consumable":
        return _PRICE_TABLE.get((r, category, None))

    # For non-consumables, attunement matters. Treat None as False.
    att = bool(attunement_required)
    return _PRICE_TABLE.get((r, category, att))
