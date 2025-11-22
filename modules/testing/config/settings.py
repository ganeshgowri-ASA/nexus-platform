"""
Configuration settings for Testing & QA module
"""
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # API Settings
    API_V1_PREFIX: str = "/api/v1/testing"
    PROJECT_NAME: str = "NEXUS Testing & QA"

    # Database
    DATABASE_URL: str = "postgresql://nexus_user:nexus_pass@localhost:5432/nexus_db"

    # Redis
    REDIS_URL: str = "redis://localhost:6379/1"

    # Test Execution
    TEST_RESULTS_DIR: str = "./test_results"
    TEST_REPORTS_DIR: str = "./test_reports"
    SCREENSHOTS_DIR: str = "./screenshots"

    # Selenium Configuration
    SELENIUM_HUB_URL: Optional[str] = None
    SELENIUM_GRID_URL: Optional[str] = None
    WEBDRIVER_HEADLESS: bool = True
    WEBDRIVER_TIMEOUT: int = 30

    # Browsers
    DEFAULT_BROWSER: str = "chrome"
    AVAILABLE_BROWSERS: list = ["chrome", "firefox", "safari", "edge"]

    # Pytest Configuration
    PYTEST_ARGS: list = ["-v", "--tb=short"]
    PYTEST_MARKERS: list = ["unit", "integration", "e2e", "slow"]

    # Coverage
    COVERAGE_MIN_THRESHOLD: float = 80.0
    COVERAGE_REPORT_FORMAT: str = "html"

    # CI/CD Integration
    GITHUB_TOKEN: Optional[str] = None
    GITHUB_REPO: Optional[str] = None
    CI_ENABLED: bool = True

    # Performance Testing
    LOAD_TEST_USERS: int = 10
    LOAD_TEST_DURATION: int = 60  # seconds
    PERFORMANCE_THRESHOLD_MS: int = 1000

    # Security Testing
    SECURITY_SCAN_ENABLED: bool = True
    OWASP_ZAP_URL: Optional[str] = None

    # Email Notifications
    SMTP_HOST: Optional[str] = None
    SMTP_PORT: int = 587
    SMTP_USER: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    NOTIFICATION_EMAILS: list = []

    # Scheduling
    ENABLE_SCHEDULED_TESTS: bool = True
    SCHEDULED_TEST_CRON: str = "0 2 * * *"  # Daily at 2 AM

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
