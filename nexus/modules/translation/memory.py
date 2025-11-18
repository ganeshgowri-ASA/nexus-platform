"""
Translation Memory

Translation memory management for reusing previous translations.
"""

from typing import Dict, Any, List, Optional
import hashlib
from sqlalchemy.orm import Session
from sqlalchemy import and_
from nexus.models.translation import TranslationMemory
from config.logging import get_logger

logger = get_logger(__name__)


class TranslationMemoryManager:
    """
    Translation Memory (TM) management.

    Features:
    - Store and retrieve translation pairs
    - Fuzzy matching
    - Context-aware matching
    - TMX import/export
    - Segment matching
    """

    def __init__(self, db: Session):
        """
        Initialize TM manager.

        Args:
            db: Database session
        """
        self.db = db

    def add_translation(
        self,
        source_text: str,
        target_text: str,
        source_lang: str,
        target_lang: str,
        context: Optional[str] = None,
        quality_score: Optional[float] = None,
        domain: Optional[str] = None,
    ) -> TranslationMemory:
        """
        Add translation to memory.

        Args:
            source_text: Source text
            target_text: Target text
            source_lang: Source language
            target_lang: Target language
            context: Context information
            quality_score: Quality score
            domain: Domain/category

        Returns:
            TranslationMemory instance
        """
        # Generate context hash
        context_hash = self._generate_context_hash(context) if context else None

        # Check if exact match already exists
        existing = (
            self.db.query(TranslationMemory)
            .filter(
                and_(
                    TranslationMemory.source_text == source_text,
                    TranslationMemory.target_text == target_text,
                    TranslationMemory.source_language == source_lang,
                    TranslationMemory.target_language == target_lang,
                    TranslationMemory.context_hash == context_hash,
                )
            )
            .first()
        )

        if existing:
            # Update usage count and quality
            existing.usage_count += 1
            if quality_score:
                # Update average quality score
                existing.quality_score = (
                    existing.quality_score * (existing.usage_count - 1) + quality_score
                ) / existing.usage_count
            self.db.commit()
            logger.debug(f"Updated existing TM entry (usage: {existing.usage_count})")
            return existing

        # Create new entry
        tm_entry = TranslationMemory(
            source_text=source_text,
            target_text=target_text,
            source_language=source_lang,
            target_language=target_lang,
            context_hash=context_hash,
            quality_score=quality_score,
            domain=domain,
        )

        tm_entry.save(self.db)
        logger.debug(f"Added new TM entry for {source_lang}->{target_lang}")

        return tm_entry

    def find_match(
        self,
        source_text: str,
        source_lang: str,
        target_lang: str,
        context: Optional[str] = None,
        min_similarity: float = 0.7,
    ) -> Optional[Dict[str, Any]]:
        """
        Find matching translation in memory.

        Args:
            source_text: Source text to match
            source_lang: Source language
            target_lang: Target language
            context: Context for matching
            min_similarity: Minimum similarity threshold

        Returns:
            Best matching translation or None
        """
        context_hash = self._generate_context_hash(context) if context else None

        # First try exact match
        exact_match = (
            self.db.query(TranslationMemory)
            .filter(
                and_(
                    TranslationMemory.source_text == source_text,
                    TranslationMemory.source_language == source_lang,
                    TranslationMemory.target_language == target_lang,
                )
            )
            .first()
        )

        if exact_match:
            logger.debug("Found exact TM match")
            return {
                "source_text": exact_match.source_text,
                "target_text": exact_match.target_text,
                "similarity": 1.0,
                "quality_score": exact_match.quality_score,
                "usage_count": exact_match.usage_count,
                "match_type": "exact",
            }

        # Fuzzy matching
        candidates = (
            self.db.query(TranslationMemory)
            .filter(
                and_(
                    TranslationMemory.source_language == source_lang,
                    TranslationMemory.target_language == target_lang,
                )
            )
            .all()
        )

        best_match = None
        best_similarity = 0.0

        for candidate in candidates:
            similarity = self._calculate_similarity(
                source_text, candidate.source_text
            )

            if similarity > best_similarity and similarity >= min_similarity:
                best_similarity = similarity
                best_match = candidate

        if best_match:
            logger.debug(f"Found fuzzy TM match (similarity: {best_similarity:.2f})")
            return {
                "source_text": best_match.source_text,
                "target_text": best_match.target_text,
                "similarity": best_similarity,
                "quality_score": best_match.quality_score,
                "usage_count": best_match.usage_count,
                "match_type": "fuzzy",
            }

        return None

    def find_segments(
        self,
        source_text: str,
        source_lang: str,
        target_lang: str,
        min_segment_length: int = 5,
    ) -> List[Dict[str, Any]]:
        """
        Find segment-level matches.

        Args:
            source_text: Source text
            source_lang: Source language
            target_lang: Target language
            min_segment_length: Minimum segment length to consider

        Returns:
            List of segment matches
        """
        # Split into segments (sentences)
        segments = self._segment_text(source_text)

        matches = []

        for segment in segments:
            if len(segment.split()) >= min_segment_length:
                match = self.find_match(
                    segment, source_lang, target_lang, min_similarity=0.8
                )
                if match:
                    matches.append({
                        "source_segment": segment,
                        "target_segment": match["target_text"],
                        "similarity": match["similarity"],
                    })

        return matches

    def _calculate_similarity(self, text1: str, text2: str) -> float:
        """
        Calculate similarity between two texts.

        Args:
            text1: First text
            text2: Second text

        Returns:
            Similarity score (0-1)
        """
        # Simple word-based Jaccard similarity
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())

        if not words1 and not words2:
            return 1.0

        intersection = len(words1 & words2)
        union = len(words1 | words2)

        if union == 0:
            return 0.0

        # Jaccard similarity
        jaccard = intersection / union

        # Also consider length similarity
        len_similarity = 1.0 - abs(len(text1) - len(text2)) / max(len(text1), len(text2))

        # Combine metrics
        return (jaccard * 0.7 + len_similarity * 0.3)

    def _generate_context_hash(self, context: str) -> str:
        """
        Generate hash for context string.

        Args:
            context: Context string

        Returns:
            SHA256 hash
        """
        return hashlib.sha256(context.encode()).hexdigest()

    def _segment_text(self, text: str) -> List[str]:
        """
        Segment text into sentences.

        Args:
            text: Text to segment

        Returns:
            List of segments
        """
        # Simple sentence segmentation (use proper NLP in production)
        import re

        # Split on sentence boundaries
        segments = re.split(r'[.!?]+', text)

        # Clean and filter
        segments = [s.strip() for s in segments if s.strip()]

        return segments

    def export_tmx(
        self,
        source_lang: str,
        target_lang: str,
        domain: Optional[str] = None,
    ) -> str:
        """
        Export translation memory as TMX.

        Args:
            source_lang: Source language
            target_lang: Target language
            domain: Optional domain filter

        Returns:
            TMX XML string
        """
        query = self.db.query(TranslationMemory).filter(
            and_(
                TranslationMemory.source_language == source_lang,
                TranslationMemory.target_language == target_lang,
            )
        )

        if domain:
            query = query.filter(TranslationMemory.domain == domain)

        entries = query.all()

        # Generate TMX
        tmx = f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE tmx SYSTEM "tmx14.dtd">
<tmx version="1.4">
  <header
    creationtool="NEXUS Translation Platform"
    creationtoolversion="1.0"
    datatype="plaintext"
    segtype="sentence"
    adminlang="en"
    srclang="{source_lang}"
    o-tmf="unknown">
  </header>
  <body>
"""

        for entry in entries:
            # Escape XML special characters
            source_text = self._escape_xml(entry.source_text)
            target_text = self._escape_xml(entry.target_text)

            tmx += f"""    <tu>
      <tuv xml:lang="{source_lang}">
        <seg>{source_text}</seg>
      </tuv>
      <tuv xml:lang="{target_lang}">
        <seg>{target_text}</seg>
      </tuv>
    </tu>
"""

        tmx += """  </body>
</tmx>"""

        logger.info(f"Exported {len(entries)} TM entries to TMX")
        return tmx

    def import_tmx(self, tmx_content: str) -> int:
        """
        Import translation memory from TMX.

        Args:
            tmx_content: TMX XML content

        Returns:
            Number of entries imported
        """
        import xml.etree.ElementTree as ET

        try:
            root = ET.fromstring(tmx_content)
            count = 0

            # Get source language from header
            header = root.find(".//header")
            source_lang = header.get("srclang") if header is not None else None

            # Process translation units
            for tu in root.findall(".//tu"):
                tuvs = tu.findall("tuv")

                if len(tuvs) >= 2:
                    # Get source and target
                    source_tuv = tuvs[0]
                    target_tuv = tuvs[1]

                    source_lang_code = source_tuv.get("{http://www.w3.org/XML/1998/namespace}lang") or source_lang
                    target_lang_code = target_tuv.get("{http://www.w3.org/XML/1998/namespace}lang")

                    source_seg = source_tuv.find("seg")
                    target_seg = target_tuv.find("seg")

                    if source_seg is not None and target_seg is not None:
                        source_text = source_seg.text or ""
                        target_text = target_seg.text or ""

                        if source_text and target_text:
                            self.add_translation(
                                source_text=source_text,
                                target_text=target_text,
                                source_lang=source_lang_code,
                                target_lang=target_lang_code,
                            )
                            count += 1

            logger.info(f"Imported {count} entries from TMX")
            return count

        except Exception as e:
            logger.error(f"TMX import failed: {e}")
            raise

    def _escape_xml(self, text: str) -> str:
        """Escape XML special characters."""
        import html
        return html.escape(text)

    def get_statistics(
        self,
        source_lang: Optional[str] = None,
        target_lang: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Get translation memory statistics.

        Args:
            source_lang: Filter by source language
            target_lang: Filter by target language

        Returns:
            Statistics dictionary
        """
        query = self.db.query(TranslationMemory)

        if source_lang:
            query = query.filter(TranslationMemory.source_language == source_lang)

        if target_lang:
            query = query.filter(TranslationMemory.target_language == target_lang)

        entries = query.all()

        total_usage = sum(e.usage_count for e in entries)
        avg_quality = (
            sum(e.quality_score for e in entries if e.quality_score) / len(entries)
            if entries
            else 0
        )

        return {
            "total_entries": len(entries),
            "total_usage": total_usage,
            "average_quality_score": avg_quality,
            "languages": list(set((e.source_language, e.target_language) for e in entries)),
        }


class SegmentMatcher:
    """Advanced segment-level matching for translation memory."""

    @staticmethod
    def fuzzy_match_score(source: str, candidate: str) -> float:
        """
        Calculate fuzzy match score between segments.

        Args:
            source: Source segment
            candidate: Candidate segment

        Returns:
            Match score (0-1)
        """
        # Levenshtein distance-based scoring
        # Simplified version - use python-Levenshtein in production
        source_lower = source.lower()
        candidate_lower = candidate.lower()

        if source_lower == candidate_lower:
            return 1.0

        # Simple character-based similarity
        max_len = max(len(source), len(candidate))
        if max_len == 0:
            return 1.0

        differences = sum(
            1 for a, b in zip(source_lower, candidate_lower) if a != b
        )
        differences += abs(len(source) - len(candidate))

        similarity = 1.0 - (differences / max_len)

        return max(0.0, similarity)
