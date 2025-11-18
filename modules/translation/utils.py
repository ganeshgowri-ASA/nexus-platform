"""
Utility functions for the translation module
"""

import hashlib
import json
from typing import Any, Dict, Optional
from datetime import datetime
import os


def generate_cache_key(
    text: str,
    source_language: str,
    target_language: str,
    provider: str
) -> str:
    """
    Generate a cache key for translation

    Args:
        text: Source text
        source_language: Source language code
        target_language: Target language code
        provider: Translation provider

    Returns:
        Cache key string
    """
    content = f"{text}:{source_language}:{target_language}:{provider}"
    return hashlib.md5(content.encode()).hexdigest()


def validate_language_code(language_code: str) -> bool:
    """
    Validate language code format

    Args:
        language_code: Language code to validate

    Returns:
        True if valid, False otherwise
    """
    from .constants import SUPPORTED_LANGUAGES
    return language_code in SUPPORTED_LANGUAGES


def format_translation_response(
    source_text: str,
    translated_text: str,
    source_language: str,
    target_language: str,
    provider: str,
    quality_score: Optional[float] = None,
    metadata: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Format translation response

    Args:
        source_text: Original text
        translated_text: Translated text
        source_language: Source language code
        target_language: Target language code
        provider: Translation provider
        quality_score: Quality score
        metadata: Additional metadata

    Returns:
        Formatted response dictionary
    """
    response = {
        'source_text': source_text,
        'translated_text': translated_text,
        'source_language': source_language,
        'target_language': target_language,
        'provider': provider,
        'character_count': len(source_text),
        'timestamp': datetime.utcnow().isoformat()
    }

    if quality_score is not None:
        response['quality_score'] = quality_score

    if metadata:
        response['metadata'] = metadata

    return response


def extract_text_from_file(file_path: str, file_type: str) -> str:
    """
    Extract text from various file types

    Args:
        file_path: Path to the file
        file_type: Type of the file (txt, pdf, docx, etc.)

    Returns:
        Extracted text

    Raises:
        ValueError: If file type is not supported
    """
    if file_type == 'txt':
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()

    elif file_type == 'json':
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return json.dumps(data, indent=2)

    elif file_type == 'csv':
        import csv
        with open(file_path, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            return '\n'.join([','.join(row) for row in reader])

    elif file_type == 'pdf':
        try:
            import PyPDF2
            with open(file_path, 'rb') as f:
                pdf_reader = PyPDF2.PdfReader(f)
                text = ''
                for page in pdf_reader.pages:
                    text += page.extract_text()
                return text
        except ImportError:
            raise ValueError("PyPDF2 is required for PDF file processing")

    elif file_type in ['docx', 'doc']:
        try:
            from docx import Document
            doc = Document(file_path)
            return '\n'.join([paragraph.text for paragraph in doc.paragraphs])
        except ImportError:
            raise ValueError("python-docx is required for DOCX file processing")

    else:
        raise ValueError(f"Unsupported file type: {file_type}")


def save_translation_to_file(
    translated_text: str,
    output_path: str,
    file_type: str = 'txt'
) -> str:
    """
    Save translated text to file

    Args:
        translated_text: Translated text
        output_path: Output file path
        file_type: Output file type

    Returns:
        Path to the saved file
    """
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    if file_type == 'txt':
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(translated_text)

    elif file_type == 'json':
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump({'translated_text': translated_text}, f, ensure_ascii=False, indent=2)

    else:
        raise ValueError(f"Unsupported output file type: {file_type}")

    return output_path


def calculate_estimated_cost(
    character_count: int,
    provider: str
) -> Dict[str, Any]:
    """
    Calculate estimated translation cost

    Args:
        character_count: Number of characters
        provider: Translation provider

    Returns:
        Cost estimation dictionary
    """
    # Pricing per million characters (approximate)
    pricing = {
        'google': 20.0,  # $20 per million characters
        'deepl': 25.0    # $25 per million characters (DeepL API Pro)
    }

    price_per_million = pricing.get(provider, 20.0)
    estimated_cost = (character_count / 1_000_000) * price_per_million

    return {
        'character_count': character_count,
        'provider': provider,
        'estimated_cost_usd': round(estimated_cost, 4),
        'price_per_million': price_per_million
    }


def sanitize_text(text: str, max_length: Optional[int] = None) -> str:
    """
    Sanitize text for translation

    Args:
        text: Text to sanitize
        max_length: Maximum length

    Returns:
        Sanitized text
    """
    # Remove null bytes
    text = text.replace('\x00', '')

    # Normalize whitespace
    text = ' '.join(text.split())

    # Truncate if necessary
    if max_length and len(text) > max_length:
        text = text[:max_length]

    return text


def chunk_text(text: str, max_chunk_size: int = 5000, overlap: int = 100) -> list:
    """
    Split text into chunks for translation

    Args:
        text: Text to split
        max_chunk_size: Maximum size of each chunk
        overlap: Number of characters to overlap between chunks

    Returns:
        List of text chunks
    """
    if len(text) <= max_chunk_size:
        return [text]

    chunks = []
    start = 0

    while start < len(text):
        end = start + max_chunk_size

        # Try to break at sentence boundary
        if end < len(text):
            # Look for sentence endings
            for delimiter in ['. ', '! ', '? ', '\n']:
                last_delim = text[start:end].rfind(delimiter)
                if last_delim != -1:
                    end = start + last_delim + len(delimiter)
                    break

        chunk = text[start:end]
        chunks.append(chunk)

        start = end - overlap

    return chunks


def merge_chunks(chunks: list) -> str:
    """
    Merge translated chunks back together

    Args:
        chunks: List of translated chunks

    Returns:
        Merged text
    """
    return ' '.join(chunks)
