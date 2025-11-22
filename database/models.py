"""Database models for all NEXUS Platform applications."""
from datetime import datetime
from sqlalchemy import (
    Column, String, Integer, Text, DateTime, Boolean,
    Float, ForeignKey, JSON
)
from sqlalchemy.orm import relationship
import uuid

# Import Base from connection to ensure single declarative base
from database.connection import Base


def generate_uuid():
    """Generate unique ID"""
    return str(uuid.uuid4())


# Base Model with common fields
class BaseModel(Base):
    __abstract__ = True

    id = Column(String, primary_key=True, default=generate_uuid)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


# ============================================
# POWERPOINT / PRESENTATION MODELS
# ============================================

class Presentation(BaseModel):
    __tablename__ = 'presentations'

    title = Column(String, nullable=False)
    theme = Column(String, default='Modern Blue')
    description = Column(Text)
    author = Column(String)
    slides_count = Column(Integer, default=0)


class Slide(BaseModel):
    __tablename__ = 'slides'

    presentation_id = Column(String, ForeignKey('presentations.id', ondelete='CASCADE'))
    slide_number = Column(Integer, nullable=False)
    title = Column(String)
    content = Column(Text)
    layout = Column(String, default='title_and_content')
    notes = Column(Text)
    background_color = Column(String)

    presentation = relationship("Presentation", backref="slides")


# ============================================
# EMAIL MODELS
# ============================================

class EmailMessage(BaseModel):
    __tablename__ = 'email_messages'

    subject = Column(String, nullable=False)
    sender = Column(String, nullable=False)
    recipients = Column(JSON)
    cc = Column(JSON)
    bcc = Column(JSON)
    body = Column(Text)
    html_body = Column(Text)
    is_draft = Column(Boolean, default=False)
    is_sent = Column(Boolean, default=False)
    is_read = Column(Boolean, default=False)
    is_starred = Column(Boolean, default=False)
    category = Column(String, default='Primary')
    thread_id = Column(String)
    parent_id = Column(String, ForeignKey('email_messages.id'))
    attachments = Column(JSON)


class EmailDraft(BaseModel):
    __tablename__ = 'email_drafts'

    subject = Column(String)
    recipients = Column(JSON)
    body = Column(Text)
    attachments = Column(JSON)


# ============================================
# CHAT MODELS
# ============================================

class ChatRoom(BaseModel):
    __tablename__ = 'chat_rooms'

    name = Column(String, nullable=False)
    description = Column(Text)
    room_type = Column(String, default='Group Chat')
    members = Column(JSON)
    is_active = Column(Boolean, default=True)
    avatar = Column(String)


class ChatMessage(BaseModel):
    __tablename__ = 'chat_messages'

    room_id = Column(String, ForeignKey('chat_rooms.id', ondelete='CASCADE'))
    sender = Column(String, nullable=False)
    message = Column(Text, nullable=False)
    message_type = Column(String, default='text')
    attachments = Column(JSON)
    reactions = Column(JSON)
    is_edited = Column(Boolean, default=False)
    is_deleted = Column(Boolean, default=False)

    room = relationship("ChatRoom", backref="messages")


# ============================================
# PROJECT MANAGEMENT MODELS
# ============================================

class Project(BaseModel):
    __tablename__ = 'projects'

    name = Column(String, nullable=False)
    description = Column(Text)
    status = Column(String, default='Planning')
    start_date = Column(DateTime)
    end_date = Column(DateTime)
    progress = Column(Float, default=0.0)
    owner = Column(String)
    team_members = Column(JSON)
    budget = Column(Float)
    tags = Column(JSON)


class Task(BaseModel):
    __tablename__ = 'tasks'

    project_id = Column(String, ForeignKey('projects.id', ondelete='CASCADE'))
    title = Column(String, nullable=False)
    description = Column(Text)
    status = Column(String, default='Not Started')
    priority = Column(String, default='Medium')
    assignee = Column(String)
    start_date = Column(DateTime)
    due_date = Column(DateTime)
    completed_date = Column(DateTime)
    progress = Column(Float, default=0.0)
    dependencies = Column(JSON)
    estimated_hours = Column(Float)
    actual_hours = Column(Float)

    project = relationship("Project", backref="tasks")


class Milestone(BaseModel):
    __tablename__ = 'milestones'

    project_id = Column(String, ForeignKey('projects.id', ondelete='CASCADE'))
    title = Column(String, nullable=False)
    description = Column(Text)
    due_date = Column(DateTime)
    is_completed = Column(Boolean, default=False)
    completion_date = Column(DateTime)

    project = relationship("Project", backref="milestones")


# ============================================
# CALENDAR MODELS
# ============================================

class CalendarEvent(BaseModel):
    __tablename__ = 'calendar_events'

    title = Column(String, nullable=False)
    description = Column(Text)
    event_type = Column(String, default='Meeting')
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime, nullable=False)
    location = Column(String)
    attendees = Column(JSON)
    is_all_day = Column(Boolean, default=False)
    recurrence_pattern = Column(String, default='None')
    recurrence_end = Column(DateTime)
    reminder_minutes = Column(Integer, default=15)
    color = Column(String)
    organizer = Column(String)


# ============================================
# VIDEO CONFERENCE MODELS
# ============================================

class VideoConference(BaseModel):
    __tablename__ = 'video_conferences'

    title = Column(String, nullable=False)
    description = Column(Text)
    host = Column(String, nullable=False)
    participants = Column(JSON)
    scheduled_time = Column(DateTime)
    duration_minutes = Column(Integer)
    status = Column(String, default='Scheduled')
    recording_url = Column(String)
    is_recording = Column(Boolean, default=False)
    room_id = Column(String, unique=True)


class ConferenceRecording(BaseModel):
    __tablename__ = 'conference_recordings'

    conference_id = Column(String, ForeignKey('video_conferences.id', ondelete='CASCADE'))
    file_path = Column(String, nullable=False)
    duration_seconds = Column(Integer)
    file_size_mb = Column(Float)

    conference = relationship("VideoConference", backref="recordings")


# ============================================
# NOTES MODELS
# ============================================

class Note(BaseModel):
    __tablename__ = 'notes'

    title = Column(String, nullable=False)
    content = Column(Text)
    folder = Column(String, default='General')
    tags = Column(JSON)
    category = Column(String, default='Personal')
    is_favorite = Column(Boolean, default=False)
    is_archived = Column(Boolean, default=False)
    color = Column(String)
    ai_summary = Column(Text)
    author = Column(String)


# ============================================
# CRM MODELS
# ============================================

class CRMContact(BaseModel):
    __tablename__ = 'crm_contacts'

    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    email = Column(String)
    phone = Column(String)
    company = Column(String)
    job_title = Column(String)
    contact_type = Column(String, default='Lead')
    address = Column(Text)
    notes = Column(Text)
    tags = Column(JSON)
    linkedin_url = Column(String)
    twitter_url = Column(String)
    website = Column(String)
    source = Column(String)
    owner = Column(String)


class CRMDeal(BaseModel):
    __tablename__ = 'crm_deals'

    contact_id = Column(String, ForeignKey('crm_contacts.id', ondelete='CASCADE'))
    title = Column(String, nullable=False)
    description = Column(Text)
    value = Column(Float)
    currency = Column(String, default='USD')
    stage = Column(String, default='Lead')
    probability = Column(Float, default=0.0)
    expected_close_date = Column(DateTime)
    actual_close_date = Column(DateTime)
    owner = Column(String)
    tags = Column(JSON)

    contact = relationship("CRMContact", backref="deals")


class CRMActivity(BaseModel):
    __tablename__ = 'crm_activities'

    contact_id = Column(String, ForeignKey('crm_contacts.id', ondelete='CASCADE'))
    deal_id = Column(String, ForeignKey('crm_deals.id', ondelete='SET NULL'))
    activity_type = Column(String, nullable=False)
    subject = Column(String)
    description = Column(Text)
    due_date = Column(DateTime)
    completed_date = Column(DateTime)
    is_completed = Column(Boolean, default=False)
    owner = Column(String)

    contact = relationship("CRMContact", backref="activities")
    deal = relationship("CRMDeal", backref="activities")
