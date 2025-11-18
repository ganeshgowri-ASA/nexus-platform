"""Contract search functionality.

This module provides full-text search, semantic search, clause search,
and metadata filters for contracts.
"""

from typing import Dict, List, Optional
from uuid import UUID
import structlog

from .contract_types import Contract

logger = structlog.get_logger(__name__)


class ContractSearchEngine:
    """Search engine for contracts."""

    def __init__(self):
        """Initialize search engine."""
        self.contracts: Dict[UUID, Contract] = {}
        self._index: Dict[str, Set[UUID]] = {}

    def index_contract(self, contract: Contract) -> None:
        """Index a contract for searching."""
        logger.info("Indexing contract", contract_id=contract.id)

        self.contracts[contract.id] = contract

        # Index title words
        for word in contract.title.lower().split():
            if word not in self._index:
                self._index[word] = set()
            self._index[word].add(contract.id)

        # Index clause content
        for clause in contract.clauses:
            for word in clause.content.lower().split():
                if len(word) > 3:  # Skip short words
                    if word not in self._index:
                        self._index[word] = set()
                    self._index[word].add(contract.id)

    def search(
        self,
        query: str,
        filters: Optional[Dict] = None,
    ) -> List[Contract]:
        """Search contracts.

        Args:
            query: Search query
            filters: Optional filters

        Returns:
            List of matching contracts
        """
        logger.info("Searching contracts", query=query)

        query_words = query.lower().split()
        matching_ids = None

        for word in query_words:
            ids = self._index.get(word, set())
            if matching_ids is None:
                matching_ids = ids
            else:
                matching_ids = matching_ids.intersection(ids)

        results = [self.contracts[id] for id in (matching_ids or set()) if id in self.contracts]

        # Apply filters
        if filters:
            if "contract_type" in filters:
                results = [c for c in results if c.contract_type == filters["contract_type"]]
            if "status" in filters:
                results = [c for c in results if c.status == filters["status"]]

        return results
