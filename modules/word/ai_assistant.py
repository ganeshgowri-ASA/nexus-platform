"""
AI Writing Assistant

Provides AI-powered writing assistance features including autocomplete,
grammar checking, style suggestions, translation, and more.
"""

from typing import Dict, List, Optional, Any, Tuple
from enum import Enum
from dataclasses import dataclass
import re


class ToneStyle(Enum):
    """Writing tone styles"""
    FORMAL = "formal"
    CASUAL = "casual"
    FRIENDLY = "friendly"
    PROFESSIONAL = "professional"
    ACADEMIC = "academic"
    CREATIVE = "creative"


class WritingTask(Enum):
    """AI writing task types"""
    AUTOCOMPLETE = "autocomplete"
    GRAMMAR_CHECK = "grammar_check"
    SPELL_CHECK = "spell_check"
    STYLE_SUGGEST = "style_suggest"
    TONE_ADJUST = "tone_adjust"
    SUMMARIZE = "summarize"
    EXPAND = "expand"
    SHORTEN = "shorten"
    REWRITE = "rewrite"
    TRANSLATE = "translate"
    CONTINUE = "continue"
    GENERATE_FROM_OUTLINE = "generate_from_outline"


@dataclass
class GrammarIssue:
    """Grammar issue information"""
    offset: int
    length: int
    message: str
    suggestions: List[str]
    category: str  # grammar, spelling, style, etc.
    severity: str  # error, warning, info


@dataclass
class StyleSuggestion:
    """Style improvement suggestion"""
    text: str
    suggestion: str
    reason: str
    improvement_type: str  # clarity, conciseness, engagement, etc.


class AIWritingAssistant:
    """
    AI Writing Assistant class providing intelligent writing support.

    Features:
    - Autocomplete suggestions
    - Grammar and spell checking
    - Style improvements
    - Tone adjustment
    - Text summarization
    - Content expansion/shortening
    - Paragraph rewriting
    - Multi-language translation
    - Continue writing
    - Generate from outline
    """

    # Supported languages for translation
    SUPPORTED_LANGUAGES = [
        "English", "Spanish", "French", "German", "Italian", "Portuguese",
        "Russian", "Chinese", "Japanese", "Korean", "Arabic", "Hindi",
        "Dutch", "Swedish", "Norwegian", "Danish", "Finnish", "Polish",
        "Turkish", "Greek", "Hebrew", "Thai", "Vietnamese", "Indonesian",
        "Malay", "Filipino", "Czech", "Hungarian", "Romanian", "Ukrainian",
        "Bengali", "Urdu", "Persian", "Swahili", "Tamil", "Telugu",
        "Marathi", "Gujarati", "Kannada", "Malayalam", "Punjabi", "Nepali",
        "Sinhala", "Burmese", "Khmer", "Lao", "Mongolian", "Georgian",
        "Armenian", "Azerbaijani", "Kazakh", "Uzbek", "Tajik", "Turkmen",
        "Kyrgyz", "Pashto", "Kurdish", "Amharic", "Tigrinya", "Somali",
    ]

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize AI writing assistant.

        Args:
            api_key: Optional API key for external services (e.g., OpenAI, Anthropic)
        """
        self.api_key = api_key
        self.ai_enabled = bool(api_key)

    def autocomplete(
        self,
        text: str,
        cursor_position: int,
        max_suggestions: int = 3
    ) -> List[str]:
        """
        Generate autocomplete suggestions.

        Args:
            text: Current text content
            cursor_position: Cursor position in text
            max_suggestions: Maximum number of suggestions

        Returns:
            List of autocomplete suggestions
        """
        if not self.ai_enabled:
            return self._basic_autocomplete(text, cursor_position, max_suggestions)

        try:
            # Extract context before cursor
            context = text[:cursor_position]

            # In production, call AI API here
            prompt = f"""Given the following text, suggest {max_suggestions} natural completions:

Text: {context}

Provide concise, contextually appropriate completions."""

            # Placeholder for AI API call
            # suggestions = self._call_ai_api(prompt, task='autocomplete')

            # For now, return basic suggestions
            return self._basic_autocomplete(text, cursor_position, max_suggestions)

        except Exception as e:
            print(f"Error in autocomplete: {e}")
            return []

    def _basic_autocomplete(
        self,
        text: str,
        cursor_position: int,
        max_suggestions: int
    ) -> List[str]:
        """Basic autocomplete without AI"""
        # Simple word completion based on common patterns
        context = text[:cursor_position]
        words = context.split()

        if not words:
            return []

        last_word = words[-1].lower()

        # Common completions
        completions = {
            "the": ["the quick", "the best", "the most"],
            "a": ["a lot", "a few", "a great"],
            "in": ["in order to", "in addition", "in conclusion"],
            "to": ["to be", "to do", "to make"],
            "for": ["for example", "for instance", "for the"],
        }

        return completions.get(last_word, [])[:max_suggestions]

    def check_grammar(self, text: str) -> List[GrammarIssue]:
        """
        Check text for grammar issues.

        Args:
            text: Text to check

        Returns:
            List of grammar issues found
        """
        issues = []

        # Basic grammar checks (in production, use LanguageTool API or similar)
        issues.extend(self._check_punctuation(text))
        issues.extend(self._check_capitalization(text))
        issues.extend(self._check_repeated_words(text))

        return issues

    def _check_punctuation(self, text: str) -> List[GrammarIssue]:
        """Check for punctuation issues"""
        issues = []

        # Check for missing spaces after punctuation
        pattern = r'[.!?,;:](?=[A-Za-z])'
        for match in re.finditer(pattern, text):
            issues.append(GrammarIssue(
                offset=match.start(),
                length=match.end() - match.start(),
                message="Missing space after punctuation",
                suggestions=[match.group(0) + " "],
                category="punctuation",
                severity="warning"
            ))

        return issues

    def _check_capitalization(self, text: str) -> List[GrammarIssue]:
        """Check for capitalization issues"""
        issues = []

        # Check sentences start with capital letter
        sentences = re.split(r'[.!?]\s+', text)
        offset = 0

        for sentence in sentences:
            if sentence and sentence[0].islower():
                issues.append(GrammarIssue(
                    offset=offset,
                    length=1,
                    message="Sentence should start with a capital letter",
                    suggestions=[sentence[0].upper()],
                    category="capitalization",
                    severity="warning"
                ))

            offset += len(sentence) + 2  # Account for punctuation and space

        return issues

    def _check_repeated_words(self, text: str) -> List[GrammarIssue]:
        """Check for repeated words"""
        issues = []

        words = re.findall(r'\b\w+\b', text.lower())
        positions = [m.start() for m in re.finditer(r'\b\w+\b', text)]

        for i in range(len(words) - 1):
            if words[i] == words[i + 1]:
                issues.append(GrammarIssue(
                    offset=positions[i + 1],
                    length=len(words[i + 1]),
                    message=f"Repeated word: '{words[i]}'",
                    suggestions=[""],  # Suggest deletion
                    category="repetition",
                    severity="info"
                ))

        return issues

    def check_spelling(self, text: str) -> List[GrammarIssue]:
        """
        Check text for spelling errors.

        Args:
            text: Text to check

        Returns:
            List of spelling issues found
        """
        # In production, integrate with a spell-checking library
        # For now, return empty list
        return []

    def suggest_style_improvements(self, text: str) -> List[StyleSuggestion]:
        """
        Suggest style improvements.

        Args:
            text: Text to analyze

        Returns:
            List of style suggestions
        """
        suggestions = []

        # Check for passive voice
        passive_patterns = [
            r'\b(is|are|was|were|be|been|being)\s+\w+ed\b',
            r'\b(is|are|was|were|be|been|being)\s+\w+en\b',
        ]

        for pattern in passive_patterns:
            for match in re.finditer(pattern, text, re.IGNORECASE):
                suggestions.append(StyleSuggestion(
                    text=match.group(0),
                    suggestion="Consider using active voice",
                    reason="Active voice is more direct and engaging",
                    improvement_type="clarity"
                ))

        # Check for wordy phrases
        wordy_phrases = {
            "in order to": "to",
            "due to the fact that": "because",
            "at this point in time": "now",
            "for the purpose of": "for",
            "in the event that": "if",
        }

        for wordy, concise in wordy_phrases.items():
            if wordy in text.lower():
                suggestions.append(StyleSuggestion(
                    text=wordy,
                    suggestion=concise,
                    reason="More concise alternative available",
                    improvement_type="conciseness"
                ))

        return suggestions

    def adjust_tone(self, text: str, target_tone: ToneStyle) -> str:
        """
        Adjust text tone to match target style.

        Args:
            text: Original text
            target_tone: Desired tone style

        Returns:
            Text adjusted to target tone
        """
        if not self.ai_enabled:
            return text

        try:
            # In production, call AI API here
            prompt = f"""Rewrite the following text in a {target_tone.value} tone:

Text: {text}

Rewritten text:"""

            # Placeholder for AI API call
            # result = self._call_ai_api(prompt, task='tone_adjust')
            # return result

            return text  # Return original for now

        except Exception as e:
            print(f"Error adjusting tone: {e}")
            return text

    def summarize(self, text: str, max_length: Optional[int] = None) -> str:
        """
        Summarize text.

        Args:
            text: Text to summarize
            max_length: Optional maximum length in words

        Returns:
            Summarized text
        """
        if not self.ai_enabled:
            return self._basic_summarize(text, max_length)

        try:
            # In production, call AI API here
            length_instruction = f" in about {max_length} words" if max_length else ""
            prompt = f"""Summarize the following text{length_instruction}:

Text: {text}

Summary:"""

            # Placeholder for AI API call
            # return self._call_ai_api(prompt, task='summarize')

            return self._basic_summarize(text, max_length)

        except Exception as e:
            print(f"Error summarizing: {e}")
            return text

    def _basic_summarize(self, text: str, max_length: Optional[int] = None) -> str:
        """Basic summarization without AI"""
        sentences = re.split(r'[.!?]\s+', text)

        if not max_length:
            max_length = max(50, len(text.split()) // 4)

        summary = []
        word_count = 0

        for sentence in sentences:
            sentence_words = len(sentence.split())
            if word_count + sentence_words <= max_length:
                summary.append(sentence)
                word_count += sentence_words
            else:
                break

        return '. '.join(summary) + '.'

    def expand_text(self, text: str, target_length: Optional[int] = None) -> str:
        """
        Expand text with more detail.

        Args:
            text: Text to expand
            target_length: Optional target length in words

        Returns:
            Expanded text
        """
        if not self.ai_enabled:
            return text

        try:
            # In production, call AI API here
            length_instruction = f" to about {target_length} words" if target_length else ""
            prompt = f"""Expand the following text with more detail and explanation{length_instruction}:

Text: {text}

Expanded text:"""

            # Placeholder for AI API call
            # return self._call_ai_api(prompt, task='expand')

            return text

        except Exception as e:
            print(f"Error expanding text: {e}")
            return text

    def shorten_text(self, text: str, target_length: Optional[int] = None) -> str:
        """
        Shorten text while preserving meaning.

        Args:
            text: Text to shorten
            target_length: Optional target length in words

        Returns:
            Shortened text
        """
        if not self.ai_enabled:
            return self._basic_summarize(text, target_length)

        try:
            # In production, call AI API here
            length_instruction = f" to about {target_length} words" if target_length else ""
            prompt = f"""Shorten the following text while preserving its key meaning{length_instruction}:

Text: {text}

Shortened text:"""

            # Placeholder for AI API call
            # return self._call_ai_api(prompt, task='shorten')

            return self._basic_summarize(text, target_length)

        except Exception as e:
            print(f"Error shortening text: {e}")
            return text

    def rewrite_paragraph(self, text: str, style: Optional[str] = None) -> str:
        """
        Rewrite paragraph with improved clarity and flow.

        Args:
            text: Text to rewrite
            style: Optional style instruction

        Returns:
            Rewritten text
        """
        if not self.ai_enabled:
            return text

        try:
            # In production, call AI API here
            style_instruction = f" in a {style} style" if style else ""
            prompt = f"""Rewrite the following paragraph with improved clarity and flow{style_instruction}:

Text: {text}

Rewritten text:"""

            # Placeholder for AI API call
            # return self._call_ai_api(prompt, task='rewrite')

            return text

        except Exception as e:
            print(f"Error rewriting: {e}")
            return text

    def translate(self, text: str, target_language: str) -> str:
        """
        Translate text to target language.

        Args:
            text: Text to translate
            target_language: Target language name

        Returns:
            Translated text
        """
        if not self.ai_enabled:
            return f"[Translation to {target_language} not available]"

        if target_language not in self.SUPPORTED_LANGUAGES:
            return f"[Language '{target_language}' not supported]"

        try:
            # In production, call AI API or translation service here
            prompt = f"""Translate the following text to {target_language}:

Text: {text}

Translation:"""

            # Placeholder for AI API call
            # return self._call_ai_api(prompt, task='translate')

            return f"[Translation to {target_language} not available]"

        except Exception as e:
            print(f"Error translating: {e}")
            return text

    def continue_writing(self, text: str, length: Optional[int] = None) -> str:
        """
        Continue writing from the given text.

        Args:
            text: Existing text to continue from
            length: Optional target length for continuation in words

        Returns:
            Continuation text
        """
        if not self.ai_enabled:
            return ""

        try:
            # In production, call AI API here
            length_instruction = f" about {length} words" if length else "1-2 paragraphs"
            prompt = f"""Continue writing from the following text. Write {length_instruction}:

Text: {text}

Continuation:"""

            # Placeholder for AI API call
            # return self._call_ai_api(prompt, task='continue')

            return ""

        except Exception as e:
            print(f"Error continuing writing: {e}")
            return ""

    def generate_from_outline(self, outline: str) -> str:
        """
        Generate full text from an outline.

        Args:
            outline: Outline or bullet points

        Returns:
            Generated full text
        """
        if not self.ai_enabled:
            return outline

        try:
            # In production, call AI API here
            prompt = f"""Generate a well-written document from the following outline:

Outline:
{outline}

Generated text:"""

            # Placeholder for AI API call
            # return self._call_ai_api(prompt, task='generate_from_outline')

            return outline

        except Exception as e:
            print(f"Error generating from outline: {e}")
            return outline

    def _call_ai_api(self, prompt: str, task: str) -> str:
        """
        Call AI API for text generation.

        Args:
            prompt: Prompt for AI
            task: Task type

        Returns:
            AI-generated response
        """
        # Placeholder for actual AI API integration
        # In production, integrate with:
        # - OpenAI API (GPT-4, GPT-3.5)
        # - Anthropic API (Claude)
        # - Local models (LLaMA, Mistral, etc.)

        try:
            # Example structure for API call:
            # import anthropic
            # client = anthropic.Anthropic(api_key=self.api_key)
            # response = client.messages.create(
            #     model="claude-3-opus-20240229",
            #     max_tokens=1024,
            #     messages=[{"role": "user", "content": prompt}]
            # )
            # return response.content[0].text

            return ""

        except Exception as e:
            print(f"Error calling AI API: {e}")
            return ""

    def get_writing_statistics(self, text: str) -> Dict[str, Any]:
        """
        Get advanced writing statistics and readability metrics.

        Args:
            text: Text to analyze

        Returns:
            Dictionary of statistics and metrics
        """
        words = text.split()
        sentences = re.split(r'[.!?]+', text)
        sentences = [s.strip() for s in sentences if s.strip()]

        # Calculate syllables (approximate)
        def count_syllables(word: str) -> int:
            word = word.lower()
            vowels = 'aeiou'
            count = 0
            prev_was_vowel = False

            for char in word:
                is_vowel = char in vowels
                if is_vowel and not prev_was_vowel:
                    count += 1
                prev_was_vowel = is_vowel

            # Adjust for silent 'e'
            if word.endswith('e'):
                count -= 1

            return max(1, count)

        total_syllables = sum(count_syllables(word) for word in words)

        # Flesch Reading Ease
        if len(sentences) > 0 and len(words) > 0:
            flesch_score = 206.835 - 1.015 * (len(words) / len(sentences)) - 84.6 * (total_syllables / len(words))
            flesch_score = max(0, min(100, flesch_score))  # Clamp to 0-100
        else:
            flesch_score = 0

        # Determine grade level
        if flesch_score >= 90:
            grade_level = "5th grade"
        elif flesch_score >= 80:
            grade_level = "6th grade"
        elif flesch_score >= 70:
            grade_level = "7th grade"
        elif flesch_score >= 60:
            grade_level = "8th-9th grade"
        elif flesch_score >= 50:
            grade_level = "10th-12th grade"
        elif flesch_score >= 30:
            grade_level = "College"
        else:
            grade_level = "College graduate"

        return {
            'flesch_reading_ease': round(flesch_score, 1),
            'grade_level': grade_level,
            'total_syllables': total_syllables,
            'avg_syllables_per_word': round(total_syllables / max(len(words), 1), 2),
            'complex_words': sum(1 for word in words if count_syllables(word) >= 3),
        }
