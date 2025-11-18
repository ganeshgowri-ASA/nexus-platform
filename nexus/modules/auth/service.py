"""
Authentication Service

Provides user authentication and management functionality.
"""

from typing import Optional
from sqlalchemy.orm import Session
from nexus.models.user import User, UserRole
from nexus.core.security import (
    get_password_hash,
    verify_password,
    create_access_token,
    create_refresh_token,
    generate_api_key,
)
from nexus.core.exceptions import AuthenticationError, ValidationError
from config.logging import get_logger

logger = get_logger(__name__)


class AuthService:
    """Service for user authentication and management."""

    def __init__(self, db: Session):
        """
        Initialize auth service.

        Args:
            db: Database session
        """
        self.db = db

    def register_user(
        self,
        email: str,
        username: str,
        password: str,
        full_name: Optional[str] = None,
        role: UserRole = UserRole.USER,
    ) -> User:
        """
        Register a new user.

        Args:
            email: User email
            username: Username
            password: Plain text password
            full_name: Full name
            role: User role

        Returns:
            Created user

        Raises:
            ValidationError: If user already exists
        """
        # Check if user exists
        existing_user = (
            self.db.query(User)
            .filter((User.email == email) | (User.username == username))
            .first()
        )

        if existing_user:
            raise ValidationError("User with this email or username already exists")

        # Create user
        user = User(
            email=email,
            username=username,
            hashed_password=get_password_hash(password),
            full_name=full_name,
            role=role,
            api_key=generate_api_key(),
        )

        user.save(self.db)
        logger.info(f"User registered: {user.email}")

        return user

    def authenticate_user(self, email: str, password: str) -> User:
        """
        Authenticate user with email and password.

        Args:
            email: User email
            password: Plain text password

        Returns:
            Authenticated user

        Raises:
            AuthenticationError: If authentication fails
        """
        user = self.db.query(User).filter(User.email == email).first()

        if not user:
            logger.warning(f"Authentication failed: user not found ({email})")
            raise AuthenticationError("Invalid email or password")

        if not verify_password(password, user.hashed_password):
            logger.warning(f"Authentication failed: incorrect password ({email})")
            raise AuthenticationError("Invalid email or password")

        if not user.is_active:
            logger.warning(f"Authentication failed: inactive user ({email})")
            raise AuthenticationError("User account is inactive")

        logger.info(f"User authenticated: {user.email}")
        return user

    def create_tokens(self, user: User) -> dict:
        """
        Create access and refresh tokens for user.

        Args:
            user: User instance

        Returns:
            Dict with access_token and refresh_token
        """
        access_token = create_access_token(
            data={"sub": user.email, "user_id": user.id, "role": user.role.value}
        )
        refresh_token = create_refresh_token(
            data={"sub": user.email, "user_id": user.id}
        )

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
        }

    def get_user_by_id(self, user_id: int) -> Optional[User]:
        """
        Get user by ID.

        Args:
            user_id: User ID

        Returns:
            User instance or None
        """
        return self.db.query(User).filter(User.id == user_id).first()

    def get_user_by_email(self, email: str) -> Optional[User]:
        """
        Get user by email.

        Args:
            email: User email

        Returns:
            User instance or None
        """
        return self.db.query(User).filter(User.email == email).first()

    def get_user_by_api_key(self, api_key: str) -> Optional[User]:
        """
        Get user by API key.

        Args:
            api_key: API key

        Returns:
            User instance or None
        """
        return self.db.query(User).filter(User.api_key == api_key).first()

    def update_user(self, user_id: int, **kwargs) -> User:
        """
        Update user information.

        Args:
            user_id: User ID
            **kwargs: Fields to update

        Returns:
            Updated user

        Raises:
            ValidationError: If user not found
        """
        user = self.get_user_by_id(user_id)

        if not user:
            raise ValidationError("User not found")

        # Handle password update separately
        if "password" in kwargs:
            kwargs["hashed_password"] = get_password_hash(kwargs.pop("password"))

        user.update(self.db, **kwargs)
        logger.info(f"User updated: {user.email}")

        return user

    def delete_user(self, user_id: int) -> None:
        """
        Soft delete a user.

        Args:
            user_id: User ID

        Raises:
            ValidationError: If user not found
        """
        user = self.get_user_by_id(user_id)

        if not user:
            raise ValidationError("User not found")

        user.soft_delete(self.db)
        logger.info(f"User deleted: {user.email}")
