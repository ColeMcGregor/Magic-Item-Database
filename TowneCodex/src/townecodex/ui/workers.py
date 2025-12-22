from __future__ import annotations

from typing import Optional, Sequence, List

from PySide6.QtCore import QObject, Signal, Slot, QRunnable

from .backend import Backend, ListItem
from townecodex.dto import CardDTO

# -------------------------------------------------------------------------------------------------------------
# Worker Threads
# -------------------------------------------------------------------------------------------------------------
#
# This module defines all QRunnable-based worker threads used by the GUI.
#
# Goals:
#   - Keep long-running or blocking operations off the Qt UI thread
#   - Maintain a strict UI ⇄ backend separation
#   - Ensure all cross-thread data is passed as plain values or DTOs
#
# Pattern used throughout:
#   - Each worker owns a Signals QObject
#   - Worker.run() performs backend work inside try/except
#   - Success emits a typed "done" signal
#   - Failure emits a string-only "error" signal
#
# IMPORTANT:
#   - Workers never mutate GUI state directly
#   - Workers never return ORM objects
#   - GUI is responsible for interpreting results and updating UI
# -------------------------------------------------------------------------------------------------------------


# ----------------------------------------------------------------------
# Import Worker
# ----------------------------------------------------------------------
#
# Purpose:
#   Import entries from a file (CSV / JSON / etc.) into the database.
#
# Characteristics:
#   - Potentially long-running
#   - Uses batching and optional sleeps to avoid hammering external services
#   - Returns only a count of rows imported
#
# Thread safety:
#   - Backend is responsible for session management
#   - Worker emits only primitive values
# ----------------------------------------------------------------------

class ImportSignals(QObject):
    done = Signal(int)     # number of rows successfully imported
    error = Signal(str)    # error message suitable for UI display


class ImportWorker(QRunnable):
    def __init__(
        self,
        backend: Backend,
        path: str,
        *,
        default_image: str | None,
        batch_size: int = 5,
        batch_sleep_seconds: float = 2.0,
    ):
        super().__init__()

        # Backend entry point for all import logic
        self.backend = backend

        # Path to import file
        self.path = path

        # Optional fallback image for entries without images
        self.default_image = default_image

        # Throttling controls
        self.batch_size = batch_size
        self.batch_sleep_seconds = batch_sleep_seconds

        # Signals owned by this worker instance
        self.signals = ImportSignals()

    @Slot()
    def run(self):
        """
        Execute the import off the UI thread.

        On success:
          - Emits done(count)

        On failure:
          - Emits error(message)
        """
        try:
            count = self.backend.import_file(
                self.path,
                default_image=self.default_image,
                batch_size=self.batch_size,
                batch_sleep_seconds=self.batch_sleep_seconds,
            )
            self.signals.done.emit(count)
        except Exception as e:
            self.signals.error.emit(str(e))


# ----------------------------------------------------------------------
# Query Worker
# ----------------------------------------------------------------------
#
# Purpose:
#   Execute filtered entry searches without blocking the UI.
#
# Characteristics:
#   - Read-only
#   - Returns lightweight ListItem DTOs
#   - Intended to feed search result tables
#
# Design:
#   - Pagination parameters are passed explicitly
#   - Filtering logic lives entirely in backend/repo layers
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

        # Search filters
        self.name_contains = name_contains
        self.type_equals = type_equals
        self.rarities = rarities
        self.attunement_required = attunement_required

        # Pagination
        self.page = page
        self.size = size

        self.signals = QuerySignals()

    @Slot()
    def run(self):
        """
        Perform a filtered query against entries.

        Emits:
          - done(list[ListItem]) on success
          - error(message) on failure
        """
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
#
# Purpose:
#   Populate missing data by scraping external sources.
#
# Characteristics:
#   - Potentially very slow
#   - Throttled intentionally
#   - Mutates database state
#
# Returns:
#   - Count of entries updated
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
        """
        Run scraping process off the UI thread.

        Emits:
          - done(count) on success
          - error(message) on failure
        """
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
#
# Purpose:
#   Automatically assign prices to entries missing value data.
#
# Characteristics:
#   - Database mutation
#   - Deterministic given same inputs
#
# Returns:
#   - Number of entries updated
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
        """
        Execute auto-pricing logic.

        Emits:
          - done(count)
          - error(message)
        """
        try:
            count = self.backend.auto_price_missing()
            self.signals.done.emit(count)
        except Exception as e:
            self.signals.error.emit(str(e))


# ----------------------------------------------------------------------
# Generator Worker
# ----------------------------------------------------------------------
#
# Purpose:
#   Run a saved GeneratorDef asynchronously and return generated items
#   for use by the GUI (typically appended into the basket).
#
# Design notes:
#   - Generator execution may be expensive (random sampling + DB access)
#   - We return CardDTOs, never ORM objects
#   - Basket mutation is intentionally NOT handled here
#
# Responsibilities:
#   - Backend:
#       * load GeneratorDef
#       * parse GeneratorConfig
#       * run generator engine
#       * convert Entries -> CardDTOs
#
#   - GUI:
#       * append returned CardDTOs into basket
#       * handle duplicates as desired
# ----------------------------------------------------------------------

class GenerateSignals(QObject):
    done = Signal(list)   # list[CardDTO]
    error = Signal(str)


class GenerateWorker(QRunnable):
    def __init__(self, backend: Backend, gen_def_id: int):
        super().__init__()

        self.backend = backend
        self.gen_def_id = int(gen_def_id)
        self.signals = GenerateSignals()

    @Slot()
    def run(self):
        """
        Run generator definition by id.

        Emits:
          - done(list[CardDTO]) on success
          - error(message) on failure
        """
        try:
            cards: List[CardDTO] = self.backend.run_generator(self.gen_def_id)
            self.signals.done.emit(cards)
        except Exception as e:
            self.signals.error.emit(str(e))
