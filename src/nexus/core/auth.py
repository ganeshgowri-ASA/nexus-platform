"""
Authentication and authorization manager
"""
import secrets
import hashlib
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
from loguru import logger


class AuthManager:
    """Simple authentication manager for API access"""

    def __init__(self, secret_key: str):
        self.secret_key = secret_key
        self._sessions: Dict[str, Dict[str, Any]] = {}

    def generate_token(self, user_id: str, metadata: Optional[Dict] = None) -> str:
        """Generate authentication token"""
        token = secrets.token_urlsafe(32)
        expires_at = datetime.now() + timedelta(hours=24)

        self._sessions[token] = {
            "user_id": user_id,
            "created_at": datetime.now(),
            "expires_at": expires_at,
            "metadata": metadata or {}
        }

        logger.info(f"Generated token for user: {user_id}")
        return token

    def validate_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Validate authentication token"""
        if token not in self._sessions:
            logger.warning(f"Invalid token: {token[:8]}...")
            return None

        session = self._sessions[token]
        if datetime.now() > session["expires_at"]:
            logger.warning(f"Expired token: {token[:8]}...")
            del self._sessions[token]
            return None

        logger.debug(f"Valid token for user: {session['user_id']}")
        return session

    def revoke_token(self, token: str):
        """Revoke authentication token"""
        if token in self._sessions:
            user_id = self._sessions[token]["user_id"]
            del self._sessions[token]
            logger.info(f"Revoked token for user: {user_id}")

    def hash_password(self, password: str) -> str:
        """Hash password for storage"""
        salt = self.secret_key
        return hashlib.pbkdf2_hmac(
            'sha256',
            password.encode('utf-8'),
            salt.encode('utf-8'),
            100000
        ).hex()

    def verify_password(self, password: str, hashed: str) -> bool:
        """Verify password against hash"""
        return self.hash_password(password) == hashed
