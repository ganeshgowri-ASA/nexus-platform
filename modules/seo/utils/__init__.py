"""Utility modules for SEO tools."""

from .exceptions import (
    SEOException,
    APIException,
    ValidationException,
    CrawlException,
    RateLimitException,
)
from .http_client import HTTPClient
from .seo_utils import (
    extract_domain,
    normalize_url,
    is_valid_url,
    extract_meta_tags,
    calculate_keyword_density,
    extract_headings,
)
from .validators import (
    validate_domain,
    validate_url,
    validate_keyword,
    validate_email,
)

__all__ = [
    "SEOException",
    "APIException",
    "ValidationException",
    "CrawlException",
    "RateLimitException",
    "HTTPClient",
    "extract_domain",
    "normalize_url",
    "is_valid_url",
    "extract_meta_tags",
    "calculate_keyword_density",
    "extract_headings",
    "validate_domain",
    "validate_url",
    "validate_keyword",
    "validate_email",
]
