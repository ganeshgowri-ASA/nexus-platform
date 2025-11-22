"""
Example test file for SEO module.

Run with: pytest tests/test_example.py
"""

import pytest
from modules.seo.utils.seo_utils import extract_domain, normalize_url, calculate_keyword_density
from modules.seo.utils.validators import validate_domain, validate_url, validate_keyword


class TestSEOUtils:
    """Test SEO utility functions."""

    def test_extract_domain(self):
        """Test domain extraction."""
        assert extract_domain("https://www.example.com/path") == "example.com"
        assert extract_domain("http://example.com") == "example.com"
        assert extract_domain("www.example.com") == "example.com"

    def test_normalize_url(self):
        """Test URL normalization."""
        assert normalize_url("example.com") == "https://example.com/"
        assert normalize_url("http://example.com/path") == "http://example.com/path"
        assert normalize_url("/path", "https://example.com") == "https://example.com/path"

    def test_keyword_density(self):
        """Test keyword density calculation."""
        text = "SEO is important. SEO tools help. SEO best practices."
        density, count, total = calculate_keyword_density(text, "SEO")
        assert count == 3
        assert total == 8
        assert density > 0


class TestValidators:
    """Test validation functions."""

    def test_validate_domain(self):
        """Test domain validation."""
        assert validate_domain("example.com") == "example.com"
        assert validate_domain("www.example.com") == "example.com"
        assert validate_domain("https://example.com") == "example.com"

        with pytest.raises(Exception):
            validate_domain("")

    def test_validate_url(self):
        """Test URL validation."""
        assert validate_url("https://example.com") == "https://example.com"
        assert validate_url("example.com") == "https://example.com"

        with pytest.raises(Exception):
            validate_url("")

    def test_validate_keyword(self):
        """Test keyword validation."""
        assert validate_keyword("seo tools") == "seo tools"
        assert validate_keyword("  keyword  ") == "keyword"

        with pytest.raises(Exception):
            validate_keyword("")


@pytest.mark.asyncio
class TestAsyncOperations:
    """Test async operations."""

    async def test_async_example(self):
        """Example async test."""
        # Placeholder for async tests
        assert True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
