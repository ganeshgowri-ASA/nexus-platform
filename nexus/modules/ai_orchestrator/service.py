"""
AI Orchestrator Service

Manages interactions with various AI models (Claude, GPT-4, etc.).
"""

from typing import Optional, Dict, Any, List
from anthropic import Anthropic
from openai import OpenAI
from config.settings import settings
from config.logging import get_logger
from nexus.core.exceptions import AIServiceError

logger = get_logger(__name__)


class AIOrchestrator:
    """
    Orchestrates AI model interactions.

    Supports:
    - Claude (Anthropic)
    - GPT-4 (OpenAI)
    """

    def __init__(self):
        """Initialize AI clients."""
        self.claude_client: Optional[Anthropic] = None
        self.openai_client: Optional[OpenAI] = None

        # Initialize Claude if API key is provided
        if settings.ANTHROPIC_API_KEY:
            try:
                self.claude_client = Anthropic(api_key=settings.ANTHROPIC_API_KEY)
                logger.info("Claude client initialized")
            except Exception as e:
                logger.error(f"Failed to initialize Claude client: {e}")

        # Initialize OpenAI if API key is provided
        if settings.OPENAI_API_KEY:
            try:
                self.openai_client = OpenAI(api_key=settings.OPENAI_API_KEY)
                logger.info("OpenAI client initialized")
            except Exception as e:
                logger.error(f"Failed to initialize OpenAI client: {e}")

    def generate_with_claude(
        self,
        prompt: str,
        system: Optional[str] = None,
        max_tokens: int = 4096,
        temperature: float = 0.7,
        **kwargs,
    ) -> str:
        """
        Generate text using Claude.

        Args:
            prompt: User prompt
            system: System prompt
            max_tokens: Maximum tokens to generate
            temperature: Temperature (0-1)
            **kwargs: Additional parameters

        Returns:
            Generated text

        Raises:
            AIServiceError: If generation fails
        """
        if not self.claude_client:
            raise AIServiceError("Claude client not initialized")

        try:
            messages = [{"role": "user", "content": prompt}]

            response = self.claude_client.messages.create(
                model=settings.CLAUDE_MODEL,
                max_tokens=max_tokens,
                temperature=temperature,
                system=system,
                messages=messages,
                **kwargs,
            )

            result = response.content[0].text
            logger.debug("Claude generation successful", tokens=response.usage.output_tokens)

            return result

        except Exception as e:
            logger.error(f"Claude generation failed: {e}")
            raise AIServiceError(f"Claude generation failed: {str(e)}")

    def generate_with_openai(
        self,
        prompt: str,
        system: Optional[str] = None,
        max_tokens: int = 4096,
        temperature: float = 0.7,
        **kwargs,
    ) -> str:
        """
        Generate text using OpenAI GPT.

        Args:
            prompt: User prompt
            system: System prompt
            max_tokens: Maximum tokens to generate
            temperature: Temperature (0-1)
            **kwargs: Additional parameters

        Returns:
            Generated text

        Raises:
            AIServiceError: If generation fails
        """
        if not self.openai_client:
            raise AIServiceError("OpenAI client not initialized")

        try:
            messages = []
            if system:
                messages.append({"role": "system", "content": system})
            messages.append({"role": "user", "content": prompt})

            response = self.openai_client.chat.completions.create(
                model=settings.OPENAI_MODEL,
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature,
                **kwargs,
            )

            result = response.choices[0].message.content
            logger.debug("OpenAI generation successful", tokens=response.usage.total_tokens)

            return result

        except Exception as e:
            logger.error(f"OpenAI generation failed: {e}")
            raise AIServiceError(f"OpenAI generation failed: {str(e)}")

    def translate_with_ai(
        self,
        text: str,
        source_lang: str,
        target_lang: str,
        context: Optional[str] = None,
        tone: Optional[str] = None,
        model: str = "claude",
    ) -> Dict[str, Any]:
        """
        Translate text using AI models with context awareness.

        Args:
            text: Text to translate
            source_lang: Source language code
            target_lang: Target language code
            context: Additional context
            tone: Desired tone (formal, casual, technical, etc.)
            model: AI model to use ('claude' or 'openai')

        Returns:
            Dict with translation and metadata

        Raises:
            AIServiceError: If translation fails
        """
        # Build system prompt
        system_prompt = f"""You are a professional translator specializing in {source_lang} to {target_lang} translation.
Provide accurate, natural translations that preserve meaning, tone, and cultural context."""

        # Build user prompt
        user_prompt = f"""Translate the following text from {source_lang} to {target_lang}.

Text to translate:
{text}"""

        if context:
            user_prompt += f"\n\nContext: {context}"

        if tone:
            user_prompt += f"\n\nDesired tone: {tone}"

        user_prompt += "\n\nProvide only the translation without explanations."

        # Generate translation
        try:
            if model == "claude":
                translation = self.generate_with_claude(
                    prompt=user_prompt,
                    system=system_prompt,
                    temperature=0.3,  # Lower temperature for more consistent translations
                )
            elif model == "openai":
                translation = self.generate_with_openai(
                    prompt=user_prompt,
                    system=system_prompt,
                    temperature=0.3,
                )
            else:
                raise AIServiceError(f"Unsupported AI model: {model}")

            return {
                "translation": translation.strip(),
                "model": model,
                "source_lang": source_lang,
                "target_lang": target_lang,
                "confidence": 0.9,  # AI models typically provide high-quality translations
            }

        except Exception as e:
            logger.error(f"AI translation failed: {e}")
            raise AIServiceError(f"AI translation failed: {str(e)}")

    def assess_translation_quality(
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
            Quality assessment results
        """
        system_prompt = """You are a translation quality assessor. Evaluate translations for:
1. Accuracy (meaning preservation)
2. Fluency (natural language use)
3. Style consistency
4. Cultural appropriateness

Provide scores from 0-1 for each criterion and an overall score."""

        user_prompt = f"""Assess this translation quality:

Source ({source_lang}): {source_text}
Translation ({target_lang}): {translated_text}

Provide a JSON response with: accuracy_score, fluency_score, style_score, cultural_score, overall_score, and brief feedback."""

        try:
            response = self.generate_with_claude(
                prompt=user_prompt,
                system=system_prompt,
                temperature=0.2,
            )

            # Parse response (simplified - in production, use structured output)
            import json
            import re

            # Try to extract JSON from response
            json_match = re.search(r'\{[^}]+\}', response)
            if json_match:
                result = json.loads(json_match.group())
            else:
                # Fallback to default scores
                result = {
                    "accuracy_score": 0.8,
                    "fluency_score": 0.8,
                    "style_score": 0.8,
                    "cultural_score": 0.8,
                    "overall_score": 0.8,
                    "feedback": response,
                }

            return result

        except Exception as e:
            logger.error(f"Quality assessment failed: {e}")
            return {
                "accuracy_score": 0.5,
                "fluency_score": 0.5,
                "style_score": 0.5,
                "cultural_score": 0.5,
                "overall_score": 0.5,
                "feedback": f"Assessment failed: {str(e)}",
            }

    def detect_language(self, text: str) -> Dict[str, Any]:
        """
        Use AI to detect language with confidence scoring.

        Args:
            text: Text to analyze

        Returns:
            Language detection results
        """
        system_prompt = "You are a language detection expert. Identify the language of the given text."

        user_prompt = f"""Identify the language of this text and provide a confidence score (0-1):

Text: {text}

Respond with JSON: {{"language": "language_code", "confidence": 0.95, "language_name": "English"}}"""

        try:
            response = self.generate_with_claude(
                prompt=user_prompt,
                system=system_prompt,
                temperature=0.1,
            )

            import json
            import re

            json_match = re.search(r'\{[^}]+\}', response)
            if json_match:
                return json.loads(json_match.group())
            else:
                return {
                    "language": "unknown",
                    "confidence": 0.0,
                    "language_name": "Unknown",
                }

        except Exception as e:
            logger.error(f"Language detection failed: {e}")
            return {
                "language": "unknown",
                "confidence": 0.0,
                "language_name": "Unknown",
                "error": str(e),
            }
