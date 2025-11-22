"""Utility functions for search operations."""

import logging
import re
from datetime import datetime
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


def clean_html(text: str) -> str:
    """Remove HTML tags from text."""
    import bleach
    return bleach.clean(text, tags=[], strip=True)


def extract_keywords(text: str, max_keywords: int = 10) -> List[str]:
    """Extract keywords from text (simple implementation)."""
    # Remove special characters and convert to lowercase
    cleaned = re.sub(r'[^a-zA-Z0-9\s]', '', text.lower())

    # Split into words
    words = cleaned.split()

    # Remove common stop words
    stop_words = {
        'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
        'of', 'with', 'is', 'was', 'are', 'were', 'been', 'be', 'have', 'has',
        'had', 'do', 'does', 'did', 'will', 'would', 'should', 'could', 'may',
        'might', 'can', 'this', 'that', 'these', 'those', 'it', 'its', 'from',
    }

    keywords = [word for word in words if word not in stop_words and len(word) > 3]

    # Count frequency and return top keywords
    keyword_freq: Dict[str, int] = {}
    for keyword in keywords:
        keyword_freq[keyword] = keyword_freq.get(keyword, 0) + 1

    # Sort by frequency
    sorted_keywords = sorted(keyword_freq.items(), key=lambda x: x[1], reverse=True)

    return [kw for kw, _ in sorted_keywords[:max_keywords]]


def truncate_text(text: str, max_length: int = 200) -> str:
    """Truncate text to max length with ellipsis."""
    if len(text) <= max_length:
        return text

    return text[:max_length - 3] + "..."


def highlight_text(text: str, query: str) -> str:
    """Highlight query terms in text."""
    if not query:
        return text

    # Split query into terms
    terms = query.lower().split()

    # Highlight each term
    highlighted = text
    for term in terms:
        pattern = re.compile(re.escape(term), re.IGNORECASE)
        highlighted = pattern.sub(f"<mark>{term}</mark>", highlighted)

    return highlighted


def format_file_size(size_bytes: int) -> str:
    """Format file size in human-readable format."""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f} PB"


def parse_date_range(date_str: str) -> Optional[datetime]:
    """Parse various date formats."""
    formats = [
        "%Y-%m-%d",
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%dT%H:%M:%S.%f",
        "%Y-%m-%d %H:%M:%S",
        "%m/%d/%Y",
        "%d/%m/%Y",
    ]

    for fmt in formats:
        try:
            return datetime.strptime(date_str, fmt)
        except ValueError:
            continue

    return None


def sanitize_query(query: str) -> str:
    """Sanitize search query to prevent injection."""
    # Remove special Elasticsearch query characters
    special_chars = ['\\', '/', '+', '-', '=', '&&', '||', '>', '<', '!', '(', ')', '{', '}', '[', ']', '^', '"', '~', '*', '?', ':']

    sanitized = query
    for char in special_chars:
        sanitized = sanitized.replace(char, f'\\{char}')

    return sanitized


def build_query_suggestion(query: str, results_count: int) -> Optional[str]:
    """Generate query suggestion if results are poor."""
    if results_count > 10:
        return None

    # Simple suggestions
    if len(query) < 3:
        return "Try using more specific keywords"

    # Check for common typos (simplified)
    words = query.lower().split()
    if any(len(word) > 15 for word in words):
        return "Check for typos in your query"

    if results_count == 0:
        return "Try using different keywords or broader terms"

    return None


class SearchLogger:
    """Logger for search queries and results."""

    def __init__(self):
        """Initialize search logger."""
        self.logger = logging.getLogger("search_queries")

    def log_search(
        self,
        query: str,
        results_count: int,
        took_ms: int,
        user_id: Optional[str] = None,
        filters: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Log a search query."""
        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "query": query,
            "results_count": results_count,
            "took_ms": took_ms,
            "user_id": user_id,
            "filters": filters,
        }

        self.logger.info(f"Search query: {log_data}")

    def log_click(
        self,
        query: str,
        document_id: str,
        position: int,
        user_id: Optional[str] = None,
    ) -> None:
        """Log a search result click."""
        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "query": query,
            "document_id": document_id,
            "position": position,
            "user_id": user_id,
        }

        self.logger.info(f"Search click: {log_data}")


# Global search logger
search_logger = SearchLogger()
