"""
Custom exceptions for SEO module.

Defines all custom exceptions used throughout the SEO tools module.
"""


class SEOException(Exception):
    """
    Base exception for all SEO module errors.

    All custom exceptions should inherit from this class.
    """

    def __init__(self, message: str, details: dict = None):
        """
        Initialize exception.

        Args:
            message: Error message
            details: Additional error details
        """
        self.message = message
        self.details = details or {}
        super().__init__(self.message)

    def __str__(self) -> str:
        """String representation."""
        if self.details:
            return f"{self.message} | Details: {self.details}"
        return self.message


class APIException(SEOException):
    """
    Exception for third-party API errors.

    Raised when external API calls fail or return errors.
    """

    def __init__(
        self,
        message: str,
        api_name: str = None,
        status_code: int = None,
        details: dict = None,
    ):
        """
        Initialize API exception.

        Args:
            message: Error message
            api_name: Name of the API that failed
            status_code: HTTP status code
            details: Additional error details
        """
        self.api_name = api_name
        self.status_code = status_code
        details = details or {}
        if api_name:
            details["api_name"] = api_name
        if status_code:
            details["status_code"] = status_code
        super().__init__(message, details)


class ValidationException(SEOException):
    """
    Exception for validation errors.

    Raised when input validation fails.
    """

    def __init__(self, message: str, field: str = None, details: dict = None):
        """
        Initialize validation exception.

        Args:
            message: Error message
            field: Field that failed validation
            details: Additional error details
        """
        self.field = field
        details = details or {}
        if field:
            details["field"] = field
        super().__init__(message, details)


class CrawlException(SEOException):
    """
    Exception for web crawling errors.

    Raised when crawling operations fail.
    """

    def __init__(
        self,
        message: str,
        url: str = None,
        status_code: int = None,
        details: dict = None,
    ):
        """
        Initialize crawl exception.

        Args:
            message: Error message
            url: URL that failed to crawl
            status_code: HTTP status code
            details: Additional error details
        """
        self.url = url
        self.status_code = status_code
        details = details or {}
        if url:
            details["url"] = url
        if status_code:
            details["status_code"] = status_code
        super().__init__(message, details)


class RateLimitException(SEOException):
    """
    Exception for rate limit errors.

    Raised when API rate limits are exceeded.
    """

    def __init__(
        self,
        message: str,
        retry_after: int = None,
        api_name: str = None,
        details: dict = None,
    ):
        """
        Initialize rate limit exception.

        Args:
            message: Error message
            retry_after: Seconds to wait before retry
            api_name: Name of the API
            details: Additional error details
        """
        self.retry_after = retry_after
        self.api_name = api_name
        details = details or {}
        if retry_after:
            details["retry_after"] = retry_after
        if api_name:
            details["api_name"] = api_name
        super().__init__(message, details)


class DatabaseException(SEOException):
    """
    Exception for database errors.

    Raised when database operations fail.
    """

    pass


class ConfigurationException(SEOException):
    """
    Exception for configuration errors.

    Raised when configuration is invalid or missing.
    """

    pass
