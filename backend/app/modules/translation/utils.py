"""Translation utility functions"""
from typing import Dict, List, Tuple
import re


# Common language codes and names
SUPPORTED_LANGUAGES = {
    "en": "English",
    "es": "Spanish",
    "fr": "French",
    "de": "German",
    "it": "Italian",
    "pt": "Portuguese",
    "ru": "Russian",
    "ja": "Japanese",
    "ko": "Korean",
    "zh": "Chinese (Simplified)",
    "zh-TW": "Chinese (Traditional)",
    "ar": "Arabic",
    "hi": "Hindi",
    "bn": "Bengali",
    "pa": "Punjabi",
    "te": "Telugu",
    "mr": "Marathi",
    "ta": "Tamil",
    "ur": "Urdu",
    "gu": "Gujarati",
    "kn": "Kannada",
    "ml": "Malayalam",
    "nl": "Dutch",
    "pl": "Polish",
    "sv": "Swedish",
    "no": "Norwegian",
    "da": "Danish",
    "fi": "Finnish",
    "tr": "Turkish",
    "el": "Greek",
    "cs": "Czech",
    "hu": "Hungarian",
    "ro": "Romanian",
    "th": "Thai",
    "vi": "Vietnamese",
    "id": "Indonesian",
    "ms": "Malay",
    "fil": "Filipino",
    "uk": "Ukrainian",
    "bg": "Bulgarian",
    "hr": "Croatian",
    "sr": "Serbian",
    "sk": "Slovak",
    "sl": "Slovenian",
    "lt": "Lithuanian",
    "lv": "Latvian",
    "et": "Estonian",
    "he": "Hebrew",
    "fa": "Persian",
    "sw": "Swahili",
    "af": "Afrikaans",
}


def get_supported_languages() -> List[Dict[str, str]]:
    """Get list of supported languages"""
    return [{"code": code, "name": name} for code, name in SUPPORTED_LANGUAGES.items()]


def validate_language_code(code: str) -> bool:
    """Validate if language code is supported"""
    return code in SUPPORTED_LANGUAGES or code == "auto"


def get_language_name(code: str) -> str:
    """Get language name from code"""
    return SUPPORTED_LANGUAGES.get(code, code)


def split_text_into_chunks(text: str, max_length: int = 5000) -> List[str]:
    """Split long text into chunks for translation"""
    if len(text) <= max_length:
        return [text]

    chunks = []
    current_chunk = ""

    # Split by paragraphs first
    paragraphs = text.split("\n\n")

    for paragraph in paragraphs:
        if len(current_chunk) + len(paragraph) + 2 <= max_length:
            current_chunk += paragraph + "\n\n"
        else:
            if current_chunk:
                chunks.append(current_chunk.strip())
            current_chunk = paragraph + "\n\n"

    if current_chunk:
        chunks.append(current_chunk.strip())

    return chunks


def calculate_quality_score(
    source_text: str,
    translated_text: str,
    confidence: float
) -> float:
    """Calculate translation quality score based on various metrics"""
    # Basic quality metrics
    score = confidence * 100

    # Penalize if lengths are very different (might indicate issues)
    length_ratio = len(translated_text) / len(source_text) if len(source_text) > 0 else 1
    if length_ratio < 0.5 or length_ratio > 2.0:
        score *= 0.9

    # Check if translation is just the same as source
    if source_text.strip() == translated_text.strip():
        score *= 0.8

    # Bonus for proper punctuation preservation
    source_punct = set(re.findall(r'[.,!?;:]', source_text))
    trans_punct = set(re.findall(r'[.,!?;:]', translated_text))
    if source_punct == trans_punct:
        score *= 1.1

    return min(score, 100.0)


def apply_glossary(text: str, glossary: Dict[str, str]) -> Tuple[str, int]:
    """Apply glossary terms to translated text"""
    replacements = 0

    for term, translation in glossary.items():
        # Case-insensitive replacement with word boundaries
        pattern = re.compile(r'\b' + re.escape(term) + r'\b', re.IGNORECASE)
        new_text = pattern.sub(translation, text)

        if new_text != text:
            replacements += len(pattern.findall(text))
            text = new_text

    return text, replacements


def detect_language_simple(text: str) -> Tuple[str, float]:
    """Simple language detection fallback"""
    # This is a very basic fallback
    # In production, use proper language detection library
    try:
        from langdetect import detect, detect_langs

        detected = detect(text)
        langs = detect_langs(text)

        confidence = next((lang.prob for lang in langs if lang.lang == detected), 0.5)

        return detected, confidence

    except Exception:
        # If langdetect fails, default to English
        return "en", 0.5


def format_translation_metadata(
    source_lang: str,
    target_lang: str,
    service: str,
    processing_time: float,
    character_count: int
) -> Dict[str, any]:
    """Format translation metadata"""
    return {
        "source_language": source_lang,
        "target_language": target_lang,
        "service": service,
        "processing_time_seconds": round(processing_time, 3),
        "character_count": character_count,
        "estimated_cost": calculate_estimated_cost(character_count, service)
    }


def calculate_estimated_cost(character_count: int, service: str) -> float:
    """Calculate estimated cost based on character count"""
    # Rough estimates (in USD per 1M characters)
    rates = {
        "google": 20.0,
        "deepl": 25.0,
        "anthropic": 15.0
    }

    rate = rates.get(service, 20.0)
    return (character_count / 1_000_000) * rate


def validate_glossary_entries(entries: Dict[str, str]) -> Tuple[bool, List[str]]:
    """Validate glossary entries"""
    errors = []

    if not entries:
        errors.append("Glossary must have at least one entry")

    for term, translation in entries.items():
        if not term or not term.strip():
            errors.append("Glossary term cannot be empty")

        if not translation or not translation.strip():
            errors.append(f"Translation for term '{term}' cannot be empty")

        if len(term) > 200:
            errors.append(f"Term '{term}' exceeds maximum length of 200 characters")

    return len(errors) == 0, errors
