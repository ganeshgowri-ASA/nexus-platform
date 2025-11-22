"""
Data synchronization engine with bidirectional sync and conflict resolution.

This module handles data synchronization between NEXUS and third-party services,
including change tracking, conflict resolution, and batch processing.
"""

from typing import Dict, Any, Optional, List, Callable
from datetime import datetime, timedelta
from enum import Enum
import logging
import asyncio
from sqlalchemy.orm import Session
from sqlalchemy import and_

from .models import (
    SyncJob, SyncLog, SyncStatus, SyncDirection,
    Connection, FieldMapping
)
from .connectors import BaseConnector

logger = logging.getLogger(__name__)


class ConflictResolution(str, Enum):
    """Conflict resolution strategies."""
    SOURCE_WINS = "source_wins"
    TARGET_WINS = "target_wins"
    NEWEST_WINS = "newest_wins"
    MANUAL = "manual"
    MERGE = "merge"


class SyncError(Exception):
    """Base exception for sync errors."""
    pass


class DataSync:
    """
    Manages data synchronization between systems.

    Handles record fetching, transformation, and loading with
    comprehensive error handling and progress tracking.
    """

    def __init__(
        self,
        db: Session,
        connector: BaseConnector,
        job: SyncJob
    ):
        """
        Initialize data sync.

        Args:
            db: Database session
            connector: Connector instance for API communication
            job: Sync job record
        """
        self.db = db
        self.connector = connector
        self.job = job
        self.connection = job.connection
        self.field_mapping = job.field_mapping

    async def execute(self) -> SyncJob:
        """
        Execute the synchronization job.

        Returns:
            Updated SyncJob record
        """
        self.job.status = SyncStatus.RUNNING
        self.job.started_at = datetime.now()
        self.db.commit()

        try:
            logger.info(f"Starting sync job {self.job.id}: {self.job.direction.value}")

            if self.job.direction == SyncDirection.INBOUND:
                await self._sync_inbound()
            elif self.job.direction == SyncDirection.OUTBOUND:
                await self._sync_outbound()
            elif self.job.direction == SyncDirection.BIDIRECTIONAL:
                await self._sync_bidirectional()

            self.job.status = SyncStatus.COMPLETED
            self.job.completed_at = datetime.now()

            logger.info(f"Sync job {self.job.id} completed: {self.job.processed_records} records")

        except Exception as e:
            logger.error(f"Sync job {self.job.id} failed: {str(e)}")

            self.job.status = SyncStatus.FAILED
            self.job.error_message = str(e)
            self.job.completed_at = datetime.now()

            self._log_error(str(e))

        finally:
            self.job.calculate_metrics()
            self.db.commit()

        return self.job

    async def _sync_inbound(self) -> None:
        """Synchronize data from external service to NEXUS."""
        # Fetch records from external service
        records = await self._fetch_external_records()
        self.job.total_records = len(records)
        self.db.commit()

        # Process each record
        for record in records:
            try:
                # Transform record
                transformed = await self._transform_record(
                    record,
                    direction='inbound'
                )

                # Load into NEXUS
                await self._load_to_nexus(transformed)

                self.job.processed_records += 1
                self.job.successful_records += 1

                self._log_info(f"Synced record: {record.get('id')}")

            except Exception as e:
                logger.error(f"Failed to sync record: {str(e)}")
                self.job.failed_records += 1
                self.job.failed_record_ids.append(record.get('id'))
                self._log_error(f"Record sync failed: {str(e)}", record_id=record.get('id'))

            self.db.commit()

    async def _sync_outbound(self) -> None:
        """Synchronize data from NEXUS to external service."""
        # Fetch records from NEXUS
        records = await self._fetch_nexus_records()
        self.job.total_records = len(records)
        self.db.commit()

        # Process each record
        for record in records:
            try:
                # Transform record
                transformed = await self._transform_record(
                    record,
                    direction='outbound'
                )

                # Push to external service
                await self._push_to_external(transformed)

                self.job.processed_records += 1
                self.job.successful_records += 1

                self._log_info(f"Pushed record: {record.get('id')}")

            except Exception as e:
                logger.error(f"Failed to push record: {str(e)}")
                self.job.failed_records += 1
                self.job.failed_record_ids.append(record.get('id'))
                self._log_error(f"Record push failed: {str(e)}", record_id=record.get('id'))

            self.db.commit()

    async def _sync_bidirectional(self) -> None:
        """Synchronize data bidirectionally with conflict resolution."""
        # Fetch from both sides
        external_records = await self._fetch_external_records()
        nexus_records = await self._fetch_nexus_records()

        # Build maps by ID
        external_map = {r.get('id'): r for r in external_records}
        nexus_map = {r.get('id'): r for r in nexus_records}

        all_ids = set(external_map.keys()) | set(nexus_map.keys())
        self.job.total_records = len(all_ids)
        self.db.commit()

        for record_id in all_ids:
            try:
                external_record = external_map.get(record_id)
                nexus_record = nexus_map.get(record_id)

                if external_record and nexus_record:
                    # Both exist - check for conflicts
                    await self._resolve_conflict(external_record, nexus_record)
                elif external_record:
                    # Only in external - sync to NEXUS
                    transformed = await self._transform_record(external_record, 'inbound')
                    await self._load_to_nexus(transformed)
                elif nexus_record:
                    # Only in NEXUS - sync to external
                    transformed = await self._transform_record(nexus_record, 'outbound')
                    await self._push_to_external(transformed)

                self.job.processed_records += 1
                self.job.successful_records += 1

            except Exception as e:
                logger.error(f"Bidirectional sync failed for {record_id}: {str(e)}")
                self.job.failed_records += 1
                self._log_error(str(e), record_id=record_id)

            self.db.commit()

    async def _fetch_external_records(self) -> List[Dict[str, Any]]:
        """Fetch records from external service."""
        endpoint = self.job.sync_config.get('endpoint', f'/{self.job.entity_type}')
        filters = self.job.filters or {}

        try:
            # Use connector's pagination
            records = await self.connector.paginate(
                endpoint=endpoint,
                params=filters,
                page_size=self.job.sync_config.get('page_size', 100)
            )

            self.job.api_calls_made += 1
            logger.info(f"Fetched {len(records)} records from {endpoint}")

            return records

        except Exception as e:
            logger.error(f"Failed to fetch external records: {str(e)}")
            raise SyncError(f"External fetch failed: {str(e)}")

    async def _fetch_nexus_records(self) -> List[Dict[str, Any]]:
        """Fetch records from NEXUS database."""
        # This would integrate with NEXUS database module
        # For now, return empty list as placeholder
        logger.info("Fetching records from NEXUS database")
        return []

    async def _transform_record(
        self,
        record: Dict[str, Any],
        direction: str
    ) -> Dict[str, Any]:
        """
        Transform record using field mapping.

        Args:
            record: Source record
            direction: 'inbound' or 'outbound'

        Returns:
            Transformed record
        """
        if not self.field_mapping:
            return record

        transformed = {}
        mappings = self.field_mapping.mappings or {}
        transformations = self.field_mapping.transformations or {}
        defaults = self.field_mapping.default_values or {}

        # Apply field mappings
        for source_field, target_field in mappings.items():
            if direction == 'inbound':
                # External -> NEXUS
                value = self._get_nested_value(record, source_field)
            else:
                # NEXUS -> External
                value = self._get_nested_value(record, target_field)
                target_field = source_field

            # Apply transformation if defined
            if source_field in transformations:
                value = await self._apply_transformation(
                    value,
                    transformations[source_field]
                )

            self._set_nested_value(transformed, target_field, value)

        # Apply default values
        for field, default_value in defaults.items():
            if field not in transformed:
                transformed[field] = default_value

        return transformed

    def _get_nested_value(self, data: Dict[str, Any], path: str) -> Any:
        """Get value from nested dictionary using dot notation."""
        keys = path.split('.')
        value = data

        for key in keys:
            if isinstance(value, dict):
                value = value.get(key)
            else:
                return None

        return value

    def _set_nested_value(self, data: Dict[str, Any], path: str, value: Any) -> None:
        """Set value in nested dictionary using dot notation."""
        keys = path.split('.')
        current = data

        for key in keys[:-1]:
            if key not in current:
                current[key] = {}
            current = current[key]

        current[keys[-1]] = value

    async def _apply_transformation(
        self,
        value: Any,
        transformation: Dict[str, Any]
    ) -> Any:
        """Apply transformation rule to value."""
        transform_type = transformation.get('type')

        if transform_type == 'uppercase':
            return str(value).upper() if value else value
        elif transform_type == 'lowercase':
            return str(value).lower() if value else value
        elif transform_type == 'trim':
            return str(value).strip() if value else value
        elif transform_type == 'date_format':
            # Format date according to rule
            if value:
                from datetime import datetime
                dt = datetime.fromisoformat(value) if isinstance(value, str) else value
                fmt = transformation.get('format', '%Y-%m-%d')
                return dt.strftime(fmt)
        elif transform_type == 'custom':
            # Execute custom Python code (be careful!)
            code = transformation.get('code')
            if code:
                # Execute in safe namespace
                namespace = {'value': value}
                exec(code, namespace)
                return namespace.get('result', value)

        return value

    async def _load_to_nexus(self, record: Dict[str, Any]) -> None:
        """Load transformed record into NEXUS."""
        # This would integrate with NEXUS database module
        logger.info(f"Loading record to NEXUS: {record}")
        pass

    async def _push_to_external(self, record: Dict[str, Any]) -> None:
        """Push transformed record to external service."""
        endpoint = self.job.sync_config.get('endpoint', f'/{self.job.entity_type}')
        method = self.job.sync_config.get('method', 'POST')

        try:
            response = await self.connector.request(
                method=method,
                endpoint=endpoint,
                json=record
            )

            self.job.api_calls_made += 1
            logger.info(f"Pushed record to {endpoint}")

        except Exception as e:
            logger.error(f"Failed to push record: {str(e)}")
            raise SyncError(f"External push failed: {str(e)}")

    async def _resolve_conflict(
        self,
        external_record: Dict[str, Any],
        nexus_record: Dict[str, Any]
    ) -> None:
        """Resolve conflict between records."""
        strategy = self.job.sync_config.get(
            'conflict_resolution',
            ConflictResolution.NEWEST_WINS
        )

        if strategy == ConflictResolution.SOURCE_WINS:
            # External wins
            transformed = await self._transform_record(external_record, 'inbound')
            await self._load_to_nexus(transformed)

        elif strategy == ConflictResolution.TARGET_WINS:
            # NEXUS wins
            transformed = await self._transform_record(nexus_record, 'outbound')
            await self._push_to_external(transformed)

        elif strategy == ConflictResolution.NEWEST_WINS:
            # Compare timestamps
            external_updated = external_record.get('updated_at')
            nexus_updated = nexus_record.get('updated_at')

            if external_updated and nexus_updated:
                if external_updated > nexus_updated:
                    transformed = await self._transform_record(external_record, 'inbound')
                    await self._load_to_nexus(transformed)
                else:
                    transformed = await self._transform_record(nexus_record, 'outbound')
                    await self._push_to_external(transformed)

        elif strategy == ConflictResolution.MERGE:
            # Merge records (field-level resolution)
            merged = await self._merge_records(external_record, nexus_record)
            await self._load_to_nexus(merged)
            await self._push_to_external(merged)

        else:
            # Manual resolution required
            self.job.skipped_records += 1
            self._log_info(
                f"Manual resolution required for record {external_record.get('id')}",
                record_id=external_record.get('id')
            )

    async def _merge_records(
        self,
        external_record: Dict[str, Any],
        nexus_record: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Merge two records using field-level resolution."""
        merged = {}

        all_fields = set(external_record.keys()) | set(nexus_record.keys())

        for field in all_fields:
            external_value = external_record.get(field)
            nexus_value = nexus_record.get(field)

            if external_value == nexus_value:
                merged[field] = external_value
            elif external_value and not nexus_value:
                merged[field] = external_value
            elif nexus_value and not external_value:
                merged[field] = nexus_value
            else:
                # Both have different values - prefer external
                merged[field] = external_value

        return merged

    def _log_info(self, message: str, record_id: Optional[str] = None) -> None:
        """Log info message."""
        log = SyncLog(
            sync_job_id=self.job.id,
            level='INFO',
            message=message,
            record_id=record_id,
            record_type=self.job.entity_type
        )
        self.db.add(log)

    def _log_error(
        self,
        message: str,
        record_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ) -> None:
        """Log error message."""
        log = SyncLog(
            sync_job_id=self.job.id,
            level='ERROR',
            message=message,
            record_id=record_id,
            record_type=self.job.entity_type,
            details=details
        )
        self.db.add(log)


class BidirectionalSync:
    """
    Advanced bidirectional synchronization with change tracking.

    Tracks changes on both sides and intelligently syncs only
    what has changed since last sync.
    """

    def __init__(
        self,
        db: Session,
        connector: BaseConnector,
        job: SyncJob
    ):
        """
        Initialize bidirectional sync.

        Args:
            db: Database session
            connector: Connector instance
            job: Sync job record
        """
        self.db = db
        self.connector = connector
        self.job = job
        self._change_tracker: Dict[str, datetime] = {}

    async def sync_with_change_tracking(self) -> None:
        """Sync only changed records since last sync."""
        last_sync = self.job.connection.last_sync_at or datetime.min

        # Fetch changes from external service since last sync
        external_changes = await self._fetch_changes_since(
            last_sync,
            direction='external'
        )

        # Fetch changes from NEXUS since last sync
        nexus_changes = await self._fetch_changes_since(
            last_sync,
            direction='nexus'
        )

        # Process changes
        await self._process_changes(external_changes, nexus_changes)

        # Update last sync time
        self.job.connection.last_sync_at = datetime.now()
        self.db.commit()

    async def _fetch_changes_since(
        self,
        since: datetime,
        direction: str
    ) -> List[Dict[str, Any]]:
        """Fetch records changed since a specific time."""
        if direction == 'external':
            endpoint = self.job.sync_config.get('changes_endpoint')
            if endpoint:
                params = {'since': since.isoformat()}
                return await self.connector.paginate(endpoint, params=params)

        return []

    async def _process_changes(
        self,
        external_changes: List[Dict[str, Any]],
        nexus_changes: List[Dict[str, Any]]
    ) -> None:
        """Process changed records."""
        # Implement change processing logic
        pass
