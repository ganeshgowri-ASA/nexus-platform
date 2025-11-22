"""
Translation quality scoring service
"""

from typing import Dict, Any, List
import re
from difflib import SequenceMatcher

from ..constants import QUALITY_THRESHOLDS


class QualityScoringService:
    """Service for evaluating translation quality"""

    def __init__(self):
        """Initialize quality scoring service"""
        pass

    async def calculate_quality_score(
        self,
        source_text: str,
        translated_text: str,
        source_language: str,
        target_language: str
    ) -> Dict[str, Any]:
        """
        Calculate quality score for a translation

        Args:
            source_text: Original text
            translated_text: Translated text
            source_language: Source language code
            target_language: Target language code

        Returns:
            Dictionary containing quality score and analysis
        """
        factors = {}

        # 1. Length ratio check (target should be within reasonable range of source)
        length_ratio = self._calculate_length_ratio(source_text, translated_text)
        factors['length_ratio'] = length_ratio

        # 2. Character diversity (check if translation has varied characters)
        char_diversity = self._calculate_character_diversity(translated_text)
        factors['character_diversity'] = char_diversity

        # 3. Punctuation preservation
        punctuation_score = self._calculate_punctuation_preservation(source_text, translated_text)
        factors['punctuation_preservation'] = punctuation_score

        # 4. Formatting preservation (newlines, spacing)
        formatting_score = self._calculate_formatting_preservation(source_text, translated_text)
        factors['formatting_preservation'] = formatting_score

        # 5. Number preservation (numbers should be preserved)
        number_score = self._calculate_number_preservation(source_text, translated_text)
        factors['number_preservation'] = number_score

        # 6. Word repetition detection (excessive repetition indicates poor quality)
        repetition_score = self._calculate_repetition_score(translated_text)
        factors['repetition_score'] = repetition_score

        # 7. Special characters preservation
        special_chars_score = self._calculate_special_chars_preservation(source_text, translated_text)
        factors['special_chars_preservation'] = special_chars_score

        # Calculate weighted overall score
        weights = {
            'length_ratio': 0.20,
            'character_diversity': 0.15,
            'punctuation_preservation': 0.15,
            'formatting_preservation': 0.10,
            'number_preservation': 0.20,
            'repetition_score': 0.10,
            'special_chars_preservation': 0.10
        }

        overall_score = sum(
            factors[factor] * weights[factor]
            for factor in weights.keys()
        )

        # Determine rating
        rating = self._get_rating(overall_score)

        # Generate suggestions
        suggestions = self._generate_suggestions(factors)

        return {
            'score': round(overall_score, 3),
            'rating': rating,
            'factors': {k: round(v, 3) for k, v in factors.items()},
            'suggestions': suggestions
        }

    def _calculate_length_ratio(self, source: str, target: str) -> float:
        """Calculate score based on length ratio"""
        if len(source) == 0:
            return 0.0

        ratio = len(target) / len(source)

        # Ideal ratio is between 0.5 and 2.0
        if 0.7 <= ratio <= 1.5:
            return 1.0
        elif 0.5 <= ratio <= 2.0:
            return 0.8
        elif 0.3 <= ratio <= 3.0:
            return 0.6
        else:
            return 0.3

    def _calculate_character_diversity(self, text: str) -> float:
        """Calculate character diversity score"""
        if len(text) == 0:
            return 0.0

        unique_chars = len(set(text.lower()))
        total_chars = len(text)

        # Higher diversity is better (up to a point)
        diversity_ratio = unique_chars / total_chars

        if diversity_ratio >= 0.3:
            return 1.0
        elif diversity_ratio >= 0.2:
            return 0.8
        elif diversity_ratio >= 0.1:
            return 0.6
        else:
            return 0.4

    def _calculate_punctuation_preservation(self, source: str, target: str) -> float:
        """Calculate punctuation preservation score"""
        source_punct = set(re.findall(r'[.,!?;:()\[\]{}"\'`]', source))
        target_punct = set(re.findall(r'[.,!?;:()\[\]{}"\'`]', target))

        if len(source_punct) == 0 and len(target_punct) == 0:
            return 1.0

        if len(source_punct) == 0:
            return 0.8  # Source has no punctuation, target has some

        # Calculate Jaccard similarity
        intersection = len(source_punct & target_punct)
        union = len(source_punct | target_punct)

        return intersection / union if union > 0 else 0.0

    def _calculate_formatting_preservation(self, source: str, target: str) -> float:
        """Calculate formatting preservation score"""
        source_newlines = source.count('\n')
        target_newlines = target.count('\n')

        source_tabs = source.count('\t')
        target_tabs = target.count('\t')

        # Check if formatting is similar
        newline_score = 1.0 if abs(source_newlines - target_newlines) <= 1 else 0.5
        tab_score = 1.0 if abs(source_tabs - target_tabs) <= 1 else 0.5

        return (newline_score + tab_score) / 2

    def _calculate_number_preservation(self, source: str, target: str) -> float:
        """Calculate number preservation score"""
        source_numbers = set(re.findall(r'\d+', source))
        target_numbers = set(re.findall(r'\d+', target))

        if len(source_numbers) == 0 and len(target_numbers) == 0:
            return 1.0

        if len(source_numbers) == 0:
            return 0.8  # Source has no numbers

        # Check if all numbers are preserved
        preserved = source_numbers & target_numbers
        preservation_ratio = len(preserved) / len(source_numbers)

        return preservation_ratio

    def _calculate_repetition_score(self, text: str) -> float:
        """Calculate score based on word repetition"""
        words = text.lower().split()

        if len(words) == 0:
            return 0.0

        # Count word frequencies
        word_freq = {}
        for word in words:
            word_freq[word] = word_freq.get(word, 0) + 1

        # Calculate repetition ratio
        max_repetition = max(word_freq.values()) if word_freq else 0
        repetition_ratio = max_repetition / len(words)

        # Lower repetition is better
        if repetition_ratio <= 0.1:
            return 1.0
        elif repetition_ratio <= 0.2:
            return 0.8
        elif repetition_ratio <= 0.3:
            return 0.6
        else:
            return 0.4

    def _calculate_special_chars_preservation(self, source: str, target: str) -> float:
        """Calculate special characters preservation score"""
        # Find special characters like @, #, $, %, &, etc.
        special_pattern = r'[@#$%&*+=<>/_|~]'
        source_special = set(re.findall(special_pattern, source))
        target_special = set(re.findall(special_pattern, target))

        if len(source_special) == 0 and len(target_special) == 0:
            return 1.0

        if len(source_special) == 0:
            return 0.9  # Source has no special chars

        # Check preservation
        preserved = source_special & target_special
        preservation_ratio = len(preserved) / len(source_special)

        return preservation_ratio

    def _get_rating(self, score: float) -> str:
        """Get quality rating from score"""
        if score >= QUALITY_THRESHOLDS['excellent']:
            return 'excellent'
        elif score >= QUALITY_THRESHOLDS['good']:
            return 'good'
        elif score >= QUALITY_THRESHOLDS['acceptable']:
            return 'acceptable'
        else:
            return 'poor'

    def _generate_suggestions(self, factors: Dict[str, float]) -> List[str]:
        """Generate improvement suggestions based on factors"""
        suggestions = []

        if factors['length_ratio'] < 0.6:
            suggestions.append("Translation length is significantly different from source")

        if factors['character_diversity'] < 0.5:
            suggestions.append("Translation has low character diversity, may indicate repetition")

        if factors['punctuation_preservation'] < 0.7:
            suggestions.append("Punctuation marks are not well preserved")

        if factors['number_preservation'] < 0.9:
            suggestions.append("Some numbers from the source are missing in translation")

        if factors['repetition_score'] < 0.7:
            suggestions.append("Translation contains excessive word repetition")

        if not suggestions:
            suggestions.append("Translation quality appears good")

        return suggestions

    def compare_translations(
        self,
        translations: List[Dict[str, str]]
    ) -> Dict[str, Any]:
        """
        Compare multiple translations of the same source

        Args:
            translations: List of translation dictionaries with 'text' and 'provider' keys

        Returns:
            Comparison results
        """
        if len(translations) < 2:
            return {'error': 'At least 2 translations required for comparison'}

        # Calculate similarity between translations
        similarities = []
        for i, trans1 in enumerate(translations):
            for j, trans2 in enumerate(translations[i+1:], i+1):
                similarity = SequenceMatcher(
                    None,
                    trans1['text'],
                    trans2['text']
                ).ratio()

                similarities.append({
                    'provider1': trans1.get('provider', f'Translation {i+1}'),
                    'provider2': trans2.get('provider', f'Translation {j+1}'),
                    'similarity': round(similarity, 3)
                })

        # Calculate average similarity
        avg_similarity = sum(s['similarity'] for s in similarities) / len(similarities)

        return {
            'similarities': similarities,
            'average_similarity': round(avg_similarity, 3),
            'consensus': 'high' if avg_similarity >= 0.8 else 'medium' if avg_similarity >= 0.6 else 'low'
        }
