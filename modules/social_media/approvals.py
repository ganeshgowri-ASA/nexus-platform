"""
Social Media Module - Approval Workflow Management.

This module provides multi-level approval workflows, revision requests,
team collaboration, and role-based permissions for content approval.
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4

from .social_types import ApprovalStatus, Post

logger = logging.getLogger(__name__)


class ApprovalError(Exception):
    """Base exception for approval workflow errors."""

    pass


class ApprovalWorkflow:
    """Content approval workflow manager."""

    def __init__(self):
        """Initialize approval workflow manager."""
        self._approvals: Dict[UUID, Dict[str, Any]] = {}  # post_id -> approval_data
        self._user_roles: Dict[UUID, str] = {}  # user_id -> role
        self._approval_history: List[Dict[str, Any]] = []

    def set_user_role(self, user_id: UUID, role: str) -> None:
        """
        Set role for a user.

        Args:
            user_id: User UUID
            role: Role name (admin, manager, editor, contributor)
        """
        valid_roles = ["admin", "manager", "editor", "contributor"]
        if role not in valid_roles:
            raise ValueError(f"Invalid role. Must be one of: {valid_roles}")

        self._user_roles[user_id] = role
        logger.info(f"Set role for user {user_id}: {role}")

    def get_user_role(self, user_id: UUID) -> Optional[str]:
        """
        Get role for a user.

        Args:
            user_id: User UUID

        Returns:
            Role string or None
        """
        return self._user_roles.get(user_id)

    def can_approve(self, user_id: UUID) -> bool:
        """
        Check if user can approve content.

        Args:
            user_id: User UUID

        Returns:
            True if user can approve
        """
        role = self._user_roles.get(user_id)
        return role in ["admin", "manager"]

    def submit_for_approval(
        self,
        post: Post,
        submitted_by: UUID,
        approvers: List[UUID],
        notes: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Submit a post for approval.

        Args:
            post: Post to submit
            submitted_by: User UUID who submitted
            approvers: List of user UUIDs who can approve
            notes: Optional submission notes

        Returns:
            Approval data dictionary

        Raises:
            ApprovalError: If submission fails
        """
        try:
            # Validate approvers can approve
            for approver_id in approvers:
                if not self.can_approve(approver_id):
                    role = self._user_roles.get(approver_id, "none")
                    logger.warning(
                        f"User {approver_id} with role '{role}' cannot approve"
                    )

            approval_data = {
                "post_id": post.id,
                "status": ApprovalStatus.PENDING,
                "submitted_by": submitted_by,
                "submitted_at": datetime.utcnow(),
                "approvers": approvers,
                "approvals": [],
                "rejections": [],
                "revision_requests": [],
                "notes": notes,
                "current_approver_index": 0,
            }

            self._approvals[post.id] = approval_data
            post.approval_status = ApprovalStatus.PENDING

            # Log to history
            self._approval_history.append(
                {
                    "action": "submitted",
                    "post_id": str(post.id),
                    "user_id": str(submitted_by),
                    "timestamp": datetime.utcnow().isoformat(),
                    "notes": notes,
                }
            )

            logger.info(f"Submitted post {post.id} for approval")
            return approval_data

        except Exception as e:
            logger.error(f"Failed to submit for approval: {e}")
            raise ApprovalError(f"Submission failed: {e}")

    def approve_post(
        self,
        post_id: UUID,
        approver_id: UUID,
        notes: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Approve a post.

        Args:
            post_id: Post UUID
            approver_id: Approver user UUID
            notes: Optional approval notes

        Returns:
            Updated approval data

        Raises:
            ApprovalError: If approval fails
        """
        if post_id not in self._approvals:
            raise ApprovalError(f"Post {post_id} not in approval workflow")

        if not self.can_approve(approver_id):
            raise ApprovalError(f"User {approver_id} does not have approval permissions")

        approval_data = self._approvals[post_id]

        if approval_data["status"] != ApprovalStatus.PENDING:
            raise ApprovalError(
                f"Post cannot be approved. Current status: {approval_data['status'].value}"
            )

        # Check if this approver is in the list
        if approver_id not in approval_data["approvers"]:
            raise ApprovalError(f"User {approver_id} is not an approver for this post")

        # Check if already approved by this user
        if any(a["approver_id"] == approver_id for a in approval_data["approvals"]):
            raise ApprovalError(f"User {approver_id} has already approved this post")

        # Add approval
        approval_data["approvals"].append(
            {
                "approver_id": approver_id,
                "approved_at": datetime.utcnow(),
                "notes": notes,
            }
        )

        # Check if all approvers have approved
        if len(approval_data["approvals"]) >= len(approval_data["approvers"]):
            approval_data["status"] = ApprovalStatus.APPROVED
            approval_data["approved_at"] = datetime.utcnow()

        # Log to history
        self._approval_history.append(
            {
                "action": "approved",
                "post_id": str(post_id),
                "user_id": str(approver_id),
                "timestamp": datetime.utcnow().isoformat(),
                "notes": notes,
            }
        )

        logger.info(f"Post {post_id} approved by user {approver_id}")
        return approval_data

    def reject_post(
        self,
        post_id: UUID,
        rejector_id: UUID,
        reason: str,
    ) -> Dict[str, Any]:
        """
        Reject a post.

        Args:
            post_id: Post UUID
            rejector_id: Rejector user UUID
            reason: Rejection reason

        Returns:
            Updated approval data

        Raises:
            ApprovalError: If rejection fails
        """
        if post_id not in self._approvals:
            raise ApprovalError(f"Post {post_id} not in approval workflow")

        if not self.can_approve(rejector_id):
            raise ApprovalError(f"User {rejector_id} does not have approval permissions")

        approval_data = self._approvals[post_id]

        if approval_data["status"] != ApprovalStatus.PENDING:
            raise ApprovalError(
                f"Post cannot be rejected. Current status: {approval_data['status'].value}"
            )

        # Add rejection
        approval_data["rejections"].append(
            {
                "rejector_id": rejector_id,
                "rejected_at": datetime.utcnow(),
                "reason": reason,
            }
        )

        approval_data["status"] = ApprovalStatus.REJECTED
        approval_data["rejected_at"] = datetime.utcnow()

        # Log to history
        self._approval_history.append(
            {
                "action": "rejected",
                "post_id": str(post_id),
                "user_id": str(rejector_id),
                "timestamp": datetime.utcnow().isoformat(),
                "reason": reason,
            }
        )

        logger.info(f"Post {post_id} rejected by user {rejector_id}")
        return approval_data

    def request_revision(
        self,
        post_id: UUID,
        requester_id: UUID,
        feedback: str,
    ) -> Dict[str, Any]:
        """
        Request revisions for a post.

        Args:
            post_id: Post UUID
            requester_id: Requester user UUID
            feedback: Revision feedback

        Returns:
            Updated approval data

        Raises:
            ApprovalError: If request fails
        """
        if post_id not in self._approvals:
            raise ApprovalError(f"Post {post_id} not in approval workflow")

        if not self.can_approve(requester_id):
            raise ApprovalError(
                f"User {requester_id} does not have approval permissions"
            )

        approval_data = self._approvals[post_id]

        # Add revision request
        approval_data["revision_requests"].append(
            {
                "requester_id": requester_id,
                "requested_at": datetime.utcnow(),
                "feedback": feedback,
                "resolved": False,
            }
        )

        approval_data["status"] = ApprovalStatus.REVISION_REQUESTED

        # Log to history
        self._approval_history.append(
            {
                "action": "revision_requested",
                "post_id": str(post_id),
                "user_id": str(requester_id),
                "timestamp": datetime.utcnow().isoformat(),
                "feedback": feedback,
            }
        )

        logger.info(f"Revision requested for post {post_id} by user {requester_id}")
        return approval_data

    def resubmit_after_revision(
        self,
        post_id: UUID,
        submitted_by: UUID,
        revision_notes: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Resubmit a post after making revisions.

        Args:
            post_id: Post UUID
            submitted_by: User UUID who resubmitted
            revision_notes: Optional notes about revisions made

        Returns:
            Updated approval data

        Raises:
            ApprovalError: If resubmission fails
        """
        if post_id not in self._approvals:
            raise ApprovalError(f"Post {post_id} not in approval workflow")

        approval_data = self._approvals[post_id]

        if approval_data["status"] != ApprovalStatus.REVISION_REQUESTED:
            raise ApprovalError(
                "Post must be in revision requested status to resubmit"
            )

        # Mark revision requests as resolved
        for request in approval_data["revision_requests"]:
            if not request["resolved"]:
                request["resolved"] = True
                request["resolved_at"] = datetime.utcnow()
                request["resolution_notes"] = revision_notes

        # Reset to pending
        approval_data["status"] = ApprovalStatus.PENDING
        approval_data["approvals"] = []  # Clear previous approvals

        # Log to history
        self._approval_history.append(
            {
                "action": "resubmitted",
                "post_id": str(post_id),
                "user_id": str(submitted_by),
                "timestamp": datetime.utcnow().isoformat(),
                "notes": revision_notes,
            }
        )

        logger.info(f"Post {post_id} resubmitted by user {submitted_by}")
        return approval_data

    def get_approval_status(self, post_id: UUID) -> Optional[Dict[str, Any]]:
        """
        Get approval status for a post.

        Args:
            post_id: Post UUID

        Returns:
            Approval data or None
        """
        return self._approvals.get(post_id)

    def get_pending_approvals(
        self, approver_id: Optional[UUID] = None
    ) -> List[Dict[str, Any]]:
        """
        Get pending approvals.

        Args:
            approver_id: Optional filter by specific approver

        Returns:
            List of pending approval data
        """
        pending = []

        for approval_data in self._approvals.values():
            if approval_data["status"] != ApprovalStatus.PENDING:
                continue

            if approver_id:
                # Check if this approver is assigned and hasn't approved yet
                if approver_id not in approval_data["approvers"]:
                    continue
                if any(
                    a["approver_id"] == approver_id
                    for a in approval_data["approvals"]
                ):
                    continue

            pending.append(approval_data)

        return pending

    def get_approval_history(
        self,
        post_id: Optional[UUID] = None,
        user_id: Optional[UUID] = None,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """
        Get approval history.

        Args:
            post_id: Optional filter by post
            user_id: Optional filter by user
            limit: Maximum records to return

        Returns:
            List of approval history records
        """
        history = self._approval_history

        if post_id:
            history = [h for h in history if h["post_id"] == str(post_id)]
        if user_id:
            history = [h for h in history if h["user_id"] == str(user_id)]

        # Sort by timestamp descending
        history.sort(
            key=lambda h: datetime.fromisoformat(h["timestamp"]), reverse=True
        )

        return history[:limit]

    def get_statistics(self) -> Dict[str, Any]:
        """
        Get approval workflow statistics.

        Returns:
            Statistics dictionary
        """
        total_submissions = len(self._approvals)
        pending = sum(
            1
            for a in self._approvals.values()
            if a["status"] == ApprovalStatus.PENDING
        )
        approved = sum(
            1
            for a in self._approvals.values()
            if a["status"] == ApprovalStatus.APPROVED
        )
        rejected = sum(
            1
            for a in self._approvals.values()
            if a["status"] == ApprovalStatus.REJECTED
        )
        revision_requested = sum(
            1
            for a in self._approvals.values()
            if a["status"] == ApprovalStatus.REVISION_REQUESTED
        )

        # Calculate average approval time for approved posts
        approval_times = []
        for approval_data in self._approvals.values():
            if (
                approval_data["status"] == ApprovalStatus.APPROVED
                and "approved_at" in approval_data
            ):
                time_diff = (
                    approval_data["approved_at"] - approval_data["submitted_at"]
                )
                approval_times.append(time_diff.total_seconds() / 3600)  # hours

        avg_approval_time = (
            sum(approval_times) / len(approval_times) if approval_times else 0.0
        )

        return {
            "total_submissions": total_submissions,
            "pending": pending,
            "approved": approved,
            "rejected": rejected,
            "revision_requested": revision_requested,
            "approval_rate": round((approved / total_submissions * 100), 2)
            if total_submissions > 0
            else 0.0,
            "avg_approval_time_hours": round(avg_approval_time, 2),
            "total_users": len(self._user_roles),
        }
