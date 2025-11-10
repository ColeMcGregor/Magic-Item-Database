from __future__ import annotations

import requests
import html
import re
import markdown


"""
Scraper for townecodex.

- Scrapes a Reddit post for title, rarity, attunement, description, and image url
- also 
"""

class RedditScraper:
    UA = "townecodex-scraper/0.1"

    # --- helpers ----------------------------------------------------

    @staticmethod
    def best_image_url(post_data: dict) -> str | None:
        preview = post_data.get("preview") or {}
        images = preview.get("images") or []
        if images:
            src = images[0].get("source", {}).get("url")
            if src:
                return html.unescape(src)

        direct = post_data.get("url_overridden_by_dest")
        if direct and direct.lower().endswith((".jpg", ".jpeg", ".png", ".gif")):
            return html.unescape(direct)

        if post_data.get("is_gallery") and "media_metadata" in post_data:
            for meta in (post_data["media_metadata"] or {}).values():
                if (meta.get("e") == "Image") or (meta.get("m", "").startswith("image/")):
                    u = (meta.get("s") or {}).get("u")
                    if u:
                        return html.unescape(u)

        return None

    @staticmethod
    def clean_description_raw(text: str) -> str:
        """
        Clean Reddit description:
        - Find the first '**' that comes after any '&#x200B;'
        - Cut everything from that '**' onwards
        - Remove all '&#x200B;' markers
        """
        if not text:
            return text

        marker = text.find("&#x200B;")
        if marker != -1:
            cut = text.find("**", marker)
            if cut != -1:
                text = text[:cut]

        text = text.replace("&#x200B;", "")
        return text.strip()

    @staticmethod
    def clean_title(title: str) -> str:
        # remove braces from title
        title = title.replace("{The Griffon's Saddlebag}", "")
        return title.strip()

    # --- main fetch -------------------------------------------------

    @classmethod
    def fetch_post_data(cls, url: str) -> dict:
        """
        Fetch a Reddit post JSON and extract card data.
        Returns dict with keys: title, rarity, attunement, description, image_url
        """
        if not url.endswith(".json"):
            url = url.rstrip("/") + "/.json"

        headers = {"User-Agent": cls.UA}
        params = {"sort": "top", "limit": 500, "depth": 1}

        resp = requests.get(url, headers=headers, params=params, timeout=20)
        resp.raise_for_status()
        data = resp.json()

        post_data = data[0]["data"]["children"][0]["data"]
        title = cls.clean_title(post_data.get("title", "Unknown Title"))
        image_url = cls.best_image_url(post_data)

        # --- helpers -------------------------------------------------------
        rar_att_re = re.compile(
            r"""^\s*
                (?P<type>[^,()]+(?:\s*\([^)]*\))?)   # "Wondrous item" or "Armor (shield)"
                \s*,\s*
                (?P<rarity>[^()]+?)                  # "common" / "rare" / "common or very rare"
                (?:\s*\(\s*(?P<paren>[^)]*)\s*\))?   # optional: "(requires attunement ...)"
                \s*$
            """,
            re.IGNORECASE | re.VERBOSE,
        )

        def parse_rarity_attunement(italic_line: str) -> tuple[str, str]:
            line = italic_line.strip("*_ ").strip()
            m = rar_att_re.match(line)
            if not m:
                parts = [p.strip() for p in line.split(",")]
                rarity_guess = parts[-1] if parts else "Unknown"
                return rarity_guess, "None"

            rarity_txt = m.group("rarity").strip()
            paren = (m.group("paren") or "").strip()
            if "attun" in paren.lower():
                attun_txt = paren  # e.g., "requires attunement by a wizard"
            else:
                attun_txt = "None"
            return rarity_txt, attun_txt

        def _title_case_keep_connectors(s: str) -> str:
            if not s:
                return s
            parts = s.split()
            keep_lower = {"or", "and", "of"}
            out = []
            for i, w in enumerate(parts):
                lw = w.lower()
                if lw in keep_lower:
                    out.append(lw)
                else:
                    out.append(lw.capitalize() if len(w) > 1 else lw.upper())
            return " ".join(out)

        def normalize_rarity(r: str | None) -> str:
            if not r:
                return "Unknown"
            # collapse spaces, lowercase, split on 'or' and title case each segment
            r_low = " ".join(r.split()).lower()
            segs = [seg.strip() for seg in r_low.split(" or ")]
            segs = [_title_case_keep_connectors(seg) for seg in segs if seg]
            return " or ".join(segs) if segs else "Unknown"

        def normalize_attunement(att: str | None) -> str:
            """
            Map:
            None/No/Missing -> "None"
            "requires attunement" -> "Requires Attunement"
            "requires attunement by a wizard" -> "Requires Attunement (Wizard)"
            "Requires Attunement (Paladin)" -> "Requires Attunement (Paladin)"
            """
            if not att:
                return "None"
            s = att.strip()
            low = s.lower()
            if low in {"none", "no", "missing", "n/a"} or low.startswith("no"):
                return "None"
            if "attun" in low:
                # Prefer parentheses if present
                m = re.search(r"\(([^)]+)\)", s)
                if m:
                    crit = m.group(1).strip()
                else:
                    # Or "... by <criteria>"
                    m2 = re.search(r"\bby\s+(.+)$", s, flags=re.IGNORECASE)
                    if m2:
                        crit = m2.group(1).strip()
                    else:
                        crit = ""
                # Strip leading articles and normalize connectors
                crit = re.sub(r"^(?:an?\s+)", "", crit, flags=re.IGNORECASE).strip()
                crit_norm = _title_case_keep_connectors(crit)
                return "Requires Attunement" if not crit_norm else f"Requires Attunement ({crit_norm})"
            # Fallback: treat any other non-empty text as criteria
            crit_norm = _title_case_keep_connectors(s)
            return f"Requires Attunement ({crit_norm})"

        # --- find griff-mac comment --------------------------------------
        description = None
        rarity, attunement = None, None
        comments = data[1]["data"]["children"]
        for c in comments:
            if c.get("kind") != "t1":
                continue
            if c["data"].get("author") == "griff-mac":
                raw_body = c["data"].get("body")
                if raw_body:
                    description = cls.clean_description_raw(raw_body)
                    lines = [ln.strip() for ln in description.splitlines() if ln.strip()]
                    if len(lines) >= 2:
                        italic_line = lines[1].strip("*_")
                        rarity, attunement = parse_rarity_attunement(italic_line)
                break

        # --- normalized outputs ------------------------------------------
        rarity_norm = normalize_rarity((rarity or "Unknown").strip())
        attune_norm = normalize_attunement((attunement or "None").strip())

        return {
            "title": title,
            "rarity": rarity_norm,
            "attunement": attune_norm,
            "description": description or None,
            "image_url": image_url or None,
        }
