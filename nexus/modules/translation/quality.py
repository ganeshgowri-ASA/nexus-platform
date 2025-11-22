"""
Quality Assessment

Translation quality assessment and validation.
"""

from typing import Dict, Any, Optional
from config.logging import get_logger
from config.settings import settings

logger = get_logger(__name__)


class QualityAssessment:
    """
    Translation quality assessment.

    Provides:
    - Fluency scoring
    - Adequacy scoring
    - Back-translation validation
    - Error detection
    - Quality metrics
    """

    def __init__(self):
        """Initialize quality assessor."""
        self.logger = get_logger(__name__)

    def assess(
        self,
        source_text: str,
        translated_text: str,
        source_lang: str,
        target_lang: str,
        use_ai: bool = True,
    ) -> Dict[str, Any]:
        """
        Assess translation quality.

        Args:
            source_text: Original text
            translated_text: Translated text
            source_lang: Source language
            target_lang: Target language
            use_ai: Whether to use AI-based assessment

        Returns:
            Quality scores and feedback
        """
        scores = {}

        # Basic metrics
        scores["length_ratio"] = self._calculate_length_ratio(
            source_text, translated_text
        )

        # Character/word preservation
        scores["preservation_score"] = self._calculate_preservation(
            source_text, translated_text
        )

        # AI-based assessment
        if use_ai and settings.ENABLE_QUALITY_ASSESSMENT:
            try:
                ai_scores = self._ai_assessment(
                    source_text, translated_text, source_lang, target_lang
                )
                scores.update(ai_scores)
            except Exception as e:
                self.logger.error(f"AI assessment failed: {e}")

        # Calculate overall score
        scores["overall_score"] = self._calculate_overall_score(scores)

        self.logger.debug(f"Quality assessment: {scores['overall_score']:.2f}")

        return scores

    def _calculate_length_ratio(self, source: str, target: str) -> float:
        """
        Calculate length ratio between source and target.

        Args:
            source: Source text
            target: Target text

        Returns:
            Length ratio score (0-1)
        """
        if not source or not target:
            return 0.0

        source_len = len(source.split())
        target_len = len(target.split())

        if source_len == 0:
            return 0.0

        ratio = target_len / source_len

        # Expect 0.7 to 1.5 ratio for most language pairs
        if 0.7 <= ratio <= 1.5:
            return 1.0
        elif 0.5 <= ratio <= 2.0:
            return 0.8
        elif 0.3 <= ratio <= 3.0:
            return 0.5
        else:
            return 0.3

    def _calculate_preservation(self, source: str, target: str) -> float:
        """
        Calculate how well numbers, names, and special characters are preserved.

        Args:
            source: Source text
            target: Target text

        Returns:
            Preservation score (0-1)
        """
        import re

        # Extract numbers from source
        source_numbers = set(re.findall(r'\d+', source))
        target_numbers = set(re.findall(r'\d+', target))

        if source_numbers:
            # Check how many numbers are preserved
            preserved = len(source_numbers & target_numbers)
            preservation_score = preserved / len(source_numbers)
        else:
            preservation_score = 1.0

        return preservation_score

    def _ai_assessment(
        self,
        source_text: str,
        translated_text: str,
        source_lang: str,
        target_lang: str,
    ) -> Dict[str, Any]:
        """
        Use AI to assess translation quality.

        Args:
            source_text: Original text
            translated_text: Translated text
            source_lang: Source language
            target_lang: Target language

        Returns:
            AI-based quality scores
        """
        from nexus.modules.ai_orchestrator import AIOrchestrator

        ai = AIOrchestrator()
        scores = ai.assess_translation_quality(
            source_text, translated_text, source_lang, target_lang
        )

        return {
            "fluency_score": scores.get("fluency_score", 0.8),
            "adequacy_score": scores.get("accuracy_score", 0.8),
            "style_score": scores.get("style_score", 0.8),
            "cultural_score": scores.get("cultural_score", 0.8),
            "feedback": scores.get("feedback", ""),
        }

    def _calculate_overall_score(self, scores: Dict[str, Any]) -> float:
        """
        Calculate overall quality score from individual metrics.

        Args:
            scores: Dict of individual scores

        Returns:
            Overall score (0-1)
        """
        weights = {
            "fluency_score": 0.3,
            "adequacy_score": 0.3,
            "style_score": 0.15,
            "cultural_score": 0.15,
            "preservation_score": 0.05,
            "length_ratio": 0.05,
        }

        total_weight = 0.0
        weighted_sum = 0.0

        for metric, weight in weights.items():
            if metric in scores and scores[metric] is not None:
                weighted_sum += scores[metric] * weight
                total_weight += weight

        if total_weight > 0:
            return weighted_sum / total_weight
        else:
            return 0.5  # Default score

    def back_translate(
        self,
        translated_text: str,
        original_lang: str,
        translation_lang: str,
    ) -> Dict[str, Any]:
        """
        Perform back-translation for validation.

        Args:
            translated_text: Translated text to back-translate
            original_lang: Original language
            translation_lang: Language of translation

        Returns:
            Back-translation result with similarity score
        """
        from nexus.modules.translation.engines import EngineFactory

        try:
            # Back-translate using a different engine for validation
            engine = EngineFactory.create_engine("google")  # Use different engine
            result = engine.translate(
                translated_text,
                target_lang=original_lang,
                source_lang=translation_lang,
            )

            back_translated = result["translated_text"]

            # Calculate similarity (simplified - use proper similarity metrics in production)
            similarity = self._calculate_similarity(translated_text, back_translated)

            return {
                "back_translation": back_translated,
                "similarity": similarity,
                "reliable": similarity > 0.7,
            }

        except Exception as e:
            self.logger.error(f"Back-translation failed: {e}")
            return {
                "back_translation": None,
                "similarity": 0.0,
                "reliable": False,
                "error": str(e),
            }

    def _calculate_similarity(self, text1: str, text2: str) -> float:
        """
        Calculate similarity between two texts.

        Args:
            text1: First text
            text2: Second text

        Returns:
            Similarity score (0-1)
        """
        # Simple Jaccard similarity
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())

        if not words1 and not words2:
            return 1.0

        intersection = len(words1 & words2)
        union = len(words1 | words2)

        if union == 0:
            return 0.0

        return intersection / union


class TranslationScoring:
    """Advanced scoring metrics for translations."""

    @staticmethod
    def calculate_bleu_score(reference: str, hypothesis: str) -> float:
        """
        Calculate BLEU score (simplified version).

        Args:
            reference: Reference translation
            hypothesis: Hypothesis translation

        Returns:
            BLEU score (0-1)
        """
        # Simplified BLEU - in production use nltk.translate.bleu_score
        ref_words = reference.lower().split()
        hyp_words = hypothesis.lower().split()

        if not hyp_words:
            return 0.0

        # Calculate unigram precision
        matches = sum(1 for word in hyp_words if word in ref_words)
        precision = matches / len(hyp_words) if hyp_words else 0

        # Apply brevity penalty
        bp = min(1.0, len(hyp_words) / len(ref_words)) if ref_words else 0

        return precision * bp

    @staticmethod
    def calculate_meteor_score(reference: str, hypothesis: str) -> float:
        """
        Calculate METEOR score (simplified).

        Args:
            reference: Reference translation
            hypothesis: Hypothesis translation

        Returns:
            METEOR score (0-1)
        """
        # Simplified version - use actual METEOR implementation in production
        ref_words = set(reference.lower().split())
        hyp_words = set(hypothesis.lower().split())

        if not hyp_words:
            return 0.0

        matches = len(ref_words & hyp_words)
        precision = matches / len(hyp_words)
        recall = matches / len(ref_words) if ref_words else 0

        if precision + recall == 0:
            return 0.0

        f_mean = (precision * recall) / (precision + recall)

        return f_mean
