"""
User model for authentication and authorization.

This module defines the User model and related enums.
"""

from enum import Enum as PyEnum
from sqlalchemy import Column, String, Boolean, Enum
from sqlalchemy.orm import relationship

from app.models.base import BaseModel


class UserRole(str, PyEnum):
    """User roles for access control."""

    ADMIN = "admin"
    MANAGER = "manager"
    MEMBER = "member"
    VIEWER = "viewer"


class User(BaseModel):
    """
    User model for authentication and authorization.

    Attributes:
        email: Unique email address
        username: Unique username
        hashed_password: Bcrypt hashed password
        full_name: User's full name
        role: User role (admin, manager, member, viewer)
        is_active: Whether user account is active
        is_verified: Whether email is verified
    """

    __tablename__ = "users"

    email = Column(String(255), unique=True, index=True, nullable=False)
    username = Column(String(100), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=True)

    # Role and permissions
    role = Column(
        Enum(UserRole),
        default=UserRole.MEMBER,
        nullable=False,
        index=True
    )

    # Status flags
    is_active = Column(Boolean, default=True, nullable=False)
    is_verified = Column(Boolean, default=False, nullable=False)

    # Relationships
    campaigns = relationship(
        "Campaign",
        back_populates="owner",
        foreign_keys="Campaign.owner_id"
    )

    team_members = relationship(
        "TeamMember",
        back_populates="user",
        cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<User {self.username} ({self.email})>"

    def has_permission(self, required_role: UserRole) -> bool:
        """
        Check if user has required permission level.

        Permission hierarchy: admin > manager > member > viewer

        Args:
            required_role: Minimum required role

        Returns:
            bool: True if user has sufficient permissions
        """
        role_hierarchy = {
            UserRole.ADMIN: 4,
            UserRole.MANAGER: 3,
            UserRole.MEMBER: 2,
            UserRole.VIEWER: 1,
        }

        user_level = role_hierarchy.get(self.role, 0)
        required_level = role_hierarchy.get(required_role, 0)

        return user_level >= required_level

    def can_manage_campaign(self, campaign) -> bool:
        """
        Check if user can manage a specific campaign.

        Args:
            campaign: Campaign instance

        Returns:
            bool: True if user can manage the campaign
        """
        # Admins can manage all campaigns
        if self.role == UserRole.ADMIN:
            return True

        # Campaign owner can manage
        if campaign.owner_id == self.id:
            return True

        # Check team membership with appropriate role
        for team_member in campaign.team_members:
            if (
                team_member.user_id == self.id
                and team_member.role in ["manager", "admin"]
            ):
                return True

        return False
