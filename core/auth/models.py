"""Authentication models."""
from sqlalchemy import Column, String, Integer, DateTime, Boolean, Text
from sqlalchemy.orm import relationship
from core.database.base import Base
from passlib.hash import bcrypt
import datetime
from typing import Optional


class User(Base):
    """User model for authentication and authorization."""

    __tablename__ = 'users'

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=True)
    avatar_url = Column(String(500), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    is_admin = Column(Boolean, default=False, nullable=False)
    bio = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
    last_login = Column(DateTime, nullable=True)

    # Relationships
    spreadsheets = relationship("Spreadsheet", back_populates="user", cascade="all, delete-orphan")
    shared_spreadsheets = relationship("SpreadsheetShare", back_populates="user", cascade="all, delete-orphan")

    def set_password(self, password: str) -> None:
        """
        Hash and set user password.

        Args:
            password: Plain text password
        """
        self.password_hash = bcrypt.hash(password)

    def check_password(self, password: str) -> bool:
        """
        Verify password against stored hash.

        Args:
            password: Plain text password to verify

        Returns:
            bool: True if password matches, False otherwise
        """
        return bcrypt.verify(password, self.password_hash)

    def update_last_login(self) -> None:
        """Update last login timestamp."""
        self.last_login = datetime.datetime.utcnow()

    def to_dict(self) -> dict:
        """
        Convert user to dictionary.

        Returns:
            dict: User data (excluding password)
        """
        return {
            'id': self.id,
            'email': self.email,
            'full_name': self.full_name,
            'avatar_url': self.avatar_url,
            'is_active': self.is_active,
            'is_admin': self.is_admin,
            'bio': self.bio,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'last_login': self.last_login.isoformat() if self.last_login else None
        }

    def __repr__(self) -> str:
        """String representation of User."""
        return f"<User(id={self.id}, email='{self.email}', full_name='{self.full_name}')>"
