# townecodex/admin_ops.py
from __future__ import annotations

"""
Admin-level database operations for Towne Codex.

This module centralizes "big hammer" actions that affect whole tables
or groups of tables, for use by the Admin menu in the GUI.

Concepts:
    - AdminScope: what part of the DB you are targeting
        * WHOLE_DB
        * ENTRIES_AND_DEPENDENTS  (entries + inventories + inventory_items + type catalog)
        * INVENTORIES             (inventories + inventory_items only)
        * GENERATORS              (generator definitions table)
        * TYPE_CATALOG            (general_types + specific_types only)

    - AdminAction: what you want to do
        * CREATE   -> create tables for this scope (no-op if already exist)
        * DROP     -> drop tables for this scope (data and schema gone)
        * RESET    -> DROP + CREATE for this scope
        * CLEAR    -> delete all rows but keep schema (truncate)

    - DB status:
        * get_db_status(): introspects which tables exist and row counts.

Notes:
    - InventoryItems are always treated as dependent on Inventories; there
      is no direct control surface for them.
    - GeneralType and SpecificType are treated as a unit.
    - When ENTRIES are destroyed/cleared, inventories, inventory_items, and
      type catalog are also destroyed/cleared. Generators remain intact.

author: Cole McGregor, ChatGPT
date: 2025-11-24
version: 0.1.0
"""

from dataclasses import dataclass
from enum import Enum, auto
from typing import Dict, List

from sqlalchemy import delete, func, inspect, select
from sqlalchemy.exc import SQLAlchemyError

from .db import engine, SessionLocal
from .models import (
    Base,
    Entry,
    Inventory,
    InventoryItem,
    GeneratorDef,
    GeneralType,
    SpecificType,
)


# ---------------------------------------------------------------------------
# Scopes & actions
# ---------------------------------------------------------------------------


class AdminScope(Enum):
    """Logical scope for admin operations."""

    WHOLE_DB = auto()
    ENTRIES_AND_DEPENDENTS = auto()
    INVENTORIES = auto()
    GENERATORS = auto()
    TYPE_CATALOG = auto()


class AdminAction(Enum):
    """Admin operations that can be performed on a scope."""

    CREATE = auto()
    DROP = auto()
    RESET = auto()
    CLEAR = auto()


@dataclass(frozen=True)
class AdminResult:
    """Summary of an admin operation."""

    scope: AdminScope
    action: AdminAction
    success: bool
    message: str
    tables_affected: List[str]


# ---------------------------------------------------------------------------
# Table groups
# ---------------------------------------------------------------------------

# Basic label -> model mapping, for status probes mostly
_TABLE_MODELS: Dict[str, type] = {
    "entries": Entry,
    "inventories": Inventory,
    "inventory_items": InventoryItem,
    "generators": GeneratorDef,
    "general_types": GeneralType,
    "specific_types": SpecificType,
}

# Higher-level groups per scope (model classes, not table names).
# Note: ordering of tables for DROP/CREATE is handled by SQLAlchemy's metadata
# when using Base.metadata.drop_all/create_all(tables=...).
_SCOPE_TABLES: Dict[AdminScope, List[type]] = {
    AdminScope.ENTRIES_AND_DEPENDENTS: [
        InventoryItem,
        Inventory,
        Entry,
        SpecificType,
        GeneralType,
    ],
    AdminScope.INVENTORIES: [
        InventoryItem,
        Inventory,
    ],
    AdminScope.GENERATORS: [
        GeneratorDef,
    ],
    AdminScope.TYPE_CATALOG: [
        SpecificType,
        GeneralType,
    ],
}


# ---------------------------------------------------------------------------
# DB status / ping
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class TableStatus:
    table_name: str
    exists: bool
    row_count: int | None  # None if table does not exist


def get_db_status() -> Dict[str, TableStatus]:
    """
    Inspect the database and report existence + row counts for known tables.

    Returns:
        Dict keyed by logical label (e.g. "entries") with:
            - table_name: actual DB table name
            - exists: whether the table currently exists
            - row_count: number of rows (if exists), else None
    """
    inspector = inspect(engine)
    existing_tables = set(inspector.get_table_names())
    status: Dict[str, TableStatus] = {}

    with SessionLocal() as s:
        for label, model in _TABLE_MODELS.items():
            tbl_name = model.__tablename__
            exists = tbl_name in existing_tables

            if exists:
                count = s.execute(
                    select(func.count()).select_from(model)
                ).scalar_one()
                row_count: int | None = int(count)
            else:
                row_count = None

            status[label] = TableStatus(
                table_name=tbl_name,
                exists=exists,
                row_count=row_count,
            )

    return status


# ---------------------------------------------------------------------------
# Core helpers
# ---------------------------------------------------------------------------


def _tables_for_scope(scope: AdminScope) -> List[type]:
    """Return model classes for the given scope."""
    if scope is AdminScope.WHOLE_DB:
        # Whole DB: all mapped tables in this metadata
        return list(Base.metadata.tables.values())  # type: ignore[list-item]
    return _SCOPE_TABLES.get(scope, [])


def _create_scope_tables(scope: AdminScope) -> List[str]:
    """Create tables for the given scope. Returns list of table names affected."""
    if scope is AdminScope.WHOLE_DB:
        Base.metadata.create_all(bind=engine)
        return list(Base.metadata.tables.keys())

    tables = _tables_for_scope(scope)
    if not tables:
        return []

    Base.metadata.create_all(bind=engine, tables=[m.__table__ for m in tables])
    return [m.__tablename__ for m in tables]


def _drop_scope_tables(scope: AdminScope) -> List[str]:
    """Drop tables for the given scope. Returns list of table names affected."""
    if scope is AdminScope.WHOLE_DB:
        names = list(Base.metadata.tables.keys())
        Base.metadata.drop_all(bind=engine)
        return names

    tables = _tables_for_scope(scope)
    if not tables:
        return []

    # drop_all will work out correct dependency order
    Base.metadata.drop_all(bind=engine, tables=[m.__table__ for m in tables])
    return [m.__tablename__ for m in tables]


def _clear_scope_rows(scope: AdminScope) -> List[str]:
    """
    Delete all rows for the given scope, keeping schema.

    Returns list of table names affected.
    """
    affected: List[str] = []

    if scope is AdminScope.WHOLE_DB:
        # Clear everything explicitly. Order: children first.
        model_order = [
            InventoryItem,
            Inventory,
            SpecificType,
            GeneralType,
            GeneratorDef,
            Entry,
        ]
    elif scope is AdminScope.ENTRIES_AND_DEPENDENTS:
        model_order = [
            InventoryItem,
            Inventory,
            SpecificType,
            GeneralType,
            Entry,
        ]
    elif scope is AdminScope.INVENTORIES:
        model_order = [
            InventoryItem,
            Inventory,
        ]
    elif scope is AdminScope.GENERATORS:
        model_order = [GeneratorDef]
    elif scope is AdminScope.TYPE_CATALOG:
        model_order = [
            SpecificType,
            GeneralType,
        ]
    else:
        model_order = []

    if not model_order:
        return affected

    with SessionLocal() as s:
        try:
            for model in model_order:
                tbl_name = model.__tablename__
                s.execute(delete(model))
                affected.append(tbl_name)
            s.commit()
        except SQLAlchemyError:
            s.rollback()
            raise

    return affected


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def create_scope(scope: AdminScope) -> AdminResult:
    """
    Create tables for the given scope.

    WHOLE_DB:
        - Create all tables in the metadata.
    Other scopes:
        - Create only the tables mapped to that scope.
    """
    try:
        tables = _create_scope_tables(scope)
        msg = "Created tables: " + ", ".join(sorted(tables)) if tables else "No tables to create."
        return AdminResult(
            scope=scope,
            action=AdminAction.CREATE,
            success=True,
            message=msg,
            tables_affected=sorted(tables),
        )
    except Exception as exc:
        return AdminResult(
            scope=scope,
            action=AdminAction.CREATE,
            success=False,
            message=f"CREATE failed: {exc}",
            tables_affected=[],
        )


def drop_scope(scope: AdminScope) -> AdminResult:
    """
    Drop tables for the given scope.

    WHOLE_DB:
        - Drop the entire schema (all tables).
    ENTRIES_AND_DEPENDENTS:
        - Drop entries, inventories, inventory_items, type catalog tables.
        - GeneratorDef is left intact.
    INVENTORIES:
        - Drop inventories and inventory_items.
    GENERATORS:
        - Drop generators table only.
    TYPE_CATALOG:
        - Drop general_types and specific_types tables.
    """
    try:
        tables = _drop_scope_tables(scope)
        msg = "Dropped tables: " + ", ".join(sorted(tables)) if tables else "No tables to drop."
        return AdminResult(
            scope=scope,
            action=AdminAction.DROP,
            success=True,
            message=msg,
            tables_affected=sorted(tables),
        )
    except Exception as exc:
        return AdminResult(
            scope=scope,
            action=AdminAction.DROP,
            success=False,
            message=f"DROP failed: {exc}",
            tables_affected=[],
        )


def clear_scope(scope: AdminScope) -> AdminResult:
    """
    Delete all rows in the tables for this scope but keep the schema.

    Cascades:
        - For ENTRIES_AND_DEPENDENTS: entries, inventories, inventory_items,
          and type catalog are cleared together. Generators remain intact.
        - For INVENTORIES: inventories and inventory_items are cleared.
        - For TYPE_CATALOG: both general_types and specific_types are cleared.
        - For WHOLE_DB: all known tables are cleared.
    """
    try:
        tables = _clear_scope_rows(scope)
        msg = "Cleared rows in tables: " + ", ".join(sorted(tables)) if tables else "No tables cleared."
        return AdminResult(
            scope=scope,
            action=AdminAction.CLEAR,
            success=True,
            message=msg,
            tables_affected=sorted(tables),
        )
    except Exception as exc:
        return AdminResult(
            scope=scope,
            action=AdminAction.CLEAR,
            success=False,
            message=f"CLEAR failed: {exc}",
            tables_affected=[],
        )


def reset_scope(scope: AdminScope) -> AdminResult:
    """
    Reset a scope: DROP its tables and CREATE them again.

    This is more destructive than CLEAR, since schema is recreated.
    """
    # First drop
    drop_result = drop_scope(scope)
    if not drop_result.success:
        return AdminResult(
            scope=scope,
            action=AdminAction.RESET,
            success=False,
            message=f"RESET failed during DROP: {drop_result.message}",
            tables_affected=[],
        )

    # Then create
    create_result = create_scope(scope)
    success = create_result.success
    if not success:
        msg = f"RESET failed during CREATE: {create_result.message}"
        return AdminResult(
            scope=scope,
            action=AdminAction.RESET,
            success=False,
            message=msg,
            tables_affected=[],
        )

    # On success, union of tables from both phases
    tables = sorted(set(drop_result.tables_affected) | set(create_result.tables_affected))
    msg = "Reset tables: " + ", ".join(tables) if tables else "No tables reset."
    return AdminResult(
        scope=scope,
        action=AdminAction.RESET,
        success=True,
        message=msg,
        tables_affected=tables,
    )


def perform_admin_action(scope: AdminScope, action: AdminAction) -> AdminResult:
    """
    Convenience dispatcher for the higher-level API.

    Example usage from GUI:
        from townecodex.admin_ops import AdminScope, AdminAction, perform_admin_action

        result = perform_admin_action(AdminScope.ENTRIES_AND_DEPENDENTS, AdminAction.CLEAR)
        if result.success:
            log(result.message)
        else:
            show_error(result.message)
    """
    if action is AdminAction.CREATE:
        return create_scope(scope)
    if action is AdminAction.DROP:
        return drop_scope(scope)
    if action is AdminAction.CLEAR:
        return clear_scope(scope)
    if action is AdminAction.RESET:
        return reset_scope(scope)

    return AdminResult(
        scope=scope,
        action=action,
        success=False,
        message=f"Unsupported admin action: {action!r}",
        tables_affected=[],
    )


__all__ = [
    "AdminScope",
    "AdminAction",
    "AdminResult",
    "TableStatus",
    "get_db_status",
    "create_scope",
    "drop_scope",
    "clear_scope",
    "reset_scope",
    "perform_admin_action",
]
