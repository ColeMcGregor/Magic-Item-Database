from __future__ import annotations

from typing import Iterable, Set, Tuple


def general_type(raw: str) -> str:
    """
    Given a type string like:
      'Weapon (longsword or shortsword)'
      'Armor (leather, studded leather, or hide)'
      'Potion'
    return the general type (before the parenthesis).
    """
    s = (raw or "").strip()
    if not s:
        return ""
    if "(" in s:
        s = s.split("(", 1)[0]
    return s.strip()


def _normalize_phrase(phrase: str) -> str:
    """
    Basic cleanup of a specific-type phrase:
    - strip whitespace
    - remove standalone articles: 'a', 'an', 'the'
    - collapse extra spaces
    - capitalize the first letter
    """
    if not phrase:
        return ""

    tokens = phrase.strip().split()
    cleaned = []
    for t in tokens:
        tl = t.lower()
        if tl in ("a", "an", "the"):
            continue
        cleaned.append(t)

    if not cleaned:
        return ""

    p = " ".join(cleaned).strip()
    if not p:
        return ""

    return p[0].upper() + p[1:]


def specific_types_from_type(raw: str) -> Set[str]:
    """
    Given a raw type string, return a set of specific type tags
    for that entry.

    Rules:
      - If there are no parentheses -> empty set.
      - If the inner text contains 'any ' (case-insensitive),
        treat it as a complex / generic classification and
        collapse to {'Special'}.
      - Otherwise, split on ', or ' / ' or ' / ',' and normalize
        each part into a simple phrase.

    Examples:
      'Weapon (greataxe, greatsword, lance, or maul)'
          -> {'Greataxe', 'Greatsword', 'Lance', 'Maul'}

      'Weapon (dagger)'
          -> {'Dagger'}

      'Weapon (any slashing or piercing simple weapon)'
          -> {'Special'}

      'Armor (leather, studded leather, or hide)'
          -> {'Leather', 'Studded leather', 'Hide'}
    """
    s = (raw or "").strip()
    if "(" not in s or ")" not in s:
        return set()

    inner = s[s.index("(") + 1 : s.rindex(")")]
    inner = inner.strip()
    if not inner:
        return set()

    lower = inner.lower()

    # 'Any...' and "but not..." style or similar complex descriptors -> collapse to 'Special'
    if "any " in lower or "but not" in lower:
        return {"*Special*"}

    # Generic multi-split:
    # normalize " , or " / " or " into commas so we can split cleanly
    tmp = inner
    tmp = tmp.replace(", or ", ", ")
    tmp = tmp.replace(" or ", ", ")

    parts = [p for p in (t.strip() for t in tmp.split(",")) if p]

    result: Set[str] = set()
    for part in parts:
        norm = _normalize_phrase(part)
        if norm:
            result.add(norm)

    return result


def derive_type_info(raw_type: str) -> Tuple[str, Set[str]]:
    """
    Given a raw type string from the data, return:
        (general_type_tag, specific_type_tags_set)

    Examples:
      'Armor (shield)'
          -> ('Armor', {'Shield'})

      'Armor (leather, studded leather, or hide)'
          -> ('Armor', {'Leather', 'Studded leather', 'Hide'})

      'Weapon (greataxe, greatsword, lance, or maul)'
          -> ('Weapon', {'Greataxe', 'Greatsword', 'Lance', 'Maul'})

      'Weapon (any slashing or piercing simple weapon)'
          -> ('Weapon', {'Special'})

      'Wondrous Item'
          -> ('Wondrous Item', set())
    """
    g = general_type(raw_type) or ""
    subs = specific_types_from_type(raw_type)
    return g, subs


def extract_type_terms(raw_types: Iterable[str]) -> Tuple[Set[str], Set[str]]:
    """
    Given a bunch of raw type strings, return:
        (general_types, specific_types)

    - general_types: 'Armor', 'Weapon', 'Potion', ...
    - specific_types: 'Shield', 'Greataxe', 'Special', ...
    """
    generals: Set[str] = set()
    specifics: Set[str] = set()

    for raw in raw_types:
        g, subs = derive_type_info(raw)
        if g:
            generals.add(g)
        specifics.update(subs)

    return generals, specifics
