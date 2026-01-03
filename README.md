# TowneCodex

TowneCodex is a desktop application for browsing, editing, generating, and organizing Dungeons & Dragons 5e items.
It supports structured type catalogs, customizable loot generators, inventories, bucket rules, CSV/XLSX imports,
scraping, and admin-level schema operations.

Built with Python, SQLAlchemy, and PySide6.

## 1. Overview

TowneCodex provides a centralized interface for organizing D&D items and tools for building generators and inventories.
It is designed for DMs, worldbuilders, and homebrew creators who need fast lookup, structured filtering, and consistent
rules for item generation.

A key design goal is **explicit, deterministic behavior**: generators run from clearly defined rules, UI actions
operate on visible state, and long-running operations are isolated from the UI thread.

## 2. Features

### Item Management

- Full item browser with fast filters
- Item detail pane for viewing and editing
- Create, update, and delete items
- Structured type system using GeneralType and SpecificType tables
- Search across name, type, rarity, attunement, and description

### Importing

- CSV and XLSX import workflow
- Optional default image assignment
- Batched import with throttling to avoid UI blocking
- Upsert logic that preserves existing non-empty values

### Pricing and Metadata

- Automatic pricing for entries missing a value
- Scraping of external sources for descriptions and images
- Optional combined post-processing routines

### Generators

- Create, edit, and delete generators
- Global rules: name, purpose, min/max items, total value budget
- Bucket-based selection rules:
  - per-bucket min/max counts
  - rarity filters
  - type substring filters
  - value bounds
  - attunement constraints
  - per-bucket and global uniqueness preferences
- **Run Generator executes from the current UI state**
  - Does not require saving
  - Uses current field values and bucket definitions
  - Fails loudly if constraints cannot be satisfied
- Deterministic engine with optional RNG seeding

### Inventories

- Create inventories manually or from generator output
- Edit name, context, and budget
- Add or remove items
- Persist inventories to the database
- Inventory exports render compact, card-based HTML

### Basket

- Acts as a transient working set
- Generator results append directly into the basket
- Duplicates are allowed by design
- Totals are recomputed immediately after modification
- Basket contents can be exported or converted into inventories

### Admin Tools

- Drop tables by scope or entire schema
- Rebuild metadata-defined tables
- Explicit confirmation for destructive operations
- Operation logging

### Logging

- Central log panel for:
  - imports
  - scraping
  - pricing
  - generator runs
  - internal actions and errors

## 3. Architecture

TowneCodex follows a layered architecture with strict separation of concerns.

src/
townecodex/
ui/
main.py
gui.py
backend.py
workers.py
repos.py
models.py
db.py
dto.py
importer.py
pricing.py
scraper.py
generation/
generator_engine.py
bucket_logic.py

### UI Layer

- PySide6 GUI components
- Owns all visible state
- Talks only to the Backend
- Spawns QRunnable workers for long-running operations

### Worker Layer

- QRunnable-based background tasks
- One worker per operation type (import, query, scrape, pricing, generation)
- Communicates via typed Qt signals
- Never mutates UI state directly

### Backend Layer

- Application orchestration
- Coordinates repositories, importers, and generator engine
- Converts ORM objects into DTOs
- Exposes simple, synchronous methods consumed by workers

### Repository Layer

- SQLAlchemy-based data access
- Search, pagination, and filtering
- Bulk and upsert operations
- Type catalog synchronization

### Model Layer

- ORM classes for:
  - entries
  - inventories
  - inventory items
  - generator definitions
  - type catalogs

### Generator Engine

- Consumes GeneratorConfig and BucketConfig
- Enforces:
  - bucket counts
  - global caps
  - rarity, value, type, and attunement rules
- Processes buckets in order
- Raises explicit errors when constraints cannot be satisfied
- Returns selected entries for conversion to DTOs

## 4. Data Model Summary

### Entry

Represents a D&D item.

Fields include:

- name
- type
- rarity
- value
- attunement_required and criteria
- description
- image_url
- general_type
- specific_type_tags_json

### Inventory

Represents a named collection of items with optional context and budget.

### InventoryItem

Join record connecting an Inventory to an Entry.
Tracks:

- quantity
- unit_value
- total_value

### GeneratorDef

Database record storing a JSON-encoded GeneratorConfig.

### GeneratorConfig / BucketConfig

- In-memory schema used by the generator engine
- Serializable to/from JSON
- Supports future extension via extra fields

## 5. Usage

1. Launch the GUI:
   python -m townecodex.ui.gui
2. Initialize the database if needed.
3. Browse and filter items from the sidebar.
4. Select an item to view or edit its details.
5. Create or load a generator.
6. Modify generator rules and buckets as needed.
7. Click **Run Generator** to generate items from the current UI state.
8. Review results in the basket.
9. Export or convert basket contents into an inventory.
10. View logs for background operations.

## 6. Importing Data

- Supports CSV and XLSX
- Batched processing to keep the UI responsive
- Upserts based on source identifiers when available
- Normalizes type tags
- Optional auto-pricing
- Optional scraping for missing metadata

Post-import routines may run pricing, scraping, or both.

## 7. Development

### First-Time Setup

git clone <repository-url>
cd TowneCodex
poetry install


Poetry will:
create and manage a virtual environment
install all required dependencies (including PySide6)
use the locked dependency versions from poetry.lock

Initialize the Database
(bash)
poetry run python -m townecodex.ui.cli init-db
This only needs to be done once per database.

Run the GUI
poetry run python -m townecodex.ui.gui
