"""Spam filter for detecting and filtering spam emails."""

import re
from typing import Dict, Any, List, Optional, Tuple
from email.message import Message
import logging

from src.core.config import settings
from src.modules.email.parser import EmailParser

logger = logging.getLogger(__name__)


class SpamFilter:
    """Spam filter for email classification."""

    def __init__(
        self,
        spam_keywords: Optional[List[str]] = None,
        threshold: Optional[float] = None
    ):
        """Initialize spam filter.

        Args:
            spam_keywords: List of spam keywords
            threshold: Spam score threshold (0.0 to 1.0)
        """
        self.spam_keywords = spam_keywords or settings.spam_keywords_list
        self.threshold = threshold or settings.spam_filter_threshold

        # Compile keyword patterns
        self.keyword_patterns = [
            re.compile(r'\b' + re.escape(kw) + r'\b', re.IGNORECASE)
            for kw in self.spam_keywords
        ]

    def analyze_email(
        self,
        msg: Message,
        detailed: bool = False
    ) -> Dict[str, Any]:
        """Analyze email for spam indicators.

        Args:
            msg: Email message object
            detailed: Return detailed analysis

        Returns:
            Dict with spam analysis results
        """
        score = 0.0
        indicators = []
        weights = {
            'spam_keywords': 0.3,
            'suspicious_links': 0.2,
            'excessive_caps': 0.15,
            'suspicious_sender': 0.15,
            'no_subject': 0.05,
            'excessive_exclamation': 0.1,
            'suspicious_attachments': 0.2,
            'too_many_links': 0.15
        }

        # Parse email
        parsed = EmailParser.parse_message(msg)

        subject = parsed.get('subject', '')
        body_text = parsed.get('body_text', '') or ''
        body_html = parsed.get('body_html', '') or ''
        from_email = parsed.get('from_email', '')

        # Combine text for analysis
        full_text = f"{subject} {body_text}"

        # 1. Check for spam keywords
        keyword_score = self._check_spam_keywords(full_text)
        if keyword_score > 0:
            score += keyword_score * weights['spam_keywords']
            indicators.append(f"Spam keywords detected (score: {keyword_score:.2f})")

        # 2. Check for suspicious links
        if body_html or body_text:
            link_score = self._check_suspicious_links(body_html or body_text)
            if link_score > 0:
                score += link_score * weights['suspicious_links']
                indicators.append(f"Suspicious links found (score: {link_score:.2f})")

        # 3. Check for excessive capitalization
        caps_score = self._check_excessive_caps(subject)
        if caps_score > 0:
            score += caps_score * weights['excessive_caps']
            indicators.append(f"Excessive capitalization (score: {caps_score:.2f})")

        # 4. Check for suspicious sender
        sender_score = self._check_suspicious_sender(from_email)
        if sender_score > 0:
            score += sender_score * weights['suspicious_sender']
            indicators.append(f"Suspicious sender (score: {sender_score:.2f})")

        # 5. Check for no subject
        if not subject or subject.strip() == '':
            score += weights['no_subject']
            indicators.append("No subject line")

        # 6. Check for excessive exclamation marks
        exclaim_score = self._check_excessive_exclamation(full_text)
        if exclaim_score > 0:
            score += exclaim_score * weights['excessive_exclamation']
            indicators.append(f"Excessive exclamation marks (score: {exclaim_score:.2f})")

        # 7. Check for suspicious attachments
        attachments = parsed.get('attachments', [])
        if attachments:
            attach_score = self._check_suspicious_attachments(attachments)
            if attach_score > 0:
                score += attach_score * weights['suspicious_attachments']
                indicators.append(f"Suspicious attachments (score: {attach_score:.2f})")

        # 8. Check for too many links
        if body_html or body_text:
            urls = EmailParser.extract_urls(body_html or body_text)
            if len(urls) > 10:
                link_ratio = min(len(urls) / 20, 1.0)
                score += link_ratio * weights['too_many_links']
                indicators.append(f"Too many links ({len(urls)} links)")

        # Normalize score to 0-1 range
        score = min(score, 1.0)

        # Determine if spam
        is_spam = score >= self.threshold

        result = {
            'is_spam': is_spam,
            'spam_score': score,
            'threshold': self.threshold,
            'confidence': abs(score - self.threshold)
        }

        if detailed:
            result['indicators'] = indicators
            result['analysis'] = {
                'subject': subject,
                'from_email': from_email,
                'link_count': len(EmailParser.extract_urls(body_html or body_text)),
                'attachment_count': len(attachments),
                'text_length': len(full_text)
            }

        logger.info(
            f"Spam analysis: score={score:.2f}, is_spam={is_spam}, "
            f"indicators={len(indicators)}"
        )

        return result

    def _check_spam_keywords(self, text: str) -> float:
        """Check for spam keywords in text.

        Args:
            text: Text to analyze

        Returns:
            Score from 0.0 to 1.0
        """
        if not text:
            return 0.0

        matches = 0
        for pattern in self.keyword_patterns:
            if pattern.search(text):
                matches += 1

        # Calculate score based on matches
        score = min(matches / 5, 1.0)  # Cap at 5 keyword matches
        return score

    def _check_suspicious_links(self, text: str) -> float:
        """Check for suspicious links.

        Args:
            text: Text to analyze

        Returns:
            Score from 0.0 to 1.0
        """
        urls = EmailParser.extract_urls(text)

        if not urls:
            return 0.0

        suspicious_patterns = [
            r'bit\.ly',
            r'tinyurl',
            r'goo\.gl',
            r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}',  # IP addresses
            r'\.tk$',
            r'\.ml$',
            r'\.ga$',
            r'\.cf$',
            r'\.gq$',  # Free TLDs
        ]

        suspicious_count = 0
        for url in urls:
            for pattern in suspicious_patterns:
                if re.search(pattern, url, re.IGNORECASE):
                    suspicious_count += 1
                    break

        score = min(suspicious_count / len(urls), 1.0)
        return score

    def _check_excessive_caps(self, text: str) -> float:
        """Check for excessive capitalization.

        Args:
            text: Text to analyze

        Returns:
            Score from 0.0 to 1.0
        """
        if not text or len(text) < 10:
            return 0.0

        # Count capital letters
        caps_count = sum(1 for c in text if c.isupper())
        total_letters = sum(1 for c in text if c.isalpha())

        if total_letters == 0:
            return 0.0

        caps_ratio = caps_count / total_letters

        # Excessive if more than 50% caps
        if caps_ratio > 0.5:
            return min((caps_ratio - 0.5) * 2, 1.0)

        return 0.0

    def _check_suspicious_sender(self, email_address: str) -> float:
        """Check for suspicious sender.

        Args:
            email_address: Email address to check

        Returns:
            Score from 0.0 to 1.0
        """
        if not email_address:
            return 0.5  # No sender is suspicious

        suspicious_indicators = 0

        # Check for numeric username
        username = email_address.split('@')[0]
        if re.match(r'^\d+$', username):
            suspicious_indicators += 1

        # Check for random-looking username
        if len(username) > 15 and re.match(r'^[a-z0-9]{15,}$', username):
            suspicious_indicators += 1

        # Check for suspicious domain patterns
        domain_patterns = [
            r'\.tk$',
            r'\.ml$',
            r'\.ga$',
            r'\.cf$',
            r'\.gq$',
            r'noreply',
            r'donotreply'
        ]

        for pattern in domain_patterns:
            if re.search(pattern, email_address, re.IGNORECASE):
                suspicious_indicators += 1
                break

        score = min(suspicious_indicators / 3, 1.0)
        return score

    def _check_excessive_exclamation(self, text: str) -> float:
        """Check for excessive exclamation marks.

        Args:
            text: Text to analyze

        Returns:
            Score from 0.0 to 1.0
        """
        if not text:
            return 0.0

        exclaim_count = text.count('!')

        if exclaim_count > 3:
            return min(exclaim_count / 10, 1.0)

        return 0.0

    def _check_suspicious_attachments(self, attachments: List[Dict[str, Any]]) -> float:
        """Check for suspicious attachments.

        Args:
            attachments: List of attachment info dicts

        Returns:
            Score from 0.0 to 1.0
        """
        if not attachments:
            return 0.0

        suspicious_extensions = [
            '.exe', '.scr', '.bat', '.cmd', '.com', '.pif',
            '.vbs', '.js', '.jar', '.zip', '.rar'
        ]

        suspicious_count = 0
        for attachment in attachments:
            filename = attachment.get('filename', '').lower()
            for ext in suspicious_extensions:
                if filename.endswith(ext):
                    suspicious_count += 1
                    break

        score = min(suspicious_count / len(attachments), 1.0)
        return score

    def is_spam(self, msg: Message) -> bool:
        """Check if email is spam.

        Args:
            msg: Email message object

        Returns:
            True if spam
        """
        result = self.analyze_email(msg)
        return result['is_spam']

    def get_spam_score(self, msg: Message) -> float:
        """Get spam score for email.

        Args:
            msg: Email message object

        Returns:
            Spam score (0.0 to 1.0)
        """
        result = self.analyze_email(msg)
        return result['spam_score']

    def train(self, spam_emails: List[Message], ham_emails: List[Message]):
        """Train spam filter with examples.

        Note: This is a placeholder for future ML-based filtering.

        Args:
            spam_emails: List of known spam emails
            ham_emails: List of known legitimate emails
        """
        logger.info(
            f"Training spam filter with {len(spam_emails)} spam "
            f"and {len(ham_emails)} ham emails"
        )

        # Extract keywords from spam emails
        spam_keywords = set()
        for msg in spam_emails:
            parsed = EmailParser.parse_message(msg)
            text = f"{parsed.get('subject', '')} {parsed.get('body_text', '')}"

            # Extract common words (simplified)
            words = re.findall(r'\b\w+\b', text.lower())
            for word in words:
                if len(word) > 3:  # Ignore short words
                    spam_keywords.add(word)

        # Filter out common words found in ham
        for msg in ham_emails:
            parsed = EmailParser.parse_message(msg)
            text = f"{parsed.get('subject', '')} {parsed.get('body_text', '')}"
            words = set(re.findall(r'\b\w+\b', text.lower()))
            spam_keywords -= words

        # Update spam keywords (keep top 100)
        self.spam_keywords = list(spam_keywords)[:100]
        self.keyword_patterns = [
            re.compile(r'\b' + re.escape(kw) + r'\b', re.IGNORECASE)
            for kw in self.spam_keywords
        ]

        logger.info(f"Updated spam filter with {len(self.spam_keywords)} keywords")

    def whitelist_sender(self, email_address: str):
        """Add sender to whitelist.

        Note: This is a placeholder for future whitelisting functionality.

        Args:
            email_address: Email address to whitelist
        """
        logger.info(f"Whitelisted sender: {email_address}")

    def blacklist_sender(self, email_address: str):
        """Add sender to blacklist.

        Note: This is a placeholder for future blacklisting functionality.

        Args:
            email_address: Email address to blacklist
        """
        logger.info(f"Blacklisted sender: {email_address}")
