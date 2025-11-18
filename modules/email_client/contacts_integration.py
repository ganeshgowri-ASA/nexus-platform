"""
Contacts Integration

Address book and contact management for email client.
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, Set
from uuid import uuid4

logger = logging.getLogger(__name__)


@dataclass
class Contact:
    """Contact information."""
    contact_id: str = field(default_factory=lambda: str(uuid4()))

    # Basic info
    email_address: str = ""
    display_name: str = ""
    first_name: str = ""
    last_name: str = ""

    # Additional emails
    alternate_emails: List[str] = field(default_factory=list)

    # Contact details
    phone_numbers: List[str] = field(default_factory=list)
    company: str = ""
    job_title: str = ""
    notes: str = ""

    # Organization
    groups: Set[str] = field(default_factory=set)
    tags: Set[str] = field(default_factory=set)

    # Metadata
    avatar_url: Optional[str] = None
    is_favorite: bool = False
    interaction_count: int = 0  # Number of emails exchanged
    last_interaction: Optional[datetime] = None

    # Social
    linkedin_url: Optional[str] = None
    twitter_handle: Optional[str] = None

    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class ContactGroup:
    """Contact group/distribution list."""
    group_id: str = field(default_factory=lambda: str(uuid4()))
    name: str = ""
    description: str = ""
    members: Set[str] = field(default_factory=set)  # Contact IDs
    color: str = "#0066cc"
    created_at: datetime = field(default_factory=datetime.utcnow)


class ContactsManager:
    """
    Contacts and address book manager.

    Manages contacts, groups, and provides autocomplete functionality.
    """

    def __init__(self, db_connection: Optional[Any] = None):
        """
        Initialize contacts manager.

        Args:
            db_connection: Database connection for storing contacts
        """
        self.db_connection = db_connection
        self.contacts: Dict[str, Contact] = {}
        self.groups: Dict[str, ContactGroup] = {}
        self.email_to_contact: Dict[str, str] = {}  # Email -> Contact ID mapping
        self.recent_contacts: List[str] = []  # Recent contact IDs

    async def add_contact(self, contact: Contact) -> str:
        """
        Add a new contact.

        Args:
            contact: Contact to add

        Returns:
            str: Contact ID
        """
        # Store contact
        self.contacts[contact.contact_id] = contact

        # Index by email
        self.email_to_contact[contact.email_address.lower()] = contact.contact_id

        # Index alternate emails
        for email in contact.alternate_emails:
            self.email_to_contact[email.lower()] = contact.contact_id

        logger.info(f"Added contact: {contact.display_name or contact.email_address}")
        return contact.contact_id

    async def update_contact(self, contact: Contact) -> bool:
        """Update an existing contact."""
        if contact.contact_id in self.contacts:
            contact.updated_at = datetime.utcnow()
            self.contacts[contact.contact_id] = contact

            # Update email index
            self._reindex_contact(contact)

            return True
        return False

    def _reindex_contact(self, contact: Contact) -> None:
        """Reindex a contact's emails."""
        # Remove old mappings
        to_remove = [
            email for email, cid in self.email_to_contact.items()
            if cid == contact.contact_id
        ]
        for email in to_remove:
            del self.email_to_contact[email]

        # Add new mappings
        self.email_to_contact[contact.email_address.lower()] = contact.contact_id
        for email in contact.alternate_emails:
            self.email_to_contact[email.lower()] = contact.contact_id

    async def delete_contact(self, contact_id: str) -> bool:
        """Delete a contact."""
        if contact_id in self.contacts:
            contact = self.contacts[contact_id]

            # Remove from email index
            self.email_to_contact = {
                email: cid for email, cid in self.email_to_contact.items()
                if cid != contact_id
            }

            # Remove from contacts
            del self.contacts[contact_id]

            # Remove from recent
            if contact_id in self.recent_contacts:
                self.recent_contacts.remove(contact_id)

            return True
        return False

    async def get_contact(self, contact_id: str) -> Optional[Contact]:
        """Get a contact by ID."""
        return self.contacts.get(contact_id)

    async def get_contact_by_email(self, email: str) -> Optional[Contact]:
        """
        Get a contact by email address.

        Args:
            email: Email address

        Returns:
            Optional[Contact]: Contact if found
        """
        contact_id = self.email_to_contact.get(email.lower())
        if contact_id:
            return self.contacts.get(contact_id)
        return None

    async def find_or_create_contact(self, email: str, name: str = "") -> Contact:
        """
        Find existing contact or create a new one.

        Args:
            email: Email address
            name: Display name

        Returns:
            Contact: Existing or new contact
        """
        # Try to find existing
        contact = await self.get_contact_by_email(email)
        if contact:
            return contact

        # Create new contact
        contact = Contact(
            email_address=email,
            display_name=name or email
        )

        await self.add_contact(contact)
        return contact

    async def search_contacts(self, query: str) -> List[Contact]:
        """
        Search contacts.

        Args:
            query: Search query

        Returns:
            List[Contact]: Matching contacts
        """
        query = query.lower()
        results = []

        for contact in self.contacts.values():
            # Search in name, email, company
            searchable = ' '.join([
                contact.email_address,
                contact.display_name,
                contact.first_name,
                contact.last_name,
                contact.company
            ]).lower()

            if query in searchable:
                results.append(contact)

        # Sort by interaction count (most frequent first)
        results.sort(key=lambda c: c.interaction_count, reverse=True)

        return results

    async def autocomplete(self, prefix: str, limit: int = 10) -> List[Contact]:
        """
        Get autocomplete suggestions.

        Args:
            prefix: Search prefix
            limit: Maximum results

        Returns:
            List[Contact]: Suggested contacts
        """
        prefix = prefix.lower()
        suggestions = []

        # First, check recent contacts
        for contact_id in reversed(self.recent_contacts):
            if len(suggestions) >= limit:
                break

            contact = self.contacts.get(contact_id)
            if contact:
                searchable = f"{contact.display_name} {contact.email_address}".lower()
                if prefix in searchable:
                    suggestions.append(contact)

        # Then search all contacts
        if len(suggestions) < limit:
            for contact in self.contacts.values():
                if len(suggestions) >= limit:
                    break

                if contact.contact_id in [c.contact_id for c in suggestions]:
                    continue

                searchable = f"{contact.display_name} {contact.email_address}".lower()
                if prefix in searchable:
                    suggestions.append(contact)

        return suggestions[:limit]

    async def record_interaction(self, email_address: str) -> None:
        """
        Record an interaction with a contact.

        Args:
            email_address: Contact's email address
        """
        contact = await self.get_contact_by_email(email_address)
        if not contact:
            # Create new contact
            contact = await self.find_or_create_contact(email_address)

        # Update interaction stats
        contact.interaction_count += 1
        contact.last_interaction = datetime.utcnow()

        # Add to recent contacts
        if contact.contact_id in self.recent_contacts:
            self.recent_contacts.remove(contact.contact_id)
        self.recent_contacts.append(contact.contact_id)

        # Keep only last 100 recent contacts
        if len(self.recent_contacts) > 100:
            self.recent_contacts = self.recent_contacts[-100:]

    async def get_recent_contacts(self, limit: int = 20) -> List[Contact]:
        """
        Get recent contacts.

        Args:
            limit: Maximum results

        Returns:
            List[Contact]: Recent contacts
        """
        contacts = []
        for contact_id in reversed(self.recent_contacts[-limit:]):
            contact = self.contacts.get(contact_id)
            if contact:
                contacts.append(contact)
        return contacts

    async def get_frequent_contacts(self, limit: int = 20) -> List[Contact]:
        """
        Get most frequently contacted.

        Args:
            limit: Maximum results

        Returns:
            List[Contact]: Frequent contacts
        """
        contacts = list(self.contacts.values())
        contacts.sort(key=lambda c: c.interaction_count, reverse=True)
        return contacts[:limit]

    async def get_favorites(self) -> List[Contact]:
        """Get favorite contacts."""
        return [c for c in self.contacts.values() if c.is_favorite]

    async def set_favorite(self, contact_id: str, is_favorite: bool = True) -> bool:
        """Set/unset contact as favorite."""
        contact = self.contacts.get(contact_id)
        if contact:
            contact.is_favorite = is_favorite
            return True
        return False

    # Group management

    async def create_group(self, group: ContactGroup) -> str:
        """
        Create a contact group.

        Args:
            group: Contact group

        Returns:
            str: Group ID
        """
        self.groups[group.group_id] = group
        logger.info(f"Created contact group: {group.name}")
        return group.group_id

    async def update_group(self, group: ContactGroup) -> bool:
        """Update a contact group."""
        if group.group_id in self.groups:
            self.groups[group.group_id] = group
            return True
        return False

    async def delete_group(self, group_id: str) -> bool:
        """Delete a contact group."""
        if group_id in self.groups:
            del self.groups[group_id]
            return True
        return False

    async def add_to_group(self, contact_id: str, group_id: str) -> bool:
        """Add a contact to a group."""
        group = self.groups.get(group_id)
        contact = self.contacts.get(contact_id)

        if group and contact:
            group.members.add(contact_id)
            contact.groups.add(group_id)
            return True
        return False

    async def remove_from_group(self, contact_id: str, group_id: str) -> bool:
        """Remove a contact from a group."""
        group = self.groups.get(group_id)
        contact = self.contacts.get(contact_id)

        if group and contact:
            group.members.discard(contact_id)
            contact.groups.discard(group_id)
            return True
        return False

    async def get_group_contacts(self, group_id: str) -> List[Contact]:
        """Get all contacts in a group."""
        group = self.groups.get(group_id)
        if not group:
            return []

        contacts = []
        for contact_id in group.members:
            contact = self.contacts.get(contact_id)
            if contact:
                contacts.append(contact)

        return contacts

    async def list_groups(self) -> List[ContactGroup]:
        """List all contact groups."""
        return list(self.groups.values())

    # Import/Export

    async def import_contacts(self, contacts_data: List[Dict[str, Any]]) -> int:
        """
        Import contacts from data.

        Args:
            contacts_data: List of contact dicts

        Returns:
            int: Number of contacts imported
        """
        count = 0

        for data in contacts_data:
            try:
                contact = Contact(**data)
                await self.add_contact(contact)
                count += 1
            except Exception as e:
                logger.error(f"Failed to import contact: {e}")

        logger.info(f"Imported {count} contacts")
        return count

    async def export_contacts(self) -> List[Dict[str, Any]]:
        """
        Export all contacts.

        Returns:
            List[Dict]: Contact data
        """
        contacts_data = []

        for contact in self.contacts.values():
            data = {
                'email_address': contact.email_address,
                'display_name': contact.display_name,
                'first_name': contact.first_name,
                'last_name': contact.last_name,
                'alternate_emails': list(contact.alternate_emails),
                'phone_numbers': list(contact.phone_numbers),
                'company': contact.company,
                'job_title': contact.job_title,
                'notes': contact.notes,
            }
            contacts_data.append(data)

        return contacts_data

    def get_contact_statistics(self) -> Dict[str, Any]:
        """Get contacts statistics."""
        return {
            'total_contacts': len(self.contacts),
            'total_groups': len(self.groups),
            'recent_contacts': len(self.recent_contacts),
            'favorite_contacts': len([c for c in self.contacts.values() if c.is_favorite]),
            'contacts_with_phone': len([c for c in self.contacts.values() if c.phone_numbers]),
            'contacts_with_company': len([c for c in self.contacts.values() if c.company]),
        }
