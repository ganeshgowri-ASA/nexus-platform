"""
Tests for data transformers.
"""

import pytest
from modules.etl.transformers import (
    DataCleaner,
    DataValidator,
    DataEnricher,
    DataAggregator,
    DataMapper,
    TypeConverter,
    TransformationPipeline,
    TransformerFactory
)


def test_data_cleaner_basic(sample_data):
    """Test basic data cleaning."""
    cleaner = DataCleaner({"trim_whitespace": True})
    result = cleaner.transform(sample_data)

    assert len(result) == len(sample_data)
    assert all("name" in record for record in result)


def test_data_cleaner_null_handling():
    """Test null value handling."""
    data = [
        {"id": 1, "name": "John", "value": None},
        {"id": 2, "name": None, "value": 100}
    ]

    cleaner = DataCleaner({"fill_null": True, "null_value": "N/A"})
    result = cleaner.transform(data)

    assert result[0]["value"] == "N/A"
    assert result[1]["name"] == "N/A"


def test_data_validator():
    """Test data validation."""
    data = [
        {"id": 1, "name": "John", "age": 30},
        {"id": 2, "name": "Jane", "age": 25}
    ]

    config = {
        "validation_rules": {
            "id": {"required": True, "type": "integer"},
            "name": {"required": True, "type": "string"},
            "age": {"type": "integer", "min": 0, "max": 150}
        }
    }

    validator = DataValidator(config)
    result = validator.transform(data)

    assert len(result) == 2


def test_data_enricher():
    """Test data enrichment."""
    data = [
        {"first_name": "John", "last_name": "Doe"},
        {"first_name": "Jane", "last_name": "Smith"}
    ]

    config = {
        "computed_fields": {
            "full_name": "{first_name} {last_name}"
        },
        "constant_fields": {
            "country": "USA"
        }
    }

    enricher = DataEnricher(config)
    result = enricher.transform(data)

    assert "full_name" in result[0]
    assert result[0]["country"] == "USA"


def test_data_aggregator():
    """Test data aggregation."""
    data = [
        {"category": "A", "value": 10},
        {"category": "A", "value": 20},
        {"category": "B", "value": 30},
        {"category": "B", "value": 40}
    ]

    config = {
        "group_by": ["category"],
        "aggregations": {"value": "sum"}
    }

    aggregator = DataAggregator(config)
    result = aggregator.transform(data)

    assert len(result) == 2
    assert any(r["category"] == "A" and r["value"] == 30 for r in result)
    assert any(r["category"] == "B" and r["value"] == 70 for r in result)


def test_data_mapper():
    """Test field mapping."""
    data = [
        {"old_name": "John", "old_age": 30},
        {"old_name": "Jane", "old_age": 25}
    ]

    config = {
        "field_mappings": {
            "old_name": "name",
            "old_age": "age"
        }
    }

    mapper = DataMapper(config)
    result = mapper.transform(data)

    assert "name" in result[0]
    assert "age" in result[0]
    assert result[0]["name"] == "John"


def test_type_converter():
    """Test type conversion."""
    data = [
        {"id": "123", "age": "30", "active": "true"},
        {"id": "456", "age": "25", "active": "false"}
    ]

    config = {
        "type_conversions": {
            "id": "integer",
            "age": "integer",
            "active": "boolean"
        }
    }

    converter = TypeConverter(config)
    result = converter.transform(data)

    assert isinstance(result[0]["id"], int)
    assert isinstance(result[0]["age"], int)
    assert isinstance(result[0]["active"], bool)
    assert result[0]["active"] is True


def test_transformation_pipeline():
    """Test transformation pipeline."""
    data = [
        {"old_name": "  John  ", "value": None},
        {"old_name": "  Jane  ", "value": None}
    ]

    # Create pipeline
    pipeline = TransformationPipeline()

    # Add transformers
    cleaner = DataCleaner({"trim_whitespace": True, "fill_null": True, "null_value": 0})
    mapper = DataMapper({"field_mappings": {"old_name": "name"}})

    pipeline.add_transformer(cleaner)
    pipeline.add_transformer(mapper)

    # Execute pipeline
    result = pipeline.transform(data)

    assert "name" in result[0]
    assert result[0]["name"] == "John"
    assert result[0]["value"] == 0


def test_transformer_factory():
    """Test transformer factory."""
    # Create cleaner
    cleaner = TransformerFactory.create_transformer("cleaner", {})
    assert isinstance(cleaner, DataCleaner)

    # Create validator
    validator = TransformerFactory.create_transformer("validator", {})
    assert isinstance(validator, DataValidator)

    # Create mapper
    mapper = TransformerFactory.create_transformer("mapper", {})
    assert isinstance(mapper, DataMapper)


def test_create_pipeline_from_config():
    """Test creating pipeline from configuration."""
    config = [
        {"type": "cleaner", "config": {"trim_whitespace": True}},
        {"type": "mapper", "config": {"field_mappings": {"old": "new"}}}
    ]

    pipeline = TransformerFactory.create_pipeline(config)

    assert len(pipeline.transformers) == 2
    assert isinstance(pipeline.transformers[0], DataCleaner)
    assert isinstance(pipeline.transformers[1], DataMapper)
