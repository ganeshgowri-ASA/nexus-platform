"""
Tests for data synchronization.
"""

import pytest
from datetime import datetime
from unittest.mock import Mock, AsyncMock, patch

from ..sync import DataSync, ConflictResolution
from ..models import SyncJob, SyncDirection, SyncStatus, Connection


class TestDataSync:
    """Test DataSync class."""

    @pytest.fixture
    def db_session(self):
        """Create mock database session."""
        return Mock()

    @pytest.fixture
    def connector(self):
        """Create mock connector."""
        connector = Mock()
        connector.paginate = AsyncMock(return_value=[
            {'id': '1', 'name': 'Test 1'},
            {'id': '2', 'name': 'Test 2'}
        ])
        connector.request = AsyncMock(return_value={'success': True})
        return connector

    @pytest.fixture
    def sync_job(self, db_session):
        """Create test sync job."""
        connection = Connection(
            id=1,
            integration_id=1,
            user_id=1,
            name="Test Connection"
        )

        job = SyncJob(
            id=1,
            connection_id=1,
            direction=SyncDirection.INBOUND,
            entity_type='contact',
            sync_config={'endpoint': '/contacts'},
            filters={}
        )
        job.connection = connection
        return job

    @pytest.mark.asyncio
    async def test_inbound_sync(self, db_session, connector, sync_job):
        """Test inbound synchronization."""
        sync = DataSync(db_session, connector, sync_job)

        await sync.execute()

        assert sync_job.status == SyncStatus.COMPLETED
        assert sync_job.total_records == 2

    @pytest.mark.asyncio
    async def test_transform_record(self, db_session, connector, sync_job):
        """Test record transformation."""
        sync = DataSync(db_session, connector, sync_job)

        record = {'external_id': '123', 'external_name': 'Test'}
        transformed = await sync._transform_record(record, 'inbound')

        # Without mapping, should return original
        assert transformed == record

    def test_get_nested_value(self, db_session, connector, sync_job):
        """Test getting nested values."""
        sync = DataSync(db_session, connector, sync_job)

        data = {
            'user': {
                'name': 'John',
                'address': {
                    'city': 'New York'
                }
            }
        }

        assert sync._get_nested_value(data, 'user.name') == 'John'
        assert sync._get_nested_value(data, 'user.address.city') == 'New York'

    def test_set_nested_value(self, db_session, connector, sync_job):
        """Test setting nested values."""
        sync = DataSync(db_session, connector, sync_job)

        data = {}
        sync._set_nested_value(data, 'user.name', 'John')

        assert data['user']['name'] == 'John'

    @pytest.mark.asyncio
    async def test_conflict_resolution_source_wins(self, db_session, connector, sync_job):
        """Test conflict resolution with source wins."""
        sync = DataSync(db_session, connector, sync_job)
        sync_job.sync_config['conflict_resolution'] = ConflictResolution.SOURCE_WINS

        external = {'id': '1', 'name': 'External Name'}
        nexus = {'id': '1', 'name': 'Nexus Name'}

        sync._transform_record = AsyncMock(return_value=external)
        sync._load_to_nexus = AsyncMock()

        await sync._resolve_conflict(external, nexus)

        sync._load_to_nexus.assert_called_once()
