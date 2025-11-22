"""
Post-Processing Module

Spell checking, language correction, and formatting preservation.
"""

import logging
import re
from typing import List, Dict, Any, Optional, Set
from collections import defaultdict

logger = logging.getLogger(__name__)


class SpellChecker:
    """Spell checker for OCR output"""

    def __init__(self, language: str = "en"):
        self.language = language
        self.logger = logging.getLogger(f"{__name__}.SpellChecker")
        self._dictionary: Optional[Set[str]] = None
        self._initialize()

    def _initialize(self):
        """Initialize spell checker"""
        try:
            # Try to use enchant library
            import enchant
            self._dictionary = enchant.Dict(self.language)
            self.logger.info(f"Spell checker initialized with language: {self.language}")
        except ImportError:
            self.logger.warning("pyenchant not installed, spell checking disabled")
        except Exception as e:
            self.logger.warning(f"Could not initialize spell checker: {e}")

    def check_word(self, word: str) -> bool:
        """Check if word is spelled correctly"""
        try:
            if self._dictionary is None:
                return True
            return self._dictionary.check(word)
        except:
            return True

    def suggest_corrections(self, word: str, max_suggestions: int = 5) -> List[str]:
        """Get spelling suggestions for word"""
        try:
            if self._dictionary is None:
                return [word]
            suggestions = self._dictionary.suggest(word)
            return suggestions[:max_suggestions]
        except:
            return [word]

    def correct_text(self, text: str, confidence_threshold: float = 0.6) -> str:
        """
        Correct spelling errors in text

        Args:
            text: Input text
            confidence_threshold: Only correct words below this confidence

        Returns:
            Corrected text
        """
        try:
            if self._dictionary is None:
                return text

            words = text.split()
            corrected_words = []

            for word in words:
                # Skip punctuation and numbers
                clean_word = re.sub(r'[^\w]', '', word)
                if not clean_word or clean_word.isdigit():
                    corrected_words.append(word)
                    continue

                # Check spelling
                if not self.check_word(clean_word):
                    suggestions = self.suggest_corrections(clean_word, 1)
                    if suggestions:
                        # Replace with suggestion, preserving punctuation
                        corrected = word.replace(clean_word, suggestions[0])
                        corrected_words.append(corrected)
                    else:
                        corrected_words.append(word)
                else:
                    corrected_words.append(word)

            return ' '.join(corrected_words)

        except Exception as e:
            self.logger.error(f"Error correcting text: {e}")
            return text


class LanguageCorrection:
    """Language-specific corrections and improvements"""

    def __init__(self, language: str = "en"):
        self.language = language
        self.logger = logging.getLogger(f"{__name__}.LanguageCorrection")

    def fix_common_ocr_errors(self, text: str) -> str:
        """
        Fix common OCR errors

        Args:
            text: Input text

        Returns:
            Corrected text
        """
        try:
            # Common OCR substitutions
            corrections = {
                r'\b0(?=[a-zA-Z])': 'O',  # 0 -> O in words
                r'(?<=[a-zA-Z])0\b': 'O',
                r'\bl(?=[A-Z])': 'I',     # l -> I before capitals
                r'\brn\b': 'm',           # rn -> m
                r'\bvv': 'w',             # vv -> w
                r'\|': 'I',               # | -> I
                r'(?<=\d),(?=\d{3}\b)': '',  # Remove comma in numbers
            }

            corrected = text
            for pattern, replacement in corrections.items():
                corrected = re.sub(pattern, replacement, corrected)

            return corrected

        except Exception as e:
            self.logger.error(f"Error fixing OCR errors: {e}")
            return text

    def normalize_whitespace(self, text: str) -> str:
        """Normalize whitespace in text"""
        try:
            # Replace multiple spaces with single space
            text = re.sub(r' +', ' ', text)

            # Replace multiple newlines with double newline (paragraph break)
            text = re.sub(r'\n{3,}', '\n\n', text)

            # Remove spaces before punctuation
            text = re.sub(r'\s+([.,;:!?])', r'\1', text)

            # Add space after punctuation if missing
            text = re.sub(r'([.,;:!?])(?=[A-Za-z])', r'\1 ', text)

            return text.strip()

        except Exception as e:
            self.logger.error(f"Error normalizing whitespace: {e}")
            return text

    def fix_capitalization(self, text: str) -> str:
        """Fix capitalization errors"""
        try:
            lines = text.split('\n')
            corrected_lines = []

            for line in lines:
                if not line.strip():
                    corrected_lines.append(line)
                    continue

                # Capitalize first letter of line
                line = line[0].upper() + line[1:] if len(line) > 0 else line

                # Fix "i" -> "I"
                line = re.sub(r'\bi\b', 'I', line)

                corrected_lines.append(line)

            return '\n'.join(corrected_lines)

        except Exception as e:
            self.logger.error(f"Error fixing capitalization: {e}")
            return text


class FormattingPreservation:
    """Preserve document formatting during OCR"""

    def __init__(self):
        self.logger = logging.getLogger(f"{__name__}.FormattingPreservation")

    def preserve_structure(
        self,
        text_blocks: List[Dict[str, Any]],
        layout_info: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Preserve document structure when converting to text

        Args:
            text_blocks: List of text blocks with position info
            layout_info: Optional layout information

        Returns:
            Formatted text
        """
        try:
            if not text_blocks:
                return ""

            # Sort blocks by reading order (top to bottom, left to right)
            sorted_blocks = sorted(
                text_blocks,
                key=lambda b: (b.get('bbox', (0, 0, 0, 0))[1], b.get('bbox', (0, 0, 0, 0))[0])
            )

            # Group blocks into lines and paragraphs
            lines = self._group_into_lines(sorted_blocks)

            # Format output
            formatted_text = []
            prev_line_y = 0

            for line in lines:
                current_y = line['y']

                # Add paragraph break if vertical gap is large
                if prev_line_y > 0 and current_y - prev_line_y > line['height'] * 1.5:
                    formatted_text.append("")  # Empty line for paragraph break

                formatted_text.append(line['text'])
                prev_line_y = current_y + line['height']

            return '\n'.join(formatted_text)

        except Exception as e:
            self.logger.error(f"Error preserving structure: {e}")
            return '\n'.join(b.get('text', '') for b in text_blocks)

    def _group_into_lines(self, blocks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Group text blocks into lines"""
        try:
            if not blocks:
                return []

            lines = []
            current_line = {
                'blocks': [blocks[0]],
                'y': blocks[0].get('bbox', (0, 0, 0, 0))[1],
                'height': blocks[0].get('bbox', (0, 0, 0, 0))[3]
            }

            for block in blocks[1:]:
                bbox = block.get('bbox', (0, 0, 0, 0))
                block_y = bbox[1]
                block_height = bbox[3]

                # Check if block is on same line
                if abs(block_y - current_line['y']) < current_line['height'] * 0.5:
                    current_line['blocks'].append(block)
                else:
                    # Finalize current line
                    current_line['text'] = ' '.join(
                        b.get('text', '') for b in current_line['blocks']
                    )
                    lines.append(current_line)

                    # Start new line
                    current_line = {
                        'blocks': [block],
                        'y': block_y,
                        'height': block_height
                    }

            # Add last line
            if current_line['blocks']:
                current_line['text'] = ' '.join(
                    b.get('text', '') for b in current_line['blocks']
                )
                lines.append(current_line)

            return lines

        except Exception as e:
            self.logger.error(f"Error grouping into lines: {e}")
            return []

    def preserve_tables(self, text: str) -> str:
        """Preserve table formatting"""
        try:
            # Simple table detection based on aligned text
            lines = text.split('\n')
            formatted_lines = []

            for line in lines:
                # Check if line contains multiple columns (multiple spaces)
                if re.search(r'\s{3,}', line):
                    # Convert to tab-separated
                    formatted_line = re.sub(r'\s{2,}', '\t', line)
                    formatted_lines.append(formatted_line)
                else:
                    formatted_lines.append(line)

            return '\n'.join(formatted_lines)

        except Exception as e:
            self.logger.error(f"Error preserving tables: {e}")
            return text


class TextPostProcessor:
    """Main post-processing coordinator"""

    def __init__(self, language: str = "en"):
        self.spell_checker = SpellChecker(language)
        self.language_correction = LanguageCorrection(language)
        self.formatting = FormattingPreservation()
        self.logger = logging.getLogger(f"{__name__}.TextPostProcessor")

    def process(
        self,
        text: str,
        enable_spell_check: bool = True,
        enable_error_correction: bool = True,
        enable_formatting: bool = True
    ) -> str:
        """
        Apply complete post-processing pipeline

        Args:
            text: Input text
            enable_spell_check: Enable spell checking
            enable_error_correction: Enable error correction
            enable_formatting: Enable formatting

        Returns:
            Processed text
        """
        try:
            processed = text

            # Fix common OCR errors
            if enable_error_correction:
                processed = self.language_correction.fix_common_ocr_errors(processed)

            # Normalize whitespace
            if enable_formatting:
                processed = self.language_correction.normalize_whitespace(processed)

            # Fix capitalization
            if enable_error_correction:
                processed = self.language_correction.fix_capitalization(processed)

            # Spell check
            if enable_spell_check:
                processed = self.spell_checker.correct_text(processed)

            # Preserve table formatting
            if enable_formatting:
                processed = self.formatting.preserve_tables(processed)

            self.logger.info("Post-processing completed")
            return processed

        except Exception as e:
            self.logger.error(f"Error in post-processing: {e}")
            return text
