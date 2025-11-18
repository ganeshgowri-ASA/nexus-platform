"""
Claude API client for AI-powered features.
"""
import os
from typing import Optional, Iterator
from anthropic import Anthropic, APIError
from config.settings import settings
from config.constants import AI_PROMPTS


class ClaudeAPIClient:
    """Client for interacting with Claude AI API."""

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize Claude API client.

        Args:
            api_key: Optional API key. If not provided, uses environment variable.
        """
        self.api_key = api_key or settings.anthropic_api_key or os.getenv("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise ValueError(
                "Anthropic API key not found. Set ANTHROPIC_API_KEY environment variable "
                "or provide it in .env file."
            )
        self.client = Anthropic(api_key=self.api_key)
        self.model = "claude-3-5-sonnet-20241022"
        self.max_tokens = 4096

    def _create_message(self, prompt: str, system: Optional[str] = None) -> str:
        """
        Create a message using Claude API.

        Args:
            prompt: User prompt
            system: Optional system prompt

        Returns:
            Generated response text
        """
        try:
            kwargs = {
                "model": self.model,
                "max_tokens": self.max_tokens,
                "messages": [{"role": "user", "content": prompt}],
            }
            if system:
                kwargs["system"] = system

            message = self.client.messages.create(**kwargs)
            return message.content[0].text
        except APIError as e:
            raise Exception(f"Claude API error: {str(e)}")

    def _stream_message(self, prompt: str, system: Optional[str] = None) -> Iterator[str]:
        """
        Stream a message using Claude API.

        Args:
            prompt: User prompt
            system: Optional system prompt

        Yields:
            Text chunks from the response
        """
        try:
            kwargs = {
                "model": self.model,
                "max_tokens": self.max_tokens,
                "messages": [{"role": "user", "content": prompt}],
            }
            if system:
                kwargs["system"] = system

            with self.client.messages.stream(**kwargs) as stream:
                for text in stream.text_stream:
                    yield text
        except APIError as e:
            raise Exception(f"Claude API error: {str(e)}")

    def check_grammar(self, text: str) -> str:
        """
        Check grammar and spelling in text.

        Args:
            text: Text to check

        Returns:
            Grammar suggestions
        """
        prompt = AI_PROMPTS["grammar_check"].format(text=text)
        system = (
            "You are an expert grammar and spelling checker. "
            "Provide clear, concise corrections with explanations."
        )
        return self._create_message(prompt, system)

    def summarize_text(self, text: str) -> str:
        """
        Summarize text.

        Args:
            text: Text to summarize

        Returns:
            Summary
        """
        prompt = AI_PROMPTS["summarize"].format(text=text)
        system = "You are an expert at creating concise, accurate summaries."
        return self._create_message(prompt, system)

    def expand_text(self, text: str) -> str:
        """
        Expand text with more details.

        Args:
            text: Text to expand

        Returns:
            Expanded text
        """
        prompt = AI_PROMPTS["expand"].format(text=text)
        system = "You are an expert writer who can elaborate on ideas with relevant details and examples."
        return self._create_message(prompt, system)

    def adjust_tone(self, text: str, tone: str = "professional") -> str:
        """
        Adjust the tone of text.

        Args:
            text: Text to adjust
            tone: Target tone (professional, casual, formal)

        Returns:
            Text with adjusted tone
        """
        tone_key = f"tone_{tone.lower()}"
        if tone_key not in AI_PROMPTS:
            raise ValueError(f"Unsupported tone: {tone}")

        prompt = AI_PROMPTS[tone_key].format(text=text)
        system = f"You are an expert at rewriting text in a {tone} tone while preserving the meaning."
        return self._create_message(prompt, system)

    def get_writing_suggestions(self, text: str) -> str:
        """
        Get writing improvement suggestions.

        Args:
            text: Text to improve

        Returns:
            Writing suggestions
        """
        prompt = AI_PROMPTS["writing_assistant"].format(text=text)
        system = (
            "You are an expert writing assistant. Provide actionable suggestions "
            "to improve clarity, style, and effectiveness."
        )
        return self._create_message(prompt, system)

    def autocomplete_text(self, text: str) -> Iterator[str]:
        """
        Generate autocomplete suggestions (streaming).

        Args:
            text: Current text

        Yields:
            Text continuation chunks
        """
        prompt = AI_PROMPTS["autocomplete"].format(text=text)
        system = (
            "You are an expert writing assistant. Continue the text naturally "
            "while maintaining consistency in style and tone."
        )
        yield from self._stream_message(prompt, system)

    def create_outline(self, topic: str) -> str:
        """
        Create a document outline.

        Args:
            topic: Document topic

        Returns:
            Structured outline
        """
        prompt = AI_PROMPTS["outline"].format(topic=topic)
        system = (
            "You are an expert at creating well-structured document outlines. "
            "Provide a clear hierarchy with main topics and subtopics."
        )
        return self._create_message(prompt, system)

    def generate_content(
        self, prompt: str, stream: bool = False
    ) -> Optional[str] | Iterator[str]:
        """
        Generate content based on a custom prompt.

        Args:
            prompt: Custom prompt
            stream: Whether to stream the response

        Returns:
            Generated content or iterator of content chunks
        """
        system = "You are an expert writing assistant helping create high-quality content."
        if stream:
            return self._stream_message(prompt, system)
        return self._create_message(prompt, system)
