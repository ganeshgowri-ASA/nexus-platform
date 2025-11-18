"""
User Model

Defines user accounts and authentication data.
"""

import enum
from sqlalchemy import Column, String, Boolean, Enum, JSON
from sqlalchemy.orm import relationship
from nexus.models.base import BaseModel, SoftDeleteMixin


class UserRole(str, enum.Enum):
    """User roles for authorization."""

    ADMIN = "admin"
    USER = "user"
    TRANSLATOR = "translator"
    REVIEWER = "reviewer"
    GUEST = "guest"


class User(BaseModel, SoftDeleteMixin):
    """
    User model for authentication and authorization.

    Attributes:
        email: User email (unique)
        username: User username (unique)
        hashed_password: Bcrypt hashed password
        full_name: User's full name
        role: User role for authorization
        is_active: Whether user account is active
        is_verified: Whether email is verified
        api_key: API key for programmatic access
        preferences: JSON field for user preferences
        translations: Relationship to translations
    """

    __tablename__ = "users"

    email = Column(String(255), unique=True, index=True, nullable=False)
    username = Column(String(100), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=True)
    role = Column(Enum(UserRole), default=UserRole.USER, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    is_verified = Column(Boolean, default=False, nullable=False)
    api_key = Column(String(255), unique=True, nullable=True, index=True)
    preferences = Column(JSON, default=dict, nullable=False)

    # Relationships
    translations = relationship(
        "Translation",
        back_populates="user",
        cascade="all, delete-orphan",
    )
    glossaries = relationship(
        "Glossary",
        back_populates="user",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        """String representation."""
        return f"<User(id={self.id}, email={self.email}, role={self.role})>"

    def has_permission(self, permission: str) -> bool:
        """
        Check if user has a specific permission.

        Args:
            permission: Permission to check

        Returns:
            True if user has permission
        """
        role_permissions = {
            UserRole.ADMIN: ["*"],
            UserRole.TRANSLATOR: [
                "translate",
                "view_translations",
                "edit_glossary",
            ],
            UserRole.REVIEWER: [
                "translate",
                "view_translations",
                "review_translations",
            ],
            UserRole.USER: ["translate", "view_translations"],
            UserRole.GUEST: ["translate"],
        }

        permissions = role_permissions.get(self.role, [])
        return "*" in permissions or permission in permissions
