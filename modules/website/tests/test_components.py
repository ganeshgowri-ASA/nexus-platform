"""
Tests for component library
"""

import pytest
from modules.website.components import ComponentLibrary, ComponentCategory


def test_component_library_initialization():
    """Test component library initialization"""
    library = ComponentLibrary()

    assert len(library.components) > 0
    assert library.get_component_count() >= 100


def test_get_component():
    """Test getting a specific component"""
    library = ComponentLibrary()

    component = library.get_component("button")

    assert component is not None
    assert component.component_id == "button"
    assert component.name == "Button"


def test_get_components_by_category():
    """Test getting components by category"""
    library = ComponentLibrary()

    layout_components = library.get_components_by_category(ComponentCategory.LAYOUT)

    assert len(layout_components) > 0
    assert all(c.category == ComponentCategory.LAYOUT for c in layout_components)


def test_search_components():
    """Test searching components"""
    library = ComponentLibrary()

    results = library.search_components("button")

    assert len(results) > 0
    assert any("button" in c.name.lower() for c in results)


def test_component_properties():
    """Test component property definitions"""
    library = ComponentLibrary()

    button = library.get_component("button")

    assert len(button.properties) > 0
    assert any(prop.name == "text" for prop in button.properties)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
