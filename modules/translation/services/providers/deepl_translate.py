"""
DeepL Translation API provider
"""

import asyncio
from typing import Optional, Dict, Any, List
import aiohttp

from .base import BaseTranslationProvider
from ...constants import SUPPORTED_LANGUAGES


class DeepLTranslateProvider(BaseTranslationProvider):
    """DeepL Translation API implementation"""

    def __init__(self, api_key: Optional[str] = None, **kwargs):
        super().__init__(api_key, **kwargs)

        if not api_key:
            raise ValueError("DeepL API key is required")

        # Determine API endpoint based on key type
        if api_key.endswith(':fx'):
            self.api_url = "https://api-free.deepl.com/v2"
        else:
            self.api_url = "https://api.deepl.com/v2"

        self.headers = {
            "Authorization": f"DeepL-Auth-Key {api_key}"
        }

    async def translate(
        self,
        text: str,
        source_language: str,
        target_language: str,
        glossary_terms: Optional[Dict[str, str]] = None,
        **kwargs
    ) -> str:
        """Translate text using DeepL API"""

        # Apply glossary if provided
        if glossary_terms:
            text = self.apply_glossary(text, glossary_terms)

        # Convert language codes to DeepL format
        source_lang = self._convert_language_code(source_language)
        target_lang = self._convert_language_code(target_language)

        async with aiohttp.ClientSession() as session:
            data = {
                'text': text,
                'source_lang': source_lang,
                'target_lang': target_lang,
                'formality': kwargs.get('formality', 'default'),
                'preserve_formatting': kwargs.get('preserve_formatting', True)
            }

            async with session.post(
                f"{self.api_url}/translate",
                headers=self.headers,
                data=data
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    return result['translations'][0]['text']
                else:
                    error_text = await response.text()
                    raise Exception(f"DeepL API error: {response.status} - {error_text}")

    async def translate_batch(
        self,
        texts: List[str],
        source_language: str,
        target_language: str,
        glossary_terms: Optional[Dict[str, str]] = None,
        **kwargs
    ) -> List[str]:
        """Translate multiple texts using DeepL API"""

        # Apply glossary if provided
        if glossary_terms:
            texts = [self.apply_glossary(text, glossary_terms) for text in texts]

        # Convert language codes
        source_lang = self._convert_language_code(source_language)
        target_lang = self._convert_language_code(target_language)

        async with aiohttp.ClientSession() as session:
            data = {
                'text': texts,
                'source_lang': source_lang,
                'target_lang': target_lang,
                'formality': kwargs.get('formality', 'default'),
                'preserve_formatting': kwargs.get('preserve_formatting', True)
            }

            async with session.post(
                f"{self.api_url}/translate",
                headers=self.headers,
                data=data
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    return [t['text'] for t in result['translations']]
                else:
                    error_text = await response.text()
                    raise Exception(f"DeepL API error: {response.status} - {error_text}")

    async def detect_language(self, text: str) -> Dict[str, Any]:
        """Detect language using DeepL API (via translation with auto-detect)"""

        async with aiohttp.ClientSession() as session:
            data = {
                'text': text[:1000],  # Limit to first 1000 chars for detection
                'target_lang': 'EN'  # Dummy target language
            }

            async with session.post(
                f"{self.api_url}/translate",
                headers=self.headers,
                data=data
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    detected_lang = result['translations'][0]['detected_source_language']

                    return {
                        'language': detected_lang.lower(),
                        'language_name': SUPPORTED_LANGUAGES.get(detected_lang.lower(), 'Unknown'),
                        'confidence': 0.95,  # DeepL doesn't provide confidence scores
                        'raw_result': result
                    }
                else:
                    error_text = await response.text()
                    raise Exception(f"DeepL API error: {response.status} - {error_text}")

    def get_supported_languages(self) -> List[str]:
        """Get list of supported languages from DeepL"""
        # DeepL supported languages (as of 2024)
        return [
            'ar', 'bg', 'cs', 'da', 'de', 'el', 'en', 'es', 'et', 'fi', 'fr',
            'hu', 'id', 'it', 'ja', 'ko', 'lt', 'lv', 'nb', 'nl', 'pl', 'pt',
            'ro', 'ru', 'sk', 'sl', 'sv', 'tr', 'uk', 'zh'
        ]

    def _convert_language_code(self, lang_code: str) -> str:
        """
        Convert language code to DeepL format

        Args:
            lang_code: Language code (e.g., 'en', 'zh-CN')

        Returns:
            DeepL-formatted language code
        """
        # Handle special cases
        lang_map = {
            'zh-CN': 'ZH',
            'zh-TW': 'ZH',
            'en': 'EN',
            'pt': 'PT'
        }

        if lang_code in lang_map:
            return lang_map[lang_code]

        # Default: uppercase the code
        return lang_code.upper()

    async def get_usage(self) -> Dict[str, Any]:
        """Get API usage statistics"""

        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{self.api_url}/usage",
                headers=self.headers
            ) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    error_text = await response.text()
                    raise Exception(f"DeepL API error: {response.status} - {error_text}")
