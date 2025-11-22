"""
Utility functions for NEXUS Platform.

This module provides common utility functions used throughout the application.
"""
import hashlib
import secrets
import re
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from uuid import UUID

from jose import jwt
from passlib.context import CryptContext

from config.settings import settings
from config.logging_config import get_logger

logger = get_logger(__name__)

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def generate_uuid() -> str:
    """
    Generate a random UUID string.

    Returns:
        UUID string
    """
    from uuid import uuid4
    return str(uuid4())


def hash_password(password: str) -> str:
    """
    Hash a password using bcrypt.

    Args:
        password: Plain text password

    Returns:
        Hashed password
    """
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a password against its hash.

    Args:
        plain_password: Plain text password
        hashed_password: Hashed password

    Returns:
        True if password matches, False otherwise
    """
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """
    Create a JWT access token.

    Args:
        data: Data to encode in token
        expires_delta: Token expiration time

    Returns:
        Encoded JWT token
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.access_token_expire_minutes)

    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.secret_key, algorithm=settings.jwt_algorithm)
    return encoded_jwt


def decode_token(token: str) -> Dict[str, Any]:
    """
    Decode a JWT token.

    Args:
        token: JWT token

    Returns:
        Decoded token data

    Raises:
        ValueError: If token is invalid or expired
    """
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.jwt_algorithm])
        return payload
    except jwt.JWTError as e:
        logger.error("Failed to decode token", error=str(e))
        raise ValueError("Invalid token")


def validate_email(email: str) -> bool:
    """
    Validate email format.

    Args:
        email: Email address

    Returns:
        True if valid, False otherwise
    """
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None


def validate_phone(phone: str) -> bool:
    """
    Validate phone number format.

    Args:
        phone: Phone number

    Returns:
        True if valid, False otherwise
    """
    # Simple validation - can be made more sophisticated
    pattern = r'^\+?1?\d{9,15}$'
    return re.match(pattern, phone.replace(" ", "").replace("-", "")) is not None


def generate_random_token(length: int = 32) -> str:
    """
    Generate a random token for various purposes.

    Args:
        length: Token length

    Returns:
        Random token string
    """
    return secrets.token_urlsafe(length)


def calculate_percentage(part: float, total: float) -> float:
    """
    Calculate percentage.

    Args:
        part: Part value
        total: Total value

    Returns:
        Percentage (0-100)
    """
    if total == 0:
        return 0.0
    return round((part / total) * 100, 2)


def paginate_query(
    query: Any,
    page: int = 1,
    page_size: int = 20,
) -> Dict[str, Any]:
    """
    Paginate a SQLAlchemy query.

    Args:
        query: SQLAlchemy query
        page: Page number (1-indexed)
        page_size: Number of items per page

    Returns:
        Dictionary with items, total, page, and page_size
    """
    total = query.count()
    items = query.offset((page - 1) * page_size).limit(page_size).all()

    return {
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": (total + page_size - 1) // page_size,
    }


def sanitize_html(html: str) -> str:
    """
    Sanitize HTML content (basic implementation).

    Args:
        html: HTML content

    Returns:
        Sanitized HTML

    Note:
        In production, use a library like bleach for comprehensive sanitization
    """
    # Basic sanitization - remove script tags
    html = re.sub(r'<script[^>]*>.*?</script>', '', html, flags=re.DOTALL)
    return html


def generate_unsubscribe_token(contact_id: str, campaign_id: str) -> str:
    """
    Generate an unsubscribe token.

    Args:
        contact_id: Contact ID
        campaign_id: Campaign ID

    Returns:
        Unsubscribe token
    """
    data = f"{contact_id}:{campaign_id}:{settings.secret_key}"
    return hashlib.sha256(data.encode()).hexdigest()


def verify_unsubscribe_token(
    token: str,
    contact_id: str,
    campaign_id: str,
) -> bool:
    """
    Verify an unsubscribe token.

    Args:
        token: Unsubscribe token
        contact_id: Contact ID
        campaign_id: Campaign ID

    Returns:
        True if valid, False otherwise
    """
    expected_token = generate_unsubscribe_token(contact_id, campaign_id)
    return secrets.compare_digest(token, expected_token)


def format_datetime(dt: datetime, format_str: str = "%Y-%m-%d %H:%M:%S") -> str:
    """
    Format datetime to string.

    Args:
        dt: Datetime object
        format_str: Format string

    Returns:
        Formatted datetime string
    """
    return dt.strftime(format_str)


def parse_template_variables(template: str) -> List[str]:
    """
    Parse template variables from template string.

    Args:
        template: Template string with {{variable}} syntax

    Returns:
        List of variable names

    Example:
        >>> parse_template_variables("Hello {{name}}, your score is {{score}}")
        ['name', 'score']
    """
    pattern = r'\{\{(\w+)\}\}'
    return re.findall(pattern, template)


def replace_template_variables(template: str, variables: Dict[str, Any]) -> str:
    """
    Replace template variables with values.

    Args:
        template: Template string with {{variable}} syntax
        variables: Dictionary of variable values

    Returns:
        String with variables replaced

    Example:
        >>> replace_template_variables(
        ...     "Hello {{name}}, your score is {{score}}",
        ...     {"name": "John", "score": 95}
        ... )
        'Hello John, your score is 95'
    """
    result = template
    for key, value in variables.items():
        result = result.replace(f"{{{{{key}}}}}", str(value))
    return result


def calculate_lead_score(interactions: List[Dict[str, Any]]) -> int:
    """
    Calculate lead score based on interactions.

    Args:
        interactions: List of interaction events

    Returns:
        Lead score (0-1000)
    """
    from config.constants import LEAD_SCORING_POINTS, LeadScoringAttribute

    score = 0
    for interaction in interactions:
        interaction_type = interaction.get("type")
        if interaction_type in LeadScoringAttribute.__members__.values():
            score += LEAD_SCORING_POINTS.get(
                LeadScoringAttribute(interaction_type),
                0
            )

    return min(score, 1000)  # Cap at 1000


def chunk_list(lst: List[Any], chunk_size: int) -> List[List[Any]]:
    """
    Split a list into chunks.

    Args:
        lst: List to chunk
        chunk_size: Size of each chunk

    Returns:
        List of chunks

    Example:
        >>> chunk_list([1, 2, 3, 4, 5], 2)
        [[1, 2], [3, 4], [5]]
    """
    return [lst[i:i + chunk_size] for i in range(0, len(lst), chunk_size)]


def is_valid_uuid(value: str) -> bool:
    """
    Check if a string is a valid UUID.

    Args:
        value: String to check

    Returns:
        True if valid UUID, False otherwise
    """
    try:
        UUID(value)
        return True
    except (ValueError, AttributeError):
        return False
