# towne_codex/repo.py
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Optional, Sequence

from contextlib import contextmanager
from sqlalchemy import select, update, func, delete
from sqlalchemy.orm import Session

from .db import SessionLocal
from .models import Entry, GeneratorDef


# --- Search filters for Entries -------------------------------------------------

@dataclass
class EntryFilters:
    """
    Typed filters for searching entries.
    - name_contains: case-insensitive substring over Entry.name, used in tandem with a b-tree index on Entry.name and the trie index on Entry.name
    - type_equals: exact match on Entry.type
    - rarity_in: list/tuple of allowed rarities (exact)
    - attunement_required: True/False to filter, None to ignore
    - text: naive contains search over name + description (case-insensitive)
    """
    name_contains: Optional[str] = None
    type_equals: Optional[str] = None
    rarity_in: Optional[Sequence[str]] = None
    attunement_required: Optional[bool] = None
    text: Optional[str] = None


# --- Repo base utilities --------------------------------------------------------

@contextmanager
def session_scope(session_factory=SessionLocal):
    """
    Provide a transactional scope around a series of operations.
    - Commits if all is well
    - Rolls back on exception
    - Closes the session
    """
    session: Session = session_factory()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


# --- Entry Repository -----------------------------------------------------------

class EntryRepository:
    """
    Data-access boundary for Entry objects.
    - Hides ORM/session details
    - Enforces upsert/dedup rules
    - Owns invariants like price update flag
    - Optionally notifies a SearchService after writes
    """

    def __init__(
        self,
        session_factory=SessionLocal,
        on_entry_changed: Optional[Callable[[Entry], None]] = None,
        on_entry_deleted: Optional[Callable[[int], None]] = None,
    ):
        self._session_factory = session_factory
        self._on_entry_changed = on_entry_changed
        self._on_entry_deleted = on_entry_deleted

    # ---- helpers ---------------------------------------------------------------

    def _notify_changed(self, entry: Entry):
        if self._on_entry_changed:
            try:
                self._on_entry_changed(entry)
            except Exception:
                pass  # don't break writes if the notifier fails

    def _notify_deleted(self, entry_id: int):
        if self._on_entry_deleted:
            try:
                self._on_entry_deleted(entry_id)
            except Exception:
                pass

    # ---- basic reads -----------------------------------------------------------

    def get_by_id(self, entry_id: int) -> Optional[Entry]:
        with session_scope(self._session_factory) as s:
            return s.get(Entry, entry_id)

    def get_by_source_link(self, link: str) -> Optional[Entry]:
        if not link:
            return None
        with session_scope(self._session_factory) as s:
            stmt = select(Entry).where(Entry.source_link == link.strip())
            return s.execute(stmt).scalar_one_or_none()

    # ---- upsert & insert -------------------------------------------------------

    def upsert_entry(self, data: dict) -> Entry:
        """
        Idempotent write:
        - If source_link is present and matches an existing Entry -> update selected fields.
        - Else if (name, type) matches exactly one Entry and no source_link -> update that.
        - Else -> insert a new Entry.

        Expected keys you might provide:
          name, type, rarity,
          attunement_required, attunement_criteria,
          source_link,
          description,
          image_url,             # <--- URL only (no image_path support)
          value, value_updated
        """
        with session_scope(self._session_factory) as s:
            target: Optional[Entry] = None
            link = (data.get("source_link") or "").strip()

            if link:
                target = s.execute(select(Entry).where(Entry.source_link == link)).scalar_one_or_none()
            else:
                nm = (data.get("name") or "").strip()
                tp = (data.get("type") or "").strip()
                if nm and tp:
                    matches = s.execute(select(Entry).where(Entry.name == nm, Entry.type == tp)).scalars().all()
                    if len(matches) == 1:
                        target = matches[0]

            if target is None:
                # INSERT
                target = Entry(
                    name=data.get("name") or "MISSING",
                    type=data.get("type") or "MISSING",
                    rarity=data.get("rarity") or "MISSING",
                    attunement_required=bool(data.get("attunement_required")) if data.get("attunement_required") is not None else False,
                    attunement_criteria=data.get("attunement_criteria"),
                    source_link=link or None,
                    description=data.get("description"),
                    image_url=data.get("image_url"),   # URL only
                    value=data.get("value"),
                    value_updated=bool(data.get("value_updated")) if data.get("value_updated") is not None else False,
                )
                s.add(target)
                s.flush()  # populate id
            else:
                # UPDATE (do not clobber with None/empty)
                _assign_if_present(target, "name", data)
                _assign_if_present(target, "type", data)
                _assign_if_present(target, "rarity", data)
                _assign_if_present(target, "attunement_required", data)
                _assign_if_present(target, "attunement_criteria", data)
                _assign_if_present(target, "description", data)
                _assign_if_present(target, "image_url", data)  # URL only

                # Value is special: only update if provided; don't flip value_updated here
                if "value" in data and data["value"] is not None:
                    target.value = data["value"]
                if "value_updated" in data and data["value_updated"] is not None:
                    target.value_updated = bool(data["value_updated"])

        # Notify after commit
        saved = self.get_by_id(target.id)  # type: ignore[arg-type]
        if saved:
            self._notify_changed(saved)
            return saved
        return target  # type: ignore[return-value]

    # ---- price updates ---------------------------------------------------------

    def update_price(self, entry_id: int, new_value: int) -> None:
        with session_scope(self._session_factory) as s:
            stmt = update(Entry).where(Entry.id == entry_id).values(value=new_value, value_updated=True)
            s.execute(stmt)
        updated = self.get_by_id(entry_id)
        if updated:
            self._notify_changed(updated)

    # ---- delete ---------------------------------------------------------------

    def delete_by_id(self, entry_id: int) -> bool:
        with session_scope(self._session_factory) as s:
            obj = s.get(Entry, entry_id)
            if not obj:
                return False
            s.delete(obj)
        self._notify_deleted(entry_id)
        return True

    def clear_all_entries(self) -> int:
        with session_scope(self._session_factory) as s:
            result = s.execute(delete(Entry))
            return result.rowcount or 0

    # ---- search & list --------------------------------------------------------

    def search(self, filters: EntryFilters, *, page: int = 1, size: int = 50, sort: Optional[str] = None) -> list[Entry]:
        """
        Simple search with pagination and optional sort.
        sort examples: "name", "-name", "rarity", "-value"
        """
        with session_scope(self._session_factory) as s:
            stmt = select(Entry)

            if filters.name_contains:
                stmt = stmt.where(Entry.name.ilike(f"%{filters.name_contains}%"))

            if filters.type_equals:
                stmt = stmt.where(Entry.type == filters.type_equals)

            if filters.rarity_in:
                stmt = stmt.where(Entry.rarity.in_(list(filters.rarity_in)))

            if filters.attunement_required is not None:
                stmt = stmt.where(Entry.attunement_required == filters.attunement_required)

            if filters.text:
                q = f"%{filters.text}%"
                # COALESCE avoids NULL swallowing the predicate when description is NULL
                stmt = stmt.where(
                    (Entry.name.ilike(q)) | (func.coalesce(Entry.description, "").ilike(q))
                )

            # Sorting
            if sort:
                desc = sort.startswith("-")
                key = sort[1:] if desc else sort
                col = {
                    "id": Entry.id,
                    "name": Entry.name,
                    "type": Entry.type,
                    "rarity": Entry.rarity,
                    "value": Entry.value,
                }.get(key, Entry.name)
                stmt = stmt.order_by(col.desc() if desc else col.asc())
            else:
                stmt = stmt.order_by(Entry.name.asc())

            page = max(1, page)
            size = max(1, size)
            stmt = stmt.offset((page - 1) * size).limit(size)
            return list(s.execute(stmt).scalars().all())

    def list(self, *, page: int = 1, size: int = 50, sort: Optional[str] = None) -> list[Entry]:
        return self.search(EntryFilters(), page=page, size=size, sort=sort)


# --- Generator Repository -------------------------------------------------------

class GeneratorRepository:
    def __init__(self, session_factory=SessionLocal):
        self._session_factory = session_factory

    def insert(self, generator: GeneratorDef) -> GeneratorDef:
        with session_scope(self._session_factory) as s:
            s.add(generator)
            s.flush()
            return generator

    def get_by_id(self, gen_id: int) -> Optional[GeneratorDef]:
        with session_scope(self._session_factory) as s:
            return s.get(GeneratorDef, gen_id)

    def list_all(self) -> list[GeneratorDef]:
        with session_scope(self._session_factory) as s:
            stmt = select(GeneratorDef).order_by(GeneratorDef.name.asc())
            return list(s.execute(stmt).scalars().all())
    
    def delete_by_id(self, gen_id: int) -> bool:
        with session_scope(self._session_factory) as s:
            obj = s.get(GeneratorDef, gen_id)
            if not obj:
                return False
            s.delete(obj)
        return True


# --- internal helpers -----------------------------------------------------------

def _assign_if_present(obj: object, field: str, data: dict):
    if field in data and data[field] is not None:
        setattr(obj, field, data[field])
