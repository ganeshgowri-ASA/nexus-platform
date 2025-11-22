"""
Base translation provider interface
"""

from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, List


class BaseTranslationProvider(ABC):
    """Abstract base class for translation providers"""

    def __init__(self, api_key: Optional[str] = None, **kwargs):
        """
        Initialize the translation provider

        Args:
            api_key: API key for the translation service
            **kwargs: Additional provider-specific configuration
        """
        self.api_key = api_key
        self.config = kwargs

    @abstractmethod
    async def translate(
        self,
        text: str,
        source_language: str,
        target_language: str,
        glossary_terms: Optional[Dict[str, str]] = None,
        **kwargs
    ) -> str:
        """
        Translate text from source language to target language

        Args:
            text: Text to translate
            source_language: Source language code
            target_language: Target language code
            glossary_terms: Optional dictionary of terms for glossary-based translation
            **kwargs: Additional provider-specific parameters

        Returns:
            Translated text
        """
        pass

    @abstractmethod
    async def translate_batch(
        self,
        texts: List[str],
        source_language: str,
        target_language: str,
        glossary_terms: Optional[Dict[str, str]] = None,
        **kwargs
    ) -> List[str]:
        """
        Translate multiple texts in batch

        Args:
            texts: List of texts to translate
            source_language: Source language code
            target_language: Target language code
            glossary_terms: Optional dictionary of terms for glossary-based translation
            **kwargs: Additional provider-specific parameters

        Returns:
            List of translated texts
        """
        pass

    @abstractmethod
    async def detect_language(self, text: str) -> Dict[str, Any]:
        """
        Detect the language of the given text

        Args:
            text: Text to analyze

        Returns:
            Dictionary containing detected language info
        """
        pass

    @abstractmethod
    def get_supported_languages(self) -> List[str]:
        """
        Get list of supported language codes

        Returns:
            List of language codes
        """
        pass

    def apply_glossary(self, text: str, glossary_terms: Dict[str, str], case_sensitive: bool = False) -> str:
        """
        Apply glossary terms to text before translation

        Args:
            text: Original text
            glossary_terms: Dictionary mapping source terms to target terms
            case_sensitive: Whether to apply case-sensitive matching

        Returns:
            Text with glossary terms applied
        """
        if not glossary_terms:
            return text

        result = text
        for source_term, target_term in glossary_terms.items():
            if case_sensitive:
                result = result.replace(source_term, target_term)
            else:
                # Case-insensitive replacement
                import re
                pattern = re.compile(re.escape(source_term), re.IGNORECASE)
                result = pattern.sub(target_term, result)

        return result
