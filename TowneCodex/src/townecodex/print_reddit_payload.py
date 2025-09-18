import sys
import requests
import html
import re
import markdown

'''
Fetch a Reddit post (TheGriffonsSaddlebag), extract:
- Title
- Rarity + Attunement (from italic 2nd line in griff-mac's comment)
- Description
- Image URL

Print to console and save a basic HTML page.

author: Cole McGregor
date: 2025-09-18
version: 0.3.0
'''

UA = "townecodex-scraper/0.1"

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


def clean_description_raw(text: str) -> str:
    """
    Clean Reddit description:
    - Find the first '**' that comes after any '&amp;#x200B;'
    - Cut everything from that '**' onwards
    - Remove all '&amp;#x200B;' markers
    """
    if not text:
        return text

    # Find marker position
    marker = text.find("&amp;#x200B;")
    if marker != -1:
        # Look for '**' after the marker
        cut = text.find("**", marker)
        if cut != -1:
            text = text[:cut]

    # Scrub all instances of &amp;#x200B;
    text = text.replace("&amp;#x200B;", "")

    return text.strip()

# clean the title, removing source and braces
def clean_title(title: str) -> str:
    # remove braces from title
    title = title.replace("{The Griffon's Saddlebag}", "")
    return title.strip()



def main():
    if len(sys.argv) < 2:
        print("Usage: python print_reddit_payload.py <reddit_post_url>")
        sys.exit(1)

    url = sys.argv[1].rstrip("/")
    if not url.endswith(".json"):
        url = url + "/.json"

    headers = {"User-Agent": UA}
    params = {"sort": "top", "limit": 500, "depth": 1}

    resp = requests.get(url, headers=headers, params=params, timeout=20)
    resp.raise_for_status()
    data = resp.json()

    post_data = data[0]["data"]["children"][0]["data"]
    title = post_data.get("title", "Unknown Title")
    img = best_image_url(post_data)

    # clean braces and source from title
    title = clean_title(title)

    # find griff-mac comment
    description = None
    comments = data[1]["data"]["children"]
    for c in comments:
        if c.get("kind") != "t1":
            continue
        if c["data"].get("author") == "griff-mac":
            description = c["data"].get("body")
            break

    #clean the description be removing everything past the first instance of &amp;#x200B;
    if description:
        description = clean_description_raw(description)


    rarity, attunement = None, None
    if description:
        lines = [ln.strip() for ln in description.splitlines() if ln.strip()]
        if len(lines) >= 2:
            italic_line = lines[1]
            # strip markdown *...*
            italic_line = italic_line.strip("*_")
            rarity = italic_line
            # crude parse for attunement mention
            if "attunement" in italic_line.lower():
                attunement = italic_line

    description_html = markdown.markdown(description or "")

    # --- console output ---
    print(f"Title: {title}")
    print(f"Rarity: {rarity or 'Unknown'}")
    print(f"Attunement: {attunement or 'None'}")
    print(f"Image URL: {img or 'None'}")
    print("-" * 40)
    print(description or "No description found")
    print("-" * 40)

    # --- HTML output ---
    html_doc = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>{html.escape(title)}</title>
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
  <h1>{html.escape(title)}</h1>
  <div class="meta">Rarity: {html.escape(rarity or 'Unknown')}<br>
  Attunement: {html.escape(attunement or 'None')}</div>
  {'<img src="' + html.escape(img) + '" alt="Item image">' if img else ''}
  <p>{description_html}</p>
</div>
</body>
</html>"""

    with open("output.html", "w", encoding="utf-8") as f:
        f.write(html_doc)
    print("HTML written to output.html")

if __name__ == "__main__":
    main()
