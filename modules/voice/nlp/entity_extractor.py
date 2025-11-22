"""Entity extraction from text."""

import re
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import json


class EntityExtractor:
    """Extract entities from text (dates, times, numbers, names, etc.)."""

    def __init__(self, llm_client=None):
        """
        Initialize entity extractor.

        Args:
            llm_client: Optional LLM client for advanced extraction
        """
        self.llm_client = llm_client

    def extract_entities(self, text: str) -> Dict[str, List]:
        """
        Extract all entities from text.

        Args:
            text: Input text

        Returns:
            Dict with entity types as keys and lists of entities as values
        """
        entities = {
            "dates": self.extract_dates(text),
            "times": self.extract_times(text),
            "numbers": self.extract_numbers(text),
            "emails": self.extract_emails(text),
            "urls": self.extract_urls(text),
            "phone_numbers": self.extract_phone_numbers(text),
            "names": self.extract_names(text),
            "durations": self.extract_durations(text)
        }

        # Remove empty lists
        return {k: v for k, v in entities.items() if v}

    def extract_dates(self, text: str) -> List[Dict]:
        """Extract dates from text."""
        dates = []
        text_lower = text.lower()

        # Relative dates
        relative_patterns = {
            r'\btoday\b': 0,
            r'\btomorrow\b': 1,
            r'\byesterday\b': -1,
            r'next\s+week': 7,
            r'next\s+month': 30,
            r'in\s+(\d+)\s+days?': lambda m: int(m.group(1)),
            r'(\d+)\s+days?\s+ago': lambda m: -int(m.group(1))
        }

        for pattern, offset in relative_patterns.items():
            matches = re.finditer(pattern, text_lower)
            for match in matches:
                if callable(offset):
                    days = offset(match)
                else:
                    days = offset

                target_date = datetime.now() + timedelta(days=days)
                dates.append({
                    "text": match.group(0),
                    "date": target_date.strftime("%Y-%m-%d"),
                    "type": "relative"
                })

        # Specific dates (MM/DD/YYYY, DD-MM-YYYY, etc.)
        date_patterns = [
            (r'(\d{1,2})[/-](\d{1,2})[/-](\d{4})', 'MM/DD/YYYY'),
            (r'(\d{4})[/-](\d{1,2})[/-](\d{1,2})', 'YYYY-MM-DD'),
        ]

        for pattern, format_type in date_patterns:
            matches = re.finditer(pattern, text)
            for match in matches:
                dates.append({
                    "text": match.group(0),
                    "date": match.group(0),
                    "type": "absolute",
                    "format": format_type
                })

        # Day names
        days = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']
        for day in days:
            if day in text_lower:
                # Find the next occurrence of this day
                today = datetime.now()
                current_day = today.weekday()
                target_day = days.index(day)
                days_ahead = (target_day - current_day) % 7
                if days_ahead == 0:
                    days_ahead = 7
                target_date = today + timedelta(days=days_ahead)

                dates.append({
                    "text": day,
                    "date": target_date.strftime("%Y-%m-%d"),
                    "type": "day_name"
                })

        return dates

    def extract_times(self, text: str) -> List[Dict]:
        """Extract times from text."""
        times = []

        # 24-hour format (HH:MM)
        pattern_24h = r'\b([0-2]?\d):([0-5]\d)\b'
        for match in re.finditer(pattern_24h, text):
            times.append({
                "text": match.group(0),
                "hour": int(match.group(1)),
                "minute": int(match.group(2)),
                "format": "24h"
            })

        # 12-hour format (HH:MM AM/PM)
        pattern_12h = r'\b(\d{1,2}):?(\d{2})?\s*(am|pm)\b'
        for match in re.finditer(pattern_12h, text.lower()):
            hour = int(match.group(1))
            minute = int(match.group(2)) if match.group(2) else 0
            period = match.group(3)

            # Convert to 24h
            if period == 'pm' and hour != 12:
                hour += 12
            elif period == 'am' and hour == 12:
                hour = 0

            times.append({
                "text": match.group(0),
                "hour": hour,
                "minute": minute,
                "format": "12h",
                "period": period
            })

        # Relative times
        relative_patterns = {
            r'in\s+(\d+)\s+hours?': 'hour',
            r'in\s+(\d+)\s+minutes?': 'minute'
        }

        for pattern, unit in relative_patterns.items():
            matches = re.finditer(pattern, text.lower())
            for match in matches:
                amount = int(match.group(1))
                target_time = datetime.now()

                if unit == 'hour':
                    target_time += timedelta(hours=amount)
                elif unit == 'minute':
                    target_time += timedelta(minutes=amount)

                times.append({
                    "text": match.group(0),
                    "hour": target_time.hour,
                    "minute": target_time.minute,
                    "format": "relative"
                })

        return times

    def extract_numbers(self, text: str) -> List[Dict]:
        """Extract numbers from text."""
        numbers = []

        # Integers and floats
        pattern = r'\b(\d+(?:\.\d+)?)\b'
        for match in re.finditer(pattern, text):
            value = float(match.group(1)) if '.' in match.group(1) else int(match.group(1))
            numbers.append({
                "text": match.group(0),
                "value": value,
                "type": "float" if '.' in match.group(1) else "integer"
            })

        # Written numbers
        word_to_num = {
            'zero': 0, 'one': 1, 'two': 2, 'three': 3, 'four': 4,
            'five': 5, 'six': 6, 'seven': 7, 'eight': 8, 'nine': 9,
            'ten': 10, 'eleven': 11, 'twelve': 12, 'thirteen': 13,
            'fourteen': 14, 'fifteen': 15, 'twenty': 20, 'thirty': 30,
            'forty': 40, 'fifty': 50, 'hundred': 100, 'thousand': 1000
        }

        text_lower = text.lower()
        for word, value in word_to_num.items():
            if f' {word} ' in f' {text_lower} ':
                numbers.append({
                    "text": word,
                    "value": value,
                    "type": "word"
                })

        return numbers

    def extract_emails(self, text: str) -> List[str]:
        """Extract email addresses."""
        pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        return re.findall(pattern, text)

    def extract_urls(self, text: str) -> List[str]:
        """Extract URLs."""
        pattern = r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
        return re.findall(pattern, text)

    def extract_phone_numbers(self, text: str) -> List[str]:
        """Extract phone numbers."""
        patterns = [
            r'\b\d{3}[-.\s]?\d{3}[-.\s]?\d{4}\b',  # US format
            r'\b\(\d{3}\)\s*\d{3}[-.\s]?\d{4}\b',  # (XXX) XXX-XXXX
        ]

        phone_numbers = []
        for pattern in patterns:
            phone_numbers.extend(re.findall(pattern, text))

        return phone_numbers

    def extract_names(self, text: str) -> List[str]:
        """Extract potential names (capitalized words)."""
        # Simple heuristic: consecutive capitalized words
        pattern = r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)+\b'
        return re.findall(pattern, text)

    def extract_durations(self, text: str) -> List[Dict]:
        """Extract duration expressions."""
        durations = []

        patterns = {
            r'(\d+)\s*hours?': ('hour', 3600),
            r'(\d+)\s*minutes?': ('minute', 60),
            r'(\d+)\s*seconds?': ('second', 1),
            r'(\d+)\s*days?': ('day', 86400),
            r'(\d+)\s*weeks?': ('week', 604800)
        }

        for pattern, (unit, seconds_multiplier) in patterns.items():
            matches = re.finditer(pattern, text.lower())
            for match in matches:
                amount = int(match.group(1))
                durations.append({
                    "text": match.group(0),
                    "amount": amount,
                    "unit": unit,
                    "seconds": amount * seconds_multiplier
                })

        return durations

    def extract_with_llm(self, text: str, entity_types: List[str]) -> Dict:
        """
        Use LLM for advanced entity extraction.

        Args:
            text: Input text
            entity_types: Types of entities to extract

        Returns:
            Dict with extracted entities
        """
        if not self.llm_client:
            return {}

        prompt = f"""Extract the following entities from this text: {', '.join(entity_types)}

Text: "{text}"

Respond with JSON only:
{{
  "entity_type": ["value1", "value2", ...]
}}"""

        try:
            # This is a placeholder - implement based on your LLM client
            # response = self.llm_client.generate(prompt)
            # return json.loads(response)
            return {}
        except Exception:
            return {}
