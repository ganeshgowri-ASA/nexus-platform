"""
Language Detection

Automatic language detection with confidence scoring.
"""

from typing import Dict, Any, List, Optional
from config.logging import get_logger
from nexus.core.exceptions import LanguageDetectionError

logger = get_logger(__name__)


class LanguageDetector:
    """
    Language detection with multiple backends and confidence scoring.

    Supports:
    - langdetect
    - langid
    - pycld2
    - AI-based detection (Claude/GPT-4)
    """

    def __init__(self):
        """Initialize language detector."""
        self.detectors = []
        self._initialize_detectors()

    def _initialize_detectors(self) -> None:
        """Initialize available detection libraries."""
        # Try langdetect
        try:
            import langdetect
            self.detectors.append(("langdetect", langdetect))
            logger.debug("langdetect initialized")
        except ImportError:
            logger.warning("langdetect not available")

        # Try langid
        try:
            import langid
            self.detectors.append(("langid", langid))
            logger.debug("langid initialized")
        except ImportError:
            logger.warning("langid not available")

        # Try pycld2
        try:
            import pycld2 as cld2
            self.detectors.append(("cld2", cld2))
            logger.debug("cld2 initialized")
        except ImportError:
            logger.warning("pycld2 not available")

        if not self.detectors:
            logger.warning("No language detection libraries available")

    def detect(self, text: str, use_ai: bool = False) -> Dict[str, Any]:
        """
        Detect language of text.

        Args:
            text: Text to analyze
            use_ai: Whether to use AI-based detection as fallback

        Returns:
            Dict with language code, confidence, and name

        Raises:
            LanguageDetectionError: If detection fails
        """
        if not text or not text.strip():
            raise LanguageDetectionError("Empty text provided")

        results = []

        # Try each detector
        for detector_name, detector in self.detectors:
            try:
                if detector_name == "langdetect":
                    result = self._detect_langdetect(detector, text)
                elif detector_name == "langid":
                    result = self._detect_langid(detector, text)
                elif detector_name == "cld2":
                    result = self._detect_cld2(detector, text)
                else:
                    continue

                if result:
                    results.append(result)

            except Exception as e:
                logger.error(f"{detector_name} detection failed: {e}")

        # If no results and AI is enabled, use AI detection
        if not results and use_ai:
            try:
                from nexus.modules.ai_orchestrator import AIOrchestrator
                ai = AIOrchestrator()
                result = ai.detect_language(text)
                results.append(result)
            except Exception as e:
                logger.error(f"AI detection failed: {e}")

        if not results:
            raise LanguageDetectionError("All detection methods failed")

        # Return result with highest confidence
        best_result = max(results, key=lambda x: x.get("confidence", 0))

        logger.info(
            f"Detected language: {best_result['language']} "
            f"(confidence: {best_result['confidence']:.2f})"
        )

        return best_result

    def _detect_langdetect(self, langdetect, text: str) -> Dict[str, Any]:
        """Detect using langdetect."""
        try:
            lang = langdetect.detect(text)
            # Get probability distribution
            probs = langdetect.detect_langs(text)

            # Find confidence for detected language
            confidence = 0.0
            for prob in probs:
                if prob.lang == lang:
                    confidence = prob.prob
                    break

            return {
                "language": lang,
                "confidence": confidence,
                "language_name": self._get_language_name(lang),
                "detector": "langdetect",
            }

        except Exception as e:
            logger.error(f"langdetect error: {e}")
            return None

    def _detect_langid(self, langid, text: str) -> Dict[str, Any]:
        """Detect using langid."""
        try:
            lang, confidence = langid.classify(text)

            return {
                "language": lang,
                "confidence": confidence,
                "language_name": self._get_language_name(lang),
                "detector": "langid",
            }

        except Exception as e:
            logger.error(f"langid error: {e}")
            return None

    def _detect_cld2(self, cld2, text: str) -> Dict[str, Any]:
        """Detect using CLD2."""
        try:
            is_reliable, text_bytes_found, details = cld2.detect(text)

            if details and len(details) > 0:
                # Get top detection
                lang_name, lang_code, confidence, _ = details[0]

                return {
                    "language": lang_code.lower(),
                    "confidence": confidence / 100.0,  # Convert to 0-1
                    "language_name": lang_name,
                    "detector": "cld2",
                    "reliable": is_reliable,
                }

        except Exception as e:
            logger.error(f"cld2 error: {e}")
            return None

    def detect_multiple(
        self, texts: List[str], aggregate: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Detect language for multiple texts.

        Args:
            texts: List of texts to analyze
            aggregate: Whether to aggregate results

        Returns:
            List of detection results or aggregated result
        """
        results = []

        for text in texts:
            try:
                result = self.detect(text)
                results.append(result)
            except Exception as e:
                logger.error(f"Detection failed for text: {e}")
                results.append({
                    "language": "unknown",
                    "confidence": 0.0,
                    "language_name": "Unknown",
                })

        if aggregate and results:
            # Find most common language
            lang_counts = {}
            for result in results:
                lang = result["language"]
                lang_counts[lang] = lang_counts.get(lang, 0) + 1

            most_common = max(lang_counts, key=lang_counts.get)
            confidence = lang_counts[most_common] / len(results)

            return [{
                "language": most_common,
                "confidence": confidence,
                "language_name": self._get_language_name(most_common),
                "sample_size": len(results),
            }]

        return results

    def _get_language_name(self, lang_code: str) -> str:
        """
        Get language name from code.

        Args:
            lang_code: ISO 639-1 language code

        Returns:
            Language name
        """
        # Simple mapping - in production, use comprehensive library
        language_names = {
            "en": "English",
            "es": "Spanish",
            "fr": "French",
            "de": "German",
            "it": "Italian",
            "pt": "Portuguese",
            "ru": "Russian",
            "zh": "Chinese",
            "ja": "Japanese",
            "ko": "Korean",
            "ar": "Arabic",
            "hi": "Hindi",
            "bn": "Bengali",
            "pa": "Punjabi",
            "jv": "Javanese",
            "vi": "Vietnamese",
            "tr": "Turkish",
            "ta": "Tamil",
            "ur": "Urdu",
            "fa": "Persian",
            "pl": "Polish",
            "uk": "Ukrainian",
            "ro": "Romanian",
            "nl": "Dutch",
            "el": "Greek",
            "sv": "Swedish",
            "cs": "Czech",
            "hu": "Hungarian",
            "fi": "Finnish",
            "da": "Danish",
            "no": "Norwegian",
            "sk": "Slovak",
            "bg": "Bulgarian",
            "hr": "Croatian",
            "sr": "Serbian",
            "lt": "Lithuanian",
            "lv": "Latvian",
            "et": "Estonian",
            "sl": "Slovenian",
            "ga": "Irish",
            "mt": "Maltese",
        }

        return language_names.get(lang_code.lower(), lang_code.upper())


class ConfidenceScoring:
    """Confidence scoring for language detection results."""

    @staticmethod
    def calculate_confidence(results: List[Dict[str, Any]]) -> float:
        """
        Calculate aggregated confidence from multiple detectors.

        Args:
            results: List of detection results

        Returns:
            Aggregated confidence score (0-1)
        """
        if not results:
            return 0.0

        # If all detectors agree, high confidence
        languages = [r["language"] for r in results]
        if len(set(languages)) == 1:
            # Average confidence scores
            avg_confidence = sum(r["confidence"] for r in results) / len(results)
            return min(avg_confidence * 1.1, 1.0)  # Boost for agreement

        # If detectors disagree, lower confidence
        # Use weighted average based on individual confidences
        weighted_sum = sum(r["confidence"] ** 2 for r in results)
        return weighted_sum / len(results)

    @staticmethod
    def is_reliable(confidence: float, threshold: float = 0.8) -> bool:
        """
        Check if detection result is reliable.

        Args:
            confidence: Confidence score
            threshold: Minimum threshold

        Returns:
            True if reliable
        """
        return confidence >= threshold
