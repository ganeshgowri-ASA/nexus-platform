"""
NEXUS Translation Module

Provides comprehensive translation services including:
- Text and document translation
- Real-time translation
- Language detection
- Glossary management
- Batch translation
- Quality scoring
- 100+ language support
"""

__version__ = "1.0.0"
__author__ = "NEXUS Platform"

from .config import TranslationConfig
from .constants import SUPPORTED_LANGUAGES, SUPPORTED_FILE_FORMATS

__all__ = [
    "TranslationConfig",
    "SUPPORTED_LANGUAGES",
    "SUPPORTED_FILE_FORMATS",
]
