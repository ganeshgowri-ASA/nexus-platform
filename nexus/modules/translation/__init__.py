"""
Translation Module for NEXUS Platform

Production-ready translation system with:
- Multi-engine support (Google, DeepL, Azure, AWS, OpenAI, Claude)
- Language detection
- Translation memory
- Glossary management
- Quality assessment
- Document translation
- Real-time translation
- Caching and optimization
"""

from .translator import Translator, BatchTranslator, StreamingTranslator
from .engines import (
    GoogleTranslateEngine,
    DeepLEngine,
    AzureTranslatorEngine,
    AWSTranslateEngine,
    OpenAITranslateEngine,
    ClaudeTranslateEngine,
)
from .language_detection import LanguageDetector
from .glossary import GlossaryManager
from .quality import QualityAssessment
from .cache import TranslationCache
from .memory import TranslationMemoryManager

__all__ = [
    "Translator",
    "BatchTranslator",
    "StreamingTranslator",
    "GoogleTranslateEngine",
    "DeepLEngine",
    "AzureTranslatorEngine",
    "AWSTranslateEngine",
    "OpenAITranslateEngine",
    "ClaudeTranslateEngine",
    "LanguageDetector",
    "GlossaryManager",
    "QualityAssessment",
    "TranslationCache",
    "TranslationMemoryManager",
]

__version__ = "1.0.0"
