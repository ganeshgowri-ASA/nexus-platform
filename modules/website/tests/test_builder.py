"""
Tests for website builder functionality
"""

import pytest
from datetime import datetime
from modules.website.builder import (
    WebsiteBuilder,
    BuilderConfig,
    BuilderState,
    ComponentState,
    DeviceType,
    BuilderMode,
)


def test_builder_config_creation():
    """Test builder configuration creation"""
    config = BuilderConfig(
        project_id="test_project",
        project_name="Test Website",
    )

    assert config.project_id == "test_project"
    assert config.project_name == "Test Website"
    assert config.auto_save is True
    assert config.max_pages == 100


def test_builder_initialization():
    """Test builder initialization"""
    config = BuilderConfig(
        project_id="test_project",
        project_name="Test Website",
    )

    builder = WebsiteBuilder(config)

    assert builder.config == config
    assert builder.state is None
    assert builder.last_save is None


def test_create_project():
    """Test project creation"""
    config = BuilderConfig(
        project_id="test_project",
        project_name="Test Website",
    )

    builder = WebsiteBuilder(config)
    project = builder.create_project()

    assert project["project_id"] == "test_project"
    assert project["project_name"] == "Test Website"
    assert "created_at" in project
    assert "config" in project


def test_initialize_builder():
    """Test builder initialization for a page"""
    config = BuilderConfig(
        project_id="test_project",
        project_name="Test Website",
    )

    builder = WebsiteBuilder(config)
    state = builder.initialize_builder("page_001")

    assert state.page_id == "page_001"
    assert len(state.components) == 0
    assert state.device_type == DeviceType.DESKTOP
    assert state.mode == BuilderMode.DESIGN


def test_add_component():
    """Test adding a component"""
    config = BuilderConfig(
        project_id="test_project",
        project_name="Test Website",
    )

    builder = WebsiteBuilder(config)
    builder.initialize_builder("page_001")

    component = builder.add_component(
        component_type="button",
        position={"x": 100, "y": 100, "width": 200, "height": 50},
        properties={"text": "Click Me"},
        styles={"background": "#007bff"},
    )

    assert component.component_type == "button"
    assert component.position["x"] == 100
    assert component.properties["text"] == "Click Me"
    assert component.styles["background"] == "#007bff"


def test_remove_component():
    """Test removing a component"""
    config = BuilderConfig(
        project_id="test_project",
        project_name="Test Website",
    )

    builder = WebsiteBuilder(config)
    builder.initialize_builder("page_001")

    component = builder.add_component(
        component_type="button",
        position={"x": 100, "y": 100, "width": 200, "height": 50},
    )

    assert len(builder.state.components) == 1

    result = builder.remove_component(component.component_id)

    assert result is True
    assert len(builder.state.components) == 0


def test_update_component():
    """Test updating component properties"""
    config = BuilderConfig(
        project_id="test_project",
        project_name="Test Website",
    )

    builder = WebsiteBuilder(config)
    builder.initialize_builder("page_001")

    component = builder.add_component(
        component_type="button",
        position={"x": 100, "y": 100, "width": 200, "height": 50},
        properties={"text": "Click Me"},
    )

    updated = builder.update_component(
        component.component_id,
        properties={"text": "Updated Text"},
    )

    assert updated.properties["text"] == "Updated Text"


def test_duplicate_component():
    """Test duplicating a component"""
    config = BuilderConfig(
        project_id="test_project",
        project_name="Test Website",
    )

    builder = WebsiteBuilder(config)
    builder.initialize_builder("page_001")

    original = builder.add_component(
        component_type="button",
        position={"x": 100, "y": 100, "width": 200, "height": 50},
        properties={"text": "Click Me"},
    )

    duplicate = builder.duplicate_component(original.component_id)

    assert duplicate is not None
    assert duplicate.component_id != original.component_id
    assert duplicate.component_type == original.component_type
    assert duplicate.properties["text"] == original.properties["text"]
    assert len(builder.state.components) == 2


def test_lock_component():
    """Test locking a component"""
    config = BuilderConfig(
        project_id="test_project",
        project_name="Test Website",
    )

    builder = WebsiteBuilder(config)
    builder.initialize_builder("page_001")

    component = builder.add_component(
        component_type="button",
        position={"x": 100, "y": 100, "width": 200, "height": 50},
    )

    result = builder.lock_component(component.component_id)

    assert result is True
    assert component.locked is True

    # Should not be able to remove locked component
    remove_result = builder.remove_component(component.component_id)
    assert remove_result is False


def test_save_and_load_state():
    """Test saving and loading builder state"""
    config = BuilderConfig(
        project_id="test_project",
        project_name="Test Website",
    )

    builder = WebsiteBuilder(config)
    builder.initialize_builder("page_001")

    builder.add_component(
        component_type="button",
        position={"x": 100, "y": 100, "width": 200, "height": 50},
        properties={"text": "Click Me"},
    )

    # Save state
    saved_data = builder.save_state()

    assert "state" in saved_data
    assert "saved_at" in saved_data

    # Create new builder and load state
    new_builder = WebsiteBuilder(config)
    result = new_builder.load_state(saved_data)

    assert result is True
    assert new_builder.state.page_id == "page_001"
    assert len(new_builder.state.components) == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
