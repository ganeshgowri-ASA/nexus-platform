"""
AI-powered features for Word Editor module.
"""
from typing import Optional, List, Dict, Iterator
import language_tool_python
from spellchecker import SpellChecker
from core.api_client import ClaudeAPIClient
from core.logging import get_logger

logger = get_logger(__name__)


class AIFeatures:
    """AI-powered features for document editing."""

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize AI features.

        Args:
            api_key: Optional Claude API key
        """
        self.claude_client = ClaudeAPIClient(api_key) if api_key else None
        self.language_tool: Optional[language_tool_python.LanguageTool] = None
        self.spell_checker = SpellChecker()

    def initialize_language_tool(self, language: str = "en-US") -> None:
        """
        Initialize LanguageTool for grammar checking.

        Args:
            language: Language code
        """
        try:
            if self.language_tool is None:
                self.language_tool = language_tool_python.LanguageTool(language)
                logger.info(f"LanguageTool initialized for {language}")
        except Exception as e:
            logger.error(f"Failed to initialize LanguageTool: {e}")

    def check_grammar(self, text: str, use_claude: bool = False) -> List[Dict[str, str]]:
        """
        Check grammar in text.

        Args:
            text: Text to check
            use_claude: Whether to use Claude AI for grammar checking

        Returns:
            List of grammar issues
        """
        if use_claude and self.claude_client:
            try:
                result = self.claude_client.check_grammar(text)
                return [{"type": "ai_suggestion", "message": result}]
            except Exception as e:
                logger.error(f"Claude grammar check failed: {e}")
                use_claude = False

        # Fallback to LanguageTool
        if not use_claude:
            if self.language_tool is None:
                self.initialize_language_tool()

            try:
                matches = self.language_tool.check(text)
                issues = []
                for match in matches:
                    issues.append({
                        "type": match.ruleId,
                        "message": match.message,
                        "context": match.context,
                        "offset": match.offset,
                        "length": match.errorLength,
                        "suggestions": match.replacements[:3],  # Top 3 suggestions
                    })
                return issues
            except Exception as e:
                logger.error(f"LanguageTool check failed: {e}")
                return []

        return []

    def check_spelling(self, text: str) -> List[Dict[str, any]]:
        """
        Check spelling in text.

        Args:
            text: Text to check

        Returns:
            List of misspelled words with suggestions
        """
        words = text.split()
        misspelled = self.spell_checker.unknown(words)

        results = []
        for word in misspelled:
            suggestions = self.spell_checker.candidates(word)
            results.append({
                "word": word,
                "suggestions": list(suggestions)[:5] if suggestions else [],
            })

        return results

    def summarize(self, text: str, length: str = "medium") -> str:
        """
        Summarize text using Claude AI.

        Args:
            text: Text to summarize
            length: Summary length (short, medium, long)

        Returns:
            Summary text
        """
        if not self.claude_client:
            raise ValueError("Claude API client not initialized")

        try:
            prompt = f"Provide a {length} summary of the following text:\n\n{text}"
            return self.claude_client.summarize_text(text)
        except Exception as e:
            logger.error(f"Summarization failed: {e}")
            raise

    def expand_text(self, text: str) -> str:
        """
        Expand text with more details.

        Args:
            text: Text to expand

        Returns:
            Expanded text
        """
        if not self.claude_client:
            raise ValueError("Claude API client not initialized")

        try:
            return self.claude_client.expand_text(text)
        except Exception as e:
            logger.error(f"Text expansion failed: {e}")
            raise

    def adjust_tone(self, text: str, tone: str) -> str:
        """
        Adjust the tone of text.

        Args:
            text: Text to adjust
            tone: Target tone (professional, casual, formal)

        Returns:
            Text with adjusted tone
        """
        if not self.claude_client:
            raise ValueError("Claude API client not initialized")

        try:
            return self.claude_client.adjust_tone(text, tone)
        except Exception as e:
            logger.error(f"Tone adjustment failed: {e}")
            raise

    def get_writing_suggestions(self, text: str) -> str:
        """
        Get writing improvement suggestions.

        Args:
            text: Text to improve

        Returns:
            Writing suggestions
        """
        if not self.claude_client:
            raise ValueError("Claude API client not initialized")

        try:
            return self.claude_client.get_writing_suggestions(text)
        except Exception as e:
            logger.error(f"Getting writing suggestions failed: {e}")
            raise

    def autocomplete(self, text: str) -> Iterator[str]:
        """
        Generate autocomplete suggestions (streaming).

        Args:
            text: Current text

        Yields:
            Text continuation chunks
        """
        if not self.claude_client:
            raise ValueError("Claude API client not initialized")

        try:
            yield from self.claude_client.autocomplete_text(text)
        except Exception as e:
            logger.error(f"Autocomplete failed: {e}")
            raise

    def create_outline(self, topic: str) -> str:
        """
        Create a document outline.

        Args:
            topic: Document topic

        Returns:
            Structured outline
        """
        if not self.claude_client:
            raise ValueError("Claude API client not initialized")

        try:
            return self.claude_client.create_outline(topic)
        except Exception as e:
            logger.error(f"Outline creation failed: {e}")
            raise

    def paraphrase(self, text: str) -> str:
        """
        Paraphrase text.

        Args:
            text: Text to paraphrase

        Returns:
            Paraphrased text
        """
        if not self.claude_client:
            raise ValueError("Claude API client not initialized")

        try:
            prompt = f"Paraphrase the following text while preserving its meaning:\n\n{text}"
            return self.claude_client.generate_content(prompt, stream=False)
        except Exception as e:
            logger.error(f"Paraphrasing failed: {e}")
            raise

    def generate_title(self, text: str) -> str:
        """
        Generate a title for text.

        Args:
            text: Document text

        Returns:
            Generated title
        """
        if not self.claude_client:
            raise ValueError("Claude API client not initialized")

        try:
            prompt = (
                f"Generate a concise, descriptive title (max 10 words) for the following text:\n\n"
                f"{text[:1000]}"  # Use first 1000 chars
            )
            return self.claude_client.generate_content(prompt, stream=False)
        except Exception as e:
            logger.error(f"Title generation failed: {e}")
            raise

    def suggest_keywords(self, text: str, num_keywords: int = 5) -> List[str]:
        """
        Suggest keywords for text.

        Args:
            text: Document text
            num_keywords: Number of keywords to suggest

        Returns:
            List of keywords
        """
        if not self.claude_client:
            raise ValueError("Claude API client not initialized")

        try:
            prompt = (
                f"Extract {num_keywords} key topics or keywords from the following text. "
                f"Return only the keywords separated by commas:\n\n{text}"
            )
            result = self.claude_client.generate_content(prompt, stream=False)
            keywords = [kw.strip() for kw in result.split(",")]
            return keywords[:num_keywords]
        except Exception as e:
            logger.error(f"Keyword suggestion failed: {e}")
            raise

    def improve_sentence(self, sentence: str) -> str:
        """
        Improve a specific sentence.

        Args:
            sentence: Sentence to improve

        Returns:
            Improved sentence
        """
        if not self.claude_client:
            raise ValueError("Claude API client not initialized")

        try:
            prompt = (
                f"Improve the following sentence for clarity, conciseness, and impact. "
                f"Provide only the improved version:\n\n{sentence}"
            )
            return self.claude_client.generate_content(prompt, stream=False)
        except Exception as e:
            logger.error(f"Sentence improvement failed: {e}")
            raise

    def translate(self, text: str, target_language: str) -> str:
        """
        Translate text to another language.

        Args:
            text: Text to translate
            target_language: Target language

        Returns:
            Translated text
        """
        if not self.claude_client:
            raise ValueError("Claude API client not initialized")

        try:
            prompt = f"Translate the following text to {target_language}:\n\n{text}"
            return self.claude_client.generate_content(prompt, stream=False)
        except Exception as e:
            logger.error(f"Translation failed: {e}")
            raise

    def check_readability(self, text: str) -> Dict[str, any]:
        """
        Analyze text readability.

        Args:
            text: Text to analyze

        Returns:
            Readability analysis
        """
        # Simple readability metrics
        words = text.split()
        sentences = text.count(".") + text.count("!") + text.count("?")
        sentences = max(sentences, 1)

        avg_word_length = sum(len(word) for word in words) / len(words) if words else 0
        avg_sentence_length = len(words) / sentences

        # Rough readability score (simplified Flesch Reading Ease)
        score = 206.835 - 1.015 * avg_sentence_length - 84.6 * (avg_word_length / 5)
        score = max(0, min(100, score))

        if score >= 90:
            level = "Very Easy"
        elif score >= 80:
            level = "Easy"
        elif score >= 70:
            level = "Fairly Easy"
        elif score >= 60:
            level = "Standard"
        elif score >= 50:
            level = "Fairly Difficult"
        elif score >= 30:
            level = "Difficult"
        else:
            level = "Very Difficult"

        return {
            "score": round(score, 1),
            "level": level,
            "avg_word_length": round(avg_word_length, 1),
            "avg_sentence_length": round(avg_sentence_length, 1),
            "total_words": len(words),
            "total_sentences": sentences,
        }

    def cleanup(self) -> None:
        """Clean up resources."""
        if self.language_tool:
            self.language_tool.close()
