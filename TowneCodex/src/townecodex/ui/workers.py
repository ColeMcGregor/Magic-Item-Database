# townecodex/ui/workers.py
from __future__ import annotations

from typing import Optional, Sequence, List

from PySide6.QtCore import QObject, Signal, Slot, QRunnable

from .backend import Backend, ListItem


# ----------------------------------------------------------------------
# Import Worker
# ----------------------------------------------------------------------

class ImportSignals(QObject):
    done = Signal(int)     # rows imported
    error = Signal(str)    # error text


class ImportWorker(QRunnable):
    def __init__(
        self,
        backend: Backend,
        path: str,
        *,
        scrape: bool,
        default_image: str | None,
    ):
        super().__init__()
        self.backend = backend
        self.path = path
        self.scrape = scrape
        self.default_image = default_image
        self.signals = ImportSignals()

    @Slot()
    def run(self):
        try:
            count = self.backend.import_file(
                self.path,
                scrape=self.scrape,
                default_image=self.default_image,
            )
            self.signals.done.emit(count)
        except Exception as e:
            self.signals.error.emit(str(e))


# ----------------------------------------------------------------------
# Query Worker
# ----------------------------------------------------------------------

class QuerySignals(QObject):
    done = Signal(list)   # list[ListItem]
    error = Signal(str)


class QueryWorker(QRunnable):
    def __init__(
        self,
        backend: Backend,
        *,
        name_contains: Optional[str],
        type_equals: Optional[str],
        rarities: Optional[Sequence[str]],
        attunement_required: Optional[bool],
        page: int = 1,
        size: int = 500,
    ):
        super().__init__()
        self.backend = backend
        self.name_contains = name_contains
        self.type_equals = type_equals
        self.rarities = rarities
        self.attunement_required = attunement_required
        self.page = page
        self.size = size
        self.signals = QuerySignals()

    @Slot()
    def run(self):
        try:
            items: List[ListItem] = self.backend.list_items(
                name_contains=self.name_contains,
                type_equals=self.type_equals,
                rarities=self.rarities,
                attunement_required=self.attunement_required,
                page=self.page,
                size=self.size,
            )
            self.signals.done.emit(items)
        except Exception as e:
            self.signals.error.emit(str(e))


# ----------------------------------------------------------------------
# Scrape Worker
# ----------------------------------------------------------------------

class ScrapeSignals(QObject):
    done = Signal(int)   # number of entries scraped
    error = Signal(str)


class ScrapeWorker(QRunnable):
    def __init__(
        self,
        backend: Backend,
        *,
        throttle_seconds: float = 1.0,
    ):
        super().__init__()
        self.backend = backend
        self.throttle_seconds = throttle_seconds
        self.signals = ScrapeSignals()

    @Slot()
    def run(self):
        try:
            count = self.backend.scrape_existing_missing(
                throttle_seconds=self.throttle_seconds
            )
            self.signals.done.emit(count)
        except Exception as e:
            self.signals.error.emit(str(e))


# ----------------------------------------------------------------------
# Auto-price Worker
# ----------------------------------------------------------------------

class AutoPriceSignals(QObject):
    done = Signal(int)   # number of entries updated
    error = Signal(str)


class AutoPriceWorker(QRunnable):
    def __init__(self, backend: Backend):
        super().__init__()
        self.backend = backend
        self.signals = AutoPriceSignals()

    @Slot()
    def run(self):
        try:
            count = self.backend.auto_price_missing()
            self.signals.done.emit(count)
        except Exception as e:
            self.signals.error.emit(str(e))
