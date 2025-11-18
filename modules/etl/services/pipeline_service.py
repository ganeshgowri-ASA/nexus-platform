"""Pipeline orchestration service."""
from typing import Any, Dict, Optional
import pandas as pd
from datetime import datetime
from modules.etl.connectors.factory import ConnectorFactory
from modules.etl.services.transformation_service import TransformationService
from modules.etl.services.validation_service import ValidationService
from modules.etl.services.deduplication_service import DeduplicationService
from shared.utils.logger import get_logger

logger = get_logger(__name__)


class PipelineService:
    """Service for orchestrating ETL pipeline execution."""

    def __init__(self):
        self.logger = logger
        self.transformation_service = TransformationService()
        self.validation_service = ValidationService()
        self.deduplication_service = DeduplicationService()

    def execute_pipeline(
        self, pipeline_config: Dict[str, Any], source_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Execute a complete ETL pipeline.

        Args:
            pipeline_config: Pipeline configuration
            source_config: Data source configuration

        Returns:
            Execution report
        """
        execution_report = {
            "status": "pending",
            "started_at": datetime.utcnow().isoformat(),
            "completed_at": None,
            "duration_seconds": None,
            "records_extracted": 0,
            "records_transformed": 0,
            "records_loaded": 0,
            "records_failed": 0,
            "records_duplicates": 0,
            "steps": [],
            "errors": [],
        }

        try:
            execution_report["status"] = "running"

            # Step 1: Extract
            self.logger.info("Starting extraction...")
            df, extract_report = self._extract_data(source_config, pipeline_config.get("extract_config", {}))
            execution_report["records_extracted"] = len(df)
            execution_report["steps"].append({"name": "extract", "status": "completed", "report": extract_report})
            self.logger.info(f"Extracted {len(df)} records")

            # Step 2: Validate (pre-transformation)
            if pipeline_config.get("validation_rules"):
                self.logger.info("Running pre-transformation validation...")
                df, validation_report = self.validation_service.validate_data(
                    df, pipeline_config["validation_rules"]
                )
                execution_report["steps"].append(
                    {"name": "pre_validation", "status": "completed", "report": validation_report}
                )

            # Step 3: Transform
            if pipeline_config.get("transform_config", {}).get("transformations"):
                self.logger.info("Applying transformations...")
                df = self.transformation_service.apply_transformations(
                    df, pipeline_config["transform_config"]["transformations"]
                )
                execution_report["records_transformed"] = len(df)
                execution_report["steps"].append(
                    {"name": "transform", "status": "completed", "records": len(df)}
                )
                self.logger.info(f"Transformed {len(df)} records")

            # Step 4: Deduplicate
            if pipeline_config.get("deduplication_config"):
                self.logger.info("Removing duplicates...")
                df, dedup_report = self.deduplication_service.deduplicate(
                    df, pipeline_config["deduplication_config"]
                )
                execution_report["records_duplicates"] = dedup_report["duplicates_removed"]
                execution_report["steps"].append(
                    {"name": "deduplication", "status": "completed", "report": dedup_report}
                )
                self.logger.info(f"Removed {dedup_report['duplicates_removed']} duplicates")

            # Step 5: Validate (post-transformation)
            if pipeline_config.get("validation_rules"):
                self.logger.info("Running post-transformation validation...")
                df, validation_report = self.validation_service.validate_data(
                    df, pipeline_config["validation_rules"]
                )
                execution_report["steps"].append(
                    {"name": "post_validation", "status": "completed", "report": validation_report}
                )

            # Step 6: Load
            self.logger.info("Loading data...")
            load_report = self._load_data(df, pipeline_config.get("load_config", {}))
            execution_report["records_loaded"] = load_report.get("records_loaded", len(df))
            execution_report["steps"].append({"name": "load", "status": "completed", "report": load_report})
            self.logger.info(f"Loaded {execution_report['records_loaded']} records")

            # Success
            execution_report["status"] = "completed"

        except Exception as e:
            self.logger.error(f"Pipeline execution failed: {e}")
            execution_report["status"] = "failed"
            execution_report["errors"].append(str(e))

        finally:
            execution_report["completed_at"] = datetime.utcnow().isoformat()
            started_at = datetime.fromisoformat(execution_report["started_at"])
            completed_at = datetime.fromisoformat(execution_report["completed_at"])
            execution_report["duration_seconds"] = (completed_at - started_at).total_seconds()

        return execution_report

    def _extract_data(
        self, source_config: Dict[str, Any], extract_config: Dict[str, Any]
    ) -> tuple[pd.DataFrame, Dict[str, Any]]:
        """Extract data from source."""
        try:
            source_type = source_config.get("source_type")
            connector_config = source_config.get("connection_config", {})

            # Create connector
            connector = ConnectorFactory.create_connector(source_type, connector_config)

            # Connect
            if not connector.connect():
                raise RuntimeError("Failed to connect to data source")

            # Extract
            df = connector.extract(extract_config.get("query"))

            # Disconnect
            connector.disconnect()

            report = {
                "source_type": source_type,
                "records_extracted": len(df),
                "columns": list(df.columns),
            }

            return df, report

        except Exception as e:
            self.logger.error(f"Extraction failed: {e}")
            raise

    def _load_data(self, df: pd.DataFrame, load_config: Dict[str, Any]) -> Dict[str, Any]:
        """Load data to destination."""
        try:
            destination_type = load_config.get("type", "csv")
            destination_config = load_config.get("config", {})

            if destination_type == "csv":
                output_path = destination_config.get("path", "/app/data/output.csv")
                df.to_csv(output_path, index=False)
                self.logger.info(f"Saved to CSV: {output_path}")

            elif destination_type == "json":
                output_path = destination_config.get("path", "/app/data/output.json")
                df.to_json(output_path, orient=destination_config.get("orient", "records"))
                self.logger.info(f"Saved to JSON: {output_path}")

            elif destination_type == "sql":
                from sqlalchemy import create_engine

                connection_string = destination_config.get("connection_string")
                table_name = destination_config.get("table_name")
                if_exists = destination_config.get("if_exists", "replace")

                engine = create_engine(connection_string)
                df.to_sql(table_name, engine, if_exists=if_exists, index=False)
                self.logger.info(f"Saved to SQL table: {table_name}")

            elif destination_type == "parquet":
                output_path = destination_config.get("path", "/app/data/output.parquet")
                df.to_parquet(output_path, index=False)
                self.logger.info(f"Saved to Parquet: {output_path}")

            else:
                raise ValueError(f"Unsupported destination type: {destination_type}")

            return {
                "records_loaded": len(df),
                "destination_type": destination_type,
                "destination": destination_config.get("path") or destination_config.get("table_name"),
            }

        except Exception as e:
            self.logger.error(f"Load failed: {e}")
            raise
