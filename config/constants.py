<<<<<<< HEAD
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
=======
"""
Constants for the NEXUS platform.
"""

# Module Names
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
}

# Word Editor Constants
WORD_EDITOR = {
    "max_chars": 1_000_000,
    "auto_save_interval": 30,  # seconds
    "default_font": "Arial",
    "default_font_size": 12,
    "supported_export_formats": ["pdf", "docx", "html", "markdown", "txt"],
    "supported_import_formats": ["docx", "html", "markdown", "txt"],
}

# Font Options
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

# Font Sizes
FONT_SIZES = [8, 9, 10, 11, 12, 14, 16, 18, 20, 22, 24, 26, 28, 36, 48, 72]

# Heading Levels
HEADING_STYLES = {
    "Normal": {"size": 12, "bold": False},
    "Heading 1": {"size": 24, "bold": True},
    "Heading 2": {"size": 20, "bold": True},
    "Heading 3": {"size": 16, "bold": True},
    "Heading 4": {"size": 14, "bold": True},
    "Heading 5": {"size": 12, "bold": True},
    "Heading 6": {"size": 11, "bold": True},
}

# Text Colors
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

# AI Feature Prompts
AI_PROMPTS = {
    "grammar_check": "Check the following text for grammar and spelling errors. Provide corrections and explanations:\n\n{text}",
    "summarize": "Summarize the following text concisely while preserving key points:\n\n{text}",
    "expand": "Expand on the following text with more details and examples:\n\n{text}",
    "tone_professional": "Rewrite the following text in a professional tone:\n\n{text}",
    "tone_casual": "Rewrite the following text in a casual, friendly tone:\n\n{text}",
    "tone_formal": "Rewrite the following text in a formal tone:\n\n{text}",
    "writing_assistant": "Provide suggestions to improve the following text:\n\n{text}",
    "autocomplete": "Continue writing based on the following text:\n\n{text}",
    "outline": "Create an outline for a document about: {topic}",
}

# Document Templates
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

# Export PDF Settings
PDF_SETTINGS = {
    "page_sizes": ["A4", "Letter", "Legal", "A3"],
    "margins": {
        "narrow": {"top": 0.5, "bottom": 0.5, "left": 0.5, "right": 0.5},
        "normal": {"top": 1.0, "bottom": 1.0, "left": 1.0, "right": 1.0},
        "wide": {"top": 1.0, "bottom": 1.0, "left": 2.0, "right": 2.0},
    },
    "orientations": ["portrait", "landscape"],
}

# Collaborative Features
COLLABORATION = {
    "max_concurrent_users": 50,
    "cursor_colors": [
        "#FF6B6B", "#4ECDC4", "#45B7D1", "#FFA07A", "#98D8C8",
        "#F7DC6F", "#BB8FCE", "#85C1E2", "#F8B195", "#A8E6CF"
    ],
    "comment_max_length": 1000,
}

# Version History
VERSION_HISTORY = {
    "max_versions": 100,
    "auto_version_interval": 300,  # seconds (5 minutes)
}

# Reading Time Calculation (words per minute)
READING_SPEED_WPM = 200
>>>>>>> origin/claude/word-editor-module-01PPyUEeNUgZmU4swtfxgoCB
