"""Authentication service."""
from typing import Optional
import jwt
import datetime
from sqlalchemy.orm import Session
from config.settings import settings
from .models import User


class AuthService:
    """Service for authentication and authorization."""

    @classmethod
    def register_user(cls, db: Session, email: str, password: str,
                     full_name: Optional[str] = None) -> User:
        """
        Register a new user.

        Args:
            db: Database session
            email: User email
            password: Plain text password
            full_name: Optional full name

        Returns:
            User: Created user

        Raises:
            ValueError: If email already exists
        """
        # Check if email already exists
        existing_user = db.query(User).filter_by(email=email).first()
        if existing_user:
            raise ValueError(f"User with email {email} already exists")

        # Create new user
        user = User(email=email, full_name=full_name)
        user.set_password(password)

        db.add(user)
        db.commit()
        db.refresh(user)

        return user

    @classmethod
    def authenticate(cls, db: Session, email: str, password: str) -> Optional[User]:
        """
        Authenticate user with email and password.

        Args:
            db: Database session
            email: User email
            password: Plain text password

        Returns:
            User if authentication successful, None otherwise
        """
        user = db.query(User).filter_by(email=email, is_active=True).first()
        if user and user.check_password(password):
            user.update_last_login()
            db.commit()
            return user
        return None

    @classmethod
    def create_token(cls, user_id: int) -> str:
        """
        Create JWT token for user.

        Args:
            user_id: User ID

        Returns:
            str: JWT token
        """
        payload = {
            'user_id': user_id,
            'exp': datetime.datetime.utcnow() + datetime.timedelta(days=settings.JWT_EXPIRATION_DAYS),
            'iat': datetime.datetime.utcnow()
        }
        return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)

    @classmethod
    def verify_token(cls, token: str) -> Optional[int]:
        """
        Verify JWT token and return user_id.

        Args:
            token: JWT token

        Returns:
            int: User ID if token valid, None otherwise
        """
        try:
            payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
            return payload.get('user_id')
        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None

    @classmethod
    def get_user_by_id(cls, db: Session, user_id: int) -> Optional[User]:
        """
        Get user by ID.

        Args:
            db: Database session
            user_id: User ID

        Returns:
            User if found, None otherwise
        """
        return db.query(User).filter_by(id=user_id, is_active=True).first()

    @classmethod
    def update_user(cls, db: Session, user_id: int, **kwargs) -> Optional[User]:
        """
        Update user information.

        Args:
            db: Database session
            user_id: User ID
            **kwargs: Fields to update

        Returns:
            Updated user if found, None otherwise
        """
        user = db.query(User).filter_by(id=user_id).first()
        if not user:
            return None

        # Update allowed fields
        allowed_fields = ['full_name', 'bio', 'avatar_url']
        for field, value in kwargs.items():
            if field in allowed_fields:
                setattr(user, field, value)

        db.commit()
        db.refresh(user)
        return user

    @classmethod
    def change_password(cls, db: Session, user_id: int, old_password: str,
                       new_password: str) -> bool:
        """
        Change user password.

        Args:
            db: Database session
            user_id: User ID
            old_password: Current password
            new_password: New password

        Returns:
            bool: True if password changed successfully
        """
        user = db.query(User).filter_by(id=user_id).first()
        if not user or not user.check_password(old_password):
            return False

        user.set_password(new_password)
        db.commit()
        return True
