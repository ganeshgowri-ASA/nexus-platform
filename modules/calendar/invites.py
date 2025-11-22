"""
Invite Manager Module

Handles meeting invitations, RSVP responses, and guest management.
"""

from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field, asdict
from enum import Enum
import uuid

from .event_manager import Event, EventManager, Attendee, AttendeeStatus


class InviteStatus(Enum):
    """Invitation status."""
    PENDING = "pending"
    SENT = "sent"
    VIEWED = "viewed"
    RESPONDED = "responded"
    EXPIRED = "expired"


class GuestPermission(Enum):
    """Guest permissions for events."""
    NONE = "none"
    VIEW_ATTENDEES = "view_attendees"
    INVITE_OTHERS = "invite_others"
    MODIFY_EVENT = "modify_event"


@dataclass
class Invitation:
    """
    Represents a meeting invitation.

    Attributes:
        id: Unique invitation ID
        event_id: Associated event ID
        event_title: Event title
        event_start: Event start time
        event_end: Event end time
        organizer: Organizer email
        attendee_email: Invitee email
        attendee_name: Invitee name
        status: Invitation status
        response_status: RSVP response status
        message: Personal message from organizer
        sent_at: When invitation was sent
        viewed_at: When invitation was viewed
        responded_at: When invitee responded
        response_comment: Comment from invitee
        is_optional: Whether attendance is optional
    """
    id: str
    event_id: str
    event_title: str
    event_start: datetime
    event_end: datetime
    organizer: str
    attendee_email: str
    attendee_name: Optional[str] = None
    status: InviteStatus = InviteStatus.PENDING
    response_status: AttendeeStatus = AttendeeStatus.NEEDS_ACTION
    message: Optional[str] = None
    sent_at: Optional[datetime] = None
    viewed_at: Optional[datetime] = None
    responded_at: Optional[datetime] = None
    response_comment: Optional[str] = None
    is_optional: bool = False

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "event_id": self.event_id,
            "event_title": self.event_title,
            "event_start": self.event_start.isoformat(),
            "event_end": self.event_end.isoformat(),
            "organizer": self.organizer,
            "attendee_email": self.attendee_email,
            "attendee_name": self.attendee_name,
            "status": self.status.value,
            "response_status": self.response_status.value,
            "message": self.message,
            "sent_at": self.sent_at.isoformat() if self.sent_at else None,
            "viewed_at": self.viewed_at.isoformat() if self.viewed_at else None,
            "responded_at": self.responded_at.isoformat() if self.responded_at else None,
            "response_comment": self.response_comment,
            "is_optional": self.is_optional,
        }


class InviteManager:
    """
    Manages meeting invitations and RSVP responses.

    Features:
    - Send invitations
    - Track RSVP responses
    - Manage guest permissions
    - Send reminder emails
    - Handle invitation updates
    """

    def __init__(
        self,
        event_manager: Optional[EventManager] = None,
    ):
        """
        Initialize the invite manager.

        Args:
            event_manager: Event manager instance
        """
        self.event_manager = event_manager or EventManager()
        self._invitations: Dict[str, Invitation] = {}
        self._guest_permissions: Dict[str, List[GuestPermission]] = {}

    def create_invitation(
        self,
        event: Event,
        attendee: Attendee,
        message: Optional[str] = None,
    ) -> Invitation:
        """
        Create an invitation for an attendee.

        Args:
            event: Event to invite to
            attendee: Attendee to invite
            message: Optional personal message

        Returns:
            Created Invitation instance
        """
        invitation = Invitation(
            id=str(uuid.uuid4()),
            event_id=event.id,
            event_title=event.title,
            event_start=event.start_time,
            event_end=event.end_time,
            organizer=event.organizer or "",
            attendee_email=attendee.email,
            attendee_name=attendee.name,
            message=message,
            is_optional=attendee.optional,
            response_status=attendee.status,
        )

        self._invitations[invitation.id] = invitation
        return invitation

    def send_invitation(
        self,
        invitation_id: str,
    ) -> bool:
        """
        Send an invitation.

        Args:
            invitation_id: Invitation ID

        Returns:
            True if sent successfully
        """
        invitation = self._invitations.get(invitation_id)
        if not invitation:
            return False

        # Send invitation email
        success = self._send_invitation_email(invitation)

        if success:
            invitation.status = InviteStatus.SENT
            invitation.sent_at = datetime.now()

        return success

    def _send_invitation_email(self, invitation: Invitation) -> bool:
        """
        Send invitation email.

        Args:
            invitation: Invitation to send

        Returns:
            True if sent successfully
        """
        # TODO: Integrate with email module
        subject = f"Invitation: {invitation.event_title}"

        body = f"""
You have been invited to: {invitation.event_title}

When: {invitation.event_start.strftime('%A, %B %d, %Y at %I:%M %p')}
Duration: {int((invitation.event_end - invitation.event_start).total_seconds() / 60)} minutes
Organizer: {invitation.organizer}
"""

        if invitation.message:
            body += f"\nMessage from organizer:\n{invitation.message}"

        body += f"""

Please respond to this invitation:
- Accept
- Decline
- Tentative

[Accept] [Decline] [Maybe]
"""

        print(f"[EMAIL INVITATION] To: {invitation.attendee_email}")
        print(f"Subject: {subject}")
        print(f"Body: {body}")

        return True

    def send_invitations_for_event(
        self,
        event_id: str,
        message: Optional[str] = None,
    ) -> List[Invitation]:
        """
        Send invitations to all attendees of an event.

        Args:
            event_id: Event ID
            message: Optional message to include

        Returns:
            List of sent invitations
        """
        event = self.event_manager.get_event(event_id)
        if not event:
            return []

        sent_invitations = []

        for attendee in event.attendees:
            # Skip organizer
            if attendee.organizer:
                continue

            # Create and send invitation
            invitation = self.create_invitation(event, attendee, message)
            if self.send_invitation(invitation.id):
                sent_invitations.append(invitation)

        return sent_invitations

    def respond_to_invitation(
        self,
        invitation_id: str,
        response: AttendeeStatus,
        comment: Optional[str] = None,
    ) -> bool:
        """
        Respond to an invitation.

        Args:
            invitation_id: Invitation ID
            response: Response status
            comment: Optional comment

        Returns:
            True if response recorded successfully
        """
        invitation = self._invitations.get(invitation_id)
        if not invitation:
            return False

        # Update invitation
        invitation.response_status = response
        invitation.status = InviteStatus.RESPONDED
        invitation.responded_at = datetime.now()
        invitation.response_comment = comment

        # Update attendee status in event
        success = self.event_manager.update_attendee_status(
            event_id=invitation.event_id,
            email=invitation.attendee_email,
            status=response,
        )

        # Notify organizer
        if success:
            self._notify_organizer_of_response(invitation)

        return success

    def _notify_organizer_of_response(self, invitation: Invitation) -> None:
        """
        Notify organizer of an RSVP response.

        Args:
            invitation: Invitation with response
        """
        # TODO: Integrate with email module
        response_text = {
            AttendeeStatus.ACCEPTED: "accepted",
            AttendeeStatus.DECLINED: "declined",
            AttendeeStatus.TENTATIVE: "tentatively accepted",
        }.get(invitation.response_status, "responded to")

        subject = f"RSVP: {invitation.attendee_email} {response_text} {invitation.event_title}"

        body = f"""
{invitation.attendee_email} has {response_text} your invitation to:

Event: {invitation.event_title}
When: {invitation.event_start.strftime('%A, %B %d, %Y at %I:%M %p')}
"""

        if invitation.response_comment:
            body += f"\nComment: {invitation.response_comment}"

        print(f"[ORGANIZER NOTIFICATION] To: {invitation.organizer}")
        print(f"Subject: {subject}")
        print(f"Body: {body}")

    def accept_invitation(
        self,
        invitation_id: str,
        comment: Optional[str] = None,
    ) -> bool:
        """
        Accept an invitation.

        Args:
            invitation_id: Invitation ID
            comment: Optional comment

        Returns:
            True if accepted successfully
        """
        return self.respond_to_invitation(
            invitation_id=invitation_id,
            response=AttendeeStatus.ACCEPTED,
            comment=comment,
        )

    def decline_invitation(
        self,
        invitation_id: str,
        comment: Optional[str] = None,
    ) -> bool:
        """
        Decline an invitation.

        Args:
            invitation_id: Invitation ID
            comment: Optional comment

        Returns:
            True if declined successfully
        """
        return self.respond_to_invitation(
            invitation_id=invitation_id,
            response=AttendeeStatus.DECLINED,
            comment=comment,
        )

    def tentative_invitation(
        self,
        invitation_id: str,
        comment: Optional[str] = None,
    ) -> bool:
        """
        Tentatively accept an invitation.

        Args:
            invitation_id: Invitation ID
            comment: Optional comment

        Returns:
            True if response recorded successfully
        """
        return self.respond_to_invitation(
            invitation_id=invitation_id,
            response=AttendeeStatus.TENTATIVE,
            comment=comment,
        )

    def mark_invitation_viewed(
        self,
        invitation_id: str,
    ) -> bool:
        """
        Mark an invitation as viewed.

        Args:
            invitation_id: Invitation ID

        Returns:
            True if marked successfully
        """
        invitation = self._invitations.get(invitation_id)
        if not invitation:
            return False

        if invitation.status == InviteStatus.SENT:
            invitation.status = InviteStatus.VIEWED
            invitation.viewed_at = datetime.now()

        return True

    def get_pending_invitations(
        self,
        attendee_email: str,
    ) -> List[Invitation]:
        """
        Get pending invitations for an attendee.

        Args:
            attendee_email: Attendee email

        Returns:
            List of pending invitations
        """
        pending = []

        for invitation in self._invitations.values():
            if (invitation.attendee_email == attendee_email and
                invitation.response_status == AttendeeStatus.NEEDS_ACTION and
                invitation.event_start > datetime.now()):
                pending.append(invitation)

        # Sort by event start time
        pending.sort(key=lambda i: i.event_start)

        return pending

    def get_invitations_for_event(
        self,
        event_id: str,
    ) -> List[Invitation]:
        """
        Get all invitations for an event.

        Args:
            event_id: Event ID

        Returns:
            List of invitations
        """
        return [
            inv for inv in self._invitations.values()
            if inv.event_id == event_id
        ]

    def get_invitation_summary(
        self,
        event_id: str,
    ) -> Dict[str, Any]:
        """
        Get summary of invitation responses for an event.

        Args:
            event_id: Event ID

        Returns:
            Summary with response counts
        """
        invitations = self.get_invitations_for_event(event_id)

        accepted = sum(1 for i in invitations if i.response_status == AttendeeStatus.ACCEPTED)
        declined = sum(1 for i in invitations if i.response_status == AttendeeStatus.DECLINED)
        tentative = sum(1 for i in invitations if i.response_status == AttendeeStatus.TENTATIVE)
        pending = sum(1 for i in invitations if i.response_status == AttendeeStatus.NEEDS_ACTION)

        return {
            "total_invitations": len(invitations),
            "accepted": accepted,
            "declined": declined,
            "tentative": tentative,
            "pending": pending,
            "response_rate": ((accepted + declined + tentative) / len(invitations) * 100)
                             if len(invitations) > 0 else 0,
        }

    def set_guest_permissions(
        self,
        event_id: str,
        permissions: List[GuestPermission],
    ) -> None:
        """
        Set guest permissions for an event.

        Args:
            event_id: Event ID
            permissions: List of permissions to grant
        """
        self._guest_permissions[event_id] = permissions

    def get_guest_permissions(
        self,
        event_id: str,
    ) -> List[GuestPermission]:
        """
        Get guest permissions for an event.

        Args:
            event_id: Event ID

        Returns:
            List of permissions
        """
        return self._guest_permissions.get(event_id, [GuestPermission.NONE])

    def can_guest_invite_others(
        self,
        event_id: str,
    ) -> bool:
        """
        Check if guests can invite others to an event.

        Args:
            event_id: Event ID

        Returns:
            True if guests can invite others
        """
        permissions = self.get_guest_permissions(event_id)
        return GuestPermission.INVITE_OTHERS in permissions

    def send_invitation_reminder(
        self,
        invitation_id: str,
    ) -> bool:
        """
        Send a reminder for a pending invitation.

        Args:
            invitation_id: Invitation ID

        Returns:
            True if reminder sent successfully
        """
        invitation = self._invitations.get(invitation_id)
        if not invitation:
            return False

        if invitation.response_status != AttendeeStatus.NEEDS_ACTION:
            return False

        # Send reminder email
        subject = f"Reminder: Please respond to invitation for {invitation.event_title}"

        body = f"""
This is a reminder to respond to the invitation for:

Event: {invitation.event_title}
When: {invitation.event_start.strftime('%A, %B %d, %Y at %I:%M %p')}
Organizer: {invitation.organizer}

Please respond as soon as possible.

[Accept] [Decline] [Maybe]
"""

        print(f"[INVITATION REMINDER] To: {invitation.attendee_email}")
        print(f"Subject: {subject}")
        print(f"Body: {body}")

        return True

    def send_reminders_for_pending_invitations(
        self,
        event_id: str,
    ) -> int:
        """
        Send reminders for all pending invitations to an event.

        Args:
            event_id: Event ID

        Returns:
            Number of reminders sent
        """
        invitations = self.get_invitations_for_event(event_id)

        sent = 0
        for invitation in invitations:
            if invitation.response_status == AttendeeStatus.NEEDS_ACTION:
                if self.send_invitation_reminder(invitation.id):
                    sent += 1

        return sent
