"""Contract negotiation management.

This module handles version tracking, redlines, comments,
and collaborative negotiation workflows.
"""

from datetime import datetime
from typing import Dict, List, Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field
import structlog

from .contract_types import Contract

logger = structlog.get_logger(__name__)


class Comment(BaseModel):
    """Contract comment or annotation."""

    id: UUID = Field(default_factory=uuid4)
    contract_id: UUID
    clause_id: Optional[UUID] = None
    user_id: UUID
    user_name: str
    content: str
    position: Optional[int] = None  # Character position in text
    resolved: bool = False
    resolved_by: Optional[UUID] = None
    resolved_at: Optional[datetime] = None
    parent_id: Optional[UUID] = None  # For threaded comments
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class Redline(BaseModel):
    """Contract redline/change tracking."""

    id: UUID = Field(default_factory=uuid4)
    contract_id: UUID
    version: str
    user_id: UUID
    user_name: str
    change_type: str  # "addition", "deletion", "modification"
    field_name: str
    old_value: Optional[str] = None
    new_value: Optional[str] = None
    clause_id: Optional[UUID] = None
    accepted: Optional[bool] = None
    accepted_by: Optional[UUID] = None
    accepted_at: Optional[datetime] = None
    reason: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)


class ContractVersion(BaseModel):
    """Contract version snapshot."""

    id: UUID = Field(default_factory=uuid4)
    contract_id: UUID
    version: str
    contract_data: Dict
    created_by: UUID
    created_by_name: str
    change_summary: Optional[str] = None
    is_major: bool = False
    created_at: datetime = Field(default_factory=datetime.utcnow)


class NegotiationManager:
    """Manages contract negotiation process."""

    def __init__(self):
        """Initialize negotiation manager."""
        self.versions: Dict[UUID, List[ContractVersion]] = {}
        self.comments: Dict[UUID, List[Comment]] = {}
        self.redlines: Dict[UUID, List[Redline]] = {}

    def create_version(
        self,
        contract: Contract,
        user_id: UUID,
        user_name: str,
        change_summary: Optional[str] = None,
        is_major: bool = False,
    ) -> ContractVersion:
        """Create a new contract version.

        Args:
            contract: Contract instance
            user_id: User creating version
            user_name: User's name
            change_summary: Summary of changes
            is_major: Whether this is a major version

        Returns:
            New version instance
        """
        logger.info("Creating contract version", contract_id=contract.id)

        # Increment version number
        current_major, current_minor = map(int, contract.version.split('.'))
        if is_major:
            new_version = f"{current_major + 1}.0"
        else:
            new_version = f"{current_major}.{current_minor + 1}"

        version = ContractVersion(
            contract_id=contract.id,
            version=new_version,
            contract_data=contract.dict(),
            created_by=user_id,
            created_by_name=user_name,
            change_summary=change_summary,
            is_major=is_major,
        )

        if contract.id not in self.versions:
            self.versions[contract.id] = []
        self.versions[contract.id].append(version)

        contract.version = new_version

        logger.info(
            "Contract version created",
            contract_id=contract.id,
            version=new_version,
        )

        return version

    def get_versions(self, contract_id: UUID) -> List[ContractVersion]:
        """Get all versions of a contract.

        Args:
            contract_id: Contract ID

        Returns:
            List of versions, newest first
        """
        versions = self.versions.get(contract_id, [])
        return sorted(versions, key=lambda v: v.created_at, reverse=True)

    def compare_versions(
        self,
        contract_id: UUID,
        version1: str,
        version2: str,
    ) -> List[Dict]:
        """Compare two contract versions.

        Args:
            contract_id: Contract ID
            version1: First version number
            version2: Second version number

        Returns:
            List of differences
        """
        logger.info(
            "Comparing contract versions",
            contract_id=contract_id,
            version1=version1,
            version2=version2,
        )

        versions = self.get_versions(contract_id)
        v1_data = next((v.contract_data for v in versions if v.version == version1), None)
        v2_data = next((v.contract_data for v in versions if v.version == version2), None)

        if not v1_data or not v2_data:
            return []

        differences = []
        for key in set(list(v1_data.keys()) + list(v2_data.keys())):
            if v1_data.get(key) != v2_data.get(key):
                differences.append({
                    "field": key,
                    "old_value": v1_data.get(key),
                    "new_value": v2_data.get(key),
                })

        return differences

    def add_comment(
        self,
        contract_id: UUID,
        user_id: UUID,
        user_name: str,
        content: str,
        clause_id: Optional[UUID] = None,
        parent_id: Optional[UUID] = None,
    ) -> Comment:
        """Add a comment to contract or clause.

        Args:
            contract_id: Contract ID
            user_id: Commenter's ID
            user_name: Commenter's name
            content: Comment content
            clause_id: Optional clause ID
            parent_id: Optional parent comment ID for threading

        Returns:
            New comment instance
        """
        logger.info("Adding comment", contract_id=contract_id, user_id=user_id)

        comment = Comment(
            contract_id=contract_id,
            clause_id=clause_id,
            user_id=user_id,
            user_name=user_name,
            content=content,
            parent_id=parent_id,
        )

        if contract_id not in self.comments:
            self.comments[contract_id] = []
        self.comments[contract_id].append(comment)

        return comment

    def get_comments(
        self,
        contract_id: UUID,
        clause_id: Optional[UUID] = None,
        resolved: Optional[bool] = None,
    ) -> List[Comment]:
        """Get comments for contract or clause.

        Args:
            contract_id: Contract ID
            clause_id: Optional clause ID filter
            resolved: Optional resolved status filter

        Returns:
            List of comments
        """
        comments = self.comments.get(contract_id, [])

        if clause_id:
            comments = [c for c in comments if c.clause_id == clause_id]

        if resolved is not None:
            comments = [c for c in comments if c.resolved == resolved]

        return sorted(comments, key=lambda c: c.created_at)

    def resolve_comment(
        self,
        comment_id: UUID,
        user_id: UUID,
    ) -> Optional[Comment]:
        """Resolve a comment.

        Args:
            comment_id: Comment ID
            user_id: User resolving comment

        Returns:
            Updated comment or None
        """
        for comments in self.comments.values():
            for comment in comments:
                if comment.id == comment_id:
                    comment.resolved = True
                    comment.resolved_by = user_id
                    comment.resolved_at = datetime.utcnow()
                    logger.info("Comment resolved", comment_id=comment_id)
                    return comment
        return None

    def add_redline(
        self,
        contract_id: UUID,
        user_id: UUID,
        user_name: str,
        change_type: str,
        field_name: str,
        old_value: Optional[str] = None,
        new_value: Optional[str] = None,
        clause_id: Optional[UUID] = None,
        reason: Optional[str] = None,
    ) -> Redline:
        """Add a redline change.

        Args:
            contract_id: Contract ID
            user_id: User making change
            user_name: User's name
            change_type: Type of change
            field_name: Field being changed
            old_value: Previous value
            new_value: New value
            clause_id: Optional clause ID
            reason: Optional reason for change

        Returns:
            New redline instance
        """
        logger.info(
            "Adding redline",
            contract_id=contract_id,
            change_type=change_type,
            field_name=field_name,
        )

        redline = Redline(
            contract_id=contract_id,
            version="draft",
            user_id=user_id,
            user_name=user_name,
            change_type=change_type,
            field_name=field_name,
            old_value=old_value,
            new_value=new_value,
            clause_id=clause_id,
            reason=reason,
        )

        if contract_id not in self.redlines:
            self.redlines[contract_id] = []
        self.redlines[contract_id].append(redline)

        return redline

    def get_redlines(
        self,
        contract_id: UUID,
        accepted: Optional[bool] = None,
    ) -> List[Redline]:
        """Get redlines for contract.

        Args:
            contract_id: Contract ID
            accepted: Optional acceptance status filter

        Returns:
            List of redlines
        """
        redlines = self.redlines.get(contract_id, [])

        if accepted is not None:
            redlines = [r for r in redlines if r.accepted == accepted]

        return sorted(redlines, key=lambda r: r.created_at)

    def accept_redline(
        self,
        redline_id: UUID,
        user_id: UUID,
    ) -> Optional[Redline]:
        """Accept a redline change.

        Args:
            redline_id: Redline ID
            user_id: User accepting change

        Returns:
            Updated redline or None
        """
        for redlines in self.redlines.values():
            for redline in redlines:
                if redline.id == redline_id:
                    redline.accepted = True
                    redline.accepted_by = user_id
                    redline.accepted_at = datetime.utcnow()
                    logger.info("Redline accepted", redline_id=redline_id)
                    return redline
        return None

    def reject_redline(
        self,
        redline_id: UUID,
        user_id: UUID,
    ) -> Optional[Redline]:
        """Reject a redline change.

        Args:
            redline_id: Redline ID
            user_id: User rejecting change

        Returns:
            Updated redline or None
        """
        for redlines in self.redlines.values():
            for redline in redlines:
                if redline.id == redline_id:
                    redline.accepted = False
                    redline.accepted_by = user_id
                    redline.accepted_at = datetime.utcnow()
                    logger.info("Redline rejected", redline_id=redline_id)
                    return redline
        return None

    def get_pending_changes(self, contract_id: UUID) -> Dict[str, List]:
        """Get all pending changes for a contract.

        Args:
            contract_id: Contract ID

        Returns:
            Dictionary with pending comments and redlines
        """
        return {
            "comments": self.get_comments(contract_id, resolved=False),
            "redlines": self.get_redlines(contract_id, accepted=None),
        }
