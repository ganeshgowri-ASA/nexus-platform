"""Base connector class."""
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
import pandas as pd
from shared.utils.logger import get_logger

logger = get_logger(__name__)


class BaseConnector(ABC):
    """Abstract base class for data connectors."""

    def __init__(self, config: Dict[str, Any]):
        """Initialize connector with configuration."""
        self.config = config
        self.logger = logger

    @abstractmethod
    def connect(self) -> bool:
        """Establish connection to data source."""
        pass

    @abstractmethod
    def extract(self, query: Optional[Dict[str, Any]] = None) -> pd.DataFrame:
        """Extract data from source."""
        pass

    @abstractmethod
    def disconnect(self) -> None:
        """Close connection to data source."""
        pass

    @abstractmethod
    def test_connection(self) -> bool:
        """Test if connection is valid."""
        pass

    def validate_config(self) -> bool:
        """Validate connector configuration."""
        required_fields = self.get_required_fields()
        for field in required_fields:
            if field not in self.config:
                raise ValueError(f"Missing required configuration field: {field}")
        return True

    @abstractmethod
    def get_required_fields(self) -> list:
        """Get list of required configuration fields."""
        pass

    def get_schema(self) -> Optional[Dict[str, Any]]:
        """Get schema information from source."""
        return None

    def get_sample_data(self, limit: int = 10) -> pd.DataFrame:
        """Get sample data from source."""
        try:
            df = self.extract()
            return df.head(limit)
        except Exception as e:
            self.logger.error(f"Error getting sample data: {e}")
            return pd.DataFrame()
