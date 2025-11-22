"""
Google Cloud Translation API provider
"""

import asyncio
from typing import Optional, Dict, Any, List
from google.cloud import translate_v2 as translate
from google.oauth2 import service_account
import os

from .base import BaseTranslationProvider
from ...constants import SUPPORTED_LANGUAGES


class GoogleTranslateProvider(BaseTranslationProvider):
    """Google Cloud Translation API implementation"""

    def __init__(self, api_key: Optional[str] = None, project_id: Optional[str] = None, **kwargs):
        super().__init__(api_key, **kwargs)
        self.project_id = project_id

        # Initialize the translation client
        if api_key:
            self.client = translate.Client(api_key=api_key)
        elif 'credentials_path' in kwargs:
            credentials = service_account.Credentials.from_service_account_file(
                kwargs['credentials_path']
            )
            self.client = translate.Client(credentials=credentials)
        else:
            # Use default credentials
            self.client = translate.Client()

    async def translate(
        self,
        text: str,
        source_language: str,
        target_language: str,
        glossary_terms: Optional[Dict[str, str]] = None,
        **kwargs
    ) -> str:
        """Translate text using Google Cloud Translation API"""

        # Apply glossary if provided
        if glossary_terms:
            text = self.apply_glossary(text, glossary_terms)

        # Run translation in thread pool to avoid blocking
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            None,
            lambda: self.client.translate(
                text,
                source_language=source_language,
                target_language=target_language,
                format_='text'
            )
        )

        return result['translatedText']

    async def translate_batch(
        self,
        texts: List[str],
        source_language: str,
        target_language: str,
        glossary_terms: Optional[Dict[str, str]] = None,
        **kwargs
    ) -> List[str]:
        """Translate multiple texts using Google Cloud Translation API"""

        # Apply glossary if provided
        if glossary_terms:
            texts = [self.apply_glossary(text, glossary_terms) for text in texts]

        # Run batch translation in thread pool
        loop = asyncio.get_event_loop()
        results = await loop.run_in_executor(
            None,
            lambda: self.client.translate(
                texts,
                source_language=source_language,
                target_language=target_language,
                format_='text'
            )
        )

        if isinstance(results, list):
            return [result['translatedText'] for result in results]
        else:
            return [results['translatedText']]

    async def detect_language(self, text: str) -> Dict[str, Any]:
        """Detect language using Google Cloud Translation API"""

        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            None,
            lambda: self.client.detect_language(text)
        )

        language_code = result['language']
        confidence = result['confidence']

        return {
            'language': language_code,
            'language_name': SUPPORTED_LANGUAGES.get(language_code, 'Unknown'),
            'confidence': confidence,
            'raw_result': result
        }

    def get_supported_languages(self) -> List[str]:
        """Get list of supported languages from Google Translate"""
        results = self.client.get_languages()
        return [lang['language'] for lang in results]

    async def translate_document(
        self,
        file_path: str,
        source_language: str,
        target_language: str,
        output_path: str,
        **kwargs
    ) -> str:
        """
        Translate a document file

        Args:
            file_path: Path to the source document
            source_language: Source language code
            target_language: Target language code
            output_path: Path to save the translated document

        Returns:
            Path to the translated document
        """
        # Read the document content
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Translate the content
        translated_content = await self.translate(
            content,
            source_language,
            target_language,
            **kwargs
        )

        # Write the translated content
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(translated_content)

        return output_path
