# towne_codex/repo.py
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Optional, Sequence, Iterable, Dict, Any, Tuple, List
from contextlib import contextmanager

from sqlalchemy import select, update, func, delete
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from .pricing import compute_price
from .db import SessionLocal
from .models import Entry, GeneratorDef


# --- Search filters ------------------------------------------------------------

@dataclass
class EntryFilters:
    name_contains: Optional[str] = None
    type_equals: Optional[str] = None
    rarity_in: Optional[Sequence[str]] = None
    attunement_required: Optional[bool] = None
    text: Optional[str] = None


# --- Session scope -------------------------------------------------------------

@contextmanager
def session_scope(session_factory=SessionLocal):
    s: Session = session_factory()
    try:
        yield s
        s.commit()
    except Exception:
        s.rollback()
        raise
    finally:
        s.close()


# --- Internal helpers ----------------------------------------------------------

def _trim(s: Optional[str]) -> Optional[str]:
    if s is None:
        return None
    t = s.strip()
    return t if t else None

def _assign_if_present_nonempty(obj: object, field: str, data: Dict[str, Any]) -> None:
    if field not in data:
        return
    v = data[field]
    if isinstance(v, str):
        v = _trim(v)
    if v is None or v == "":
        return
    setattr(obj, field, v)

def _coerce_bool(v: Any, default: bool = False) -> bool:
    if v is None:
        return default
    return bool(v)


# --- Entry Repository ----------------------------------------------------------

class EntryRepository:
    """
    Data-access boundary for Entry objects.
    - Upsert by source_link; fallback to (name,type) when link is absent and unique.
    - Never clobber existing fields with empty/whitespace values.
    - Trims all incoming strings.
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

    # -- notifications ----------------------------------------------------------

    def _notify_changed(self, entry: Entry) -> None:
        if self._on_entry_changed:
            try:
                self._on_entry_changed(entry)
            except Exception:
                pass

    def _notify_deleted(self, entry_id: int) -> None:
        if self._on_entry_deleted:
            try:
                self._on_entry_deleted(entry_id)
            except Exception:
                pass

    # -- basic reads ------------------------------------------------------------

    def get_by_id(self, entry_id: int) -> Optional[Entry]:
        with session_scope(self._session_factory) as s:
            return s.get(Entry, entry_id)

    def get_by_source_link(self, link: str) -> Optional[Entry]:
        link = _trim(link) or ""
        if not link:
            return None
        with session_scope(self._session_factory) as s:
            stmt = select(Entry).where(Entry.source_link == link)
            return s.execute(stmt).scalar_one_or_none()

    # -- upsert/insert ----------------------------------------------------------

    def upsert_entry(self, data: Dict[str, Any]) -> Entry:
        # Pre-trim the common string fields up front
        for k in ("name", "type", "rarity", "attunement_criteria", "source_link", "description", "image_url"):
            if k in data and isinstance(data[k], str):
                data[k] = _trim(data[k])

        obj_id: Optional[int] = None

        with session_scope(self._session_factory) as s:
            target: Optional[Entry] = None
            link = data.get("source_link") or ""

            if link:
                target = s.execute(select(Entry).where(Entry.source_link == link)).scalar_one_or_none()
            else:
                nm = data.get("name") or ""
                tp = data.get("type") or ""
                if nm and tp:
                    matches = s.execute(select(Entry).where(Entry.name == nm, Entry.type == tp)).scalars().all()
                    if len(matches) == 1:
                        target = matches[0]

            if target is None:
                # INSERT (defaults applied; no empty sentinels)
                target = Entry(
                    name=data.get("name") or "Unknown",
                    type=data.get("type") or "Unknown",
                    rarity=data.get("rarity") or "Unknown",
                    attunement_required=_coerce_bool(data.get("attunement_required"), False),
                    attunement_criteria=data.get("attunement_criteria"),
                    source_link=link or None,
                    description=data.get("description"),
                    image_url=data.get("image_url"),
                    value=data.get("value"),
                    value_updated=_coerce_bool(data.get("value_updated"), False),
                )
                s.add(target)
                try:
                    s.flush()  # ensure PK populated
                except IntegrityError:
                    s.rollback()
                    # Race: another transaction inserted this link; retry as update
                    with session_scope(self._session_factory) as s2:
                        existing = s2.execute(select(Entry).where(Entry.source_link == link)).scalar_one_or_none()
                        if existing:
                            self._update_existing_internal(existing, data, s2)
                            obj_id = int(existing.id)
                        else:
                            raise
                else:
                    obj_id = int(target.id)
            else:
                self._update_existing_internal(target, data, s)
                obj_id = int(target.id)

        # Reload in a fresh session for clean, attached instance
        if obj_id is not None:
            saved = self.get_by_id(obj_id)
            if saved:
                self._notify_changed(saved)
                return saved
        # Fallback (shouldn't happen)
        return target  # type: ignore[return-value]


    def _update_existing_internal(self, target: Entry, data: Dict[str, Any], s: Session) -> Entry:
        # String fields: assign only if non-empty present
        for fld in ("name", "type", "rarity", "attunement_criteria", "description", "image_url"):
            _assign_if_present_nonempty(target, fld, data)

        # Booleans: explicit control (do not infer from empty)
        if "attunement_required" in data and data["attunement_required"] is not None:
            target.attunement_required = bool(data["attunement_required"])

        # Value semantics
        if "value" in data and data["value"] is not None:
            target.value = int(data["value"])
        if "value_updated" in data and data["value_updated"] is not None:
            target.value_updated = bool(data["value_updated"])

        s.flush()
        return target

    def bulk_upsert(self, items: Iterable[Dict[str, Any]]) -> Tuple[int, int]:
        """
        Upsert many entries in one transaction.
        Returns: (created_count, updated_count)
        """
        created = 0
        updated = 0
        with session_scope(self._session_factory) as s:
            for data in items:
                # Trim strings
                for k in ("name", "type", "rarity", "attunement_criteria", "source_link", "description", "image_url"):
                    if k in data and isinstance(data[k], str):
                        data[k] = _trim(data[k])

                link = data.get("source_link") or ""
                target: Optional[Entry] = None
                if link:
                    target = s.execute(select(Entry).where(Entry.source_link == link)).scalar_one_or_none()
                else:
                    nm = data.get("name") or ""
                    tp = data.get("type") or ""
                    if nm and tp:
                        rows = s.execute(select(Entry).where(Entry.name == nm, Entry.type == tp)).scalars().all()
                        if len(rows) == 1:
                            target = rows[0]

                if target is None:
                    e = Entry(
                        name=data.get("name") or "Unknown",
                        type=data.get("type") or "Unknown",
                        rarity=data.get("rarity") or "Unknown",
                        attunement_required=_coerce_bool(data.get("attunement_required"), False),
                        attunement_criteria=data.get("attunement_criteria"),
                        source_link=link or None,
                        description=data.get("description"),
                        image_url=data.get("image_url"),
                        value=data.get("value"),
                        value_updated=_coerce_bool(data.get("value_updated"), False),
                    )
                    s.add(e)
                    try:
                        s.flush()
                    except IntegrityError:
                        s.rollback()
                        # Retry as update if another tx inserted it
                        with session_scope(self._session_factory) as s2:
                            existing = s2.execute(select(Entry).where(Entry.source_link == link)).scalar_one_or_none()
                            if existing:
                                self._update_existing_internal(existing, data, s2)
                                updated += 1
                            else:
                                raise
                    else:
                        created += 1
                else:
                    self._update_existing_internal(target, data, s)
                    updated += 1

        return created, updated

    # -- price updates ----------------------------------------------------------

    def update_price(self, entry_id: int, new_value: int) -> None:
        with session_scope(self._session_factory) as s:
            stmt = update(Entry).where(Entry.id == entry_id).values(value=new_value, value_updated=True)
            s.execute(stmt)
        updated = self.get_by_id(entry_id)
        if updated:
            self._notify_changed(updated)

    def fill_missing_prices_from_chart(self, *, commit: bool = True) -> int:
        """
        Walk all entries with value == NULL and set a default price using
        the pricing chart. Returns the number of entries updated.
        """
        updated = 0
        with SessionLocal() as session:
            q = session.query(Entry).filter(Entry.value.is_(None))
            for e in q:
                price = compute_price(
                    rarity=e.rarity,
                    type_text=e.type,
                    attunement_required=e.attunement_required,
                )
                if price is None:
                    continue
                e.value = price
                # this is an automatic chart price, not a user override
                e.value_updated = False
                updated += 1

            if commit and updated:
                session.commit()
            elif not commit:
                session.rollback()

        return updated

    # -- delete -----------------------------------------------------------------

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
            # Rely on FK cascade for inventory_items; add DB test to confirm.
            return result.rowcount or 0

    # -- search & list ----------------------------------------------------------

    def search(
        self,
        filters: EntryFilters,
        *,
        page: int = 1,
        size: int = 50,
        sort: Optional[str] = None
    ) -> List[Entry]:
        items, _ = self.search_with_total(filters, page=page, size=size, sort=sort)
        return items

    def search_with_total(
        self,
        filters: EntryFilters,
        *,
        page: int = 1,
        size: int = 50,
        sort: Optional[str] = None
    ) -> Tuple[List[Entry], int]:
        """
        Returns (items, total_count) for pagination UIs.
        """
        with session_scope(self._session_factory) as s:
            base = select(Entry)

            if filters.name_contains:
                base = base.where(Entry.name.ilike(f"%{filters.name_contains}%"))

            if filters.type_equals:
                # decide case-sensitivity policy; ilike is friendlier:
                base = base.where(Entry.type.ilike(filters.type_equals))

            if filters.rarity_in:
                # assume caller passes normalized display rarities
                base = base.where(Entry.rarity.in_(list(filters.rarity_in)))

            if filters.attunement_required is not None:
                base = base.where(Entry.attunement_required == filters.attunement_required)

            if filters.text:
                q = f"%{filters.text}%"
                base = base.where(
                    (Entry.name.ilike(q)) | (func.coalesce(Entry.description, "").ilike(q))
                )

            # total
            total = s.execute(
                select(func.count()).select_from(base.subquery())
            ).scalar_one()

            # sort
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
                base = base.order_by(col.desc() if desc else col.asc())
            else:
                base = base.order_by(Entry.name.asc(), Entry.id.asc())

            page = max(1, page)
            size = max(1, size)
            stmt = base.offset((page - 1) * size).limit(size)
            items = list(s.execute(stmt).scalars().all())
            return items, int(total)

    def list(self, *, page: int = 1, size: int = 50, sort: Optional[str] = None) -> List[Entry]:
        return self.search(filters=EntryFilters(), page=page, size=size, sort=sort)

        # -- iterators for bulk operations ----------------------------------------

    def iter_missing_price(self, session):
        """
        Yield entries whose price is missing (value is NULL/None).
        Intended for bulk auto-pricing passes.
        """
        return (
            session.query(Entry)
            .filter(Entry.value.is_(None))
            .yield_per(100)
        )

    def iter_needing_scrape(self, session):
        """
        Yield entries that have a source_link but are missing description and/or image.
        Intended for bulk scraping passes.
        """
        return (
            session.query(Entry)
            .filter(Entry.source_link.isnot(None))
            .filter(
                (Entry.description.is_(None)) |
                (Entry.image_url.is_(None))
            )
            .yield_per(50)
        )



# --- Generator Repository ------------------------------------------------------

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

    def list_all(self) -> List[GeneratorDef]:
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
