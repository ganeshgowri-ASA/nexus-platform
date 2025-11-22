"""
Pytest configuration and fixtures for ETL module tests.
"""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from modules.etl.models import Base, DataSource, DataTarget, Mapping, ETLJob, SourceType, DatabaseType, LoadStrategy


@pytest.fixture(scope="session")
def engine():
    """Create test database engine."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    return engine


@pytest.fixture(scope="function")
def db_session(engine):
    """Create database session for tests."""
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.rollback()
    session.close()


@pytest.fixture
def sample_data_source(db_session):
    """Create sample data source."""
    source = DataSource(
        name="Test MySQL Source",
        source_type=SourceType.DATABASE,
        database_type=DatabaseType.MYSQL,
        host="localhost",
        port=3306,
        database_name="test_db",
        username="test_user",
        password="test_pass"
    )
    db_session.add(source)
    db_session.commit()
    return source


@pytest.fixture
def sample_data_target(db_session):
    """Create sample data target."""
    target = DataTarget(
        name="Test PostgreSQL Target",
        target_type=SourceType.DATABASE,
        database_type=DatabaseType.POSTGRESQL,
        host="localhost",
        port=5432,
        database_name="test_db",
        username="test_user",
        password="test_pass",
        load_strategy=LoadStrategy.APPEND
    )
    db_session.add(target)
    db_session.commit()
    return target


@pytest.fixture
def sample_mapping(db_session):
    """Create sample mapping."""
    mapping = Mapping(
        name="Test Mapping",
        field_mappings={"source_field": "target_field"},
        type_conversions={"target_field": "string"}
    )
    db_session.add(mapping)
    db_session.commit()
    return mapping


@pytest.fixture
def sample_etl_job(db_session, sample_data_source, sample_data_target, sample_mapping):
    """Create sample ETL job."""
    job = ETLJob(
        name="Test ETL Job",
        source_id=sample_data_source.id,
        target_id=sample_data_target.id,
        mapping_id=sample_mapping.id,
        extraction_query="SELECT * FROM test_table",
        load_strategy=LoadStrategy.APPEND
    )
    db_session.add(job)
    db_session.commit()
    return job


@pytest.fixture
def sample_data():
    """Sample data for testing."""
    return [
        {"id": 1, "name": "John Doe", "age": 30, "email": "john@example.com"},
        {"id": 2, "name": "Jane Smith", "age": 25, "email": "jane@example.com"},
        {"id": 3, "name": "Bob Johnson", "age": 35, "email": "bob@example.com"}
    ]
