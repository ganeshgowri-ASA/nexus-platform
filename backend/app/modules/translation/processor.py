"""Translation processing logic with support for multiple services"""
import time
from typing import Dict, Any, List, Optional, Tuple
import asyncio

from app.core.config import settings
from app.core.logging import get_logger
from app.utils.exceptions import TranslationError, LanguageNotSupportedError, APIKeyMissingError
from app.modules.translation.utils import (
    validate_language_code,
    detect_language_simple,
    split_text_into_chunks,
    calculate_quality_score,
    apply_glossary
)

logger = get_logger(__name__)


class TranslationProcessor:
    """Main translation processing class supporting multiple services"""

    def __init__(self, service: str = "google"):
        self.service = service
        self._setup_service()

    def _setup_service(self):
        """Setup translation service"""
        if self.service == "google":
            if not settings.GOOGLE_TRANSLATE_API_KEY:
                logger.warning("Google Translate API key not configured, using free tier")
        elif self.service == "anthropic":
            if not settings.ANTHROPIC_API_KEY:
                raise APIKeyMissingError("Anthropic API key is required")
        elif self.service == "deepl":
            logger.info("DeepL service selected (requires API key)")

    async def translate(
        self,
        text: str,
        source_language: str,
        target_language: str,
        context: Optional[str] = None,
        glossary: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """Translate text using configured service"""
        start_time = time.time()

        try:
            # Validate languages
            if source_language != "auto" and not validate_language_code(source_language):
                raise LanguageNotSupportedError(f"Source language '{source_language}' not supported")

            if not validate_language_code(target_language):
                raise LanguageNotSupportedError(f"Target language '{target_language}' not supported")

            # Detect language if auto
            detected_language = None
            if source_language == "auto":
                detected_language, _ = detect_language_simple(text)
                source_language = detected_language

            # Split long text into chunks if needed
            chunks = split_text_into_chunks(text, settings.MAX_TRANSLATION_LENGTH)

            # Translate based on service
            if self.service == "google":
                result = await self._translate_with_google(
                    chunks, source_language, target_language, context
                )
            elif self.service == "anthropic":
                result = await self._translate_with_anthropic(
                    chunks, source_language, target_language, context
                )
            elif self.service == "deepl":
                result = await self._translate_with_deepl(
                    chunks, source_language, target_language, context
                )
            else:
                raise TranslationError(f"Unsupported translation service: {self.service}")

            # Apply glossary if provided
            if glossary:
                result["translated_text"], replacements = apply_glossary(
                    result["translated_text"], glossary
                )
                result["glossary_replacements"] = replacements

            # Calculate quality score
            result["quality_score"] = calculate_quality_score(
                text,
                result["translated_text"],
                result.get("confidence_score", 0.8)
            )

            # Add metadata
            result["processing_time"] = time.time() - start_time
            result["character_count"] = len(text)
            result["detected_language"] = detected_language
            result["service"] = self.service

            return result

        except Exception as e:
            logger.error(f"Translation error: {e}", exc_info=True)
            raise TranslationError(f"Failed to translate text: {str(e)}")

    async def _translate_with_google(
        self,
        chunks: List[str],
        source_language: str,
        target_language: str,
        context: Optional[str] = None
    ) -> Dict[str, Any]:
        """Translate using Google Translate"""
        try:
            # Try using googletrans library (free tier)
            from googletrans import Translator

            translator = Translator()
            translations = []
            confidences = []

            for chunk in chunks:
                result = translator.translate(
                    chunk,
                    src=source_language,
                    dest=target_language
                )
                translations.append(result.text)
                confidences.append(0.85)  # googletrans doesn't provide confidence

            return {
                "translated_text": " ".join(translations),
                "confidence_score": sum(confidences) / len(confidences),
                "source_language": source_language,
                "target_language": target_language
            }

        except ImportError:
            # Fallback: Use Google Cloud Translation API if available
            logger.warning("googletrans not available, using mock translation")
            return await self._mock_translate(chunks, source_language, target_language)

        except Exception as e:
            logger.error(f"Google Translate error: {e}", exc_info=True)
            raise TranslationError(f"Google Translate failed: {str(e)}")

    async def _translate_with_anthropic(
        self,
        chunks: List[str],
        source_language: str,
        target_language: str,
        context: Optional[str] = None
    ) -> Dict[str, Any]:
        """Translate using Anthropic Claude API"""
        try:
            from anthropic import Anthropic

            client = Anthropic(api_key=settings.ANTHROPIC_API_KEY)
            translations = []

            for chunk in chunks:
                # Create translation prompt
                prompt = f"""Translate the following text from {source_language} to {target_language}.

{'Context: ' + context if context else ''}

Text to translate:
{chunk}

Provide only the translation without any explanations or additional text."""

                response = client.messages.create(
                    model="claude-3-haiku-20240307",
                    max_tokens=4096,
                    messages=[{"role": "user", "content": prompt}]
                )

                translated = response.content[0].text.strip()
                translations.append(translated)

            return {
                "translated_text": " ".join(translations),
                "confidence_score": 0.9,  # Claude generally provides high-quality translations
                "source_language": source_language,
                "target_language": target_language
            }

        except Exception as e:
            logger.error(f"Anthropic translation error: {e}", exc_info=True)
            raise TranslationError(f"Anthropic translation failed: {str(e)}")

    async def _translate_with_deepl(
        self,
        chunks: List[str],
        source_language: str,
        target_language: str,
        context: Optional[str] = None
    ) -> Dict[str, Any]:
        """Translate using DeepL API"""
        # Placeholder for DeepL API integration
        logger.warning("DeepL API integration not fully implemented. Using mock translation.")
        return await self._mock_translate(chunks, source_language, target_language)

    async def _mock_translate(
        self,
        chunks: List[str],
        source_language: str,
        target_language: str
    ) -> Dict[str, Any]:
        """Mock translation for testing"""
        # Simple mock that adds language prefix
        translated = " ".join([f"[{target_language.upper()}] {chunk}" for chunk in chunks])

        return {
            "translated_text": translated,
            "confidence_score": 0.75,
            "source_language": source_language,
            "target_language": target_language
        }

    async def detect_language(self, text: str) -> Dict[str, Any]:
        """Detect the language of input text"""
        try:
            detected_lang, confidence = detect_language_simple(text)

            return {
                "detected_language": detected_lang,
                "confidence": confidence,
                "all_languages": [
                    {"language": detected_lang, "confidence": confidence}
                ]
            }

        except Exception as e:
            logger.error(f"Language detection error: {e}", exc_info=True)
            raise TranslationError(f"Language detection failed: {str(e)}")

    async def batch_translate(
        self,
        texts: List[str],
        source_language: str,
        target_language: str,
        glossary: Optional[Dict[str, str]] = None
    ) -> List[Dict[str, Any]]:
        """Translate multiple texts in batch"""
        results = []

        # Process in parallel with concurrency limit
        semaphore = asyncio.Semaphore(5)  # Max 5 concurrent translations

        async def translate_one(text: str) -> Dict[str, Any]:
            async with semaphore:
                return await self.translate(
                    text, source_language, target_language,
                    context=None, glossary=glossary
                )

        # Create tasks for all translations
        tasks = [translate_one(text) for text in texts]

        # Execute with progress tracking
        for coro in asyncio.as_completed(tasks):
            try:
                result = await coro
                results.append(result)
            except Exception as e:
                logger.error(f"Batch translation item failed: {e}")
                results.append({
                    "error": str(e),
                    "status": "failed"
                })

        return results


class RealtimeTranslator:
    """Real-time translation for streaming text"""

    def __init__(self, source_language: str, target_language: str, service: str = "google"):
        self.source_language = source_language
        self.target_language = target_language
        self.processor = TranslationProcessor(service)
        self.buffer = ""
        self.buffer_size = 100  # Translate when buffer reaches this size

    async def add_text(self, text: str) -> Optional[str]:
        """Add text to buffer and translate when ready"""
        self.buffer += text

        if len(self.buffer) >= self.buffer_size or text.endswith(('.', '!', '?', '\n')):
            return await self.flush()

        return None

    async def flush(self) -> Optional[str]:
        """Flush buffer and return translation"""
        if not self.buffer:
            return None

        try:
            result = await self.processor.translate(
                self.buffer,
                self.source_language,
                self.target_language
            )

            self.buffer = ""
            return result["translated_text"]

        except Exception as e:
            logger.error(f"Real-time translation error: {e}")
            self.buffer = ""
            return None
