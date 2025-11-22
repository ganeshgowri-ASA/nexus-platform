"""
Password utilities for hashing, verification, and validation.
"""
import re
from typing import Tuple
import bcrypt


class PasswordStrength:
    """Password strength enumeration."""
    WEAK = "weak"
    MEDIUM = "medium"
    STRONG = "strong"
    VERY_STRONG = "very_strong"


def hash_password(password: str) -> str:
    """
    Hash a password using bcrypt.

    Args:
        password: Plain text password

    Returns:
        str: Hashed password

    Raises:
        ValueError: If password is empty
    """
    if not password:
        raise ValueError("Password cannot be empty")

    # Generate salt and hash password
    salt = bcrypt.gensalt(rounds=12)
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a password against its hash.

    Args:
        plain_password: Plain text password to verify
        hashed_password: Hashed password to compare against

    Returns:
        bool: True if password matches, False otherwise
    """
    if not plain_password or not hashed_password:
        return False

    try:
        return bcrypt.checkpw(
            plain_password.encode('utf-8'),
            hashed_password.encode('utf-8')
        )
    except Exception:
        return False


def validate_password(password: str) -> Tuple[bool, str]:
    """
    Validate password against security requirements.

    Requirements:
    - Minimum 8 characters
    - At least one uppercase letter
    - At least one lowercase letter
    - At least one digit
    - At least one special character

    Args:
        password: Password to validate

    Returns:
        Tuple[bool, str]: (is_valid, error_message)
    """
    if not password:
        return False, "Password cannot be empty"

    if len(password) < 8:
        return False, "Password must be at least 8 characters long"

    if len(password) > 128:
        return False, "Password must not exceed 128 characters"

    if not re.search(r'[A-Z]', password):
        return False, "Password must contain at least one uppercase letter"

    if not re.search(r'[a-z]', password):
        return False, "Password must contain at least one lowercase letter"

    if not re.search(r'\d', password):
        return False, "Password must contain at least one digit"

    if not re.search(r'[!@#$%^&*(),.?":{}|<>_\-+=\[\]\\\/;~`]', password):
        return False, "Password must contain at least one special character"

    # Check for common patterns
    common_passwords = [
        'password', '12345678', 'qwerty', 'abc123',
        'password123', 'admin123', 'letmein'
    ]
    if password.lower() in common_passwords:
        return False, "Password is too common. Please choose a stronger password"

    return True, ""


def check_password_strength(password: str) -> Tuple[str, int]:
    """
    Check password strength and return a score.

    Args:
        password: Password to check

    Returns:
        Tuple[str, int]: (strength_level, score_out_of_100)
    """
    score = 0
    feedback = []

    if not password:
        return PasswordStrength.WEAK, 0

    # Length check (max 40 points)
    length = len(password)
    if length >= 8:
        score += min(length * 2, 40)

    # Character variety checks (15 points each)
    if re.search(r'[a-z]', password):
        score += 15
    else:
        feedback.append("Add lowercase letters")

    if re.search(r'[A-Z]', password):
        score += 15
    else:
        feedback.append("Add uppercase letters")

    if re.search(r'\d', password):
        score += 15
    else:
        feedback.append("Add numbers")

    if re.search(r'[!@#$%^&*(),.?":{}|<>_\-+=\[\]\\\/;~`]', password):
        score += 15
    else:
        feedback.append("Add special characters")

    # Penalty for common patterns
    if re.search(r'(.)\1{2,}', password):  # Repeated characters
        score -= 10

    if re.search(r'(012|123|234|345|456|567|678|789|890)', password):  # Sequential numbers
        score -= 10

    if re.search(r'(abc|bcd|cde|def|efg|fgh|ghi|hij|ijk|jkl|klm|lmn|mno|nop|opq|pqr|qrs|rst|stu|tuv|uvw|vwx|wxy|xyz)', password.lower()):
        score -= 10  # Sequential letters

    # Ensure score is between 0 and 100
    score = max(0, min(100, score))

    # Determine strength level
    if score < 40:
        strength = PasswordStrength.WEAK
    elif score < 60:
        strength = PasswordStrength.MEDIUM
    elif score < 80:
        strength = PasswordStrength.STRONG
    else:
        strength = PasswordStrength.VERY_STRONG

    return strength, score


def generate_password_requirements_text() -> str:
    """
    Generate human-readable password requirements text.

    Returns:
        str: Password requirements description
    """
    return """
Password Requirements:
• Minimum 8 characters (recommended 12+)
• At least one uppercase letter (A-Z)
• At least one lowercase letter (a-z)
• At least one digit (0-9)
• At least one special character (!@#$%^&*(),.?":{}|<>_-+=[]\\\/;~`)
• Avoid common passwords and patterns
    """.strip()


def validate_passwords_match(password: str, confirm_password: str) -> Tuple[bool, str]:
    """
    Validate that password and confirmation password match.

    Args:
        password: Password
        confirm_password: Confirmation password

    Returns:
        Tuple[bool, str]: (is_valid, error_message)
    """
    if not password or not confirm_password:
        return False, "Both password fields are required"

    if password != confirm_password:
        return False, "Passwords do not match"

    return True, ""
