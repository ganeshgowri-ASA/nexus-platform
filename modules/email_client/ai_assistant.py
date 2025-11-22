"""
AI Email Assistant

AI-powered features for email: smart replies, summarization, sentiment analysis, etc.
"""

import logging
import re
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


@dataclass
class SmartReply:
    """Smart reply suggestion."""
    text: str
    tone: str  # 'formal', 'casual', 'friendly'
    confidence: float  # 0-1


@dataclass
class EmailSummary:
    """Email summary."""
    short_summary: str  # One-line summary
    key_points: List[str]  # Bullet points
    action_items: List[str]  # Action items extracted
    mentioned_people: List[str]  # People mentioned
    mentioned_dates: List[str]  # Dates mentioned
    sentiment: str  # 'positive', 'neutral', 'negative'


@dataclass
class MeetingInfo:
    """Extracted meeting information."""
    title: str
    date: Optional[datetime]
    time: Optional[str]
    location: Optional[str]
    attendees: List[str]
    agenda: Optional[str]


class AIEmailAssistant:
    """
    AI-powered email assistant.

    Provides smart replies, summarization, sentiment analysis,
    priority scoring, and more.
    """

    def __init__(self, ai_model: Optional[Any] = None):
        """
        Initialize AI assistant.

        Args:
            ai_model: AI model instance (e.g., from AI orchestrator)
        """
        self.ai_model = ai_model

    async def process_message(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a message with AI features.

        Args:
            message: Email message

        Returns:
            Dict: Message with AI enhancements
        """
        # Calculate priority score
        message['ai_priority_score'] = await self.calculate_priority(message)

        # Categorize
        message['ai_category'] = await self.categorize_email(message)

        # Sentiment analysis
        message['ai_sentiment'] = await self.analyze_sentiment(message)

        # Generate summary
        summary = await self.summarize_email(message)
        if summary:
            message['ai_summary'] = summary.short_summary

        return message

    async def calculate_priority(self, message: Dict[str, Any]) -> float:
        """
        Calculate priority score for an email (0-1).

        Args:
            message: Email message

        Returns:
            float: Priority score
        """
        score = 0.5  # Base score

        # Factor: Sender importance
        from_addr = message.get('from_address', '').lower()

        # Check if from known important domain
        important_domains = ['@company.com', '@client.com']
        for domain in important_domains:
            if domain in from_addr:
                score += 0.2
                break

        # Factor: Keywords in subject
        subject = message.get('subject', '').lower()
        urgent_keywords = ['urgent', 'important', 'asap', 'critical', 'emergency']

        for keyword in urgent_keywords:
            if keyword in subject:
                score += 0.2
                break

        # Factor: Direct mention
        body = (message.get('body_text', '') + message.get('body_html', '')).lower()
        if 'you' in body[:200]:  # Check first 200 chars
            score += 0.1

        # Factor: Question
        if '?' in subject or '?' in body[:500]:
            score += 0.1

        # Factor: Short email (likely important)
        if len(body) < 500:
            score += 0.1

        # Normalize to 0-1
        score = min(1.0, max(0.0, score))

        return score

    async def categorize_email(self, message: Dict[str, Any]) -> str:
        """
        Categorize an email.

        Args:
            message: Email message

        Returns:
            str: Category
        """
        subject = message.get('subject', '').lower()
        body = (message.get('body_text', '') + message.get('body_html', '')).lower()
        combined = subject + ' ' + body

        # Simple keyword-based categorization
        # In production, use ML model

        if any(kw in combined for kw in ['meeting', 'calendar', 'schedule', 'appointment']):
            return 'Meetings'

        if any(kw in combined for kw in ['invoice', 'payment', 'receipt', 'billing']):
            return 'Finance'

        if any(kw in combined for kw in ['project', 'deadline', 'task', 'deliverable']):
            return 'Projects'

        if any(kw in combined for kw in ['newsletter', 'unsubscribe', 'digest']):
            return 'Newsletters'

        if any(kw in combined for kw in ['travel', 'flight', 'hotel', 'reservation']):
            return 'Travel'

        if any(kw in combined for kw in ['order', 'shipping', 'delivery', 'tracking']):
            return 'Shopping'

        return 'General'

    async def analyze_sentiment(self, message: Dict[str, Any]) -> str:
        """
        Analyze email sentiment.

        Args:
            message: Email message

        Returns:
            str: Sentiment ('positive', 'neutral', 'negative')
        """
        body = message.get('body_text', '') + message.get('body_html', '')

        # Simple keyword-based sentiment
        # In production, use sentiment analysis model

        positive_words = [
            'thank', 'thanks', 'great', 'excellent', 'wonderful',
            'appreciate', 'pleased', 'happy', 'good', 'perfect'
        ]

        negative_words = [
            'unfortunately', 'problem', 'issue', 'error', 'failed',
            'wrong', 'bad', 'poor', 'disappointed', 'urgent'
        ]

        body_lower = body.lower()

        positive_count = sum(1 for word in positive_words if word in body_lower)
        negative_count = sum(1 for word in negative_words if word in body_lower)

        if positive_count > negative_count:
            return 'positive'
        elif negative_count > positive_count:
            return 'negative'
        else:
            return 'neutral'

    async def summarize_email(self, message: Dict[str, Any]) -> Optional[EmailSummary]:
        """
        Generate email summary.

        Args:
            message: Email message

        Returns:
            Optional[EmailSummary]: Summary
        """
        body = message.get('body_text', '')
        if not body:
            return None

        # Simple extractive summary
        # In production, use abstractive summarization model

        sentences = self._split_sentences(body)

        # Take first 2 sentences as summary
        short_summary = ' '.join(sentences[:2]) if sentences else body[:200]

        # Extract key points (sentences with keywords)
        key_points = self._extract_key_points(sentences)

        # Extract action items
        action_items = self._extract_action_items(body)

        # Extract mentioned people
        mentioned_people = self._extract_people(body)

        # Extract dates
        mentioned_dates = self._extract_dates(body)

        # Sentiment
        sentiment = await self.analyze_sentiment(message)

        return EmailSummary(
            short_summary=short_summary,
            key_points=key_points,
            action_items=action_items,
            mentioned_people=mentioned_people,
            mentioned_dates=mentioned_dates,
            sentiment=sentiment
        )

    def _split_sentences(self, text: str) -> List[str]:
        """Split text into sentences."""
        # Simple sentence splitting
        sentences = re.split(r'[.!?]+', text)
        return [s.strip() for s in sentences if s.strip()]

    def _extract_key_points(self, sentences: List[str]) -> List[str]:
        """Extract key points from sentences."""
        key_points = []

        keywords = ['important', 'please', 'need', 'must', 'should', 'will', 'deadline']

        for sentence in sentences[:10]:  # Check first 10 sentences
            if any(kw in sentence.lower() for kw in keywords):
                key_points.append(sentence.strip())

            if len(key_points) >= 3:
                break

        return key_points

    def _extract_action_items(self, text: str) -> List[str]:
        """Extract action items from text."""
        action_items = []

        # Look for action verbs
        action_patterns = [
            r'please (.+?)[\.\n]',
            r'could you (.+?)[\.\n]',
            r'can you (.+?)[\.\n]',
            r'need to (.+?)[\.\n]',
            r'should (.+?)[\.\n]',
        ]

        for pattern in action_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            action_items.extend(matches)

        return action_items[:5]  # Max 5 action items

    def _extract_people(self, text: str) -> List[str]:
        """Extract mentioned people (simple implementation)."""
        # Look for capitalized names
        # In production, use NER (Named Entity Recognition)

        words = text.split()
        people = []

        for i, word in enumerate(words):
            # Check if word is capitalized and not at sentence start
            if word and word[0].isupper() and i > 0:
                # Check if previous word is lowercase (not sentence start)
                if words[i-1] and words[i-1][0].islower():
                    people.append(word)

        return list(set(people))[:10]  # Unique, max 10

    def _extract_dates(self, text: str) -> List[str]:
        """Extract mentioned dates."""
        date_patterns = [
            r'\d{1,2}/\d{1,2}/\d{2,4}',  # MM/DD/YYYY
            r'\d{4}-\d{2}-\d{2}',  # YYYY-MM-DD
            r'(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]* \d{1,2}',  # Month DD
        ]

        dates = []
        for pattern in date_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            dates.extend(matches)

        return dates[:5]  # Max 5 dates

    async def generate_smart_replies(
        self,
        message: Dict[str, Any],
        count: int = 3
    ) -> List[SmartReply]:
        """
        Generate smart reply suggestions.

        Args:
            message: Email message to reply to
            count: Number of suggestions

        Returns:
            List[SmartReply]: Reply suggestions
        """
        # Simple template-based replies
        # In production, use generative AI model

        sentiment = await self.analyze_sentiment(message)
        body = message.get('body_text', '')

        replies = []

        # Question detection
        if '?' in message.get('subject', '') or '?' in body:
            replies.append(SmartReply(
                text="Thanks for your email. I'll look into this and get back to you shortly.",
                tone='professional',
                confidence=0.8
            ))
        else:
            # Acknowledgment
            replies.append(SmartReply(
                text="Thank you for the update!",
                tone='friendly',
                confidence=0.7
            ))

        # Positive sentiment
        if sentiment == 'positive':
            replies.append(SmartReply(
                text="Thanks so much! I appreciate it.",
                tone='friendly',
                confidence=0.8
            ))

        # Meeting-related
        if any(kw in body.lower() for kw in ['meeting', 'schedule', 'calendar']):
            replies.append(SmartReply(
                text="That works for me. I'll add it to my calendar.",
                tone='professional',
                confidence=0.7
            ))

        # Generic
        replies.append(SmartReply(
            text="Got it, thanks!",
            tone='casual',
            confidence=0.6
        ))

        return replies[:count]

    async def check_grammar(self, text: str) -> Dict[str, Any]:
        """
        Check grammar and suggest corrections.

        Args:
            text: Text to check

        Returns:
            Dict: Grammar check results
        """
        # Placeholder implementation
        # In production, integrate with grammar checking API

        return {
            'has_errors': False,
            'errors': [],
            'suggestions': []
        }

    async def translate_email(
        self,
        message: Dict[str, Any],
        target_language: str
    ) -> str:
        """
        Translate email to another language.

        Args:
            message: Email message
            target_language: Target language code

        Returns:
            str: Translated text
        """
        # Placeholder implementation
        # In production, integrate with translation API

        body = message.get('body_text', '')
        logger.info(f"Would translate to {target_language}: {body[:100]}")

        return f"[Translation to {target_language}] {body}"

    async def extract_meeting_info(
        self,
        message: Dict[str, Any]
    ) -> Optional[MeetingInfo]:
        """
        Extract meeting information from email.

        Args:
            message: Email message

        Returns:
            Optional[MeetingInfo]: Extracted meeting info
        """
        body = message.get('body_text', '')
        subject = message.get('subject', '')

        # Check if it's a meeting-related email
        if not any(kw in (subject + body).lower() for kw in ['meeting', 'call', 'discussion']):
            return None

        # Extract information
        title = subject

        # Extract date/time (simple patterns)
        date_match = re.search(
            r'(?:on|at) (\w+ \d{1,2}(?:st|nd|rd|th)?)',
            body,
            re.IGNORECASE
        )
        date_str = date_match.group(1) if date_match else None

        time_match = re.search(
            r'(\d{1,2}:\d{2}\s*(?:AM|PM)?)',
            body,
            re.IGNORECASE
        )
        time_str = time_match.group(1) if time_match else None

        # Extract location
        location_match = re.search(
            r'(?:at|in|location:)\s*([A-Z][a-zA-Z\s]+)',
            body
        )
        location = location_match.group(1).strip() if location_match else None

        # Extract attendees (from To/CC)
        attendees = message.get('to_addresses', []) + message.get('cc_addresses', [])

        return MeetingInfo(
            title=title,
            date=None,  # Would parse date_str
            time=time_str,
            location=location,
            attendees=attendees,
            agenda=None
        )

    async def suggest_folder(self, message: Dict[str, Any]) -> str:
        """
        Suggest folder for email.

        Args:
            message: Email message

        Returns:
            str: Suggested folder name
        """
        category = await self.categorize_email(message)

        folder_mapping = {
            'Meetings': 'Calendar',
            'Finance': 'Finance',
            'Projects': 'Projects',
            'Newsletters': 'Newsletters',
            'Travel': 'Travel',
            'Shopping': 'Shopping',
        }

        return folder_mapping.get(category, 'Inbox')

    async def detect_phishing(self, message: Dict[str, Any]) -> Tuple[bool, float, List[str]]:
        """
        Detect potential phishing email.

        Args:
            message: Email message

        Returns:
            Tuple[bool, float, List[str]]: (is_phishing, confidence, reasons)
        """
        reasons = []
        score = 0

        from_addr = message.get('from_address', '')
        subject = message.get('subject', '')
        body = (message.get('body_text', '') + message.get('body_html', '')).lower()

        # Check for suspicious sender
        if from_addr and '@' in from_addr:
            domain = from_addr.split('@')[1]
            # Check for common phishing patterns
            if any(char in domain for char in ['1', '0']) or domain.count('-') > 2:
                score += 0.3
                reasons.append("Suspicious sender domain")

        # Check for urgent language
        urgent_phrases = ['urgent', 'immediately', 'verify account', 'suspended', 'confirm']
        if any(phrase in subject.lower() or phrase in body for phrase in urgent_phrases):
            score += 0.2
            reasons.append("Urgent language detected")

        # Check for suspicious links
        url_pattern = r'https?://[^\s<>"{}|\\^`\[\]]+'
        urls = re.findall(url_pattern, body)

        for url in urls:
            if 'bit.ly' in url or 'tinyurl' in url:
                score += 0.2
                reasons.append("Shortened URL detected")
                break

        # Check for requests for personal information
        sensitive_keywords = ['password', 'ssn', 'credit card', 'bank account']
        if any(kw in body for kw in sensitive_keywords):
            score += 0.3
            reasons.append("Requests sensitive information")

        is_phishing = score >= 0.5

        return (is_phishing, min(score, 1.0), reasons)
