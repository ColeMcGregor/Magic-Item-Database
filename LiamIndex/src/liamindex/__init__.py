"""
LiamIndex package initializer.

This sets up environment loading and exposes key classes/functions
for convenience imports.

author: Cole McGregor
date: 2025-09-16
version: 0.1.0
"""

import os
from dotenv import load_dotenv

# Load .env file if present
load_dotenv()

# Re-export commonly used components
from .db import SessionLocal, engine
from .models import Entry, GeneratorDef
from .repos import EntryRepository, GeneratorRepository
from .scraper import RedditScraper
from . import importer, query, generator

__all__ = [
    # DB
    "SessionLocal",
    "engine",
    # Models
    "Entry",
    "GeneratorDef",
    # Repos
    "EntryRepository",
    "GeneratorRepository",
    # Services
    "RedditScraper",
    "importer",
    "query",
    "generator",
]
