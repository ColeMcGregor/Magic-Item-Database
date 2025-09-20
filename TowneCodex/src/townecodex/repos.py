# towne_codex/repo.py
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Iterable, Optional, Sequence

from contextlib import contextmanager
from sqlalchemy import select, update, func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from .db import SessionLocal
from .models import Entry, GeneratorDef


# --- Search filters for Entries -------------------------------------------------

@dataclass
class EntryFilters:
    """
    Typed filters for searching entries.
    - name_contains: case-insensitive substring over Entry.name
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
        """
        on_entry_changed(entry): called after successful insert/update (commit)
        on_entry_deleted(entry_id): called after successful delete (commit)
        """
        self._session_factory = session_factory
        self._on_entry_changed = on_entry_changed
        self._on_entry_deleted = on_entry_deleted

    # ---- helpers ---------------------------------------------------------------

    def _notify_changed(self, entry: Entry):
        if self._on_entry_changed:
            try:
                self._on_entry_changed(entry)
            except Exception:
                # Don't break writes if the notifier fails
                pass

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
            stmt = select(Entry).where(Entry.source_link == link)
            return s.execute(stmt).scalar_one_or_none()

    # ---- upsert & insert -------------------------------------------------------

    def upsert_entry(self, data: dict) -> Entry:
        """
        Idempotent write:
        - If source_link is present and matches an existing Entry -> update selected fields.
        - Else if (name, type) tuple matches exactly one Entry and no source_link is provided -> update that.
        - Else -> insert a new Entry.

        Expected keys in data (use what you have):
          name, type, rarity,
          attunement_required, attunement_criteria,
          source_link,
          description,
          image_url (if your model has it) OR image_path (fallback),
          value, value_updated  (value_updated typically defaults False on first insert)
        """
        with session_scope(self._session_factory) as s:
            target: Optional[Entry] = None
            link = (data.get("source_link") or "").strip()

            if link:
                target = s.execute(select(Entry).where(Entry.source_link == link)).scalar_one_or_none()
            else:
                # Fallback dedupe: try unique (name, type) if link missing
                nm = (data.get("name") or "").strip()
                tp = (data.get("type") or "").strip()
                if nm and tp:
                    matches = s.execute(
                        select(Entry).where(Entry.name == nm, Entry.type == tp)
                    ).scalars().all()
                    if len(matches) == 1:
                        target = matches[0]

            if target is None:
                # INSERT path
                target = Entry(
                    name=data.get("name") or "MISSING",
                    type=data.get("type") or "MISSING",
                    rarity=data.get("rarity") or "MISSING",
                    attunement_required=bool(data.get("attunement_required")) if data.get("attunement_required") is not None else False,
                    attunement_criteria=data.get("attunement_criteria"),
                    source_link=link or None,
                    description=data.get("description"),
                    # support either image_url (preferred) or image_path (legacy)
                    **_image_field_kwargs(data),
                    value=data.get("value"),
                    value_updated=bool(data.get("value_updated")) if data.get("value_updated") is not None else False,
                )
                s.add(target)
                s.flush()  # populate target.id
            else:
                # UPDATE path — do not clobber existing values with None/empty unless explicitly provided
                _assign_if_present(target, "name", data)
                _assign_if_present(target, "type", data)
                _assign_if_present(target, "rarity", data)
                _assign_if_present(target, "attunement_required", data)
                _assign_if_present(target, "attunement_criteria", data)
                _assign_if_present(target, "description", data)
                # Image fields
                _assign_image_fields(target, data)
                # Value: only update if provided; do NOT flip value_updated here automatically
                # (use update_price for that invariant)
                if "value" in data and data["value"] is not None:
                    target.value = data["value"]
                if "value_updated" in data and data["value_updated"] is not None:
                    target.value_updated = bool(data["value_updated"])

            # commit happens in session_scope; call notifier after commit by fetching a detached copy
        # Fetch again to notify with a loaded instance
        saved = self.get_by_id(target.id)  # type: ignore[arg-type]
        if saved:
            self._notify_changed(saved)
            return saved
        # Should never happen
        return target  # type: ignore[return-value]

    # ---- price updates ---------------------------------------------------------

    def update_price(self, entry_id: int, new_value: int) -> None:
        """
        Update the price and flip value_updated=True (marks that user changed it).
        """
        with session_scope(self._session_factory) as s:
            stmt = (
                update(Entry)
                .where(Entry.id == entry_id)
                .values(value=new_value, value_updated=True)
            )
            s.execute(stmt)

        # Notify after commit
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
                stmt = stmt.where(
                    (Entry.name.ilike(q)) | (Entry.description.ilike(q))
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

            if page < 1:
                page = 1
            if size < 1:
                size = 50

            stmt = stmt.offset((page - 1) * size).limit(size)
            return list(s.execute(stmt).scalars().all())

    def list(self, *, page: int = 1, size: int = 50, sort: Optional[str] = None) -> list[Entry]:
        return self.search(EntryFilters(), page=page, size=size, sort=sort)


# --- Generator Repository -------------------------------------------------------

class GeneratorRepository:
    """
    Thin repository for generator definitions.
    """

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


# --- internal helpers -----------------------------------------------------------

def _assign_if_present(obj: object, field: str, data: dict):
    if field in data and data[field] is not None:
        setattr(obj, field, data[field])

def _image_field_kwargs(data: dict) -> dict:
    """
    Supports either a modern 'image_url' field or legacy 'image_path'.
    Prefer image_url if provided; otherwise pass image_path.
    """
    if "image_url" in data and data["image_url"]:
        # If your Entry model has image_url column, this will be assigned.
        return {"image_url": data["image_url"]} if hasattr(Entry, "image_url") else {"image_path": data["image_url"]}
    if "image_path" in data and data["image_path"]:
        return {"image_path": data["image_path"]}
    return {}

def _assign_image_fields(entry: Entry, data: dict):
    """
    Assign image fields safely regardless of whether the model uses image_url or image_path.
    """
    if "image_url" in data and data["image_url"]:
        if hasattr(entry, "image_url"):
            entry.image_url = data["image_url"]  # type: ignore[attr-defined]
        else:
            entry.image_path = data["image_url"]  # fallback store
    if "image_path" in data and data["image_path"]:
        entry.image_path = data["image_path"]
