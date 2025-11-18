"""
SEO utility functions.

Common SEO-related utility functions for URL parsing,
content analysis, and meta tag extraction.
"""

import re
from typing import Dict, List, Optional, Tuple
from urllib.parse import urlparse, urljoin, urlunparse

from bs4 import BeautifulSoup
import validators


def extract_domain(url: str) -> Optional[str]:
    """
    Extract domain from URL.

    Args:
        url: URL to parse

    Returns:
        Domain name or None if invalid

    Example:
        >>> extract_domain("https://www.example.com/path")
        "example.com"
    """
    try:
        parsed = urlparse(url)
        domain = parsed.netloc or parsed.path
        # Remove www prefix
        if domain.startswith("www."):
            domain = domain[4:]
        return domain.lower() if domain else None
    except Exception:
        return None


def normalize_url(url: str, base_url: Optional[str] = None) -> Optional[str]:
    """
    Normalize URL to standard format.

    Args:
        url: URL to normalize
        base_url: Base URL for relative URLs

    Returns:
        Normalized URL or None if invalid

    Example:
        >>> normalize_url("/path", "https://example.com")
        "https://example.com/path"
    """
    try:
        # Handle relative URLs
        if base_url and not url.startswith(("http://", "https://")):
            url = urljoin(base_url, url)

        parsed = urlparse(url)

        # Ensure scheme is present
        if not parsed.scheme:
            url = "https://" + url
            parsed = urlparse(url)

        # Remove fragment
        parsed = parsed._replace(fragment="")

        # Normalize path
        path = parsed.path.rstrip("/") or "/"

        # Reconstruct URL
        normalized = urlunparse(
            (
                parsed.scheme,
                parsed.netloc.lower(),
                path,
                parsed.params,
                parsed.query,
                "",
            )
        )

        return normalized if is_valid_url(normalized) else None
    except Exception:
        return None


def is_valid_url(url: str) -> bool:
    """
    Check if URL is valid.

    Args:
        url: URL to validate

    Returns:
        True if URL is valid, False otherwise

    Example:
        >>> is_valid_url("https://example.com")
        True
    """
    return bool(validators.url(url))


def extract_meta_tags(html: str) -> Dict[str, Optional[str]]:
    """
    Extract meta tags from HTML.

    Args:
        html: HTML content

    Returns:
        Dictionary of meta tag values

    Example:
        >>> html = '<meta name="description" content="Test">'
        >>> extract_meta_tags(html)
        {"description": "Test", ...}
    """
    soup = BeautifulSoup(html, "lxml")

    meta_tags = {
        "title": None,
        "description": None,
        "keywords": None,
        "robots": None,
        "canonical": None,
        "og_title": None,
        "og_description": None,
        "og_image": None,
        "og_type": None,
        "og_url": None,
        "twitter_card": None,
        "twitter_title": None,
        "twitter_description": None,
        "twitter_image": None,
    }

    # Title
    title_tag = soup.find("title")
    if title_tag:
        meta_tags["title"] = title_tag.get_text().strip()

    # Description
    description_tag = soup.find("meta", attrs={"name": "description"})
    if description_tag:
        meta_tags["description"] = description_tag.get("content", "").strip()

    # Keywords
    keywords_tag = soup.find("meta", attrs={"name": "keywords"})
    if keywords_tag:
        meta_tags["keywords"] = keywords_tag.get("content", "").strip()

    # Robots
    robots_tag = soup.find("meta", attrs={"name": "robots"})
    if robots_tag:
        meta_tags["robots"] = robots_tag.get("content", "").strip()

    # Canonical
    canonical_tag = soup.find("link", attrs={"rel": "canonical"})
    if canonical_tag:
        meta_tags["canonical"] = canonical_tag.get("href", "").strip()

    # Open Graph
    og_tags = {
        "og:title": "og_title",
        "og:description": "og_description",
        "og:image": "og_image",
        "og:type": "og_type",
        "og:url": "og_url",
    }
    for og_property, key in og_tags.items():
        og_tag = soup.find("meta", attrs={"property": og_property})
        if og_tag:
            meta_tags[key] = og_tag.get("content", "").strip()

    # Twitter Card
    twitter_tags = {
        "twitter:card": "twitter_card",
        "twitter:title": "twitter_title",
        "twitter:description": "twitter_description",
        "twitter:image": "twitter_image",
    }
    for twitter_name, key in twitter_tags.items():
        twitter_tag = soup.find("meta", attrs={"name": twitter_name})
        if twitter_tag:
            meta_tags[key] = twitter_tag.get("content", "").strip()

    return meta_tags


def extract_headings(html: str) -> Dict[str, List[str]]:
    """
    Extract all headings from HTML.

    Args:
        html: HTML content

    Returns:
        Dictionary with heading levels as keys and lists of headings

    Example:
        >>> html = '<h1>Title</h1><h2>Subtitle</h2>'
        >>> extract_headings(html)
        {"h1": ["Title"], "h2": ["Subtitle"], ...}
    """
    soup = BeautifulSoup(html, "lxml")

    headings = {
        "h1": [],
        "h2": [],
        "h3": [],
        "h4": [],
        "h5": [],
        "h6": [],
    }

    for level in headings.keys():
        tags = soup.find_all(level)
        headings[level] = [tag.get_text().strip() for tag in tags if tag.get_text().strip()]

    return headings


def calculate_keyword_density(
    text: str, keyword: str, case_sensitive: bool = False
) -> Tuple[float, int, int]:
    """
    Calculate keyword density in text.

    Args:
        text: Text content
        keyword: Target keyword
        case_sensitive: Whether to match case

    Returns:
        Tuple of (density percentage, keyword count, total words)

    Example:
        >>> calculate_keyword_density("SEO is important. SEO matters.", "SEO")
        (40.0, 2, 5)
    """
    if not case_sensitive:
        text = text.lower()
        keyword = keyword.lower()

    # Count words
    words = re.findall(r'\b\w+\b', text)
    total_words = len(words)

    if total_words == 0:
        return 0.0, 0, 0

    # Count keyword occurrences
    keyword_words = keyword.split()
    keyword_length = len(keyword_words)

    if keyword_length == 1:
        # Single word keyword
        keyword_count = text.count(keyword)
    else:
        # Multi-word keyword (phrase)
        keyword_count = text.count(keyword)

    # Calculate density
    density = (keyword_count / total_words) * 100

    return round(density, 2), keyword_count, total_words


def extract_links(html: str, base_url: str) -> Dict[str, List[str]]:
    """
    Extract all links from HTML.

    Args:
        html: HTML content
        base_url: Base URL for resolving relative links

    Returns:
        Dictionary with internal and external links

    Example:
        >>> html = '<a href="/page">Link</a>'
        >>> extract_links(html, "https://example.com")
        {"internal": ["https://example.com/page"], "external": []}
    """
    soup = BeautifulSoup(html, "lxml")
    base_domain = extract_domain(base_url)

    internal_links = []
    external_links = []

    for link in soup.find_all("a", href=True):
        href = link.get("href", "").strip()
        if not href or href.startswith(("#", "javascript:", "mailto:", "tel:")):
            continue

        # Normalize URL
        absolute_url = normalize_url(href, base_url)
        if not absolute_url:
            continue

        # Check if internal or external
        link_domain = extract_domain(absolute_url)
        if link_domain == base_domain:
            internal_links.append(absolute_url)
        else:
            external_links.append(absolute_url)

    return {
        "internal": list(set(internal_links)),
        "external": list(set(external_links)),
    }


def extract_structured_data(html: str) -> List[Dict]:
    """
    Extract JSON-LD structured data from HTML.

    Args:
        html: HTML content

    Returns:
        List of structured data objects

    Example:
        >>> html = '<script type="application/ld+json">{"@type": "Article"}</script>'
        >>> extract_structured_data(html)
        [{"@type": "Article"}]
    """
    import json

    soup = BeautifulSoup(html, "lxml")
    structured_data = []

    # Find all JSON-LD scripts
    scripts = soup.find_all("script", type="application/ld+json")

    for script in scripts:
        try:
            data = json.loads(script.string)
            structured_data.append(data)
        except (json.JSONDecodeError, TypeError):
            continue

    return structured_data


def clean_text(html: str) -> str:
    """
    Extract and clean text from HTML.

    Args:
        html: HTML content

    Returns:
        Cleaned text content

    Example:
        >>> clean_text("<p>Hello <b>World</b></p>")
        "Hello World"
    """
    soup = BeautifulSoup(html, "lxml")

    # Remove script and style tags
    for tag in soup(["script", "style", "nav", "header", "footer"]):
        tag.decompose()

    # Get text
    text = soup.get_text(separator=" ", strip=True)

    # Clean whitespace
    text = re.sub(r'\s+', ' ', text).strip()

    return text


def calculate_readability_score(text: str) -> float:
    """
    Calculate Flesch Reading Ease score.

    Args:
        text: Text content

    Returns:
        Readability score (0-100, higher is easier)

    Example:
        >>> calculate_readability_score("This is a simple sentence.")
        > 60.0
    """
    # Count sentences
    sentences = re.split(r'[.!?]+', text)
    sentence_count = len([s for s in sentences if s.strip()])

    # Count words
    words = re.findall(r'\b\w+\b', text)
    word_count = len(words)

    # Count syllables (simplified)
    syllable_count = sum(count_syllables(word) for word in words)

    if sentence_count == 0 or word_count == 0:
        return 0.0

    # Flesch Reading Ease formula
    score = (
        206.835
        - 1.015 * (word_count / sentence_count)
        - 84.6 * (syllable_count / word_count)
    )

    return max(0.0, min(100.0, round(score, 2)))


def count_syllables(word: str) -> int:
    """
    Count syllables in a word (simplified).

    Args:
        word: Word to count

    Returns:
        Estimated syllable count
    """
    word = word.lower()
    count = 0
    vowels = "aeiouy"
    previous_was_vowel = False

    for char in word:
        is_vowel = char in vowels
        if is_vowel and not previous_was_vowel:
            count += 1
        previous_was_vowel = is_vowel

    # Adjust for silent e
    if word.endswith("e"):
        count -= 1

    # Ensure at least one syllable
    return max(1, count)
