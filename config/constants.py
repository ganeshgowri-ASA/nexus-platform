"""
Application constants and enums for NEXUS Platform.

Centralized constants used across all modules.
"""

# ============================================
# PRESENTATION / POWERPOINT CONSTANTS
# ============================================

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

# ============================================
# PROJECT MANAGEMENT CONSTANTS
# ============================================

PROJECT_STATUS = [
    'Not Started',
    'Planning',
    'In Progress',
    'On Hold',
    'Completed',
    'Cancelled'
]

TASK_PRIORITY = [
    'Low',
    'Medium',
    'High',
    'Critical'
]

TASK_STATUS = [
    'Not Started',
    'In Progress',
    'Review',
    'Completed',
    'Blocked'
]

# ============================================
# EMAIL CONSTANTS
# ============================================

EMAIL_CATEGORIES = [
    'Primary',
    'Social',
    'Promotions',
    'Updates',
    'Spam'
]

# ============================================
# CRM CONSTANTS
# ============================================

CRM_DEAL_STAGES = [
    'Lead',
    'Qualified',
    'Proposal',
    'Negotiation',
    'Closed Won',
    'Closed Lost'
]

CRM_CONTACT_TYPES = [
    'Lead',
    'Customer',
    'Partner',
    'Vendor',
    'Other'
]

# ============================================
# CALENDAR CONSTANTS
# ============================================

CALENDAR_EVENT_TYPES = [
    'Meeting',
    'Call',
    'Task',
    'Reminder',
    'Appointment',
    'Deadline'
]

RECURRENCE_PATTERNS = [
    'None',
    'Daily',
    'Weekly',
    'Monthly',
    'Yearly'
]

# ============================================
# CHAT CONSTANTS
# ============================================

CHAT_ROOM_TYPES = [
    'Direct Message',
    'Group Chat',
    'Project Channel',
    'Announcement'
]

# ============================================
# NOTES CONSTANTS
# ============================================

NOTE_CATEGORIES = [
    'Personal',
    'Work',
    'Ideas',
    'Meeting Notes',
    'Research',
    'To-Do'
]

# ============================================
# EXPORT FORMATS
# ============================================

EXPORT_FORMATS = {
    'powerpoint': ['PPTX', 'PDF'],
    'email': ['EML', 'PDF', 'HTML'],
    'notes': ['PDF', 'DOCX', 'MD', 'HTML'],
    'projects': ['PDF', 'XLSX', 'JSON'],
    'calendar': ['ICS', 'PDF'],
    'crm': ['XLSX', 'CSV', 'PDF']
}

# ============================================
# WORD PROCESSOR CONSTANTS
# ============================================

FONTS = [
    "Arial",
    "Times New Roman",
    "Calibri",
    "Georgia",
    "Verdana",
    "Helvetica",
    "Courier New",
    "Comic Sans MS",
    "Impact",
    "Trebuchet MS",
]

FONT_SIZES = [8, 9, 10, 11, 12, 14, 16, 18, 20, 22, 24, 26, 28, 36, 48, 72]

HEADING_STYLES = {
    "Normal": {"size": 12, "bold": False},
    "Heading 1": {"size": 24, "bold": True},
    "Heading 2": {"size": 20, "bold": True},
    "Heading 3": {"size": 16, "bold": True},
    "Heading 4": {"size": 14, "bold": True},
    "Heading 5": {"size": 12, "bold": True},
    "Heading 6": {"size": 11, "bold": True},
}

TEXT_COLORS = {
    "Black": "#000000",
    "White": "#FFFFFF",
    "Red": "#FF0000",
    "Green": "#00FF00",
    "Blue": "#0000FF",
    "Yellow": "#FFFF00",
    "Cyan": "#00FFFF",
    "Magenta": "#FF00FF",
    "Gray": "#808080",
    "Orange": "#FFA500",
    "Purple": "#800080",
    "Brown": "#A52A2A",
}

TEMPLATE_TYPES = [
    "Blank Document",
    "Business Letter",
    "Resume",
    "Report",
    "Meeting Notes",
    "Project Proposal",
    "Essay",
    "Cover Letter",
]

# ============================================
# MODULE NAMES
# ============================================

MODULES = {
    "word": "Word Editor",
    "excel": "Excel Analyzer",
    "powerpoint": "PowerPoint Creator",
    "pdf": "PDF Manager",
    "project": "Project Manager",
    "email": "Email Client",
    "chat": "AI Chat Assistant",
    "flowchart": "Flowchart Designer",
    "analytics": "Analytics Dashboard",
    "meetings": "Meeting Scheduler",
    "crm": "CRM",
    "calendar": "Calendar",
    "notes": "Notes",
    "video_conference": "Video Conference",
}

# ============================================
# FILE SIZE LIMITS
# ============================================

MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB
ALLOWED_FILE_TYPES = [".csv", ".xlsx", ".json", ".pdf", ".docx", ".pptx"]

# ============================================
# PAGINATION
# ============================================

DEFAULT_PAGE_SIZE = 20
MAX_PAGE_SIZE = 100

# ============================================
# CACHE TTL (in seconds)
# ============================================

CACHE_TTL_SHORT = 300  # 5 minutes
CACHE_TTL_MEDIUM = 1800  # 30 minutes
CACHE_TTL_LONG = 3600  # 1 hour
