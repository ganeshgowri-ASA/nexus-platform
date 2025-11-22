"""
Glossary Management

Manages translation glossaries for consistent terminology.
"""

from typing import Dict, List, Optional
from sqlalchemy.orm import Session
from nexus.models.translation import Glossary, GlossaryTerm
from config.logging import get_logger

logger = get_logger(__name__)


class GlossaryManager:
    """
    Manages translation glossaries and term databases.

    Features:
    - Custom glossary creation
    - Term lookup and application
    - Domain-specific glossaries
    - Import/export (TMX, CSV, JSON)
    """

    def __init__(self, db: Session):
        """
        Initialize glossary manager.

        Args:
            db: Database session
        """
        self.db = db

    def create_glossary(
        self,
        name: str,
        user_id: int,
        source_lang: str,
        target_lang: str,
        description: Optional[str] = None,
        domain: Optional[str] = None,
        is_public: bool = False,
    ) -> Glossary:
        """
        Create a new glossary.

        Args:
            name: Glossary name
            user_id: Owner user ID
            source_lang: Source language code
            target_lang: Target language code
            description: Description
            domain: Domain/industry
            is_public: Whether glossary is public

        Returns:
            Created glossary
        """
        glossary = Glossary(
            name=name,
            user_id=user_id,
            source_language=source_lang,
            target_language=target_lang,
            description=description,
            domain=domain,
            is_public=is_public,
        )

        glossary.save(self.db)
        logger.info(f"Glossary created: {name}")

        return glossary

    def add_term(
        self,
        glossary_id: int,
        source_term: str,
        target_term: str,
        context: Optional[str] = None,
        case_sensitive: bool = False,
    ) -> GlossaryTerm:
        """
        Add a term to glossary.

        Args:
            glossary_id: Glossary ID
            source_term: Term in source language
            target_term: Term in target language
            context: Usage context
            case_sensitive: Whether matching is case-sensitive

        Returns:
            Created glossary term
        """
        term = GlossaryTerm(
            glossary_id=glossary_id,
            source_term=source_term,
            target_term=target_term,
            context=context,
            case_sensitive=case_sensitive,
        )

        term.save(self.db)
        logger.debug(f"Term added: {source_term} -> {target_term}")

        return term

    def get_glossaries(
        self,
        user_id: int,
        source_lang: Optional[str] = None,
        target_lang: Optional[str] = None,
        domain: Optional[str] = None,
        include_public: bool = True,
    ) -> List[Glossary]:
        """
        Get glossaries for user.

        Args:
            user_id: User ID
            source_lang: Filter by source language
            target_lang: Filter by target language
            domain: Filter by domain
            include_public: Include public glossaries

        Returns:
            List of glossaries
        """
        query = self.db.query(Glossary)

        if include_public:
            query = query.filter(
                (Glossary.user_id == user_id) | (Glossary.is_public == True)
            )
        else:
            query = query.filter(Glossary.user_id == user_id)

        if source_lang:
            query = query.filter(Glossary.source_language == source_lang)

        if target_lang:
            query = query.filter(Glossary.target_language == target_lang)

        if domain:
            query = query.filter(Glossary.domain == domain)

        return query.filter(Glossary.is_deleted == False).all()

    def apply_glossary(
        self,
        text: str,
        source_lang: str,
        target_lang: str,
        user_id: Optional[int] = None,
        domain: Optional[str] = None,
    ) -> Dict[str, str]:
        """
        Find glossary terms in text.

        Args:
            text: Text to process
            source_lang: Source language
            target_lang: Target language
            user_id: User ID (for user-specific glossaries)
            domain: Domain filter

        Returns:
            Dict mapping source terms to target terms found in text
        """
        # Get applicable glossaries
        if user_id:
            glossaries = self.get_glossaries(
                user_id, source_lang, target_lang, domain
            )
        else:
            # Public glossaries only
            glossaries = (
                self.db.query(Glossary)
                .filter(
                    Glossary.source_language == source_lang,
                    Glossary.target_language == target_lang,
                    Glossary.is_public == True,
                    Glossary.is_deleted == False,
                )
                .all()
            )

        found_terms = {}

        for glossary in glossaries:
            for term in glossary.terms:
                if term.is_approved:
                    # Check if term exists in text
                    if term.case_sensitive:
                        if term.source_term in text:
                            found_terms[term.source_term] = term.target_term
                    else:
                        if term.source_term.lower() in text.lower():
                            found_terms[term.source_term] = term.target_term

        return found_terms

    def import_glossary_from_dict(
        self,
        glossary_id: int,
        terms: Dict[str, str],
        context: Optional[str] = None,
    ) -> int:
        """
        Import multiple terms from dictionary.

        Args:
            glossary_id: Glossary ID
            terms: Dict mapping source terms to target terms
            context: Default context for all terms

        Returns:
            Number of terms imported
        """
        count = 0

        for source_term, target_term in terms.items():
            try:
                self.add_term(
                    glossary_id,
                    source_term,
                    target_term,
                    context=context,
                )
                count += 1
            except Exception as e:
                logger.error(f"Failed to import term {source_term}: {e}")

        logger.info(f"Imported {count} terms to glossary {glossary_id}")
        return count

    def export_glossary(self, glossary_id: int, format: str = "json") -> Dict:
        """
        Export glossary in specified format.

        Args:
            glossary_id: Glossary ID
            format: Export format (json, csv, tmx)

        Returns:
            Exported data
        """
        glossary = self.db.query(Glossary).filter(Glossary.id == glossary_id).first()

        if not glossary:
            raise ValueError("Glossary not found")

        terms = glossary.terms

        if format == "json":
            return {
                "glossary": {
                    "id": glossary.id,
                    "name": glossary.name,
                    "source_language": glossary.source_language,
                    "target_language": glossary.target_language,
                    "domain": glossary.domain,
                },
                "terms": [
                    {
                        "source_term": term.source_term,
                        "target_term": term.target_term,
                        "context": term.context,
                        "case_sensitive": term.case_sensitive,
                    }
                    for term in terms
                ],
            }

        elif format == "csv":
            import csv
            from io import StringIO

            output = StringIO()
            writer = csv.writer(output)
            writer.writerow(["Source Term", "Target Term", "Context", "Case Sensitive"])

            for term in terms:
                writer.writerow([
                    term.source_term,
                    term.target_term,
                    term.context or "",
                    term.case_sensitive,
                ])

            return {"csv": output.getvalue()}

        elif format == "tmx":
            # Simplified TMX export
            tmx_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<tmx version="1.4">
  <header
    creationtool="NEXUS"
    srclang="{glossary.source_language}">
  </header>
  <body>
"""
            for term in terms:
                tmx_content += f"""    <tu>
      <tuv xml:lang="{glossary.source_language}">
        <seg>{term.source_term}</seg>
      </tuv>
      <tuv xml:lang="{glossary.target_language}">
        <seg>{term.target_term}</seg>
      </tuv>
    </tu>
"""
            tmx_content += """  </body>
</tmx>"""

            return {"tmx": tmx_content}

        else:
            raise ValueError(f"Unsupported format: {format}")
