"""
Email Security

Email encryption (PGP/S/MIME), spam detection, and security features.
"""

import base64
import hashlib
import logging
import re
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


@dataclass
class SpamScore:
    """Spam detection result."""
    is_spam: bool
    confidence: float  # 0-1
    score: float  # Raw spam score
    reasons: List[str]


@dataclass
class SecurityCheck:
    """Security check result."""
    is_safe: bool
    issues: List[str]
    warnings: List[str]
    spf_result: Optional[str] = None
    dkim_result: Optional[str] = None
    dmarc_result: Optional[str] = None


class SecurityManager:
    """
    Email security manager.

    Handles encryption, spam detection, phishing protection, and security checks.
    """

    def __init__(
        self,
        spam_threshold: float = 0.7,
        enable_pgp: bool = True,
        enable_smime: bool = True
    ):
        """
        Initialize security manager.

        Args:
            spam_threshold: Spam detection threshold (0-1)
            enable_pgp: Enable PGP encryption
            enable_smime: Enable S/MIME encryption
        """
        self.spam_threshold = spam_threshold
        self.enable_pgp = enable_pgp
        self.enable_smime = enable_smime

        # Spam detection patterns
        self.spam_patterns = self._init_spam_patterns()

    def _init_spam_patterns(self) -> List[str]:
        """Initialize spam detection patterns."""
        return [
            r'viagra|cialis|pharmacy',
            r'click here now|act now|limited time',
            r'million dollars|lottery|prize',
            r'weight loss|lose weight',
            r'make money fast|work from home',
            r'nigerian prince|inheritance',
            r'congratulations! you\'ve won',
        ]

    async def check_message(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """
        Perform security checks on a message.

        Args:
            message: Email message

        Returns:
            Dict: Message with security info added
        """
        # Spam detection
        spam_result = await self.detect_spam(message)
        message['is_spam'] = spam_result.is_spam
        message['spam_score'] = spam_result.score

        # SPF/DKIM checks
        security_check = await self.check_security(message)
        message['spf_result'] = security_check.spf_result
        message['dkim_result'] = security_check.dkim_result

        # Check encryption
        message['is_encrypted'] = self._check_encryption(message)
        message['is_signed'] = self._check_signature(message)

        return message

    async def detect_spam(self, message: Dict[str, Any]) -> SpamScore:
        """
        Detect if message is spam.

        Args:
            message: Email message

        Returns:
            SpamScore: Spam detection result
        """
        score = 0.0
        reasons = []

        subject = message.get('subject', '').lower()
        body = (message.get('body_text', '') + message.get('body_html', '')).lower()
        from_addr = message.get('from_address', '').lower()

        # Check spam patterns
        for pattern in self.spam_patterns:
            if re.search(pattern, subject, re.IGNORECASE):
                score += 0.3
                reasons.append(f"Spam pattern in subject: {pattern[:20]}")

            if re.search(pattern, body, re.IGNORECASE):
                score += 0.2
                reasons.append(f"Spam pattern in body: {pattern[:20]}")

        # Check for ALL CAPS subject
        if subject and subject.isupper() and len(subject) > 10:
            score += 0.2
            reasons.append("ALL CAPS subject")

        # Check for excessive exclamation marks
        if subject.count('!') > 2:
            score += 0.1
            reasons.append("Excessive exclamation marks")

        # Check for suspicious sender
        if not from_addr or '@' not in from_addr:
            score += 0.3
            reasons.append("Invalid sender address")

        # Check for suspicious links
        url_pattern = r'https?://[^\s<>"{}|\\^`\[\]]+'
        urls = re.findall(url_pattern, body)

        if len(urls) > 10:
            score += 0.2
            reasons.append("Too many links")

        # Check for tracking pixels (1x1 images)
        if '1x1' in body or 'width="1"' in body or 'height="1"' in body:
            score += 0.1
            reasons.append("Tracking pixel detected")

        # Normalize score
        score = min(1.0, score)

        is_spam = score >= self.spam_threshold

        return SpamScore(
            is_spam=is_spam,
            confidence=score,
            score=score,
            reasons=reasons
        )

    async def check_security(self, message: Dict[str, Any]) -> SecurityCheck:
        """
        Perform security checks (SPF, DKIM, DMARC).

        Args:
            message: Email message

        Returns:
            SecurityCheck: Security check results
        """
        issues = []
        warnings = []

        # Check SPF (Sender Policy Framework)
        spf_result = await self._check_spf(message)

        # Check DKIM (DomainKeys Identified Mail)
        dkim_result = await self._check_dkim(message)

        # Check DMARC
        dmarc_result = await self._check_dmarc(message)

        # Evaluate results
        if spf_result == "fail":
            issues.append("SPF check failed")

        if dkim_result == "fail":
            issues.append("DKIM verification failed")

        if dmarc_result == "fail":
            warnings.append("DMARC policy violation")

        is_safe = len(issues) == 0

        return SecurityCheck(
            is_safe=is_safe,
            issues=issues,
            warnings=warnings,
            spf_result=spf_result,
            dkim_result=dkim_result,
            dmarc_result=dmarc_result
        )

    async def _check_spf(self, message: Dict[str, Any]) -> str:
        """
        Check SPF (Sender Policy Framework).

        Args:
            message: Email message

        Returns:
            str: 'pass', 'fail', 'neutral', or 'none'
        """
        # Placeholder implementation
        # In production, check SPF records via DNS

        headers = message.get('headers', {})
        spf_header = headers.get('received-spf', '').lower()

        if 'pass' in spf_header:
            return 'pass'
        elif 'fail' in spf_header:
            return 'fail'
        elif 'neutral' in spf_header:
            return 'neutral'

        return 'none'

    async def _check_dkim(self, message: Dict[str, Any]) -> str:
        """
        Check DKIM signature.

        Args:
            message: Email message

        Returns:
            str: 'pass', 'fail', or 'none'
        """
        # Placeholder implementation
        # In production, verify DKIM signature

        headers = message.get('headers', {})

        if 'dkim-signature' in headers:
            # Would verify signature here
            return 'pass'

        return 'none'

    async def _check_dmarc(self, message: Dict[str, Any]) -> str:
        """
        Check DMARC policy.

        Args:
            message: Email message

        Returns:
            str: 'pass', 'fail', or 'none'
        """
        # Placeholder implementation
        # In production, check DMARC policy via DNS

        return 'none'

    def _check_encryption(self, message: Dict[str, Any]) -> bool:
        """Check if message is encrypted."""
        # Check for PGP encryption
        body = message.get('body_text', '')
        if '-----BEGIN PGP MESSAGE-----' in body:
            return True

        # Check for S/MIME
        headers = message.get('headers', {})
        content_type = headers.get('content-type', '')
        if 'application/pkcs7-mime' in content_type:
            return True

        return False

    def _check_signature(self, message: Dict[str, Any]) -> bool:
        """Check if message is digitally signed."""
        # Check for PGP signature
        body = message.get('body_text', '')
        if '-----BEGIN PGP SIGNATURE-----' in body:
            return True

        # Check for S/MIME signature
        headers = message.get('headers', {})
        content_type = headers.get('content-type', '')
        if 'multipart/signed' in content_type:
            return True

        return False

    # PGP Encryption

    async def encrypt_pgp(
        self,
        message: Dict[str, Any],
        recipient_public_key: str
    ) -> Dict[str, Any]:
        """
        Encrypt message with PGP.

        Args:
            message: Email message
            recipient_public_key: Recipient's PGP public key

        Returns:
            Dict: Encrypted message
        """
        if not self.enable_pgp:
            return message

        # Placeholder implementation
        # In production, use python-gnupg or similar

        logger.info("Would encrypt message with PGP")

        # Encrypt body
        encrypted_body = f"""
-----BEGIN PGP MESSAGE-----

[Encrypted content would be here]
-----END PGP MESSAGE-----
"""

        message['body_text'] = encrypted_body
        message['is_encrypted'] = True

        return message

    async def decrypt_pgp(
        self,
        message: Dict[str, Any],
        private_key: str,
        passphrase: str
    ) -> Dict[str, Any]:
        """
        Decrypt PGP message.

        Args:
            message: Encrypted message
            private_key: Private key
            passphrase: Key passphrase

        Returns:
            Dict: Decrypted message
        """
        if not self.enable_pgp:
            return message

        # Placeholder implementation
        # In production, use python-gnupg

        logger.info("Would decrypt PGP message")

        return message

    async def sign_pgp(
        self,
        message: Dict[str, Any],
        private_key: str,
        passphrase: str
    ) -> Dict[str, Any]:
        """
        Sign message with PGP.

        Args:
            message: Email message
            private_key: Private key
            passphrase: Key passphrase

        Returns:
            Dict: Signed message
        """
        if not self.enable_pgp:
            return message

        # Placeholder implementation
        logger.info("Would sign message with PGP")

        signature = """
-----BEGIN PGP SIGNATURE-----

[Signature would be here]
-----END PGP SIGNATURE-----
"""

        message['body_text'] += '\n' + signature
        message['is_signed'] = True

        return message

    async def verify_pgp_signature(
        self,
        message: Dict[str, Any],
        sender_public_key: str
    ) -> bool:
        """
        Verify PGP signature.

        Args:
            message: Signed message
            sender_public_key: Sender's public key

        Returns:
            bool: True if signature is valid
        """
        # Placeholder implementation
        logger.info("Would verify PGP signature")
        return True

    # S/MIME Encryption

    async def encrypt_smime(
        self,
        message: Dict[str, Any],
        recipient_certificate: str
    ) -> Dict[str, Any]:
        """
        Encrypt message with S/MIME.

        Args:
            message: Email message
            recipient_certificate: Recipient's certificate

        Returns:
            Dict: Encrypted message
        """
        if not self.enable_smime:
            return message

        # Placeholder implementation
        # In production, use M2Crypto or similar

        logger.info("Would encrypt message with S/MIME")

        message['is_encrypted'] = True

        return message

    async def decrypt_smime(
        self,
        message: Dict[str, Any],
        private_key: str,
        certificate: str
    ) -> Dict[str, Any]:
        """
        Decrypt S/MIME message.

        Args:
            message: Encrypted message
            private_key: Private key
            certificate: Certificate

        Returns:
            Dict: Decrypted message
        """
        if not self.enable_smime:
            return message

        # Placeholder implementation
        logger.info("Would decrypt S/MIME message")

        return message

    async def sign_and_encrypt(
        self,
        message: Dict[str, Any],
        account: Any
    ) -> Dict[str, Any]:
        """
        Sign and encrypt message if configured.

        Args:
            message: Email message
            account: Email account with encryption settings

        Returns:
            Dict: Processed message
        """
        # Check if account has encryption configured
        # This would check account settings for PGP/S/MIME keys

        # For now, just return message as-is
        return message

    # Virus Scanning

    async def scan_for_virus(self, data: bytes) -> Tuple[bool, Optional[str]]:
        """
        Scan data for viruses.

        Args:
            data: Data to scan

        Returns:
            Tuple[bool, Optional[str]]: (is_safe, threat_name)
        """
        # Placeholder implementation
        # In production, integrate with ClamAV or similar

        # Simple heuristics
        if len(data) < 10:
            return False, "File too small"

        # Check for executable signatures
        if data[:2] == b'MZ':  # DOS/Windows executable
            return False, "Windows executable"

        if data[:4] == b'\x7fELF':  # Linux executable
            return False, "Linux executable"

        # Check for script signatures
        if data[:2] == b'#!':  # Shell script
            return False, "Shell script"

        return True, None

    # Password Protection

    def hash_password(self, password: str) -> str:
        """
        Hash a password securely.

        Args:
            password: Plain password

        Returns:
            str: Hashed password
        """
        # Use SHA-256 with salt
        salt = "nexus_email_salt"  # In production, use random salt per user
        hashed = hashlib.sha256((password + salt).encode()).hexdigest()
        return hashed

    def verify_password(self, password: str, hashed: str) -> bool:
        """
        Verify password against hash.

        Args:
            password: Plain password
            hashed: Hashed password

        Returns:
            bool: True if password matches
        """
        return self.hash_password(password) == hashed

    # Content Filtering

    async def filter_content(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """
        Filter inappropriate or dangerous content.

        Args:
            message: Email message

        Returns:
            Dict: Filtered message
        """
        # Remove scripts from HTML
        html_body = message.get('body_html', '')
        if html_body:
            # Remove script tags
            html_body = re.sub(r'<script[^>]*>.*?</script>', '', html_body, flags=re.DOTALL | re.IGNORECASE)

            # Remove event handlers
            html_body = re.sub(r'on\w+\s*=\s*["\'][^"\']*["\']', '', html_body, flags=re.IGNORECASE)

            message['body_html'] = html_body

        return message

    def sanitize_html(self, html: str) -> str:
        """
        Sanitize HTML to remove dangerous elements.

        Args:
            html: HTML content

        Returns:
            str: Sanitized HTML
        """
        # Remove dangerous tags
        dangerous_tags = ['script', 'object', 'embed', 'iframe', 'frame']

        for tag in dangerous_tags:
            html = re.sub(
                f'<{tag}[^>]*>.*?</{tag}>',
                '',
                html,
                flags=re.DOTALL | re.IGNORECASE
            )

        # Remove event handlers
        html = re.sub(r'on\w+\s*=\s*["\'][^"\']*["\']', '', html, flags=re.IGNORECASE)

        return html

    def generate_report(self, messages: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Generate security report for messages.

        Args:
            messages: List of messages

        Returns:
            Dict: Security report
        """
        total = len(messages)
        spam_count = sum(1 for m in messages if m.get('is_spam', False))
        encrypted_count = sum(1 for m in messages if m.get('is_encrypted', False))
        signed_count = sum(1 for m in messages if m.get('is_signed', False))

        return {
            'total_messages': total,
            'spam_messages': spam_count,
            'spam_percentage': (spam_count / total * 100) if total > 0 else 0,
            'encrypted_messages': encrypted_count,
            'signed_messages': signed_count,
            'secure_percentage': ((encrypted_count + signed_count) / total * 100) if total > 0 else 0
        }
