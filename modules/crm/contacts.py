"""
CRM Contacts Module - Full contact management with profiles, custom fields, tags, and segments.
"""

from typing import Dict, List, Optional, Any, Set
from datetime import datetime, date
from dataclasses import dataclass, field, asdict
from enum import Enum
import json
import csv
import io
from pathlib import Path
import hashlib


class ContactStatus(Enum):
    """Contact status types."""
    LEAD = "lead"
    PROSPECT = "prospect"
    CUSTOMER = "customer"
    PARTNER = "partner"
    INACTIVE = "inactive"


class LeadSource(Enum):
    """Lead source types."""
    WEBSITE = "website"
    REFERRAL = "referral"
    SOCIAL_MEDIA = "social_media"
    COLD_OUTREACH = "cold_outreach"
    EVENT = "event"
    PARTNER = "partner"
    ADVERTISEMENT = "advertisement"
    OTHER = "other"


@dataclass
class CustomField:
    """Custom field definition."""
    name: str
    field_type: str  # text, number, date, boolean, picklist
    value: Any
    options: Optional[List[str]] = None  # For picklist type


@dataclass
class ContactAddress:
    """Contact address information."""
    street: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    postal_code: Optional[str] = None
    country: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)


@dataclass
class SocialProfile:
    """Social media profile information."""
    linkedin: Optional[str] = None
    twitter: Optional[str] = None
    facebook: Optional[str] = None
    instagram: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)


@dataclass
class Contact:
    """Contact entity with full profile support."""
    id: str
    first_name: str
    last_name: str
    email: str
    phone: Optional[str] = None
    mobile: Optional[str] = None
    title: Optional[str] = None
    company_id: Optional[str] = None
    company_name: Optional[str] = None
    status: ContactStatus = ContactStatus.LEAD
    lead_source: Optional[LeadSource] = None
    owner_id: Optional[str] = None

    # Address
    address: Optional[ContactAddress] = None

    # Social profiles
    social_profiles: Optional[SocialProfile] = None

    # Additional info
    website: Optional[str] = None
    description: Optional[str] = None

    # Metadata
    tags: Set[str] = field(default_factory=set)
    segments: Set[str] = field(default_factory=set)
    custom_fields: Dict[str, CustomField] = field(default_factory=dict)

    # Scoring
    lead_score: int = 0

    # Timestamps
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    last_contacted: Optional[datetime] = None

    # Engagement metrics
    email_opens: int = 0
    email_clicks: int = 0
    meetings_count: int = 0

    @property
    def full_name(self) -> str:
        """Get full name."""
        return f"{self.first_name} {self.last_name}"

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        data = {
            'id': self.id,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'email': self.email,
            'phone': self.phone,
            'mobile': self.mobile,
            'title': self.title,
            'company_id': self.company_id,
            'company_name': self.company_name,
            'status': self.status.value,
            'lead_source': self.lead_source.value if self.lead_source else None,
            'owner_id': self.owner_id,
            'address': self.address.to_dict() if self.address else None,
            'social_profiles': self.social_profiles.to_dict() if self.social_profiles else None,
            'website': self.website,
            'description': self.description,
            'tags': list(self.tags),
            'segments': list(self.segments),
            'custom_fields': {k: asdict(v) for k, v in self.custom_fields.items()},
            'lead_score': self.lead_score,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'last_contacted': self.last_contacted.isoformat() if self.last_contacted else None,
            'email_opens': self.email_opens,
            'email_clicks': self.email_clicks,
            'meetings_count': self.meetings_count,
        }
        return data


class ContactManager:
    """Manage contacts with full CRUD operations and advanced features."""

    def __init__(self):
        """Initialize contact manager."""
        self.contacts: Dict[str, Contact] = {}
        self._email_index: Dict[str, str] = {}  # email -> contact_id
        self._company_index: Dict[str, List[str]] = {}  # company_id -> [contact_ids]
        self._tag_index: Dict[str, Set[str]] = {}  # tag -> {contact_ids}
        self._segment_index: Dict[str, Set[str]] = {}  # segment -> {contact_ids}

    def create_contact(self, contact: Contact) -> Contact:
        """Create a new contact."""
        # Check for duplicates
        if contact.email in self._email_index:
            raise ValueError(f"Contact with email {contact.email} already exists")

        self.contacts[contact.id] = contact
        self._email_index[contact.email] = contact.id

        # Update indexes
        if contact.company_id:
            if contact.company_id not in self._company_index:
                self._company_index[contact.company_id] = []
            self._company_index[contact.company_id].append(contact.id)

        for tag in contact.tags:
            if tag not in self._tag_index:
                self._tag_index[tag] = set()
            self._tag_index[tag].add(contact.id)

        for segment in contact.segments:
            if segment not in self._segment_index:
                self._segment_index[segment] = set()
            self._segment_index[segment].add(contact.id)

        return contact

    def get_contact(self, contact_id: str) -> Optional[Contact]:
        """Get a contact by ID."""
        return self.contacts.get(contact_id)

    def get_contact_by_email(self, email: str) -> Optional[Contact]:
        """Get a contact by email."""
        contact_id = self._email_index.get(email)
        return self.contacts.get(contact_id) if contact_id else None

    def update_contact(self, contact_id: str, updates: Dict[str, Any]) -> Optional[Contact]:
        """Update a contact."""
        contact = self.contacts.get(contact_id)
        if not contact:
            return None

        # Handle email update
        if 'email' in updates and updates['email'] != contact.email:
            if updates['email'] in self._email_index:
                raise ValueError(f"Contact with email {updates['email']} already exists")
            del self._email_index[contact.email]
            self._email_index[updates['email']] = contact_id

        # Handle company update
        if 'company_id' in updates:
            if contact.company_id and contact.company_id in self._company_index:
                self._company_index[contact.company_id].remove(contact_id)
            if updates['company_id']:
                if updates['company_id'] not in self._company_index:
                    self._company_index[updates['company_id']] = []
                self._company_index[updates['company_id']].append(contact_id)

        # Update fields
        for key, value in updates.items():
            if hasattr(contact, key):
                # Handle enum conversions
                if key == 'status' and isinstance(value, str):
                    value = ContactStatus(value)
                elif key == 'lead_source' and isinstance(value, str):
                    value = LeadSource(value)
                setattr(contact, key, value)

        contact.updated_at = datetime.now()
        return contact

    def delete_contact(self, contact_id: str) -> bool:
        """Delete a contact."""
        contact = self.contacts.get(contact_id)
        if not contact:
            return False

        # Remove from indexes
        del self._email_index[contact.email]

        if contact.company_id and contact.company_id in self._company_index:
            self._company_index[contact.company_id].remove(contact_id)

        for tag in contact.tags:
            if tag in self._tag_index:
                self._tag_index[tag].discard(contact_id)

        for segment in contact.segments:
            if segment in self._segment_index:
                self._segment_index[segment].discard(contact_id)

        del self.contacts[contact_id]
        return True

    def list_contacts(
        self,
        status: Optional[ContactStatus] = None,
        tags: Optional[List[str]] = None,
        segments: Optional[List[str]] = None,
        company_id: Optional[str] = None,
        owner_id: Optional[str] = None,
        limit: Optional[int] = None,
        offset: int = 0
    ) -> List[Contact]:
        """List contacts with filtering."""
        results = list(self.contacts.values())

        # Apply filters
        if status:
            results = [c for c in results if c.status == status]

        if tags:
            results = [c for c in results if any(tag in c.tags for tag in tags)]

        if segments:
            results = [c for c in results if any(seg in c.segments for seg in segments)]

        if company_id:
            results = [c for c in results if c.company_id == company_id]

        if owner_id:
            results = [c for c in results if c.owner_id == owner_id]

        # Sort by updated_at descending
        results.sort(key=lambda c: c.updated_at, reverse=True)

        # Apply pagination
        if limit:
            results = results[offset:offset + limit]
        else:
            results = results[offset:]

        return results

    def search_contacts(self, query: str) -> List[Contact]:
        """Search contacts by name, email, or company."""
        query_lower = query.lower()
        results = []

        for contact in self.contacts.values():
            if (query_lower in contact.first_name.lower() or
                query_lower in contact.last_name.lower() or
                query_lower in contact.email.lower() or
                (contact.company_name and query_lower in contact.company_name.lower())):
                results.append(contact)

        return results

    def add_tags(self, contact_id: str, tags: List[str]) -> Optional[Contact]:
        """Add tags to a contact."""
        contact = self.contacts.get(contact_id)
        if not contact:
            return None

        for tag in tags:
            contact.tags.add(tag)
            if tag not in self._tag_index:
                self._tag_index[tag] = set()
            self._tag_index[tag].add(contact_id)

        contact.updated_at = datetime.now()
        return contact

    def remove_tags(self, contact_id: str, tags: List[str]) -> Optional[Contact]:
        """Remove tags from a contact."""
        contact = self.contacts.get(contact_id)
        if not contact:
            return None

        for tag in tags:
            contact.tags.discard(tag)
            if tag in self._tag_index:
                self._tag_index[tag].discard(contact_id)

        contact.updated_at = datetime.now()
        return contact

    def add_to_segment(self, contact_id: str, segment: str) -> Optional[Contact]:
        """Add contact to a segment."""
        contact = self.contacts.get(contact_id)
        if not contact:
            return None

        contact.segments.add(segment)
        if segment not in self._segment_index:
            self._segment_index[segment] = set()
        self._segment_index[segment].add(contact_id)

        contact.updated_at = datetime.now()
        return contact

    def remove_from_segment(self, contact_id: str, segment: str) -> Optional[Contact]:
        """Remove contact from a segment."""
        contact = self.contacts.get(contact_id)
        if not contact:
            return None

        contact.segments.discard(segment)
        if segment in self._segment_index:
            self._segment_index[segment].discard(contact_id)

        contact.updated_at = datetime.now()
        return contact

    def get_contacts_by_tag(self, tag: str) -> List[Contact]:
        """Get all contacts with a specific tag."""
        contact_ids = self._tag_index.get(tag, set())
        return [self.contacts[cid] for cid in contact_ids if cid in self.contacts]

    def get_contacts_by_segment(self, segment: str) -> List[Contact]:
        """Get all contacts in a segment."""
        contact_ids = self._segment_index.get(segment, set())
        return [self.contacts[cid] for cid in contact_ids if cid in self.contacts]

    def set_custom_field(
        self,
        contact_id: str,
        field_name: str,
        field_type: str,
        value: Any,
        options: Optional[List[str]] = None
    ) -> Optional[Contact]:
        """Set a custom field on a contact."""
        contact = self.contacts.get(contact_id)
        if not contact:
            return None

        custom_field = CustomField(
            name=field_name,
            field_type=field_type,
            value=value,
            options=options
        )
        contact.custom_fields[field_name] = custom_field
        contact.updated_at = datetime.now()
        return contact

    def deduplicate_contacts(self) -> List[Dict[str, Any]]:
        """Find and merge duplicate contacts based on email and name similarity."""
        duplicates = []
        email_groups: Dict[str, List[str]] = {}

        # Group by email
        for contact in self.contacts.values():
            email_key = contact.email.lower()
            if email_key not in email_groups:
                email_groups[email_key] = []
            email_groups[email_key].append(contact.id)

        # Find duplicates
        for email, contact_ids in email_groups.items():
            if len(contact_ids) > 1:
                duplicates.append({
                    'email': email,
                    'contact_ids': contact_ids,
                    'contacts': [self.contacts[cid].to_dict() for cid in contact_ids]
                })

        return duplicates

    def merge_contacts(self, primary_id: str, duplicate_ids: List[str]) -> Optional[Contact]:
        """Merge duplicate contacts into a primary contact."""
        primary = self.contacts.get(primary_id)
        if not primary:
            return None

        for dup_id in duplicate_ids:
            duplicate = self.contacts.get(dup_id)
            if not duplicate or dup_id == primary_id:
                continue

            # Merge tags
            primary.tags.update(duplicate.tags)

            # Merge segments
            primary.segments.update(duplicate.segments)

            # Merge custom fields
            for field_name, field_value in duplicate.custom_fields.items():
                if field_name not in primary.custom_fields:
                    primary.custom_fields[field_name] = field_value

            # Update engagement metrics
            primary.email_opens += duplicate.email_opens
            primary.email_clicks += duplicate.email_clicks
            primary.meetings_count += duplicate.meetings_count

            # Keep the earliest created_at
            if duplicate.created_at < primary.created_at:
                primary.created_at = duplicate.created_at

            # Delete duplicate
            self.delete_contact(dup_id)

        primary.updated_at = datetime.now()
        return primary

    def export_to_csv(self, contacts: Optional[List[Contact]] = None) -> str:
        """Export contacts to CSV format."""
        if contacts is None:
            contacts = list(self.contacts.values())

        output = io.StringIO()
        if not contacts:
            return ""

        # Define CSV fields
        fieldnames = [
            'id', 'first_name', 'last_name', 'email', 'phone', 'mobile',
            'title', 'company_name', 'status', 'lead_source', 'lead_score',
            'tags', 'segments', 'created_at', 'updated_at'
        ]

        writer = csv.DictWriter(output, fieldnames=fieldnames)
        writer.writeheader()

        for contact in contacts:
            row = {
                'id': contact.id,
                'first_name': contact.first_name,
                'last_name': contact.last_name,
                'email': contact.email,
                'phone': contact.phone or '',
                'mobile': contact.mobile or '',
                'title': contact.title or '',
                'company_name': contact.company_name or '',
                'status': contact.status.value,
                'lead_source': contact.lead_source.value if contact.lead_source else '',
                'lead_score': contact.lead_score,
                'tags': ','.join(contact.tags),
                'segments': ','.join(contact.segments),
                'created_at': contact.created_at.isoformat(),
                'updated_at': contact.updated_at.isoformat(),
            }
            writer.writerow(row)

        return output.getvalue()

    def import_from_csv(self, csv_content: str) -> Dict[str, Any]:
        """Import contacts from CSV format."""
        input_stream = io.StringIO(csv_content)
        reader = csv.DictReader(input_stream)

        imported = 0
        skipped = 0
        errors = []

        for row in reader:
            try:
                # Check if contact exists
                existing = self.get_contact_by_email(row['email'])
                if existing:
                    skipped += 1
                    continue

                # Create contact
                contact = Contact(
                    id=row.get('id', self._generate_id()),
                    first_name=row['first_name'],
                    last_name=row['last_name'],
                    email=row['email'],
                    phone=row.get('phone') or None,
                    mobile=row.get('mobile') or None,
                    title=row.get('title') or None,
                    company_name=row.get('company_name') or None,
                    status=ContactStatus(row['status']) if row.get('status') else ContactStatus.LEAD,
                    lead_source=LeadSource(row['lead_source']) if row.get('lead_source') else None,
                    lead_score=int(row.get('lead_score', 0)),
                    tags=set(row.get('tags', '').split(',')) if row.get('tags') else set(),
                    segments=set(row.get('segments', '').split(',')) if row.get('segments') else set(),
                )

                self.create_contact(contact)
                imported += 1
            except Exception as e:
                errors.append(f"Row {reader.line_num}: {str(e)}")
                skipped += 1

        return {
            'imported': imported,
            'skipped': skipped,
            'errors': errors
        }

    def _generate_id(self) -> str:
        """Generate a unique contact ID."""
        import uuid
        return f"contact_{uuid.uuid4().hex[:12]}"

    def get_statistics(self) -> Dict[str, Any]:
        """Get contact statistics."""
        total = len(self.contacts)
        by_status = {}
        by_source = {}

        for contact in self.contacts.values():
            # Count by status
            status_key = contact.status.value
            by_status[status_key] = by_status.get(status_key, 0) + 1

            # Count by source
            if contact.lead_source:
                source_key = contact.lead_source.value
                by_source[source_key] = by_source.get(source_key, 0) + 1

        return {
            'total_contacts': total,
            'by_status': by_status,
            'by_source': by_source,
            'total_tags': len(self._tag_index),
            'total_segments': len(self._segment_index),
            'total_companies': len(self._company_index),
        }
