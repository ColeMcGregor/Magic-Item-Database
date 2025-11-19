# towne_codex/repo.py
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Optional, Sequence, Iterable, Dict, Any, Tuple, List
from contextlib import contextmanager

from sqlalchemy import Null, select, update, func, delete
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

import json

from .pricing import compute_price
from .db import SessionLocal
from .models import Entry, GeneratorDef, GeneralType, SpecificType


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
def _normalize_specific_tags(val: Any) -> str | None:
    """
    Normalize specific_type_tags into a sorted, deduped JSON array string,
    or None if nothing usable is provided.
    """
    if not val:
        return None

    # Accept either a single string or any iterable of strings
    if isinstance(val, str):
        tags = [val]
    else:
        try:
            tags = list(val)
        except TypeError:
            return None

    cleaned: list[str] = []
    for t in tags:
        if not isinstance(t, str):
            continue
        t2 = t.strip()
        if t2:
            cleaned.append(t2)

    if not cleaned:
        return None

    cleaned = sorted(set(cleaned))
    return json.dumps(cleaned, separators=(",", ":"))


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


    #helper

   

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
                    general_type=_trim(data.get("general_type")) if data.get("general_type") else None,
                    specific_type_tags_json=_normalize_specific_tags(data.get("specific_type_tags")),
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

        if "general_type" in data:
            gt = _trim(data["general_type"])
            if gt:
                target.general_type = gt

        if "specific_type_tags" in data:
            st_json = _normalize_specific_tags(data["specific_type_tags"])
            if st_json:
                target.specific_type_tags_json = st_json

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


    def collect_type_terms(self) -> tuple[list[str], list[str]]:
        """
        Return (general_types, specific_types) as sorted unique lists,
        derived from Entry.general_type and Entry.specific_type_tags_json.
        """
        import json

        generals: set[str] = set()
        specifics: set[str] = set()

        with session_scope(self._session_factory) as s:
            rows = s.query(Entry.general_type, Entry.specific_type_tags_json).all()
            for gt, st_json in rows:
                if isinstance(gt, str) and gt.strip():
                    generals.add(gt.strip())

                if st_json:
                    try:
                        tags = json.loads(st_json)
                    except Exception:
                        continue
                    if isinstance(tags, list):
                        for t in tags:
                            if isinstance(t, str) and t.strip():
                                specifics.add(t.strip())

        return sorted(generals), sorted(specifics)

    def sync_type_catalog(
        self,
        general_types: set[str],
        specific_map: dict[str, set[str]],
    ) -> None:
        """
        Ensure general_types / specific_types tables contain at least these values.

        This is a best-effort 'insert new ones' pass; it does not delete anything.
        """
        with session_scope(self._session_factory) as s:
            # 1) General types
            existing_generals = {
                gt.name: gt for gt in s.execute(select(GeneralType)).scalars().all()
            }

            for g_name in sorted(general_types):
                if not g_name:
                    continue
                if g_name not in existing_generals:
                    gt = GeneralType(name=g_name)
                    s.add(gt)
                    s.flush()
                    existing_generals[g_name] = gt

            # 2) Specific types under each general
            for g_name, specs in specific_map.items():
                if not g_name or not specs:
                    continue
                gt = existing_generals.get(g_name)
                if not gt:
                    # Should not happen if above loop did its job, but be defensive
                    gt = GeneralType(name=g_name)
                    s.add(gt)
                    s.flush()
                    existing_generals[g_name] = gt

                # Load existing specifics for this general
                existing_specs = {
                    st.name
                    for st in s.execute(
                        select(SpecificType).where(SpecificType.general_type_id == gt.id)
                    ).scalars().all()
                }

                for spec_name in sorted(specs):
                    if not spec_name or spec_name in existing_specs:
                        continue
                    st = SpecificType(name=spec_name, general_type_id=gt.id)
                    s.add(st)

            # session_scope will commit for us

        # ------------------------------------------------------------------ #
    # Type catalog helpers                                               #
    # ------------------------------------------------------------------ #

    def list_general_types(self) -> List[str]:
        """
        Return all known general types (e.g. 'Armor', 'Weapon', 'Potion'),
        sorted alphabetically.
        """
        with session_scope(self._session_factory) as s:
            stmt = select(GeneralType.name).order_by(GeneralType.name.asc())
            result = s.execute(stmt).all()
            return [row[0] for row in result]

    def list_specific_types_for(self, general_type: Optional[str] = None) -> List[str]:
        """
        Return specific type tags, optionally filtered by a general type.

        Examples:
          list_specific_types_for('Weapon') -> ['Battleaxe', 'Longsword', ...]
          list_specific_types_for(None)    -> all known specific tags.
        """
        with session_scope(self._session_factory) as s:
            base = select(SpecificType.name)
            if general_type:
                base = base.where(SpecificType.general_type == general_type)

            base = base.order_by(SpecificType.name.asc())
            result = s.execute(base).all()
            return [row[0] for row in result]





# --- Generator Repository ------------------------------------------------------

class GeneratorRepository:
    def __init__(self, session_factory=SessionLocal):
        self._session_factory = session_factory

    # -------- CREATE --------
    def insert(self, generator: GeneratorDef) -> GeneratorDef:
        with session_scope(self._session_factory) as s:
            s.add(generator)
            s.flush()
            return generator

    # -------- READ --------
    def get_by_id(self, gen_id: int) -> Optional[GeneratorDef]:
        with session_scope(self._session_factory) as s:
            return s.get(GeneratorDef, gen_id)

    def get_by_name(self, name: str) -> Optional[GeneratorDef]:
        with session_scope(self._session_factory) as s:
            stmt = select(GeneratorDef).where(GeneratorDef.name == name)
            return s.execute(stmt).scalar_one_or_none()

    def list_all(self) -> List[GeneratorDef]:
        with session_scope(self._session_factory) as s:
            stmt = select(GeneratorDef).order_by(GeneratorDef.name.asc())
            return list(s.execute(stmt).scalars().all())

    # -------- UPDATE --------
    def update(self, generator: GeneratorDef) -> GeneratorDef:
        """
        Accepts an existing GeneratorDef with modified fields.
        """
        with session_scope(self._session_factory) as s:
            db_obj = s.get(GeneratorDef, generator.id)
            if not db_obj:
                raise ValueError(f"Generator {generator.id} not found")

            db_obj.name = generator.name
            db_obj.context = generator.context
            db_obj.description = generator.description
            db_obj.config_json = generator.config_json

            s.flush()
            return db_obj

    # -------- DELETE --------
    def delete_by_id(self, gen_id: int) -> bool:
        with session_scope(self._session_factory) as s:
            obj = s.get(GeneratorDef, gen_id)
            if not obj:
                return False
            s.delete(obj)
        return True
