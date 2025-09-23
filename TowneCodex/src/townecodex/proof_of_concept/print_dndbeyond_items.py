# dndbeyond_scraper_poc.py

import sys
import html
import re
import requests
import markdown
import os
from html.parser import HTMLParser
from urllib.parse import urlparse, parse_qs, unquote

from playwright.sync_api import sync_playwright

UA = "townecodex-scraper/0.1"

GOOGLE_API_KEY=AIzaSyC3_LDGpnLusmSj56mt-FmWyb2IySMCKtI;
GOOGLE_CSE_CX=37f428b9c34bf436b

import re, html, os, time, requests




def scrape_item_page(url: str, debug: bool = False) -> dict:
    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)
        context = browser.new_context(user_agent=UA)
        page = context.new_page()

        debug_print(debug, f"[debug] navigating to: {url}")
        page.goto(url, timeout=45000, wait_until="domcontentloaded")
        page.wait_for_timeout(800)

        # --- updated title scrape ---
        title_locator = page.locator("h1.page-title")
        if title_locator.count():
            title = title_locator.first.inner_text().strip()
        else:
            title = "Unknown Title"

        # Description
        desc_locator = page.locator("div.detail-content")
        description = desc_locator.inner_text() if desc_locator.count() else None

        # Image
        img_locator = page.locator("aside.details-aside img.magic-item-image")
        image_url = img_locator.get_attribute("src") if img_locator.count() else None

        # Rarity / Attunement (unchanged for now)
        meta_text = ""
        details = page.locator("div.item-details")
        if details.count():
            meta_text = details.inner_text()

        rarity, attunement = None, None
        text_block = f"{title}\n{meta_text}\n{description or ''}"
        for line in (ln.strip() for ln in text_block.splitlines() if ln.strip()):
            low = line.lower()
            if (rarity is None) and ("rarity" in low or "very rare" in low or "uncommon" in low or "rare" in low or "legendary" in low or "common" in low):
                rarity = line
            if (attunement is None) and ("attunement" in low):
                attunement = line

        browser.close()

    return {
        "title": title,
        "rarity": rarity or "Unknown",
        "attunement": attunement or "None",
        "description": description or "No description found",
        "image_url": image_url,
        "source_link": url,
    }



def main():
    if len(sys.argv) < 2:
        print("Usage: python dndbeyond_scraper_poc.py <item name> [--html]")
        sys.exit(1)

    item_name = sys.argv[1]
    make_html = "--html" in sys.argv

    print(f"Searching for '{item_name}' on D&D Beyond...")

    try:
        url = duck_search_first_link(item_name)
        #url = google_search_first_link(item_name)
    except Exception as e:
        print(f"Search failed: {e}")
        sys.exit(1)

    if not url:
        print("No D&D Beyond result found.")
        sys.exit(0)

    try:
        data = scrape_item_page(url)
    except Exception as e:
        print(f"Scrape failed: {e}")
        sys.exit(1)

    # --- console output ---
    print(f"Title: {data['title']}")
    print(f"Rarity: {data['rarity']}")
    print(f"Attunement: {data['attunement']}")
    print(f"Image URL: {data['image_url'] or 'None'}")
    print(f"Source: {data['source_link']}")
    print("-" * 40)
    print(data["description"])
    print("-" * 40)

    # --- optional HTML output ---
    if make_html:
        description_html = markdown.markdown(data["description"] or "")

        html_doc = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>{html.escape(data['title'])}</title>
<style>
body {{
  font-family: Arial, sans-serif;
  margin: 2em;
  background: #582f0e;
}}
.card {{
  border: 1px solid #ccc;
  border-radius: 10px;
  padding: 1.5em;
  max-width: 600px;
  box-shadow: 2px 2px 6px rgba(0,0,0,0.1);
  background: #fdf0d5;
}}
.card img {{
  max-width: 100%;
  border-radius: 5px;
}}
h1 {{
  margin-top: 0;
}}
.meta {{
  font-style: italic;
  color: #555;
  margin-bottom: 1em;
}}
</style>
</head>
<body>
<div class="card">
  <h1>{html.escape(data['title'])}</h1>
  <div class="meta">Rarity: {html.escape(data['rarity'])}<br>
  Attunement: {html.escape(data['attunement'])}</div>
  {'<img src="' + html.escape(data['image_url']) + '" alt="Item image">' if data['image_url'] else ''}
  <p>{description_html}</p>
</div>
</body>
</html>"""

        with open("output.html", "w", encoding="utf-8") as f:
            f.write(html_doc)
        print("HTML written to output.html")


if __name__ == "__main__":
    main()
