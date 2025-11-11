# townecodex/query.py
from __future__ import annotations
from typing import Optional, Sequence

from .repos import EntryRepository, EntryFilters
from .dto import CardDTO, to_card_dto, to_card_dtos


"""
QueryService for Towne Codex.

This module provides a read-only service for fetching entry data
as lightweight DTOs, ready for rendering by the UI layer (CLI, GUI, or renderer).

It never performs any database writes or rendering logic.
All data is sourced via EntryRepository and converted into CardDTO objects.

author: Cole McGregor
date: 2025-11-11
version: 0.1.0
"""


class QueryService:
    """
    Read-only interface for listing and retrieving entries.

    Responsibilities:
    - Translate search parameters into EntryFilters.
    - Fetch results from EntryRepository.
    - Return normalized CardDTO objects.
    """

    def __init__(self, repo: Optional[EntryRepository] = None):
        self.repo = repo or EntryRepository()

    # -----------------------------------------------------------------------
    # Search / List
    # -----------------------------------------------------------------------
    def search(
        self,
        *,
        name_contains: Optional[str] = None,
        type_equals: Optional[str] = None,
        rarity_in: Optional[Sequence[str]] = None,
        attunement_required: Optional[bool] = None,
        text: Optional[str] = None,
        page: int = 1,
        size: int = 50,
        sort: Optional[str] = None,
    ) -> list[CardDTO]:
        """
        Perform a read-only search using the provided filters.
        Returns a list of CardDTO objects.
        """
        filters = EntryFilters(
            name_contains=name_contains,
            type_equals=type_equals,
            rarity_in=rarity_in,
            attunement_required=attunement_required,
            text=text,
        )
        results = self.repo.search(filters, page=page, size=size, sort=sort)
        return to_card_dtos(results)

    # -----------------------------------------------------------------------
    # Detail
    # -----------------------------------------------------------------------
    def get_entry_card(self, entry_id: int) -> Optional[CardDTO]:
        """
        Retrieve a single entry as a CardDTO by its ID.
        Returns None if not found.
        """
        entry = self.repo.get_by_id(entry_id)
        return to_card_dto(entry) if entry else None
