"""
Language detection service
"""

from typing import Dict, Any, List
from langdetect import detect, detect_langs, DetectorFactory
from langdetect.lang_detect_exception import LangDetectException

from ..constants import SUPPORTED_LANGUAGES

# Set seed for consistent results
DetectorFactory.seed = 0


class LanguageDetectionService:
    """Service for detecting languages in text"""

    def __init__(self):
        """Initialize language detection service"""
        pass

    async def detect_language(self, text: str) -> Dict[str, Any]:
        """
        Detect the primary language of the given text

        Args:
            text: Text to analyze

        Returns:
            Dictionary containing detected language information

        Raises:
            LangDetectException: If language cannot be detected
        """
        try:
            # Detect language
            language_code = detect(text)

            # Get language name
            language_name = SUPPORTED_LANGUAGES.get(language_code, "Unknown")

            # Get all detected languages with probabilities
            probabilities = detect_langs(text)

            # Find the confidence for the detected language
            confidence = 0.0
            alternative_languages = []

            for prob in probabilities:
                lang_code = str(prob.lang)
                lang_prob = prob.prob

                if lang_code == language_code:
                    confidence = lang_prob
                else:
                    alternative_languages.append({
                        'language': lang_code,
                        'language_name': SUPPORTED_LANGUAGES.get(lang_code, "Unknown"),
                        'confidence': lang_prob
                    })

            return {
                'detected_language': language_code,
                'language_name': language_name,
                'confidence': confidence,
                'alternative_languages': alternative_languages
            }

        except LangDetectException as e:
            return {
                'detected_language': 'unknown',
                'language_name': 'Unknown',
                'confidence': 0.0,
                'alternative_languages': [],
                'error': str(e)
            }

    async def detect_languages_bulk(self, texts: List[str]) -> List[Dict[str, Any]]:
        """
        Detect languages for multiple texts

        Args:
            texts: List of texts to analyze

        Returns:
            List of detection results
        """
        results = []
        for text in texts:
            result = await self.detect_language(text)
            results.append(result)

        return results

    def is_language(self, text: str, expected_language: str, threshold: float = 0.7) -> bool:
        """
        Check if text is in the expected language

        Args:
            text: Text to check
            expected_language: Expected language code
            threshold: Minimum confidence threshold

        Returns:
            True if text is likely in the expected language
        """
        try:
            detected = detect(text)
            probabilities = detect_langs(text)

            for prob in probabilities:
                if str(prob.lang) == expected_language and prob.prob >= threshold:
                    return True

            return detected == expected_language

        except LangDetectException:
            return False

    def get_text_statistics(self, text: str) -> Dict[str, Any]:
        """
        Get statistics about the text

        Args:
            text: Text to analyze

        Returns:
            Dictionary containing text statistics
        """
        return {
            'character_count': len(text),
            'word_count': len(text.split()),
            'line_count': text.count('\n') + 1,
            'whitespace_count': sum(1 for c in text if c.isspace()),
            'alphanumeric_count': sum(1 for c in text if c.isalnum())
        }
