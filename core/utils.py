"""
Utility functions for the NEXUS platform.
"""
import re
import hashlib
from datetime import datetime
from typing import Dict, List, Tuple
from config.constants import READING_SPEED_WPM


def count_words(text: str) -> int:
    """
    Count words in text.

    Args:
        text: Input text

    Returns:
        Word count
    """
    if not text:
        return 0
    # Remove extra whitespace and split
    words = text.split()
    return len(words)


def count_characters(text: str, include_spaces: bool = True) -> int:
    """
    Count characters in text.

    Args:
        text: Input text
        include_spaces: Whether to include spaces in count

    Returns:
        Character count
    """
    if not text:
        return 0
    if include_spaces:
        return len(text)
    return len(text.replace(" ", "").replace("\n", "").replace("\t", ""))


def estimate_reading_time(text: str, wpm: int = READING_SPEED_WPM) -> Dict[str, int]:
    """
    Estimate reading time for text.

    Args:
        text: Input text
        wpm: Words per minute reading speed

    Returns:
        Dictionary with minutes and seconds
    """
    word_count = count_words(text)
    total_minutes = word_count / wpm
    minutes = int(total_minutes)
    seconds = int((total_minutes - minutes) * 60)
    return {"minutes": minutes, "seconds": seconds}


def format_reading_time(text: str) -> str:
    """
    Format reading time as a string.

    Args:
        text: Input text

    Returns:
        Formatted reading time (e.g., "5 min read")
    """
    time_dict = estimate_reading_time(text)
    minutes = time_dict["minutes"]
    seconds = time_dict["seconds"]

    if minutes == 0:
        return f"{seconds} sec read"
    elif seconds < 30:
        return f"{minutes} min read"
    else:
        return f"{minutes + 1} min read"


def sanitize_filename(filename: str) -> str:
    """
    Sanitize filename to be safe for file system.

    Args:
        filename: Original filename

    Returns:
        Sanitized filename
    """
    # Remove invalid characters
    filename = re.sub(r'[<>:"/\\|?*]', "", filename)
    # Replace spaces with underscores
    filename = filename.replace(" ", "_")
    # Limit length
    if len(filename) > 255:
        name, ext = filename.rsplit(".", 1) if "." in filename else (filename, "")
        name = name[:255 - len(ext) - 1]
        filename = f"{name}.{ext}" if ext else name
    return filename


def generate_document_id() -> str:
    """
    Generate a unique document ID.

    Returns:
        Unique document ID
    """
    timestamp = datetime.now().isoformat()
    hash_obj = hashlib.sha256(timestamp.encode())
    return hash_obj.hexdigest()[:16]


def extract_headings(text: str) -> List[Dict[str, str]]:
    """
    Extract headings from text (markdown format).

    Args:
        text: Input text with markdown headings

    Returns:
        List of dictionaries with heading info
    """
    headings = []
    lines = text.split("\n")

    for i, line in enumerate(lines):
        # Match markdown headings
        match = re.match(r"^(#{1,6})\s+(.+)$", line)
        if match:
            level = len(match.group(1))
            title = match.group(2).strip()
            headings.append({
                "level": level,
                "title": title,
                "line": i + 1,
            })

    return headings


def format_file_size(size_bytes: int) -> str:
    """
    Format file size in human-readable format.

    Args:
        size_bytes: Size in bytes

    Returns:
        Formatted size string
    """
    for unit in ["B", "KB", "MB", "GB"]:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f} TB"


def validate_email(email: str) -> bool:
    """
    Validate email address format.

    Args:
        email: Email address

    Returns:
        True if valid, False otherwise
    """
    pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    return bool(re.match(pattern, email))


def validate_url(url: str) -> bool:
    """
    Validate URL format.

    Args:
        url: URL string

    Returns:
        True if valid, False otherwise
    """
    pattern = r"^https?://[^\s/$.?#].[^\s]*$"
    return bool(re.match(pattern, url))


def truncate_text(text: str, max_length: int = 100, suffix: str = "...") -> str:
    """
    Truncate text to maximum length.

    Args:
        text: Input text
        max_length: Maximum length
        suffix: Suffix to add when truncated

    Returns:
        Truncated text
    """
    if len(text) <= max_length:
        return text
    return text[:max_length - len(suffix)] + suffix


def highlight_text(text: str, query: str) -> str:
    """
    Highlight search query in text (HTML).

    Args:
        text: Input text
        query: Search query

    Returns:
        Text with highlighted query
    """
    if not query:
        return text
    pattern = re.compile(f"({re.escape(query)})", re.IGNORECASE)
    return pattern.sub(r'<mark>\1</mark>', text)


def calculate_similarity(text1: str, text2: str) -> float:
    """
    Calculate simple similarity between two texts.

    Args:
        text1: First text
        text2: Second text

    Returns:
        Similarity score (0-1)
    """
    words1 = set(text1.lower().split())
    words2 = set(text2.lower().split())

    if not words1 or not words2:
        return 0.0

    intersection = words1.intersection(words2)
    union = words1.union(words2)

    return len(intersection) / len(union)


def get_timestamp() -> str:
    """
    Get current timestamp in ISO format.

    Returns:
        ISO formatted timestamp
    """
    return datetime.now().isoformat()


def parse_markdown_links(text: str) -> List[Tuple[str, str]]:
    """
    Extract markdown links from text.

    Args:
        text: Input text with markdown links

    Returns:
        List of tuples (link_text, url)
    """
    pattern = r"\[([^\]]+)\]\(([^\)]+)\)"
    matches = re.findall(pattern, text)
    return matches


def strip_html_tags(html: str) -> str:
    """
    Strip HTML tags from text.

    Args:
        html: HTML string

    Returns:
        Plain text
    """
    clean = re.compile("<.*?>")
    return re.sub(clean, "", html)
