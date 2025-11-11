

from __future__ import annotations
import os

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from .models import Base

"""
Database setup file for the program. takes in new database url from the .env file.

author: Cole McGregor
date: 2025-09-17
version: 0.1.0
"""


# -----------------------------------------------------------------------------
# Database URL
# -----------------------------------------------------------------------------
# Default: SQLite in project root
# Override with DATABASE_URL env var (e.g., postgres://user:pass@localhost/dbname)
# -----------------------------------------------------------------------------
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///townecodex.db")

# -----------------------------------------------------------------------------
# Engine & Session
# -----------------------------------------------------------------------------
# echo=True shows all SQL emitted (good for debugging)
# future=True enables SQLAlchemy 2.0 style API
# -----------------------------------------------------------------------------
engine = create_engine(
    DATABASE_URL,
    echo=False,
    future=True,
)

# a sessionmaker is used to create a session.
# autocommit is used to commit the session. set to false to allow for manual commits.
# autoflush is used to flush the session, which means
# bind is used to bind the session to the engine.
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
    expire_on_commit=False,  
)


# -----------------------------------------------------------------------------
# Init function
# -----------------------------------------------------------------------------
def init_db() -> None:
    """
    Create all tables defined in models.py.
    Safe to call multiple times.
    """
    Base.metadata.create_all(bind=engine)
