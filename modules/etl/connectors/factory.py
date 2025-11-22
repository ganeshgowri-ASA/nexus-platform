"""Connector factory for creating appropriate connector instances."""
from typing import Dict, Any
from .base import BaseConnector
from .csv_connector import CSVConnector
from .json_connector import JSONConnector
from .sql_connector import SQLConnector
from .api_connector import APIConnector
from modules.etl.core.constants import SourceType


class ConnectorFactory:
    """Factory class for creating data source connectors."""

    @staticmethod
    def create_connector(source_type: str, config: Dict[str, Any]) -> BaseConnector:
        """Create appropriate connector based on source type."""
        connector_map = {
            SourceType.CSV: CSVConnector,
            SourceType.JSON: JSONConnector,
            SourceType.SQL: SQLConnector,
            SourceType.POSTGRESQL: SQLConnector,
            SourceType.MYSQL: SQLConnector,
            SourceType.API: APIConnector,
            SourceType.REST_API: APIConnector,
        }

        connector_class = connector_map.get(source_type)
        if not connector_class:
            raise ValueError(f"Unsupported source type: {source_type}")

        return connector_class(config)

    @staticmethod
    def get_supported_sources() -> list:
        """Get list of supported source types."""
        return [
            SourceType.CSV,
            SourceType.JSON,
            SourceType.SQL,
            SourceType.POSTGRESQL,
            SourceType.MYSQL,
            SourceType.API,
            SourceType.REST_API,
        ]
