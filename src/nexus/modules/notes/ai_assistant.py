"""AI-powered features for notes using Claude."""

import json
import logging
import re
from typing import Any, Dict, List, Optional

from anthropic import Anthropic

from nexus.core.config import settings
from nexus.core.exceptions import AIException

from .models import Note

logger = logging.getLogger(__name__)


class AIAssistant:
    """AI assistant for note-taking features."""

    def __init__(self):
        """Initialize AI assistant."""
        if not settings.CLAUDE_API_KEY:
            logger.warning("Claude API key not configured")
            self.client = None
        else:
            self.client = Anthropic(api_key=settings.CLAUDE_API_KEY)

    def _call_claude(self, prompt: str, max_tokens: int = 1024) -> str:
        """Call Claude API.

        Args:
            prompt: Prompt text
            max_tokens: Maximum tokens to generate

        Returns:
            Response text

        Raises:
            AIException: If API call fails
        """
        if not self.client:
            raise AIException("Claude API not configured")

        try:
            response = self.client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=max_tokens,
                messages=[{"role": "user", "content": prompt}],
            )
            return response.content[0].text
        except Exception as e:
            logger.error(f"Claude API error: {e}")
            raise AIException(f"AI service error: {str(e)}")

    def summarize_note(self, note: Note, max_length: int = 200) -> str:
        """Generate a summary of a note.

        Args:
            note: Note to summarize
            max_length: Maximum summary length in words

        Returns:
            Summary text
        """
        if not note.content:
            return ""

        prompt = f"""Please provide a concise summary of the following note in no more than {max_length} words.
Focus on the key points and main ideas.

Title: {note.title}

Content:
{note.content[:5000]}  # Limit content to avoid token limits

Summary:"""

        try:
            summary = self._call_claude(prompt, max_tokens=500)
            return summary.strip()
        except Exception as e:
            logger.error(f"Failed to summarize note: {e}")
            return ""

    def extract_tasks(self, note: Note) -> List[Dict[str, Any]]:
        """Extract action items and tasks from a note.

        Args:
            note: Note to analyze

        Returns:
            List of tasks with priority and due dates
        """
        if not note.content:
            return []

        prompt = f"""Analyze the following note and extract all action items, tasks, and to-dos.
For each task, identify:
1. The task description
2. Priority (high, medium, low) if mentioned
3. Due date if mentioned
4. Any assigned person if mentioned

Return the results as a JSON array of objects with keys: task, priority, due_date, assignee.

Note Title: {note.title}

Content:
{note.content[:5000]}

Tasks (JSON):"""

        try:
            response = self._call_claude(prompt, max_tokens=1024)

            # Try to parse JSON from response
            json_match = re.search(r"\[.*\]", response, re.DOTALL)
            if json_match:
                tasks = json.loads(json_match.group(0))
                return tasks
            else:
                return []
        except Exception as e:
            logger.error(f"Failed to extract tasks: {e}")
            return []

    def suggest_tags(self, note: Note, max_tags: int = 5) -> List[str]:
        """Suggest relevant tags for a note.

        Args:
            note: Note to analyze
            max_tags: Maximum number of tags to suggest

        Returns:
            List of suggested tag names
        """
        if not note.content:
            return []

        prompt = f"""Analyze the following note and suggest up to {max_tags} relevant tags or keywords
that would help categorize and find this note later.

Return only the tag names, one per line, without explanations.

Title: {note.title}

Content:
{note.content[:3000]}

Tags:"""

        try:
            response = self._call_claude(prompt, max_tokens=200)

            # Extract tags from response
            tags = [
                tag.strip().lower()
                for tag in response.split("\n")
                if tag.strip() and len(tag.strip()) > 0
            ]

            # Clean up tags (remove numbers, bullets, etc.)
            clean_tags = []
            for tag in tags[:max_tags]:
                # Remove leading numbers, bullets, dashes
                tag = re.sub(r"^[\d\-\*\.\)\]]+\s*", "", tag)
                # Remove quotes
                tag = tag.strip('"\'')
                if tag and len(tag) <= 50:  # Reasonable tag length
                    clean_tags.append(tag)

            return clean_tags[:max_tags]
        except Exception as e:
            logger.error(f"Failed to suggest tags: {e}")
            return []

    def check_grammar(self, text: str) -> Dict[str, Any]:
        """Check grammar and provide suggestions.

        Args:
            text: Text to check

        Returns:
            Dictionary with corrections and suggestions
        """
        if not text:
            return {"has_errors": False, "suggestions": []}

        prompt = f"""Please review the following text for grammar, spelling, and style issues.
Provide specific corrections and suggestions.

Return your analysis as a JSON object with:
- has_errors: boolean
- suggestions: array of objects with {{type, original, suggestion, explanation}}

Text:
{text[:3000]}

Analysis (JSON):"""

        try:
            response = self._call_claude(prompt, max_tokens=1024)

            # Try to parse JSON from response
            json_match = re.search(r"\{.*\}", response, re.DOTALL)
            if json_match:
                result = json.loads(json_match.group(0))
                return result
            else:
                return {"has_errors": False, "suggestions": []}
        except Exception as e:
            logger.error(f"Failed to check grammar: {e}")
            return {"has_errors": False, "suggestions": [], "error": str(e)}

    def generate_note_title(self, content: str) -> str:
        """Generate a title from note content.

        Args:
            content: Note content

        Returns:
            Suggested title
        """
        if not content:
            return "Untitled Note"

        # If content is very short, just use it
        if len(content) < 50:
            return content[:50]

        prompt = f"""Based on the following content, suggest a concise and descriptive title (max 10 words).
Return only the title, nothing else.

Content:
{content[:1000]}

Title:"""

        try:
            title = self._call_claude(prompt, max_tokens=100)
            # Clean up the title
            title = title.strip().strip('"\'')
            # Limit length
            if len(title) > 100:
                title = title[:100]
            return title
        except Exception as e:
            logger.error(f"Failed to generate title: {e}")
            # Fallback: use first line or first 50 chars
            first_line = content.split("\n")[0]
            return first_line[:50] if first_line else "Untitled Note"

    def expand_outline(self, outline: str) -> str:
        """Expand a brief outline into detailed content.

        Args:
            outline: Bullet points or brief outline

        Returns:
            Expanded content
        """
        if not outline:
            return ""

        prompt = f"""Please expand the following outline into a well-structured note with detailed paragraphs.
Keep the same structure but add explanations, examples, and details.

Outline:
{outline}

Expanded Note:"""

        try:
            expanded = self._call_claude(prompt, max_tokens=2048)
            return expanded.strip()
        except Exception as e:
            logger.error(f"Failed to expand outline: {e}")
            return outline

    def answer_question_about_note(self, note: Note, question: str) -> str:
        """Answer a question about note content using AI.

        Args:
            note: Note to reference
            question: User's question

        Returns:
            Answer text
        """
        prompt = f"""Based on the following note, please answer this question:

Question: {question}

Note Title: {note.title}

Note Content:
{note.content[:4000]}

Answer:"""

        try:
            answer = self._call_claude(prompt, max_tokens=1024)
            return answer.strip()
        except Exception as e:
            logger.error(f"Failed to answer question: {e}")
            return "I'm sorry, I couldn't answer that question."

    def suggest_related_topics(self, note: Note, max_topics: int = 5) -> List[str]:
        """Suggest related topics to explore.

        Args:
            note: Note to analyze
            max_topics: Maximum number of topics

        Returns:
            List of related topics
        """
        if not note.content:
            return []

        prompt = f"""Based on the following note, suggest {max_topics} related topics or areas
that the reader might want to explore further.

Return only the topic names, one per line.

Title: {note.title}

Content:
{note.content[:2000]}

Related Topics:"""

        try:
            response = self._call_claude(prompt, max_tokens=300)

            topics = [
                topic.strip()
                for topic in response.split("\n")
                if topic.strip() and len(topic.strip()) > 0
            ]

            # Clean up topics
            clean_topics = []
            for topic in topics[:max_topics]:
                topic = re.sub(r"^[\d\-\*\.\)\]]+\s*", "", topic)
                topic = topic.strip('"\'')
                if topic:
                    clean_topics.append(topic)

            return clean_topics[:max_topics]
        except Exception as e:
            logger.error(f"Failed to suggest topics: {e}")
            return []

    def format_meeting_notes(self, raw_notes: str) -> str:
        """Format raw meeting notes into a structured format.

        Args:
            raw_notes: Unstructured meeting notes

        Returns:
            Formatted meeting notes
        """
        prompt = f"""Please format these raw meeting notes into a well-structured format with:
- Meeting summary
- Attendees (if mentioned)
- Key discussion points
- Decisions made
- Action items
- Next steps

Raw Notes:
{raw_notes[:4000]}

Formatted Notes:"""

        try:
            formatted = self._call_claude(prompt, max_tokens=2048)
            return formatted.strip()
        except Exception as e:
            logger.error(f"Failed to format meeting notes: {e}")
            return raw_notes
