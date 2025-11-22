"""
Translation Engines

Implements various translation engine integrations.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
import time
from config.settings import settings
from config.logging import get_logger
from nexus.core.exceptions import TranslationError, ExternalAPIError

logger = get_logger(__name__)


class BaseTranslationEngine(ABC):
    """Base class for all translation engines."""

    def __init__(self):
        """Initialize engine."""
        self.name = self.__class__.__name__
        self.logger = get_logger(self.name)

    @abstractmethod
    def translate(
        self,
        text: str,
        target_lang: str,
        source_lang: Optional[str] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """
        Translate text.

        Args:
            text: Text to translate
            target_lang: Target language code
            source_lang: Source language code (auto-detect if None)
            **kwargs: Additional parameters

        Returns:
            Dict with translation result and metadata
        """
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """Check if engine is available (API keys configured)."""
        pass

    def _measure_time(self, func):
        """Decorator to measure execution time."""
        def wrapper(*args, **kwargs):
            start_time = time.time()
            result = func(*args, **kwargs)
            elapsed_time = (time.time() - start_time) * 1000  # Convert to ms
            result["processing_time_ms"] = int(elapsed_time)
            return result
        return wrapper


class GoogleTranslateEngine(BaseTranslationEngine):
    """Google Translate API integration."""

    def __init__(self):
        """Initialize Google Translate."""
        super().__init__()
        self.api_key = settings.GOOGLE_TRANSLATE_API_KEY
        self.client = None

        if self.is_available():
            try:
                from googletrans import Translator
                self.client = Translator()
                self.logger.info("Google Translate engine initialized")
            except Exception as e:
                self.logger.error(f"Failed to initialize Google Translate: {e}")

    def is_available(self) -> bool:
        """Check if Google Translate is available."""
        return self.api_key is not None

    def translate(
        self,
        text: str,
        target_lang: str,
        source_lang: Optional[str] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """
        Translate using Google Translate.

        Args:
            text: Text to translate
            target_lang: Target language code
            source_lang: Source language code
            **kwargs: Additional parameters

        Returns:
            Translation result

        Raises:
            TranslationError: If translation fails
        """
        if not self.client:
            raise TranslationError("Google Translate not initialized")

        try:
            start_time = time.time()

            result = self.client.translate(
                text,
                dest=target_lang,
                src=source_lang or "auto",
            )

            elapsed_time = (time.time() - start_time) * 1000

            return {
                "translated_text": result.text,
                "source_language": result.src,
                "target_language": target_lang,
                "confidence": 0.9,  # Google doesn't provide confidence
                "engine": "google",
                "processing_time_ms": int(elapsed_time),
            }

        except Exception as e:
            self.logger.error(f"Google Translate error: {e}")
            raise TranslationError(f"Google translation failed: {str(e)}")


class DeepLEngine(BaseTranslationEngine):
    """DeepL API integration."""

    def __init__(self):
        """Initialize DeepL."""
        super().__init__()
        self.api_key = settings.DEEPL_API_KEY
        self.client = None

        if self.is_available():
            try:
                import deepl
                self.client = deepl.Translator(self.api_key)
                self.logger.info("DeepL engine initialized")
            except Exception as e:
                self.logger.error(f"Failed to initialize DeepL: {e}")

    def is_available(self) -> bool:
        """Check if DeepL is available."""
        return self.api_key is not None

    def translate(
        self,
        text: str,
        target_lang: str,
        source_lang: Optional[str] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """
        Translate using DeepL.

        Args:
            text: Text to translate
            target_lang: Target language code
            source_lang: Source language code
            **kwargs: Additional parameters

        Returns:
            Translation result

        Raises:
            TranslationError: If translation fails
        """
        if not self.client:
            raise TranslationError("DeepL not initialized")

        try:
            start_time = time.time()

            result = self.client.translate_text(
                text,
                target_lang=target_lang.upper(),
                source_lang=source_lang.upper() if source_lang else None,
            )

            elapsed_time = (time.time() - start_time) * 1000

            return {
                "translated_text": result.text,
                "source_language": result.detected_source_lang.lower(),
                "target_language": target_lang,
                "confidence": 0.95,  # DeepL is highly accurate
                "engine": "deepl",
                "processing_time_ms": int(elapsed_time),
            }

        except Exception as e:
            self.logger.error(f"DeepL error: {e}")
            raise TranslationError(f"DeepL translation failed: {str(e)}")


class AzureTranslatorEngine(BaseTranslationEngine):
    """Azure Translator API integration."""

    def __init__(self):
        """Initialize Azure Translator."""
        super().__init__()
        self.api_key = settings.AZURE_TRANSLATOR_KEY
        self.region = settings.AZURE_TRANSLATOR_REGION
        self.endpoint = settings.AZURE_TRANSLATOR_ENDPOINT

    def is_available(self) -> bool:
        """Check if Azure Translator is available."""
        return all([self.api_key, self.region, self.endpoint])

    def translate(
        self,
        text: str,
        target_lang: str,
        source_lang: Optional[str] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """
        Translate using Azure Translator.

        Args:
            text: Text to translate
            target_lang: Target language code
            source_lang: Source language code
            **kwargs: Additional parameters

        Returns:
            Translation result

        Raises:
            TranslationError: If translation fails
        """
        if not self.is_available():
            raise TranslationError("Azure Translator not configured")

        try:
            import requests
            import uuid

            start_time = time.time()

            path = "/translate"
            constructed_url = self.endpoint + path

            params = {
                "api-version": "3.0",
                "to": target_lang,
            }

            if source_lang:
                params["from"] = source_lang

            headers = {
                "Ocp-Apim-Subscription-Key": self.api_key,
                "Ocp-Apim-Subscription-Region": self.region,
                "Content-type": "application/json",
                "X-ClientTraceId": str(uuid.uuid4()),
            }

            body = [{"text": text}]

            response = requests.post(
                constructed_url,
                params=params,
                headers=headers,
                json=body,
                timeout=settings.TRANSLATION_TIMEOUT_SECONDS,
            )

            response.raise_for_status()
            result = response.json()[0]

            elapsed_time = (time.time() - start_time) * 1000

            translation = result["translations"][0]

            return {
                "translated_text": translation["text"],
                "source_language": result.get("detectedLanguage", {}).get("language", source_lang),
                "target_language": target_lang,
                "confidence": result.get("detectedLanguage", {}).get("score", 0.9),
                "engine": "azure",
                "processing_time_ms": int(elapsed_time),
            }

        except Exception as e:
            self.logger.error(f"Azure Translator error: {e}")
            raise TranslationError(f"Azure translation failed: {str(e)}")


class AWSTranslateEngine(BaseTranslationEngine):
    """AWS Translate API integration."""

    def __init__(self):
        """Initialize AWS Translate."""
        super().__init__()
        self.client = None

        if self.is_available():
            try:
                import boto3
                self.client = boto3.client(
                    "translate",
                    region_name=settings.AWS_REGION,
                    aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                    aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
                )
                self.logger.info("AWS Translate engine initialized")
            except Exception as e:
                self.logger.error(f"Failed to initialize AWS Translate: {e}")

    def is_available(self) -> bool:
        """Check if AWS Translate is available."""
        return all([
            settings.AWS_ACCESS_KEY_ID,
            settings.AWS_SECRET_ACCESS_KEY,
        ])

    def translate(
        self,
        text: str,
        target_lang: str,
        source_lang: Optional[str] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """
        Translate using AWS Translate.

        Args:
            text: Text to translate
            target_lang: Target language code
            source_lang: Source language code
            **kwargs: Additional parameters

        Returns:
            Translation result

        Raises:
            TranslationError: If translation fails
        """
        if not self.client:
            raise TranslationError("AWS Translate not initialized")

        try:
            start_time = time.time()

            result = self.client.translate_text(
                Text=text,
                SourceLanguageCode=source_lang or "auto",
                TargetLanguageCode=target_lang,
            )

            elapsed_time = (time.time() - start_time) * 1000

            return {
                "translated_text": result["TranslatedText"],
                "source_language": result["SourceLanguageCode"],
                "target_language": target_lang,
                "confidence": 0.9,
                "engine": "aws",
                "processing_time_ms": int(elapsed_time),
            }

        except Exception as e:
            self.logger.error(f"AWS Translate error: {e}")
            raise TranslationError(f"AWS translation failed: {str(e)}")


class OpenAITranslateEngine(BaseTranslationEngine):
    """OpenAI GPT-based translation."""

    def __init__(self):
        """Initialize OpenAI translation."""
        super().__init__()
        self.api_key = settings.OPENAI_API_KEY

    def is_available(self) -> bool:
        """Check if OpenAI is available."""
        return self.api_key is not None

    def translate(
        self,
        text: str,
        target_lang: str,
        source_lang: Optional[str] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """
        Translate using OpenAI GPT.

        Args:
            text: Text to translate
            target_lang: Target language code
            source_lang: Source language code
            **kwargs: Additional parameters (context, tone, etc.)

        Returns:
            Translation result

        Raises:
            TranslationError: If translation fails
        """
        if not self.is_available():
            raise TranslationError("OpenAI not configured")

        try:
            from nexus.modules.ai_orchestrator import AIOrchestrator

            ai = AIOrchestrator()
            result = ai.translate_with_ai(
                text=text,
                source_lang=source_lang or "auto",
                target_lang=target_lang,
                context=kwargs.get("context"),
                tone=kwargs.get("tone"),
                model="openai",
            )

            return {
                "translated_text": result["translation"],
                "source_language": source_lang or "auto",
                "target_language": target_lang,
                "confidence": result.get("confidence", 0.9),
                "engine": "openai",
                "processing_time_ms": 0,  # Will be measured externally
            }

        except Exception as e:
            self.logger.error(f"OpenAI translation error: {e}")
            raise TranslationError(f"OpenAI translation failed: {str(e)}")


class ClaudeTranslateEngine(BaseTranslationEngine):
    """Claude AI-based translation."""

    def __init__(self):
        """Initialize Claude translation."""
        super().__init__()
        self.api_key = settings.ANTHROPIC_API_KEY

    def is_available(self) -> bool:
        """Check if Claude is available."""
        return self.api_key is not None

    def translate(
        self,
        text: str,
        target_lang: str,
        source_lang: Optional[str] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """
        Translate using Claude AI.

        Args:
            text: Text to translate
            target_lang: Target language code
            source_lang: Source language code
            **kwargs: Additional parameters (context, tone, etc.)

        Returns:
            Translation result

        Raises:
            TranslationError: If translation fails
        """
        if not self.is_available():
            raise TranslationError("Claude not configured")

        try:
            from nexus.modules.ai_orchestrator import AIOrchestrator

            ai = AIOrchestrator()
            result = ai.translate_with_ai(
                text=text,
                source_lang=source_lang or "auto",
                target_lang=target_lang,
                context=kwargs.get("context"),
                tone=kwargs.get("tone"),
                model="claude",
            )

            return {
                "translated_text": result["translation"],
                "source_language": source_lang or "auto",
                "target_language": target_lang,
                "confidence": result.get("confidence", 0.95),
                "engine": "claude",
                "processing_time_ms": 0,  # Will be measured externally
            }

        except Exception as e:
            self.logger.error(f"Claude translation error: {e}")
            raise TranslationError(f"Claude translation failed: {str(e)}")


class EngineFactory:
    """Factory for creating translation engines."""

    _engines = {
        "google": GoogleTranslateEngine,
        "deepl": DeepLEngine,
        "azure": AzureTranslatorEngine,
        "aws": AWSTranslateEngine,
        "openai": OpenAITranslateEngine,
        "claude": ClaudeTranslateEngine,
    }

    @classmethod
    def create_engine(cls, engine_name: str) -> BaseTranslationEngine:
        """
        Create a translation engine by name.

        Args:
            engine_name: Name of the engine

        Returns:
            Translation engine instance

        Raises:
            ValueError: If engine not found
        """
        engine_class = cls._engines.get(engine_name.lower())
        if not engine_class:
            raise ValueError(f"Unknown translation engine: {engine_name}")

        return engine_class()

    @classmethod
    def get_available_engines(cls) -> List[str]:
        """
        Get list of available (configured) engines.

        Returns:
            List of engine names
        """
        available = []
        for name in cls._engines:
            try:
                engine = cls.create_engine(name)
                if engine.is_available():
                    available.append(name)
            except:
                pass

        return available
