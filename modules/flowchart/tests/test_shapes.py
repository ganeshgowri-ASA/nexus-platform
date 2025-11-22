"""
Comprehensive tests for the shapes module.
"""

import pytest
from modules.flowchart.shapes import (
    Shape, Point, ShapeStyle, ShapeCategory,
    ConnectorAnchor, shape_library
)


class TestPoint:
    """Test Point class."""

    def test_point_creation(self):
        p = Point(10.0, 20.0)
        assert p.x == 10.0
        assert p.y == 20.0

    def test_point_to_dict(self):
        p = Point(15.5, 25.5)
        d = p.to_dict()
        assert d == {"x": 15.5, "y": 25.5}

    def test_point_from_dict(self):
        p = Point.from_dict({"x": 30.0, "y": 40.0})
        assert p.x == 30.0
        assert p.y == 40.0


class TestShapeStyle:
    """Test ShapeStyle class."""

    def test_default_style(self):
        style = ShapeStyle()
        assert style.fill_color == "#FFFFFF"
        assert style.stroke_color == "#000000"
        assert style.stroke_width == 2.0
        assert style.opacity == 1.0

    def test_custom_style(self):
        style = ShapeStyle(
            fill_color="#FF0000",
            stroke_width=5.0
        )
        assert style.fill_color == "#FF0000"
        assert style.stroke_width == 5.0

    def test_style_serialization(self):
        style = ShapeStyle(fill_color="#00FF00")
        d = style.to_dict()
        assert d["fill_color"] == "#00FF00"

        style2 = ShapeStyle.from_dict(d)
        assert style2.fill_color == "#00FF00"


class TestShape:
    """Test Shape class."""

    def test_shape_creation(self):
        shape = Shape(
            id="test1",
            shape_type="flowchart_process",
            category=ShapeCategory.FLOWCHART,
            position=Point(100, 100),
            width=120,
            height=60
        )
        assert shape.id == "test1"
        assert shape.shape_type == "flowchart_process"
        assert shape.width == 120
        assert shape.height == 60

    def test_shape_bounds(self):
        shape = Shape(
            id="test2",
            shape_type="basic_rectangle",
            category=ShapeCategory.BASIC,
            position=Point(50, 50),
            width=100,
            height=80
        )
        min_p, max_p = shape.get_bounds()
        assert min_p.x == 50
        assert min_p.y == 50
        assert max_p.x == 150
        assert max_p.y == 130

    def test_shape_contains_point(self):
        shape = Shape(
            id="test3",
            shape_type="basic_circle",
            category=ShapeCategory.BASIC,
            position=Point(0, 0),
            width=100,
            height=100
        )
        assert shape.contains_point(Point(50, 50))
        assert not shape.contains_point(Point(150, 150))

    def test_shape_anchor_positions(self):
        shape = Shape(
            id="test4",
            shape_type="basic_rectangle",
            category=ShapeCategory.BASIC,
            position=Point(0, 0),
            width=100,
            height=100
        )

        top = shape.get_anchor_position(ConnectorAnchor.TOP)
        assert top.x == 50
        assert top.y == 0

        center = shape.get_anchor_position(ConnectorAnchor.CENTER)
        assert center.x == 50
        assert center.y == 50

    def test_shape_serialization(self):
        shape = Shape(
            id="test5",
            shape_type="flowchart_decision",
            category=ShapeCategory.FLOWCHART,
            position=Point(200, 200),
            width=120,
            height=80,
            text="Test Decision"
        )

        d = shape.to_dict()
        assert d["id"] == "test5"
        assert d["text"] == "Test Decision"

        shape2 = Shape.from_dict(d)
        assert shape2.id == "test5"
        assert shape2.text == "Test Decision"


class TestShapeLibrary:
    """Test ShapeLibrary class."""

    def test_library_initialization(self):
        assert len(shape_library.shapes) > 100

    def test_get_shape_definition(self):
        shape_def = shape_library.get_shape_definition("flowchart_process")
        assert shape_def is not None
        assert shape_def["name"] == "Process"
        assert shape_def["category"] == ShapeCategory.FLOWCHART

    def test_get_shapes_by_category(self):
        flowchart_shapes = shape_library.get_shapes_by_category(ShapeCategory.FLOWCHART)
        assert len(flowchart_shapes) > 0

        for shape_id, shape_def in flowchart_shapes.items():
            assert shape_def["category"] == ShapeCategory.FLOWCHART

    def test_create_shape_instance(self):
        shape = shape_library.create_shape_instance(
            "flowchart_process",
            "inst1",
            Point(100, 100),
            "Test Process"
        )

        assert shape is not None
        assert shape.id == "inst1"
        assert shape.text == "Test Process"
        assert shape.shape_type == "flowchart_process"

    def test_search_shapes(self):
        results = shape_library.search_shapes("decision")
        assert len(results) > 0

        # Should find flowchart decision
        found_decision = any(
            "decision" in shape_def["name"].lower()
            for _, shape_def in results
        )
        assert found_decision

    def test_get_all_categories(self):
        categories = shape_library.get_all_categories()
        assert ShapeCategory.FLOWCHART in categories
        assert ShapeCategory.UML in categories
        assert ShapeCategory.NETWORK in categories

    def test_shape_count(self):
        count = shape_library.get_shape_count()
        assert count >= 100  # We claim 100+ shapes


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
