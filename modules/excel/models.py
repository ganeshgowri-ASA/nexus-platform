"""Database models for Excel module."""
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, JSON, Text, Boolean, Enum
from sqlalchemy.orm import relationship
from core.database.base import Base
import datetime
from typing import Optional
import enum


class PermissionLevel(enum.Enum):
    """Permission levels for spreadsheet sharing."""
    VIEW = "view"
    EDIT = "edit"
    ADMIN = "admin"


class Spreadsheet(Base):
    """Spreadsheet model."""

    __tablename__ = 'spreadsheets'

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    file_path = Column(String(500), nullable=True)

    # Spreadsheet metadata
    metadata = Column(JSON, default={})  # Stores rows, columns, sheet names, etc.

    # Data stored as JSON (for quick access without file loading)
    data_json = Column(JSON, nullable=True)

    # Settings
    settings = Column(JSON, default={})  # UI settings, default formats, etc.

    # Status
    is_active = Column(Boolean, default=True, nullable=False)
    is_template = Column(Boolean, default=False, nullable=False)

    # Timestamps
    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow,
                       onupdate=datetime.datetime.utcnow)
    last_accessed = Column(DateTime, nullable=True)

    # Relationships
    user = relationship("User", back_populates="spreadsheets")
    versions = relationship("SpreadsheetVersion", back_populates="spreadsheet",
                          cascade="all, delete-orphan", order_by="SpreadsheetVersion.version_number.desc()")
    shares = relationship("SpreadsheetShare", back_populates="spreadsheet",
                         cascade="all, delete-orphan")

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'name': self.name,
            'description': self.description,
            'metadata': self.metadata,
            'settings': self.settings,
            'is_active': self.is_active,
            'is_template': self.is_template,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'last_accessed': self.last_accessed.isoformat() if self.last_accessed else None
        }

    def __repr__(self) -> str:
        """String representation."""
        return f"<Spreadsheet(id={self.id}, name='{self.name}', user_id={self.user_id})>"


class SpreadsheetVersion(Base):
    """Version history for spreadsheets."""

    __tablename__ = 'spreadsheet_versions'

    id = Column(Integer, primary_key=True, index=True)
    spreadsheet_id = Column(Integer, ForeignKey('spreadsheets.id'), nullable=False, index=True)
    version_number = Column(Integer, nullable=False)
    file_path = Column(String(500), nullable=True)
    data_json = Column(JSON, nullable=True)
    change_summary = Column(Text, nullable=True)
    created_by = Column(Integer, ForeignKey('users.id'), nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)

    # Relationships
    spreadsheet = relationship("Spreadsheet", back_populates="versions")
    creator = relationship("User")

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            'id': self.id,
            'spreadsheet_id': self.spreadsheet_id,
            'version_number': self.version_number,
            'change_summary': self.change_summary,
            'created_by': self.created_by,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

    def __repr__(self) -> str:
        """String representation."""
        return f"<SpreadsheetVersion(id={self.id}, spreadsheet_id={self.spreadsheet_id}, version={self.version_number})>"


class SpreadsheetShare(Base):
    """Sharing and collaboration for spreadsheets."""

    __tablename__ = 'spreadsheet_shares'

    id = Column(Integer, primary_key=True, index=True)
    spreadsheet_id = Column(Integer, ForeignKey('spreadsheets.id'), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False, index=True)
    permission = Column(Enum(PermissionLevel), nullable=False, default=PermissionLevel.VIEW)
    shared_by = Column(Integer, ForeignKey('users.id'), nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)

    # Relationships
    spreadsheet = relationship("Spreadsheet", back_populates="shares")
    user = relationship("User", foreign_keys=[user_id], back_populates="shared_spreadsheets")
    sharer = relationship("User", foreign_keys=[shared_by])

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            'id': self.id,
            'spreadsheet_id': self.spreadsheet_id,
            'user_id': self.user_id,
            'permission': self.permission.value,
            'shared_by': self.shared_by,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

    def __repr__(self) -> str:
        """String representation."""
        return f"<SpreadsheetShare(id={self.id}, spreadsheet_id={self.spreadsheet_id}, user_id={self.user_id}, permission={self.permission.value})>"
