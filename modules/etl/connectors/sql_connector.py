"""SQL database connector."""
from typing import Any, Dict, Optional
import pandas as pd
from sqlalchemy import create_engine, text
from .base import BaseConnector


class SQLConnector(BaseConnector):
    """Connector for SQL databases (PostgreSQL, MySQL, etc.)."""

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.engine = None
        self.connection = None

    def get_required_fields(self) -> list:
        """Get required configuration fields."""
        return ["connection_string"]

    def connect(self) -> bool:
        """Establish connection to SQL database."""
        try:
            self.validate_config()
            connection_string = self.config["connection_string"]

            # Create SQLAlchemy engine
            self.engine = create_engine(
                connection_string,
                pool_pre_ping=True,
                pool_size=5,
                max_overflow=10,
            )

            # Test connection
            self.connection = self.engine.connect()
            self.logger.info("Connected to SQL database")
            return True

        except Exception as e:
            self.logger.error(f"Failed to connect to SQL database: {e}")
            return False

    def extract(self, query: Optional[Dict[str, Any]] = None) -> pd.DataFrame:
        """Extract data from SQL database."""
        try:
            if not self.connection:
                raise RuntimeError("Not connected to database")

            # Get SQL query from config or query parameter
            sql_query = query.get("sql") if query else self.config.get("query")

            if not sql_query:
                raise ValueError("SQL query is required")

            # Execute query and load into DataFrame
            df = pd.read_sql(sql_query, self.connection)

            # Apply additional filters if provided
            if query:
                if "limit" in query and "LIMIT" not in sql_query.upper():
                    df = df.head(query["limit"])
                if "columns" in query:
                    df = df[query["columns"]]

            self.logger.info(f"Extracted {len(df)} records from SQL database")
            return df

        except Exception as e:
            self.logger.error(f"Error extracting data from SQL: {e}")
            raise

    def disconnect(self) -> None:
        """Close database connection."""
        try:
            if self.connection:
                self.connection.close()
            if self.engine:
                self.engine.dispose()
            self.logger.info("Disconnected from SQL database")
        except Exception as e:
            self.logger.error(f"Error disconnecting from SQL: {e}")

    def test_connection(self) -> bool:
        """Test database connection."""
        try:
            if not self.connection:
                return False
            # Execute simple query
            self.connection.execute(text("SELECT 1"))
            return True
        except Exception:
            return False

    def get_schema(self) -> Optional[Dict[str, Any]]:
        """Get database schema information."""
        try:
            if not self.connection:
                return None

            # Get table list
            if "postgresql" in self.config["connection_string"]:
                tables_query = """
                    SELECT table_name
                    FROM information_schema.tables
                    WHERE table_schema = 'public'
                """
            elif "mysql" in self.config["connection_string"]:
                tables_query = "SHOW TABLES"
            else:
                return None

            tables_df = pd.read_sql(tables_query, self.connection)
            tables = tables_df.iloc[:, 0].tolist()

            return {"tables": tables, "database_type": self._get_db_type()}

        except Exception as e:
            self.logger.error(f"Error getting schema: {e}")
            return None

    def _get_db_type(self) -> str:
        """Determine database type from connection string."""
        conn_str = self.config["connection_string"].lower()
        if "postgresql" in conn_str:
            return "postgresql"
        elif "mysql" in conn_str:
            return "mysql"
        elif "sqlite" in conn_str:
            return "sqlite"
        elif "mssql" in conn_str:
            return "mssql"
        else:
            return "unknown"

    def execute_query(self, query: str) -> pd.DataFrame:
        """Execute a custom SQL query."""
        try:
            return pd.read_sql(query, self.connection)
        except Exception as e:
            self.logger.error(f"Error executing query: {e}")
            raise
