# TowneCodex

TowneCodex is a desktop application for browsing, editing, generating, and organizing Dungeons & Dragons 5e items.
It supports structured type catalogs, customizable loot generators, inventories, bucket rules, CSV/XLSX imports,
scraping, and admin-level schema operations.

Built with Python, SQLAlchemy, and PySide6.

## 1. Overview

TowneCodex provides a centralized interface for organizing D&D items and tools for building generators and inventories.
It is designed for DMs, worldbuilders, and homebrew creators who need fast lookup, structured filtering, and consistent
rules for item generation.

Key capabilities include:

- Item creation, editing, and deletion
- Structured type catalogs
- Custom loot generators
- Inventory management
- Fast search and filters
- Import workflows
- Scraping and auto-pricing
- Admin schema operations

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
- Batch import with size and sleep controls
- Upsert logic that preserves existing non-empty values

### Pricing and Metadata

- Automatic pricing for entries missing a value
- Scraping of Reddit-linked posts for descriptions and images
- Optional combined post-processing routines

### Generators

- Create, edit, and delete generators
- Global rules: name, purpose, min/max items, budget
- Bucket-based selection rules supporting rarity, price, attunement, and count constraints
- Deterministic engine for consistent results

### Inventories

- Create inventories manually or from generator results
- Edit name, context, and budget
- Add or remove items
- Save inventories persistently

### Admin Tools

- Drop tables by scope or the entire schema
- Rebuild metadata-defined tables
- Operation logging

### Logging

- Log panel for import runs, scraping, generator results, and internal actions

## 3. Architecture

TowneCodex follows a layered architecture for clarity and maintainability.

src/
townecodex/
ui/
main.py
gui.py
backend.py
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

markdown
Copy code

### UI Layer

- PySide6 GUI components
- Talks only to the Backend
- Handles forms, tables, selection, and dialogs

### Backend Layer

- Application logic
- Coordinates repositories, importers, and generators
- Provides simple methods consumed by the GUI

### Repository Layer

- SQLAlchemy-based data access
- Upsert and bulk operations
- Search, pagination, sorting
- Type catalog synchronization

### Model Layer

- ORM classes for entries, inventories, generator definitions, and type catalogs

### Generator Engine

- Reads generator configs and bucket rules
- Applies rarity, value, count, and attunement requirements
- Produces inventory-like sets of selected items

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

Represents a collection of items with a name, context, and budget.

### InventoryItem

Join record connecting an Inventory to an Entry.
Tracks:

- quantity
- unit_value
- total_value (computed)

### GeneratorDef

JSON-encoded generator configuration containing global fields and bucket rules.

### GeneralType and SpecificType

Used to construct structured type catalogs for filtering and searching.

## 5. Usage

1. Launch the GUI:

python -m townecodex.ui.gui

pgsql
Copy code

2. Initialize the database if needed.
3. Browse and filter items from the sidebar.
4. Select an item to view or edit its details.
5. Create and run generators.
6. Build inventories manually or from generator output.
7. Import data via CSV/XLSX.
8. View logs for background operations.

## 6. Importing Data

- Supports CSV and XLSX
- Uses batched processing to prevent UI blocking
- Upserts based on source_link when present
- Normalizes specific type tags
- Optional auto-pricing
- Optional scraping for missing metadata

Post-import routines can run pricing, scraping, or both.

## 7. Development

### Installation

pip install -r requirements.txt

shell
Copy code

### Database Initialization

python -m townecodex.ui.cli init-db

shell
Copy code

### Running the GUI

python -m townecodex.ui.gui

markdown
Copy code

### Testing

Recommended targets:

- Repositories
- Generator engine
- Importer
- Inventory logic
- UI workflows via stubs

## 8. License

Project is proprietary.
Do not redistribute without permission.
