"""
Glossary management service
"""

from typing import Dict, List, Optional
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from ..models.database import Glossary, GlossaryTerm
from ..models.schemas import GlossaryCreate, GlossaryUpdate


class GlossaryService:
    """Service for managing translation glossaries"""

    def create_glossary(
        self,
        db: Session,
        glossary_data: GlossaryCreate,
        user_id: Optional[str] = None
    ) -> Glossary:
        """
        Create a new glossary

        Args:
            db: Database session
            glossary_data: Glossary creation data
            user_id: User ID

        Returns:
            Created glossary

        Raises:
            ValueError: If glossary name already exists
        """
        try:
            # Create glossary
            glossary = Glossary(
                name=glossary_data.name,
                description=glossary_data.description,
                source_language=glossary_data.source_language,
                target_language=glossary_data.target_language,
                user_id=user_id,
                is_active=True
            )
            db.add(glossary)
            db.flush()

            # Add terms
            for term_data in glossary_data.terms:
                term = GlossaryTerm(
                    glossary_id=glossary.id,
                    source_term=term_data.source_term,
                    target_term=term_data.target_term,
                    description=term_data.description,
                    case_sensitive=term_data.case_sensitive
                )
                db.add(term)

            db.commit()
            db.refresh(glossary)

            return glossary

        except IntegrityError:
            db.rollback()
            raise ValueError(f"Glossary with name '{glossary_data.name}' already exists")

    def get_glossary(self, db: Session, glossary_id: int) -> Optional[Glossary]:
        """
        Get glossary by ID

        Args:
            db: Database session
            glossary_id: Glossary ID

        Returns:
            Glossary or None
        """
        return db.query(Glossary).filter(Glossary.id == glossary_id).first()

    def get_glossary_by_name(self, db: Session, name: str) -> Optional[Glossary]:
        """
        Get glossary by name

        Args:
            db: Database session
            name: Glossary name

        Returns:
            Glossary or None
        """
        return db.query(Glossary).filter(Glossary.name == name).first()

    def get_glossaries(
        self,
        db: Session,
        user_id: Optional[str] = None,
        is_active: Optional[bool] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[Glossary]:
        """
        Get list of glossaries

        Args:
            db: Database session
            user_id: Filter by user ID
            is_active: Filter by active status
            skip: Number of records to skip
            limit: Maximum number of records

        Returns:
            List of glossaries
        """
        query = db.query(Glossary)

        if user_id:
            query = query.filter(Glossary.user_id == user_id)

        if is_active is not None:
            query = query.filter(Glossary.is_active == is_active)

        query = query.order_by(Glossary.created_at.desc())
        query = query.offset(skip).limit(limit)

        return query.all()

    def update_glossary(
        self,
        db: Session,
        glossary_id: int,
        glossary_data: GlossaryUpdate
    ) -> Optional[Glossary]:
        """
        Update glossary

        Args:
            db: Database session
            glossary_id: Glossary ID
            glossary_data: Update data

        Returns:
            Updated glossary or None
        """
        glossary = self.get_glossary(db, glossary_id)
        if not glossary:
            return None

        # Update fields
        if glossary_data.name is not None:
            glossary.name = glossary_data.name

        if glossary_data.description is not None:
            glossary.description = glossary_data.description

        if glossary_data.is_active is not None:
            glossary.is_active = glossary_data.is_active

        db.commit()
        db.refresh(glossary)

        return glossary

    def delete_glossary(self, db: Session, glossary_id: int) -> bool:
        """
        Delete glossary

        Args:
            db: Database session
            glossary_id: Glossary ID

        Returns:
            True if deleted, False otherwise
        """
        glossary = self.get_glossary(db, glossary_id)
        if not glossary:
            return False

        db.delete(glossary)
        db.commit()

        return True

    def add_term(
        self,
        db: Session,
        glossary_id: int,
        source_term: str,
        target_term: str,
        description: Optional[str] = None,
        case_sensitive: bool = False
    ) -> Optional[GlossaryTerm]:
        """
        Add term to glossary

        Args:
            db: Database session
            glossary_id: Glossary ID
            source_term: Source term
            target_term: Target term
            description: Term description
            case_sensitive: Case-sensitive matching

        Returns:
            Created term or None
        """
        glossary = self.get_glossary(db, glossary_id)
        if not glossary:
            return None

        term = GlossaryTerm(
            glossary_id=glossary_id,
            source_term=source_term,
            target_term=target_term,
            description=description,
            case_sensitive=case_sensitive
        )

        db.add(term)
        db.commit()
        db.refresh(term)

        return term

    def update_term(
        self,
        db: Session,
        term_id: int,
        source_term: Optional[str] = None,
        target_term: Optional[str] = None,
        description: Optional[str] = None,
        case_sensitive: Optional[bool] = None
    ) -> Optional[GlossaryTerm]:
        """
        Update glossary term

        Args:
            db: Database session
            term_id: Term ID
            source_term: New source term
            target_term: New target term
            description: New description
            case_sensitive: Case-sensitive flag

        Returns:
            Updated term or None
        """
        term = db.query(GlossaryTerm).filter(GlossaryTerm.id == term_id).first()
        if not term:
            return None

        if source_term is not None:
            term.source_term = source_term

        if target_term is not None:
            term.target_term = target_term

        if description is not None:
            term.description = description

        if case_sensitive is not None:
            term.case_sensitive = case_sensitive

        db.commit()
        db.refresh(term)

        return term

    def delete_term(self, db: Session, term_id: int) -> bool:
        """
        Delete glossary term

        Args:
            db: Database session
            term_id: Term ID

        Returns:
            True if deleted, False otherwise
        """
        term = db.query(GlossaryTerm).filter(GlossaryTerm.id == term_id).first()
        if not term:
            return False

        db.delete(term)
        db.commit()

        return True

    def get_glossary_terms_dict(
        self,
        db: Session,
        glossary_id: int
    ) -> Dict[str, str]:
        """
        Get glossary terms as a dictionary

        Args:
            db: Database session
            glossary_id: Glossary ID

        Returns:
            Dictionary mapping source terms to target terms
        """
        glossary = self.get_glossary(db, glossary_id)
        if not glossary or not glossary.is_active:
            return {}

        return {
            term.source_term: term.target_term
            for term in glossary.terms
        }

    def search_terms(
        self,
        db: Session,
        glossary_id: int,
        search_query: str
    ) -> List[GlossaryTerm]:
        """
        Search terms in a glossary

        Args:
            db: Database session
            glossary_id: Glossary ID
            search_query: Search query

        Returns:
            List of matching terms
        """
        query = db.query(GlossaryTerm).filter(
            GlossaryTerm.glossary_id == glossary_id
        )

        # Search in source and target terms
        query = query.filter(
            (GlossaryTerm.source_term.ilike(f'%{search_query}%')) |
            (GlossaryTerm.target_term.ilike(f'%{search_query}%'))
        )

        return query.all()
