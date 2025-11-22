"""Application constants and enums"""

# Presentation Themes
PRESENTATION_THEMES = {
    'Modern Blue': {
        'background': '#FFFFFF',
        'title': '#1E3A8A',
        'text': '#1F2937',
        'accent': '#3B82F6'
    },
    'Corporate': {
        'background': '#F9FAFB',
        'title': '#111827',
        'text': '#374151',
        'accent': '#6B7280'
    },
    'Vibrant': {
        'background': '#FFFFFF',
        'title': '#7C3AED',
        'text': '#1F2937',
        'accent': '#EC4899'
    },
    'Dark': {
        'background': '#1F2937',
        'title': '#F3F4F6',
        'text': '#E5E7EB',
        'accent': '#60A5FA'
    },
}

# Project Status
PROJECT_STATUS = [
    'Not Started',
    'Planning',
    'In Progress',
    'On Hold',
    'Completed',
    'Cancelled'
]

# Task Priority
TASK_PRIORITY = [
    'Low',
    'Medium',
    'High',
    'Critical'
]

# Email Categories
EMAIL_CATEGORIES = [
    'Primary',
    'Social',
    'Promotions',
    'Updates',
    'Spam'
]

# CRM Deal Stages
CRM_DEAL_STAGES = [
    'Lead',
    'Qualified',
    'Proposal',
    'Negotiation',
    'Closed Won',
    'Closed Lost'
]

# CRM Contact Types
CRM_CONTACT_TYPES = [
    'Lead',
    'Customer',
    'Partner',
    'Vendor',
    'Other'
]

# Calendar Event Types
CALENDAR_EVENT_TYPES = [
    'Meeting',
    'Call',
    'Task',
    'Reminder',
    'Appointment',
    'Deadline'
]

# Recurrence Patterns
RECURRENCE_PATTERNS = [
    'None',
    'Daily',
    'Weekly',
    'Monthly',
    'Yearly'
]

# Chat Room Types
CHAT_ROOM_TYPES = [
    'Direct Message',
    'Group Chat',
    'Project Channel',
    'Announcement'
]

# Note Categories
NOTE_CATEGORIES = [
    'Personal',
    'Work',
    'Ideas',
    'Meeting Notes',
    'Research',
    'To-Do'
]

# Export Formats
EXPORT_FORMATS = {
    'powerpoint': ['PPTX', 'PDF'],
    'email': ['EML', 'PDF', 'HTML'],
    'notes': ['PDF', 'DOCX', 'MD', 'HTML'],
    'projects': ['PDF', 'XLSX', 'JSON'],
    'calendar': ['ICS', 'PDF'],
    'crm': ['XLSX', 'CSV', 'PDF']
}
