"""
Glossary Management Module

Terminology database with cross-references and inline definitions.
"""

import logging
from typing import Dict, List, Optional
from uuid import UUID

from sqlalchemy import or_
from sqlalchemy.orm import Session

from .kb_types import Language
from .models import GlossaryTerm

logger = logging.getLogger(__name__)


class GlossaryManager:
    """Manager for glossary terms and definitions."""

    def __init__(self, db_session: Session):
        self.db = db_session

    async def create_term(
        self,
        term: str,
        definition: str,
        abbreviation: Optional[str] = None,
        language: Language = Language.EN,
        related_terms: Optional[List[UUID]] = None,
        **kwargs,
    ) -> GlossaryTerm:
        """Create a new glossary term."""
        try:
            glossary_term = GlossaryTerm(
                term=term,
                definition=definition,
                abbreviation=abbreviation,
                language=language.value,
                related_terms=related_terms or [],
                **kwargs,
            )

            self.db.add(glossary_term)
            self.db.commit()
            self.db.refresh(glossary_term)

            logger.info(f"Created glossary term: {glossary_term.id} - {term}")
            return glossary_term

        except Exception as e:
            self.db.rollback()
            logger.error(f"Error creating glossary term: {str(e)}")
            raise

    async def update_term(self, term_id: UUID, **updates) -> GlossaryTerm:
        """Update a glossary term."""
        try:
            term = self.db.query(GlossaryTerm).filter(GlossaryTerm.id == term_id).first()
            if not term:
                raise ValueError(f"Term {term_id} not found")

            for key, value in updates.items():
                if hasattr(term, key):
                    setattr(term, key, value)

            self.db.commit()
            self.db.refresh(term)
            return term

        except Exception as e:
            self.db.rollback()
            logger.error(f"Error updating term: {str(e)}")
            raise

    async def search_terms(
        self,
        query: str,
        language: Optional[Language] = None,
        limit: int = 20,
    ) -> List[GlossaryTerm]:
        """Search glossary terms."""
        try:
            search_query = self.db.query(GlossaryTerm).filter(
                or_(
                    GlossaryTerm.term.ilike(f"%{query}%"),
                    GlossaryTerm.definition.ilike(f"%{query}%"),
                    GlossaryTerm.abbreviation.ilike(f"%{query}%"),
                )
            )

            if language:
                search_query = search_query.filter(GlossaryTerm.language == language.value)

            return search_query.limit(limit).all()

        except Exception as e:
            logger.error(f"Error searching terms: {str(e)}")
            raise

    async def get_term_by_name(
        self,
        term: str,
        language: Language = Language.EN,
    ) -> Optional[GlossaryTerm]:
        """Get glossary term by name."""
        try:
            return (
                self.db.query(GlossaryTerm)
                .filter(
                    GlossaryTerm.term.ilike(term),
                    GlossaryTerm.language == language.value,
                )
                .first()
            )

        except Exception as e:
            logger.error(f"Error getting term: {str(e)}")
            return None

    async def get_related_terms(self, term_id: UUID) -> List[GlossaryTerm]:
        """Get related glossary terms."""
        try:
            term = self.db.query(GlossaryTerm).filter(GlossaryTerm.id == term_id).first()
            if not term or not term.related_terms:
                return []

            related = (
                self.db.query(GlossaryTerm)
                .filter(GlossaryTerm.id.in_(term.related_terms))
                .all()
            )

            return related

        except Exception as e:
            logger.error(f"Error getting related terms: {str(e)}")
            return []

    async def add_translation(
        self,
        term_id: UUID,
        language: Language,
        translation: str,
    ) -> GlossaryTerm:
        """Add translation for a term."""
        try:
            term = self.db.query(GlossaryTerm).filter(GlossaryTerm.id == term_id).first()
            if not term:
                raise ValueError(f"Term {term_id} not found")

            if not term.translations:
                term.translations = {}

            term.translations[language.value] = translation
            self.db.commit()
            self.db.refresh(term)

            return term

        except Exception as e:
            self.db.rollback()
            logger.error(f"Error adding translation: {str(e)}")
            raise
