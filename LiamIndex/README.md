# LiamIndex

**LiamIndex** is a Python-based system for importing, storing, and generating item inventories — perfect for building shops, NPC gear, enemy loot, and treasure chests for tabletop or digital games.

It supports data import from CSV/XLSX files, enrichment via the Reddit API (for descriptions/images), and flexible querying/generation based on rarity, type, attunement, and budget rules.

---

## Features
- Flexible imports: CSV and Excel file parsing (strategy pattern).
- Scraping: fetch item descriptions and preview images from Reddit links.
- Manual entry: add items directly via UI or CLI.
- Structured storage: SQLite by default, portable to Postgres.
- Generators: define rules for shops, NPCs, enemies, or chests.
- Query engine: search items by type, rarity, attunement, value, etc.
- Default images: automatically attach a placeholder if no image is found.
---

## Installation

### Prerequisites
- Python 3.12+
- [Poetry](https://python-poetry.org/) for dependency management

### Setup
```bash
git clone https://github.com/[YourUsernameGoesHere]/liamindex.git
cd liamindex
poetry install
