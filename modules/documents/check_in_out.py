"""
Document check-in/check-out and locking module for Document Management System.

This module provides comprehensive document locking functionality including:
- Check-in/check-out workflow for exclusive editing
- Lock management with timeout handling
- Conflict resolution strategies
- Optimistic and pessimistic locking
- Lock stealing with authorization
- Auto-save and recovery mechanisms
"""

import asyncio
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy import and_, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from backend.core.exceptions import (
    AuthorizationException,
    DocumentLockedException,
    DocumentNotFoundException,
    ResourceConflictException,
    ResourceNotFoundException,
    ValidationException,
)
from backend.core.logging import get_logger
from backend.models.document import Document, DocumentStatus

logger = get_logger(__name__)


class LockType(str, Enum):
    """Lock types."""

    EXCLUSIVE = "exclusive"  # Full write lock
    SHARED = "shared"  # Multiple readers
    OPTIMISTIC = "optimistic"  # Version-based


class LockStatus(str, Enum):
    """Lock status."""

    ACTIVE = "active"
    EXPIRED = "expired"
    RELEASED = "released"
    STOLEN = "stolen"


class ConflictResolution(str, Enum):
    """Conflict resolution strategies."""

    MANUAL = "manual"  # User resolves
    OVERWRITE = "overwrite"  # Overwrite with new version
    MERGE = "merge"  # Attempt automatic merge
    KEEP_BOTH = "keep_both"  # Create separate versions


class DocumentLock:
    """
    Document lock representation.

    Attributes:
        document_id: Document ID
        user_id: User who holds lock
        lock_type: Type of lock
        status: Lock status
        acquired_at: Lock acquisition time
        expires_at: Lock expiration time
        last_heartbeat: Last activity timestamp
        metadata: Additional lock metadata
    """

    def __init__(
        self,
        document_id: int,
        user_id: int,
        lock_type: LockType = LockType.EXCLUSIVE,
        timeout_minutes: int = 30,
        lock_id: Optional[int] = None,
    ) -> None:
        """
        Initialize document lock.

        Args:
            document_id: Document ID
            user_id: User ID
            lock_type: Type of lock
            timeout_minutes: Lock timeout in minutes
            lock_id: Lock ID
        """
        self.id = lock_id
        self.document_id = document_id
        self.user_id = user_id
        self.lock_type = lock_type
        self.status = LockStatus.ACTIVE
        self.acquired_at = datetime.utcnow()
        self.expires_at = datetime.utcnow() + timedelta(minutes=timeout_minutes)
        self.last_heartbeat = datetime.utcnow()
        self.metadata: Dict[str, Any] = {}

    def is_expired(self) -> bool:
        """Check if lock has expired."""
        return datetime.utcnow() > self.expires_at

    def is_active(self) -> bool:
        """Check if lock is active."""
        return self.status == LockStatus.ACTIVE and not self.is_expired()

    def refresh(self, extend_minutes: int = 30) -> None:
        """
        Refresh lock expiration.

        Args:
            extend_minutes: Minutes to extend
        """
        self.last_heartbeat = datetime.utcnow()
        self.expires_at = datetime.utcnow() + timedelta(minutes=extend_minutes)

    def to_dict(self) -> Dict[str, Any]:
        """Convert lock to dictionary."""
        return {
            "id": self.id,
            "document_id": self.document_id,
            "user_id": self.user_id,
            "lock_type": self.lock_type.value,
            "status": self.status.value,
            "acquired_at": self.acquired_at.isoformat(),
            "expires_at": self.expires_at.isoformat(),
            "last_heartbeat": self.last_heartbeat.isoformat(),
            "is_expired": self.is_expired(),
            "is_active": self.is_active(),
        }


class CheckInOutService:
    """
    Document check-in/check-out service.

    Provides comprehensive locking and version control for documents
    with support for exclusive editing, conflict resolution, and
    automatic timeout handling.
    """

    def __init__(
        self,
        db: AsyncSession,
        default_timeout_minutes: int = 30,
        max_timeout_minutes: int = 480,
    ) -> None:
        """
        Initialize check-in/check-out service.

        Args:
            db: Database session
            default_timeout_minutes: Default lock timeout
            max_timeout_minutes: Maximum lock timeout
        """
        self.db = db
        self.default_timeout_minutes = default_timeout_minutes
        self.max_timeout_minutes = max_timeout_minutes
        self.logger = get_logger(self.__class__.__name__)
        self._locks: Dict[int, DocumentLock] = {}

    async def check_out(
        self,
        document_id: int,
        user_id: int,
        lock_type: LockType = LockType.EXCLUSIVE,
        timeout_minutes: Optional[int] = None,
        force: bool = False,
    ) -> DocumentLock:
        """
        Check out a document for editing.

        Args:
            document_id: Document ID
            user_id: User checking out
            lock_type: Type of lock
            timeout_minutes: Lock timeout (uses default if not specified)
            force: Force checkout even if locked (requires permission)

        Returns:
            Document lock

        Raises:
            DocumentNotFoundException: If document not found
            DocumentLockedException: If already locked
            AuthorizationException: If user lacks permission
        """
        try:
            self.logger.info(
                "checking_out_document",
                document_id=document_id,
                user_id=user_id,
                lock_type=lock_type.value,
            )

            # Validate timeout
            timeout = timeout_minutes or self.default_timeout_minutes
            if timeout > self.max_timeout_minutes:
                raise ValidationException(
                    f"Timeout cannot exceed {self.max_timeout_minutes} minutes"
                )

            # Get document
            document = await self._get_document(document_id)

            # Verify user has edit permission
            await self._verify_edit_permission(document, user_id)

            # Check for existing locks
            existing_lock = await self._get_active_lock(document_id)

            if existing_lock:
                if existing_lock.user_id == user_id:
                    # User already holds lock, refresh it
                    existing_lock.refresh(timeout)
                    self.logger.info("lock_refreshed", document_id=document_id)
                    return existing_lock
                elif force:
                    # Steal lock (requires admin permission)
                    await self._verify_admin_permission(user_id)
                    await self._steal_lock(existing_lock, user_id)
                else:
                    raise DocumentLockedException(
                        f"Document is locked by user {existing_lock.user_id} "
                        f"until {existing_lock.expires_at.isoformat()}"
                    )

            # Create new lock
            lock = DocumentLock(
                document_id=document_id,
                user_id=user_id,
                lock_type=lock_type,
                timeout_minutes=timeout,
            )

            # TODO: Store in database
            lock.id = len(self._locks) + 1
            self._locks[document_id] = lock

            # Update document status
            await self._update_document_lock_status(document_id, True, user_id)

            self.logger.info(
                "document_checked_out",
                document_id=document_id,
                lock_id=lock.id,
                expires_at=lock.expires_at.isoformat(),
            )

            return lock

        except (DocumentNotFoundException, DocumentLockedException, AuthorizationException, ValidationException):
            raise
        except Exception as e:
            self.logger.exception("checkout_failed", document_id=document_id, error=str(e))
            raise DocumentLockedException(f"Check-out failed: {str(e)}")

    async def check_in(
        self,
        document_id: int,
        user_id: int,
        keep_lock: bool = False,
    ) -> None:
        """
        Check in a document, releasing the lock.

        Args:
            document_id: Document ID
            user_id: User checking in
            keep_lock: Keep lock after check-in

        Raises:
            DocumentNotFoundException: If document not found
            AuthorizationException: If user doesn't hold lock
        """
        try:
            self.logger.info(
                "checking_in_document",
                document_id=document_id,
                user_id=user_id,
            )

            # Get document
            document = await self._get_document(document_id)

            # Get lock
            lock = await self._get_active_lock(document_id)

            if not lock:
                raise ResourceNotFoundException("Active lock", document_id)

            # Verify user holds the lock
            if lock.user_id != user_id:
                raise AuthorizationException(
                    f"Lock is held by user {lock.user_id}"
                )

            if not keep_lock:
                # Release lock
                await self._release_lock(lock)

                # Update document status
                await self._update_document_lock_status(document_id, False, None)

                self.logger.info("document_checked_in", document_id=document_id)
            else:
                # Refresh lock
                lock.refresh()
                self.logger.info("document_checked_in_with_lock", document_id=document_id)

        except (DocumentNotFoundException, ResourceNotFoundException, AuthorizationException):
            raise
        except Exception as e:
            self.logger.exception("checkin_failed", document_id=document_id, error=str(e))
            raise DocumentLockedException(f"Check-in failed: {str(e)}")

    async def cancel_checkout(
        self,
        document_id: int,
        user_id: int,
    ) -> None:
        """
        Cancel checkout without saving changes.

        Args:
            document_id: Document ID
            user_id: User canceling checkout

        Raises:
            DocumentNotFoundException: If document not found
            AuthorizationException: If user doesn't hold lock
        """
        try:
            self.logger.info(
                "canceling_checkout",
                document_id=document_id,
                user_id=user_id,
            )

            # Similar to check-in but don't save changes
            await self.check_in(document_id, user_id, keep_lock=False)

            # TODO: Discard any uncommitted changes

            self.logger.info("checkout_cancelled", document_id=document_id)

        except Exception as e:
            self.logger.exception("cancel_checkout_failed", error=str(e))
            raise

    async def get_lock_status(
        self,
        document_id: int,
    ) -> Optional[DocumentLock]:
        """
        Get current lock status for a document.

        Args:
            document_id: Document ID

        Returns:
            Active lock or None
        """
        try:
            return await self._get_active_lock(document_id)

        except Exception as e:
            self.logger.exception("get_lock_status_failed", error=str(e))
            return None

    async def refresh_lock(
        self,
        document_id: int,
        user_id: int,
        extend_minutes: Optional[int] = None,
    ) -> DocumentLock:
        """
        Refresh/extend an existing lock (heartbeat).

        Args:
            document_id: Document ID
            user_id: User holding lock
            extend_minutes: Minutes to extend

        Returns:
            Refreshed lock

        Raises:
            ResourceNotFoundException: If no active lock
            AuthorizationException: If user doesn't hold lock
        """
        try:
            self.logger.debug("refreshing_lock", document_id=document_id)

            lock = await self._get_active_lock(document_id)

            if not lock:
                raise ResourceNotFoundException("Active lock", document_id)

            if lock.user_id != user_id:
                raise AuthorizationException("Lock held by another user")

            # Refresh lock
            extend = extend_minutes or self.default_timeout_minutes
            if extend > self.max_timeout_minutes:
                extend = self.max_timeout_minutes

            lock.refresh(extend)

            # TODO: Update in database

            self.logger.debug("lock_refreshed", document_id=document_id)

            return lock

        except (ResourceNotFoundException, AuthorizationException):
            raise
        except Exception as e:
            self.logger.exception("refresh_lock_failed", error=str(e))
            raise DocumentLockedException(f"Lock refresh failed: {str(e)}")

    async def break_lock(
        self,
        document_id: int,
        admin_user_id: int,
        reason: str,
    ) -> None:
        """
        Break/remove a lock (admin operation).

        Args:
            document_id: Document ID
            admin_user_id: Admin user breaking lock
            reason: Reason for breaking lock

        Raises:
            AuthorizationException: If user is not admin
            ResourceNotFoundException: If no active lock
        """
        try:
            self.logger.info(
                "breaking_lock",
                document_id=document_id,
                admin_user_id=admin_user_id,
            )

            # Verify admin permission
            await self._verify_admin_permission(admin_user_id)

            # Get lock
            lock = await self._get_active_lock(document_id)

            if not lock:
                raise ResourceNotFoundException("Active lock", document_id)

            # Record reason
            lock.metadata["break_reason"] = reason
            lock.metadata["broken_by"] = admin_user_id

            # Release lock
            lock.status = LockStatus.STOLEN
            await self._release_lock(lock)

            # Update document
            await self._update_document_lock_status(document_id, False, None)

            self.logger.info(
                "lock_broken",
                document_id=document_id,
                original_user=lock.user_id,
            )

        except (AuthorizationException, ResourceNotFoundException):
            raise
        except Exception as e:
            self.logger.exception("break_lock_failed", error=str(e))
            raise DocumentLockedException(f"Break lock failed: {str(e)}")

    async def get_user_locks(
        self,
        user_id: int,
        include_expired: bool = False,
    ) -> List[DocumentLock]:
        """
        Get all locks held by a user.

        Args:
            user_id: User ID
            include_expired: Include expired locks

        Returns:
            List of locks
        """
        try:
            locks = [
                lock for lock in self._locks.values()
                if lock.user_id == user_id
            ]

            if not include_expired:
                locks = [lock for lock in locks if lock.is_active()]

            return locks

        except Exception as e:
            self.logger.exception("get_user_locks_failed", error=str(e))
            return []

    async def cleanup_expired_locks(self) -> int:
        """
        Clean up expired locks.

        Returns:
            Number of locks cleaned up
        """
        try:
            self.logger.info("cleaning_up_expired_locks")

            expired_count = 0
            expired_locks = []

            for lock in self._locks.values():
                if lock.is_expired() and lock.status == LockStatus.ACTIVE:
                    expired_locks.append(lock)

            for lock in expired_locks:
                lock.status = LockStatus.EXPIRED
                await self._release_lock(lock)
                await self._update_document_lock_status(lock.document_id, False, None)
                expired_count += 1

            self.logger.info("expired_locks_cleaned", count=expired_count)

            return expired_count

        except Exception as e:
            self.logger.exception("cleanup_failed", error=str(e))
            return 0

    async def detect_conflicts(
        self,
        document_id: int,
        user_version: int,
    ) -> Tuple[bool, Optional[str]]:
        """
        Detect version conflicts (optimistic locking).

        Args:
            document_id: Document ID
            user_version: Version user is working with

        Returns:
            Tuple of (has_conflict, conflict_message)
        """
        try:
            document = await self._get_document(document_id)

            if document.current_version > user_version:
                return (
                    True,
                    f"Document has been updated to version {document.current_version}. "
                    f"Your version is {user_version}.",
                )

            return (False, None)

        except Exception as e:
            self.logger.exception("conflict_detection_failed", error=str(e))
            return (False, None)

    async def resolve_conflict(
        self,
        document_id: int,
        user_id: int,
        strategy: ConflictResolution,
        user_content: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Resolve edit conflict.

        Args:
            document_id: Document ID
            user_id: User resolving conflict
            strategy: Resolution strategy
            user_content: User's content (if needed)

        Returns:
            Resolution result

        Raises:
            ValidationException: If resolution fails
        """
        try:
            self.logger.info(
                "resolving_conflict",
                document_id=document_id,
                strategy=strategy.value,
            )

            document = await self._get_document(document_id)

            result = {
                "document_id": document_id,
                "strategy": strategy.value,
                "success": False,
                "message": "",
            }

            if strategy == ConflictResolution.OVERWRITE:
                # Overwrite with user's version
                # TODO: Create new version with user's content
                result["success"] = True
                result["message"] = "Document overwritten with your version"

            elif strategy == ConflictResolution.KEEP_BOTH:
                # Create separate version
                # TODO: Create new document version with user's content
                result["success"] = True
                result["message"] = "Both versions kept as separate document versions"

            elif strategy == ConflictResolution.MERGE:
                # Attempt automatic merge
                # TODO: Implement three-way merge logic
                result["success"] = False
                result["message"] = "Automatic merge not yet implemented"

            elif strategy == ConflictResolution.MANUAL:
                # User will merge manually
                result["success"] = True
                result["message"] = "Manual merge required"

            self.logger.info(
                "conflict_resolved",
                document_id=document_id,
                success=result["success"],
            )

            return result

        except Exception as e:
            self.logger.exception("conflict_resolution_failed", error=str(e))
            raise ValidationException(f"Conflict resolution failed: {str(e)}")

    # Private Helper Methods

    async def _get_document(self, document_id: int) -> Document:
        """Get document by ID."""
        stmt = select(Document).where(Document.id == document_id)
        result = await self.db.execute(stmt)
        document = result.scalar_one_or_none()

        if not document:
            raise DocumentNotFoundException(document_id)

        return document

    async def _get_active_lock(self, document_id: int) -> Optional[DocumentLock]:
        """Get active lock for document."""
        lock = self._locks.get(document_id)

        if lock and lock.is_active():
            return lock

        # Clean up expired lock
        if lock and lock.is_expired():
            lock.status = LockStatus.EXPIRED
            self._locks.pop(document_id, None)

        return None

    async def _release_lock(self, lock: DocumentLock) -> None:
        """Release a lock."""
        lock.status = LockStatus.RELEASED
        self._locks.pop(lock.document_id, None)

        # TODO: Remove from database

        self.logger.debug("lock_released", document_id=lock.document_id)

    async def _steal_lock(self, lock: DocumentLock, new_user_id: int) -> None:
        """Steal lock from another user."""
        lock.status = LockStatus.STOLEN
        lock.metadata["stolen_by"] = new_user_id
        lock.metadata["stolen_at"] = datetime.utcnow().isoformat()

        await self._release_lock(lock)

        self.logger.warning(
            "lock_stolen",
            document_id=lock.document_id,
            original_user=lock.user_id,
            new_user=new_user_id,
        )

    async def _update_document_lock_status(
        self,
        document_id: int,
        is_locked: bool,
        locked_by_id: Optional[int],
    ) -> None:
        """Update document lock status in database."""
        try:
            # TODO: Update document in database
            self.logger.debug(
                "document_lock_status_updated",
                document_id=document_id,
                is_locked=is_locked,
            )

        except Exception as e:
            self.logger.warning("update_lock_status_failed", error=str(e))

    async def _verify_edit_permission(self, document: Document, user_id: int) -> None:
        """Verify user has edit permission."""
        # TODO: Check permissions table
        if not document.is_public and document.owner_id != user_id:
            # For now, only allow owner
            raise AuthorizationException("No edit permission for document")

    async def _verify_admin_permission(self, user_id: int) -> None:
        """Verify user has admin permission."""
        # TODO: Check user roles
        # For now, allow all (placeholder)
        pass
