"""Contract metadata and categorization management."""

from typing import Dict, List, Optional, Set
from uuid import UUID
import structlog

from .contract_types import Contract

logger = structlog.get_logger(__name__)


class MetadataManager:
    """Manages contract metadata, tags, and categorization."""

    def __init__(self):
        """Initialize metadata manager."""
        self.tags: Dict[str, Set[UUID]] = {}  # tag -> contract_ids
        self.categories: Dict[str, Set[UUID]] = {}  # category -> contract_ids

    def add_tags(self, contract_id: UUID, tags: List[str]) -> None:
        """Add tags to contract."""
        logger.info("Adding tags", contract_id=contract_id, tags=tags)
        for tag in tags:
            tag = tag.lower().strip()
            if tag not in self.tags:
                self.tags[tag] = set()
            self.tags[tag].add(contract_id)

    def remove_tag(self, contract_id: UUID, tag: str) -> None:
        """Remove tag from contract."""
        tag = tag.lower().strip()
        if tag in self.tags:
            self.tags[tag].discard(contract_id)

    def get_by_tag(self, tag: str) -> Set[UUID]:
        """Get contracts with specific tag."""
        return self.tags.get(tag.lower().strip(), set())

    def set_category(self, contract_id: UUID, category: str) -> None:
        """Set contract category."""
        logger.info("Setting category", contract_id=contract_id, category=category)
        if category not in self.categories:
            self.categories[category] = set()
        self.categories[category].add(contract_id)

    def get_by_category(self, category: str) -> Set[UUID]:
        """Get contracts in category."""
        return self.categories.get(category, set())
