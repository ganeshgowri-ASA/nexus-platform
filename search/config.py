"""Configuration management for Elasticsearch search."""

from typing import List, Optional
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class ElasticsearchSettings(BaseSettings):
    """Elasticsearch configuration settings."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )

    # Connection settings
    elasticsearch_hosts: str = Field(
        default="http://localhost:9200",
        description="Comma-separated list of Elasticsearch hosts"
    )
    elasticsearch_username: Optional[str] = None
    elasticsearch_password: Optional[str] = None
    elasticsearch_api_key: Optional[str] = None
    elasticsearch_cloud_id: Optional[str] = None
    elasticsearch_use_ssl: bool = False
    elasticsearch_verify_certs: bool = True
    elasticsearch_ca_certs: Optional[str] = None

    # Index settings
    elasticsearch_index_prefix: str = "nexus"
    elasticsearch_shards: int = 2
    elasticsearch_replicas: int = 1

    # Performance settings
    elasticsearch_bulk_size: int = 500
    elasticsearch_queue_size: int = 1000
    elasticsearch_request_timeout: int = 30
    elasticsearch_max_retries: int = 3

    # Redis settings (for async queue)
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_db: int = 0
    redis_password: Optional[str] = None

    # Application settings
    app_env: str = "development"
    log_level: str = "INFO"

    @property
    def hosts(self) -> List[str]:
        """Parse hosts from comma-separated string."""
        return [h.strip() for h in self.elasticsearch_hosts.split(",")]

    @property
    def is_production(self) -> bool:
        """Check if running in production."""
        return self.app_env.lower() == "production"

    def get_index_name(self, doc_type: str) -> str:
        """Generate index name with prefix."""
        return f"{self.elasticsearch_index_prefix}_{doc_type}"


# Global settings instance
settings = ElasticsearchSettings()
