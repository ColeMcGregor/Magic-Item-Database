from __future__ import annotations
import os
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from .models import Base

# ---------------------------------------------------------------------------
# Database Path (always absolute, in src/data)
# ---------------------------------------------------------------------------
# This resolves to: <project_root>/src/data/townecodex.db
# Override via DATABASE_URL env if needed (e.g., for tests).
# ---------------------------------------------------------------------------

PKG_DIR = Path(__file__).resolve().parent            # src/townecodex
SRC_DIR = PKG_DIR.parent                             # src
DATA_DIR = SRC_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)
DB_PATH = DATA_DIR / "townecodex.db"

# DATABASE_URL is the URL of the database
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{DB_PATH.as_posix()}")

# engine is the database engine
engine = create_engine(
    DATABASE_URL,
    echo=False,
    future=True,
    connect_args={"check_same_thread": False},  # Qt/threads-safe
)

# SessionLocal is a factory for creating new database sessions
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
    expire_on_commit=False,
)

def init_db() -> None:
    """Create all tables defined in models.py (idempotent)."""
    Base.metadata.create_all(bind=engine)
