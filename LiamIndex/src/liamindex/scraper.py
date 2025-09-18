from __future__ import annotations

import requests
import html
import re
import markdown


"""
Scraper for LiamIndex.

- Scrapes a Reddit post for title, rarity, attunement, description, and image url
- also 
"""

class RedditScraper:
    UA = "liamindex-scraper/0.1"

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

        # find griff-mac comment
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

                    # pull rarity/attunement from 2nd line if present
                    lines = [ln.strip() for ln in description.splitlines() if ln.strip()]
                    if len(lines) >= 2:
                        italic_line = lines[1].strip("*_")
                        rarity = italic_line
                        if "attunement" in italic_line.lower():
                            attunement = italic_line
                break

        return {
            "title": title,
            "rarity": rarity or "Unknown",
            "attunement": attunement or "None",
            "description": description or None,
            "image_url": image_url or None,
        }
