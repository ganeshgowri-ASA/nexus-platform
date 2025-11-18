"""NEXUS Voice Assistant Module.

A comprehensive voice assistant with speech recognition, text-to-speech,
natural language processing, and voice command execution.
"""

__version__ = "1.0.0"
__author__ = "NEXUS Team"

from .services.speech_to_text import SpeechToTextService
from .services.text_to_speech import TextToSpeechService
from .services.audio_processor import AudioProcessor
from .nlp.intent_recognizer import IntentRecognizer
from .nlp.entity_extractor import EntityExtractor
from .nlp.context_manager import ContextManager
from .utils.command_processor import CommandProcessor
from .utils.command_registry import CommandRegistry

__all__ = [
    'SpeechToTextService',
    'TextToSpeechService',
    'AudioProcessor',
    'IntentRecognizer',
    'EntityExtractor',
    'ContextManager',
    'CommandProcessor',
    'CommandRegistry'
]
