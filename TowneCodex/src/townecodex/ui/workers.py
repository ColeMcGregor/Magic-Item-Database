# townecodex/ui/workers.py
from __future__ import annotations
from typing import Optional, Sequence
from PySide6.QtCore import QObject, Signal, Slot, QRunnable

from .backend import Backend, ListItem

# ------------------------------------------------------------------------------
# Import Worker
# ------------------------------------------------------------------------------

class ImportSignals(QObject):
    done = Signal(int)     # rows imported
    error = Signal(str)    # error text

class ImportWorker(QRunnable):
    def __init__(self, backend: Backend, path: str, *, scrape: bool, default_image: str | None):
        super().__init__()
        self.backend = backend
        self.path = path
        self.scrape = scrape
        self.default_image = default_image
        self.signals = ImportSignals()

    @Slot()
    def run(self):
        try:
            count = self.backend.import_file(self.path, scrape=self.scrape, default_image=self.default_image)
            self.signals.done.emit(count)
        except Exception as e:
            self.signals.error.emit(str(e))

# ------------------------------------------------------------------------------
# Query Worker
# ------------------------------------------------------------------------------
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
    ):
        super().__init__()
        self.backend = backend
        self.name_contains = name_contains
        self.type_equals = type_equals
        self.rarities = rarities
        self.attunement_required = attunement_required
        self.signals = QuerySignals()

    @Slot()
    def run(self):
        try:
            items = self.backend.list_items(
                name_contains=self.name_contains,
                type_equals=self.type_equals,
                rarities=self.rarities,
                attunement_required=self.attunement_required,
            )
            self.signals.done.emit(items)
        except Exception as e:
            self.signals.error.emit(str(e))
