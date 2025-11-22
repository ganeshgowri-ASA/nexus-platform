"""
ETL Pipeline orchestration module.

This module provides pipeline orchestration, step execution,
error handling, and retry logic for ETL workflows.
"""

import logging
import time
import traceback
from typing import List, Dict, Any, Optional, Callable
from datetime import datetime
from enum import Enum

from modules.etl.extractors import ExtractorFactory, BaseExtractor
from modules.etl.transformers import TransformerFactory, TransformationPipeline
from modules.etl.loaders import LoaderFactory, BaseLoader
from modules.etl.validation import DataQualityCheck, SchemaValidator, ValidationResult
from modules.etl.mappings import FieldMapper
from modules.etl.models import ETLJob, JobRun, JobStatus, AuditLog

logger = logging.getLogger(__name__)


class PipelineException(Exception):
    """Base exception for pipeline errors."""
    pass


class StepException(PipelineException):
    """Exception for step execution errors."""
    pass


class PipelineStage(str, Enum):
    """Enumeration of pipeline stages."""
    EXTRACT = "extract"
    TRANSFORM = "transform"
    VALIDATE = "validate"
    LOAD = "load"


class PipelineContext:
    """Context object for pipeline execution."""

    def __init__(self):
        """Initialize pipeline context."""
        self.data: List[Dict[str, Any]] = []
        self.metadata: Dict[str, Any] = {}
        self.metrics: Dict[str, Any] = {
            "records_extracted": 0,
            "records_transformed": 0,
            "records_validated": 0,
            "records_loaded": 0,
            "records_failed": 0,
            "extraction_time": 0,
            "transformation_time": 0,
            "validation_time": 0,
            "loading_time": 0
        }
        self.errors: List[Dict[str, Any]] = []
        self.warnings: List[Dict[str, Any]] = []

    def add_error(self, stage: str, message: str, details: Optional[Dict[str, Any]] = None) -> None:
        """Add an error to the context."""
        self.errors.append({
            "stage": stage,
            "message": message,
            "details": details or {},
            "timestamp": datetime.utcnow().isoformat()
        })

    def add_warning(self, stage: str, message: str, details: Optional[Dict[str, Any]] = None) -> None:
        """Add a warning to the context."""
        self.warnings.append({
            "stage": stage,
            "message": message,
            "details": details or {},
            "timestamp": datetime.utcnow().isoformat()
        })


class StepExecutor:
    """Executes individual pipeline steps."""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize step executor.

        Args:
            config: Configuration options
        """
        self.config = config or {}
        self.logger = logging.getLogger(__name__)

    def execute(
        self,
        step_name: str,
        step_func: Callable,
        context: PipelineContext,
        *args,
        **kwargs
    ) -> Any:
        """
        Execute a single step with error handling.

        Args:
            step_name: Name of the step
            step_func: Function to execute
            context: Pipeline context
            *args: Positional arguments for step function
            **kwargs: Keyword arguments for step function

        Returns:
            Result of step execution

        Raises:
            StepException: If step execution fails
        """
        start_time = time.time()

        try:
            self.logger.info(f"Executing step: {step_name}")
            result = step_func(*args, **kwargs)

            duration = time.time() - start_time
            self.logger.info(f"Step '{step_name}' completed in {duration:.2f}s")

            return result

        except Exception as e:
            duration = time.time() - start_time
            error_msg = f"Step '{step_name}' failed after {duration:.2f}s: {str(e)}"
            self.logger.error(error_msg)
            self.logger.debug(traceback.format_exc())

            context.add_error(step_name, error_msg, {
                "exception": str(e),
                "traceback": traceback.format_exc()
            })

            raise StepException(error_msg) from e


class ErrorHandler:
    """Handles errors and implements error recovery strategies."""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize error handler.

        Args:
            config: Configuration options
        """
        self.config = config or {}
        self.logger = logging.getLogger(__name__)

    def handle_error(
        self,
        error: Exception,
        context: PipelineContext,
        stage: str
    ) -> bool:
        """
        Handle an error and determine if execution should continue.

        Args:
            error: Exception that occurred
            context: Pipeline context
            stage: Pipeline stage where error occurred

        Returns:
            True if execution should continue, False otherwise
        """
        error_msg = str(error)
        self.logger.error(f"Error in {stage}: {error_msg}")

        # Add to context
        context.add_error(stage, error_msg, {
            "exception_type": type(error).__name__,
            "traceback": traceback.format_exc()
        })

        # Check if error is recoverable
        fail_on_error = self.config.get("fail_on_error", True)

        if fail_on_error:
            return False

        # Implement error recovery logic
        recovery_strategy = self.config.get("recovery_strategy", "skip")

        if recovery_strategy == "skip":
            self.logger.info("Skipping failed records and continuing")
            return True
        elif recovery_strategy == "default":
            self.logger.info("Using default values and continuing")
            return True
        else:
            return False

    def handle_validation_errors(
        self,
        validation_result: ValidationResult,
        context: PipelineContext
    ) -> bool:
        """
        Handle validation errors.

        Args:
            validation_result: Validation result
            context: Pipeline context

        Returns:
            True if execution should continue, False otherwise
        """
        if not validation_result.is_valid:
            fail_on_validation = self.config.get("fail_on_validation_error", True)

            for error in validation_result.errors:
                context.add_error("validation", error["message"], error)

            if fail_on_validation:
                return False

        # Add warnings to context
        for warning in validation_result.warnings:
            context.add_warning("validation", warning["message"], warning)

        return True


class RetryLogic:
    """Implements retry logic for failed operations."""

    def __init__(
        self,
        max_retries: int = 3,
        retry_delay: float = 1.0,
        backoff_multiplier: float = 2.0
    ):
        """
        Initialize retry logic.

        Args:
            max_retries: Maximum number of retry attempts
            retry_delay: Initial delay between retries in seconds
            backoff_multiplier: Multiplier for exponential backoff
        """
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.backoff_multiplier = backoff_multiplier
        self.logger = logging.getLogger(__name__)

    def execute_with_retry(
        self,
        func: Callable,
        *args,
        **kwargs
    ) -> Any:
        """
        Execute a function with retry logic.

        Args:
            func: Function to execute
            *args: Positional arguments
            **kwargs: Keyword arguments

        Returns:
            Function result

        Raises:
            Exception: If all retry attempts fail
        """
        last_exception = None
        delay = self.retry_delay

        for attempt in range(self.max_retries + 1):
            try:
                if attempt > 0:
                    self.logger.info(f"Retry attempt {attempt}/{self.max_retries}")

                result = func(*args, **kwargs)

                if attempt > 0:
                    self.logger.info(f"Retry successful on attempt {attempt}")

                return result

            except Exception as e:
                last_exception = e
                self.logger.warning(f"Attempt {attempt + 1} failed: {str(e)}")

                if attempt < self.max_retries:
                    self.logger.info(f"Waiting {delay}s before retry...")
                    time.sleep(delay)
                    delay *= self.backoff_multiplier

        self.logger.error(f"All {self.max_retries} retry attempts failed")
        raise last_exception


class ETLPipeline:
    """Main ETL pipeline orchestrator."""

    def __init__(
        self,
        job: ETLJob,
        db_session: Optional[Any] = None,
        config: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize ETL pipeline.

        Args:
            job: ETL job configuration
            db_session: Database session for logging
            config: Additional configuration options
        """
        self.job = job
        self.db_session = db_session
        self.config = config or {}
        self.logger = logging.getLogger(__name__)

        self.step_executor = StepExecutor(config)
        self.error_handler = ErrorHandler(config)
        self.retry_logic = RetryLogic(
            max_retries=job.max_retries,
            retry_delay=job.retry_delay_seconds
        )

        self.context = PipelineContext()

    def execute(self) -> Dict[str, Any]:
        """
        Execute the complete ETL pipeline.

        Returns:
            Execution result dictionary
        """
        job_run = None
        start_time = time.time()

        try:
            # Create job run record
            if self.db_session:
                job_run = self._create_job_run()

            self.logger.info(f"Starting ETL pipeline for job: {self.job.name}")

            # Execute pipeline stages
            self._extract_stage()
            self._transform_stage()
            self._validate_stage()
            self._load_stage()

            duration = time.time() - start_time
            self.logger.info(f"Pipeline completed successfully in {duration:.2f}s")

            # Update job run
            if job_run and self.db_session:
                self._complete_job_run(job_run, JobStatus.COMPLETED)

            return {
                "status": "success",
                "duration": duration,
                "metrics": self.context.metrics,
                "errors": self.context.errors,
                "warnings": self.context.warnings
            }

        except Exception as e:
            duration = time.time() - start_time
            error_msg = f"Pipeline failed: {str(e)}"
            self.logger.error(error_msg)
            self.logger.debug(traceback.format_exc())

            # Update job run
            if job_run and self.db_session:
                self._fail_job_run(job_run, error_msg)

            return {
                "status": "failed",
                "duration": duration,
                "error": error_msg,
                "metrics": self.context.metrics,
                "errors": self.context.errors,
                "warnings": self.context.warnings
            }

    def _extract_stage(self) -> None:
        """Execute extraction stage."""
        start_time = time.time()

        try:
            self.logger.info("Stage 1: Extraction")

            # Create extractor
            extractor = ExtractorFactory.create_extractor(
                self.job.source,
                self.job.extraction_config
            )

            # Execute extraction with retry
            def extract():
                with extractor:
                    if self.job.is_incremental and self.job.watermark_column:
                        data = extractor.extract_incremental(
                            self.job.watermark_column,
                            self.job.last_watermark_value,
                            self.job.extraction_query
                        )
                    else:
                        data = extractor.extract(
                            query=self.job.extraction_query,
                            limit=self.config.get("extract_limit")
                        )
                return data

            self.context.data = self.retry_logic.execute_with_retry(extract)
            self.context.metrics["records_extracted"] = len(self.context.data)
            self.context.metrics["extraction_time"] = time.time() - start_time

            self.logger.info(f"Extracted {len(self.context.data)} records")

        except Exception as e:
            if not self.error_handler.handle_error(e, self.context, "extract"):
                raise

    def _transform_stage(self) -> None:
        """Execute transformation stage."""
        start_time = time.time()

        try:
            self.logger.info("Stage 2: Transformation")

            if not self.context.data:
                self.logger.warning("No data to transform")
                return

            # Apply field mapping if configured
            if self.job.mapping:
                mapper = FieldMapper(self.job.mapping)
                self.context.data = mapper.map_records(self.context.data)

            # Apply transformation steps
            if self.job.transformation_steps:
                pipeline = TransformerFactory.create_pipeline(
                    self.job.transformation_steps
                )
                self.context.data = pipeline.transform(self.context.data)

            self.context.metrics["records_transformed"] = len(self.context.data)
            self.context.metrics["transformation_time"] = time.time() - start_time

            self.logger.info(f"Transformed {len(self.context.data)} records")

        except Exception as e:
            if not self.error_handler.handle_error(e, self.context, "transform"):
                raise

    def _validate_stage(self) -> None:
        """Execute validation stage."""
        start_time = time.time()

        try:
            self.logger.info("Stage 3: Validation")

            if not self.context.data:
                self.logger.warning("No data to validate")
                return

            # Run data quality checks
            quality_config = self.config.get("data_quality", {})
            if quality_config:
                quality_checker = DataQualityCheck(quality_config)
                validation_result = quality_checker.validate(self.context.data)

                # Handle validation errors
                if not self.error_handler.handle_validation_errors(
                    validation_result,
                    self.context
                ):
                    raise PipelineException("Data quality validation failed")

                self.context.metadata["data_quality_score"] = \
                    validation_result.metrics.get("overall_score", 100.0)

            self.context.metrics["records_validated"] = len(self.context.data)
            self.context.metrics["validation_time"] = time.time() - start_time

            self.logger.info(f"Validated {len(self.context.data)} records")

        except Exception as e:
            if not self.error_handler.handle_error(e, self.context, "validate"):
                raise

    def _load_stage(self) -> None:
        """Execute loading stage."""
        start_time = time.time()

        try:
            self.logger.info("Stage 4: Loading")

            if not self.context.data:
                self.logger.warning("No data to load")
                return

            # Create loader
            loader = LoaderFactory.create_loader(
                self.job.target,
                {
                    "table_name": self.config.get("target_table"),
                    "batch_size": self.job.batch_size,
                    "key_columns": self.config.get("key_columns", [])
                }
            )

            # Execute loading with retry
            def load():
                with loader:
                    return loader.load(
                        self.context.data,
                        self.job.load_strategy
                    )

            records_loaded = self.retry_logic.execute_with_retry(load)
            self.context.metrics["records_loaded"] = records_loaded
            self.context.metrics["loading_time"] = time.time() - start_time

            self.logger.info(f"Loaded {records_loaded} records")

        except Exception as e:
            if not self.error_handler.handle_error(e, self.context, "load"):
                raise

    def _create_job_run(self) -> JobRun:
        """Create a job run record."""
        job_run = JobRun(
            job_id=self.job.id,
            status=JobStatus.RUNNING,
            started_at=datetime.utcnow(),
            triggered_by=self.config.get("triggered_by", "manual"),
            triggered_by_user=self.config.get("triggered_by_user")
        )
        self.db_session.add(job_run)
        self.db_session.commit()

        self.logger.info(f"Created job run: {job_run.id}")
        return job_run

    def _complete_job_run(self, job_run: JobRun, status: JobStatus) -> None:
        """Complete a job run record."""
        job_run.status = status
        job_run.completed_at = datetime.utcnow()
        job_run.duration_seconds = (
            job_run.completed_at - job_run.started_at
        ).total_seconds()

        # Update metrics
        job_run.records_extracted = self.context.metrics["records_extracted"]
        job_run.records_transformed = self.context.metrics["records_transformed"]
        job_run.records_loaded = self.context.metrics["records_loaded"]
        job_run.records_failed = self.context.metrics["records_failed"]

        job_run.extraction_time_seconds = self.context.metrics["extraction_time"]
        job_run.transformation_time_seconds = self.context.metrics["transformation_time"]
        job_run.loading_time_seconds = self.context.metrics["loading_time"]

        job_run.data_quality_score = self.context.metadata.get("data_quality_score")

        # Update watermark for incremental loads
        if self.job.is_incremental and self.context.data:
            watermark_column = self.job.watermark_column
            if watermark_column:
                # Get max watermark value from loaded data
                watermark_values = [
                    record.get(watermark_column)
                    for record in self.context.data
                    if watermark_column in record
                ]
                if watermark_values:
                    job_run.watermark_value = str(max(watermark_values))
                    self.job.last_watermark_value = job_run.watermark_value

        self.db_session.commit()
        self.logger.info(f"Updated job run: {job_run.id}")

    def _fail_job_run(self, job_run: JobRun, error_message: str) -> None:
        """Mark job run as failed."""
        job_run.status = JobStatus.FAILED
        job_run.completed_at = datetime.utcnow()
        job_run.duration_seconds = (
            job_run.completed_at - job_run.started_at
        ).total_seconds()
        job_run.error_message = error_message
        job_run.error_traceback = traceback.format_exc()
        job_run.error_count = len(self.context.errors)

        # Update available metrics
        job_run.records_extracted = self.context.metrics.get("records_extracted", 0)
        job_run.records_transformed = self.context.metrics.get("records_transformed", 0)
        job_run.records_loaded = self.context.metrics.get("records_loaded", 0)

        self.db_session.commit()
        self.logger.info(f"Marked job run as failed: {job_run.id}")
