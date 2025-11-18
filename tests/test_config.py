"""
Tests for Configuration Module
Tests for app/config.py settings and validation
"""

import pytest
from pathlib import Path
from app.config import (
    Settings,
    DatabaseConfig,
    AnthropicConfig,
    UIConfig,
    LoggingConfig,
    SecurityConfig,
)


class TestDatabaseConfig:
    """Tests for DatabaseConfig"""

    def test_database_config_defaults(self):
        """Test database config default values"""
        config = DatabaseConfig()
        assert config.url == "sqlite:///nexus.db"
        assert config.echo is False
        assert config.pool_size == 5
        assert config.max_overflow == 10

    def test_database_config_custom_values(self):
        """Test database config with custom values"""
        config = DatabaseConfig(
            url="postgresql://localhost/test",
            echo=True,
            pool_size=10,
            max_overflow=20,
        )
        assert config.url == "postgresql://localhost/test"
        assert config.echo is True
        assert config.pool_size == 10
        assert config.max_overflow == 20


class TestAnthropicConfig:
    """Tests for AnthropicConfig"""

    def test_anthropic_config_defaults(self):
        """Test Anthropic config default values"""
        config = AnthropicConfig()
        assert config.api_key == ""
        assert config.model == "claude-3-5-sonnet-20241022"
        assert config.max_tokens == 4096
        assert config.temperature == 0.7

    def test_anthropic_config_custom_values(self):
        """Test Anthropic config with custom values"""
        config = AnthropicConfig(
            api_key="test-key-123",
            model="claude-3-opus-20240229",
            max_tokens=8192,
            temperature=0.5,
        )
        assert config.api_key == "test-key-123"
        assert config.model == "claude-3-opus-20240229"
        assert config.max_tokens == 8192
        assert config.temperature == 0.5

    def test_api_key_validation_in_development(self, monkeypatch):
        """Test API key validation in development allows empty key"""
        monkeypatch.setenv("ENVIRONMENT", "development")
        config = AnthropicConfig(api_key="")
        assert config.api_key == ""


class TestUIConfig:
    """Tests for UIConfig"""

    def test_ui_config_defaults(self):
        """Test UI config default values"""
        config = UIConfig()
        assert config.theme == "dark"
        assert config.primary_color == "#6366f1"
        assert config.secondary_color == "#8b5cf6"
        assert config.sidebar_state == "expanded"
        assert config.layout == "wide"

    def test_ui_config_custom_values(self):
        """Test UI config with custom values"""
        config = UIConfig(
            theme="light",
            primary_color="#000000",
            secondary_color="#ffffff",
            sidebar_state="collapsed",
            layout="centered",
        )
        assert config.theme == "light"
        assert config.primary_color == "#000000"
        assert config.secondary_color == "#ffffff"
        assert config.sidebar_state == "collapsed"
        assert config.layout == "centered"


class TestLoggingConfig:
    """Tests for LoggingConfig"""

    def test_logging_config_defaults(self):
        """Test logging config default values"""
        config = LoggingConfig()
        assert config.level == "INFO"
        assert "%(asctime)s" in config.format
        assert config.file_path == "logs/nexus.log"
        assert config.max_bytes == 10485760
        assert config.backup_count == 5

    def test_logging_config_custom_values(self):
        """Test logging config with custom values"""
        config = LoggingConfig(
            level="DEBUG",
            format="%(message)s",
            file_path="/tmp/test.log",
            max_bytes=5242880,
            backup_count=3,
        )
        assert config.level == "DEBUG"
        assert config.format == "%(message)s"
        assert config.file_path == "/tmp/test.log"
        assert config.max_bytes == 5242880
        assert config.backup_count == 3


class TestSecurityConfig:
    """Tests for SecurityConfig"""

    def test_security_config_defaults(self):
        """Test security config default values"""
        config = SecurityConfig()
        assert config.secret_key == "change-me-in-production"
        assert config.allowed_origins == ["*"]
        assert config.session_timeout == 3600

    def test_security_config_custom_values(self):
        """Test security config with custom values"""
        config = SecurityConfig(
            secret_key="my-secret-key",
            allowed_origins=["http://localhost:3000"],
            session_timeout=7200,
        )
        assert config.secret_key == "my-secret-key"
        assert config.allowed_origins == ["http://localhost:3000"]
        assert config.session_timeout == 7200


class TestSettings:
    """Tests for main Settings class"""

    def test_settings_defaults(self):
        """Test settings default values"""
        settings = Settings()
        assert settings.app_name == "NEXUS Platform"
        assert settings.app_version == "1.0.0"
        assert settings.debug is True
        assert isinstance(settings.database, DatabaseConfig)
        assert isinstance(settings.anthropic, AnthropicConfig)
        assert isinstance(settings.ui, UIConfig)
        assert isinstance(settings.logging, LoggingConfig)
        assert isinstance(settings.security, SecurityConfig)

    def test_settings_feature_flags(self):
        """Test feature flags in settings"""
        settings = Settings()
        assert settings.enable_analytics is True
        assert settings.enable_ai_features is True
        assert settings.enable_collaboration is True

    def test_get_database_url(self):
        """Test get_database_url method"""
        settings = Settings()
        url = settings.get_database_url()
        assert isinstance(url, str)
        assert "sqlite" in url or "postgresql" in url

    def test_is_production(self):
        """Test is_production method"""
        settings = Settings(environment="production")
        assert settings.is_production() is True

        settings = Settings(environment="development")
        assert settings.is_production() is False

    def test_is_development(self):
        """Test is_development method"""
        settings = Settings(environment="development")
        assert settings.is_development() is True

        settings = Settings(environment="production")
        assert settings.is_development() is False

    def test_base_dir_exists(self):
        """Test that base_dir is created"""
        settings = Settings()
        assert settings.base_dir.exists()
        assert isinstance(settings.base_dir, Path)

    def test_data_dir_exists(self):
        """Test that data_dir is created"""
        settings = Settings()
        assert settings.data_dir.exists()
        assert isinstance(settings.data_dir, Path)

    def test_nested_config_override(self):
        """Test nested configuration override"""
        settings = Settings(
            database={"url": "postgresql://test", "pool_size": 15}
        )
        assert settings.database.url == "postgresql://test"
        assert settings.database.pool_size == 15

    def test_environment_variable_loading(self, monkeypatch):
        """Test loading from environment variables"""
        monkeypatch.setenv("APP_NAME", "Test NEXUS")
        monkeypatch.setenv("DEBUG", "false")
        monkeypatch.setenv("DATABASE__URL", "postgresql://envtest")

        settings = Settings()
        assert settings.app_name == "Test NEXUS"
        assert settings.debug is False
        assert settings.database.url == "postgresql://envtest"


@pytest.mark.unit
class TestConfigIntegration:
    """Integration tests for configuration"""

    def test_full_configuration_lifecycle(self):
        """Test complete configuration lifecycle"""
        # Create settings with all custom values
        settings = Settings(
            app_name="Test App",
            environment="testing",
            database={"url": "sqlite:///:memory:"},
            anthropic={"api_key": "test-key"},
            ui={"theme": "light"},
            logging={"level": "DEBUG"},
        )

        # Verify all components
        assert settings.app_name == "Test App"
        assert settings.environment == "testing"
        assert settings.database.url == "sqlite:///:memory:"
        assert settings.anthropic.api_key == "test-key"
        assert settings.ui.theme == "light"
        assert settings.logging.level == "DEBUG"

        # Verify methods
        assert settings.get_database_url() == "sqlite:///:memory:"
        assert settings.is_development() is False
        assert settings.is_production() is False
