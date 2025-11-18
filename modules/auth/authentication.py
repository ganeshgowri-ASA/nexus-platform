"""
Authentication module for user login, registration, and logout.
"""
import secrets
import re
from datetime import datetime, timedelta
from typing import Optional, Tuple, Dict, Any
from sqlalchemy.orm import Session
from jose import JWTError, jwt

from modules.database.models import User, Role, LoginHistory, UserSession
from modules.auth.password_utils import (
    hash_password,
    verify_password,
    validate_password,
    validate_passwords_match
)


# JWT Configuration
SECRET_KEY = secrets.token_urlsafe(32)  # Should be in environment variables in production
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60  # 1 hour
REFRESH_TOKEN_EXPIRE_DAYS = 30  # 30 days
MAX_FAILED_ATTEMPTS = 5
LOCKOUT_DURATION_MINUTES = 30


class AuthenticationError(Exception):
    """Base exception for authentication errors."""
    pass


class InvalidCredentialsError(AuthenticationError):
    """Raised when credentials are invalid."""
    pass


class AccountLockedError(AuthenticationError):
    """Raised when account is locked."""
    pass


class AccountNotVerifiedError(AuthenticationError):
    """Raised when account is not verified."""
    pass


class UserAlreadyExistsError(AuthenticationError):
    """Raised when user already exists."""
    pass


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Create JWT access token.

    Args:
        data: Data to encode in token
        expires_delta: Token expiration time

    Returns:
        str: Encoded JWT token
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({"exp": expire, "type": "access"})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def create_refresh_token(data: dict) -> str:
    """
    Create JWT refresh token.

    Args:
        data: Data to encode in token

    Returns:
        str: Encoded JWT refresh token
    """
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire, "type": "refresh"})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def verify_token(token: str) -> Optional[Dict[str, Any]]:
    """
    Verify and decode JWT token.

    Args:
        token: JWT token to verify

    Returns:
        Optional[Dict]: Decoded token data or None if invalid
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None


def validate_email(email: str) -> bool:
    """
    Validate email format.

    Args:
        email: Email address to validate

    Returns:
        bool: True if valid, False otherwise
    """
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))


def validate_username(username: str) -> Tuple[bool, str]:
    """
    Validate username format.

    Args:
        username: Username to validate

    Returns:
        Tuple[bool, str]: (is_valid, error_message)
    """
    if not username:
        return False, "Username cannot be empty"

    if len(username) < 3:
        return False, "Username must be at least 3 characters"

    if len(username) > 50:
        return False, "Username must not exceed 50 characters"

    if not re.match(r'^[a-zA-Z0-9_-]+$', username):
        return False, "Username can only contain letters, numbers, underscores, and hyphens"

    return True, ""


def register_user(
    db: Session,
    email: str,
    username: str,
    full_name: str,
    password: str,
    confirm_password: str,
    default_role: str = "user"
) -> Tuple[User, str]:
    """
    Register a new user.

    Args:
        db: Database session
        email: User email
        username: Username
        full_name: Full name
        password: Password
        confirm_password: Password confirmation
        default_role: Default role to assign (default: "user")

    Returns:
        Tuple[User, str]: (created_user, verification_token)

    Raises:
        UserAlreadyExistsError: If user already exists
        ValueError: If validation fails
    """
    # Validate email
    if not validate_email(email):
        raise ValueError("Invalid email format")

    # Validate username
    is_valid, error = validate_username(username)
    if not is_valid:
        raise ValueError(error)

    # Validate password
    is_valid, error = validate_password(password)
    if not is_valid:
        raise ValueError(error)

    # Validate passwords match
    is_valid, error = validate_passwords_match(password, confirm_password)
    if not is_valid:
        raise ValueError(error)

    # Check if user already exists
    existing_user = db.query(User).filter(
        (User.email == email) | (User.username == username)
    ).first()

    if existing_user:
        if existing_user.email == email:
            raise UserAlreadyExistsError("Email already registered")
        else:
            raise UserAlreadyExistsError("Username already taken")

    # Hash password
    hashed_password = hash_password(password)

    # Generate verification token
    verification_token = secrets.token_urlsafe(32)
    verification_expires = datetime.utcnow() + timedelta(hours=24)

    # Create user
    user = User(
        email=email,
        username=username,
        full_name=full_name,
        hashed_password=hashed_password,
        verification_token=verification_token,
        verification_token_expires=verification_expires,
        is_verified=False,  # Require email verification
        is_active=True,
        created_at=datetime.utcnow()
    )

    # Assign default role
    role = db.query(Role).filter(Role.name == default_role).first()
    if role:
        user.roles.append(role)

    db.add(user)
    db.commit()
    db.refresh(user)

    return user, verification_token


def login_user(
    db: Session,
    email_or_username: str,
    password: str,
    remember_me: bool = False,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None
) -> Tuple[User, str, str]:
    """
    Authenticate user and create session.

    Args:
        db: Database session
        email_or_username: Email or username
        password: Password
        remember_me: Remember me flag
        ip_address: Client IP address
        user_agent: Client user agent

    Returns:
        Tuple[User, str, str]: (user, access_token, refresh_token)

    Raises:
        InvalidCredentialsError: If credentials are invalid
        AccountLockedError: If account is locked
        AccountNotVerifiedError: If account is not verified
    """
    # Find user by email or username
    user = db.query(User).filter(
        (User.email == email_or_username) | (User.username == email_or_username)
    ).first()

    # Track login attempt
    login_success = False
    failure_reason = None

    try:
        if not user:
            failure_reason = "User not found"
            raise InvalidCredentialsError("Invalid email/username or password")

        # Check if account is locked
        if user.is_locked:
            # Check if lockout duration has passed
            if user.last_failed_login:
                lockout_end = user.last_failed_login + timedelta(minutes=LOCKOUT_DURATION_MINUTES)
                if datetime.utcnow() < lockout_end:
                    failure_reason = "Account locked"
                    raise AccountLockedError(
                        f"Account is locked due to too many failed login attempts. "
                        f"Please try again later."
                    )
                else:
                    # Unlock account
                    user.is_locked = False
                    user.failed_login_attempts = 0

        # Check if account is active
        if not user.is_active:
            failure_reason = "Account inactive"
            raise InvalidCredentialsError("Account is inactive")

        # Verify password
        if not verify_password(password, user.hashed_password):
            # Increment failed attempts
            user.failed_login_attempts += 1
            user.last_failed_login = datetime.utcnow()

            # Lock account if too many failures
            if user.failed_login_attempts >= MAX_FAILED_ATTEMPTS:
                user.is_locked = True
                failure_reason = "Too many failed attempts"
                db.commit()
                raise AccountLockedError(
                    f"Account locked due to {MAX_FAILED_ATTEMPTS} failed login attempts. "
                    f"Please try again in {LOCKOUT_DURATION_MINUTES} minutes."
                )

            failure_reason = "Invalid password"
            db.commit()
            raise InvalidCredentialsError("Invalid email/username or password")

        # Check if email is verified
        if not user.is_verified:
            failure_reason = "Email not verified"
            raise AccountNotVerifiedError(
                "Please verify your email address before logging in. "
                "Check your inbox for the verification link."
            )

        # Successful login - reset failed attempts
        user.failed_login_attempts = 0
        user.last_login = datetime.utcnow()

        # Create access and refresh tokens
        token_data = {
            "sub": str(user.id),
            "email": user.email,
            "username": user.username,
            "roles": [role.name for role in user.roles]
        }

        access_token = create_access_token(token_data)
        refresh_token = create_refresh_token(token_data)

        # Create session
        session_expires = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        if remember_me:
            session_expires = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)

        user_session = UserSession(
            user_id=user.id,
            session_token=access_token,
            refresh_token=refresh_token,
            ip_address=ip_address,
            user_agent=user_agent,
            remember_me=remember_me,
            expires_at=session_expires
        )
        db.add(user_session)

        login_success = True
        db.commit()
        db.refresh(user)

        return user, access_token, refresh_token

    finally:
        # Record login history
        login_history = LoginHistory(
            user_id=user.id if user else None,
            success=login_success,
            ip_address=ip_address,
            user_agent=user_agent,
            failure_reason=failure_reason
        )
        db.add(login_history)
        db.commit()


def logout_user(db: Session, session_token: str) -> bool:
    """
    Logout user by invalidating session.

    Args:
        db: Database session
        session_token: Session token to invalidate

    Returns:
        bool: True if logout successful
    """
    session = db.query(UserSession).filter(
        UserSession.session_token == session_token
    ).first()

    if session:
        db.delete(session)
        db.commit()
        return True

    return False


def verify_email(db: Session, token: str) -> bool:
    """
    Verify user email with verification token.

    Args:
        db: Database session
        token: Verification token

    Returns:
        bool: True if verification successful

    Raises:
        ValueError: If token is invalid or expired
    """
    user = db.query(User).filter(User.verification_token == token).first()

    if not user:
        raise ValueError("Invalid verification token")

    if user.verification_token_expires < datetime.utcnow():
        raise ValueError("Verification token has expired")

    user.is_verified = True
    user.verification_token = None
    user.verification_token_expires = None
    db.commit()

    return True


def request_password_reset(db: Session, email: str) -> str:
    """
    Request password reset and generate reset token.

    Args:
        db: Database session
        email: User email

    Returns:
        str: Reset token

    Raises:
        ValueError: If user not found
    """
    user = db.query(User).filter(User.email == email).first()

    if not user:
        raise ValueError("User not found")

    # Generate reset token
    reset_token = secrets.token_urlsafe(32)
    reset_expires = datetime.utcnow() + timedelta(hours=1)

    user.reset_token = reset_token
    user.reset_token_expires = reset_expires
    db.commit()

    return reset_token


def reset_password(db: Session, token: str, new_password: str, confirm_password: str) -> bool:
    """
    Reset user password with reset token.

    Args:
        db: Database session
        token: Reset token
        new_password: New password
        confirm_password: Password confirmation

    Returns:
        bool: True if reset successful

    Raises:
        ValueError: If token is invalid, expired, or password validation fails
    """
    user = db.query(User).filter(User.reset_token == token).first()

    if not user:
        raise ValueError("Invalid reset token")

    if user.reset_token_expires < datetime.utcnow():
        raise ValueError("Reset token has expired")

    # Validate new password
    is_valid, error = validate_password(new_password)
    if not is_valid:
        raise ValueError(error)

    # Validate passwords match
    is_valid, error = validate_passwords_match(new_password, confirm_password)
    if not is_valid:
        raise ValueError(error)

    # Update password
    user.hashed_password = hash_password(new_password)
    user.reset_token = None
    user.reset_token_expires = None
    user.password_changed_at = datetime.utcnow()

    # Invalidate all existing sessions
    db.query(UserSession).filter(UserSession.user_id == user.id).delete()

    db.commit()

    return True


def change_password(
    db: Session,
    user_id: int,
    current_password: str,
    new_password: str,
    confirm_password: str
) -> bool:
    """
    Change user password (requires current password).

    Args:
        db: Database session
        user_id: User ID
        current_password: Current password
        new_password: New password
        confirm_password: Password confirmation

    Returns:
        bool: True if change successful

    Raises:
        ValueError: If validation fails
        InvalidCredentialsError: If current password is incorrect
    """
    user = db.query(User).filter(User.id == user_id).first()

    if not user:
        raise ValueError("User not found")

    # Verify current password
    if not verify_password(current_password, user.hashed_password):
        raise InvalidCredentialsError("Current password is incorrect")

    # Validate new password
    is_valid, error = validate_password(new_password)
    if not is_valid:
        raise ValueError(error)

    # Validate passwords match
    is_valid, error = validate_passwords_match(new_password, confirm_password)
    if not is_valid:
        raise ValueError(error)

    # Check that new password is different from current
    if verify_password(new_password, user.hashed_password):
        raise ValueError("New password must be different from current password")

    # Update password
    user.hashed_password = hash_password(new_password)
    user.password_changed_at = datetime.utcnow()
    db.commit()

    return True


def get_user_by_token(db: Session, token: str) -> Optional[User]:
    """
    Get user from session token.

    Args:
        db: Database session
        token: Session token

    Returns:
        Optional[User]: User if token is valid, None otherwise
    """
    # Verify token
    payload = verify_token(token)
    if not payload:
        return None

    # Get user from token
    user_id = payload.get("sub")
    if not user_id:
        return None

    user = db.query(User).filter(User.id == int(user_id)).first()
    return user
