"""
Tests for the diagram engine.
"""

import pytest
from modules.flowchart.diagram_engine import (
    DiagramEngine, DiagramMetadata, DiagramSettings, Layer
)
from modules.flowchart.shapes import Point, ShapeStyle
from modules.flowchart.connectors import ConnectorType


class TestDiagramEngine:
    """Test DiagramEngine class."""

    def test_engine_initialization(self):
        engine = DiagramEngine()
        assert len(engine.shapes) == 0
        assert len(engine.connectors) == 0
        assert 0 in engine.layers

    def test_add_shape(self):
        engine = DiagramEngine()
        shape = engine.add_shape(
            "flowchart_process",
            Point(100, 100),
            "Test Shape"
        )

        assert shape is not None
        assert len(engine.shapes) == 1
        assert shape.id in engine.shapes

    def test_remove_shape(self):
        engine = DiagramEngine()
        shape = engine.add_shape("basic_rectangle", Point(0, 0))

        assert len(engine.shapes) == 1

        removed = engine.remove_shape(shape.id)
        assert removed
        assert len(engine.shapes) == 0

    def test_update_shape(self):
        engine = DiagramEngine()
        shape = engine.add_shape("basic_circle", Point(50, 50))

        new_position = Point(100, 100)
        engine.update_shape(shape.id, position=new_position)

        updated_shape = engine.get_shape(shape.id)
        assert updated_shape.position.x == 100
        assert updated_shape.position.y == 100

    def test_move_shape(self):
        engine = DiagramEngine()
        shape = engine.add_shape("basic_square", Point(50, 50))

        engine.move_shape(shape.id, 25, 30)

        moved_shape = engine.get_shape(shape.id)
        assert moved_shape.position.x == 75
        assert moved_shape.position.y == 80

    def test_add_connector(self):
        engine = DiagramEngine()

        shape1 = engine.add_shape("flowchart_process", Point(100, 100))
        shape2 = engine.add_shape("flowchart_process", Point(100, 250))

        connector = engine.add_connector(
            ConnectorType.STRAIGHT,
            shape1.id,
            shape2.id
        )

        assert connector is not None
        assert len(engine.connectors) == 1
        assert connector.source_shape_id == shape1.id
        assert connector.target_shape_id == shape2.id

    def test_remove_connector(self):
        engine = DiagramEngine()

        shape1 = engine.add_shape("basic_rectangle", Point(0, 0))
        shape2 = engine.add_shape("basic_rectangle", Point(100, 100))

        connector = engine.add_connector(
            ConnectorType.ELBOW,
            shape1.id,
            shape2.id
        )

        assert len(engine.connectors) == 1

        removed = engine.remove_connector(connector.id)
        assert removed
        assert len(engine.connectors) == 0

    def test_remove_shape_removes_connectors(self):
        engine = DiagramEngine()

        shape1 = engine.add_shape("flowchart_terminator", Point(100, 50))
        shape2 = engine.add_shape("flowchart_process", Point(100, 150))

        engine.add_connector(ConnectorType.STRAIGHT, shape1.id, shape2.id)

        assert len(engine.connectors) == 1

        engine.remove_shape(shape1.id)

        assert len(engine.shapes) == 1
        assert len(engine.connectors) == 0  # Connector should be removed

    def test_get_connected_shapes(self):
        engine = DiagramEngine()

        shape1 = engine.add_shape("flowchart_process", Point(100, 100))
        shape2 = engine.add_shape("flowchart_decision", Point(100, 200))
        shape3 = engine.add_shape("flowchart_process", Point(100, 300))

        engine.add_connector(ConnectorType.STRAIGHT, shape1.id, shape2.id)
        engine.add_connector(ConnectorType.STRAIGHT, shape2.id, shape3.id)

        connected = engine.get_connected_shapes(shape2.id)

        assert len(connected) == 2

        connected_ids = [sid for sid, _ in connected]
        assert shape1.id in connected_ids
        assert shape3.id in connected_ids

    def test_layer_management(self):
        engine = DiagramEngine()

        layer1 = engine.add_layer("Layer 1")
        assert layer1.name == "Layer 1"
        assert layer1.id in engine.layers

        layer2 = engine.add_layer("Layer 2")
        assert len(engine.layers) == 3  # Default + 2 new

        removed = engine.remove_layer(layer1.id)
        assert removed
        assert len(engine.layers) == 2

    def test_layer_visibility(self):
        engine = DiagramEngine()
        layer = engine.add_layer("Test Layer")

        assert layer.visible

        engine.set_layer_visibility(layer.id, False)
        assert not engine.layers[layer.id].visible

    def test_selection(self):
        engine = DiagramEngine()

        shape1 = engine.add_shape("basic_rectangle", Point(0, 0))
        shape2 = engine.add_shape("basic_circle", Point(100, 100))

        engine.select(shape1.id)
        assert shape1.id in engine.selection

        engine.select(shape2.id)
        assert len(engine.selection) == 2

        engine.deselect(shape1.id)
        assert shape1.id not in engine.selection
        assert len(engine.selection) == 1

        engine.clear_selection()
        assert len(engine.selection) == 0

    def test_select_all(self):
        engine = DiagramEngine()

        engine.add_shape("basic_rectangle", Point(0, 0))
        engine.add_shape("basic_circle", Point(100, 100))

        engine.select_all()

        assert len(engine.selection) == 2

    def test_serialization(self):
        engine = DiagramEngine()
        engine.metadata.title = "Test Diagram"

        shape1 = engine.add_shape("flowchart_process", Point(100, 100), "Step 1")
        shape2 = engine.add_shape("flowchart_decision", Point(100, 200), "Check?")

        engine.add_connector(ConnectorType.STRAIGHT, shape1.id, shape2.id)

        # Serialize to dict
        data = engine.to_dict()
        assert data["metadata"]["title"] == "Test Diagram"
        assert len(data["shapes"]) == 2
        assert len(data["connectors"]) == 1

        # Deserialize
        engine2 = DiagramEngine.from_dict(data)
        assert engine2.metadata.title == "Test Diagram"
        assert len(engine2.shapes) == 2
        assert len(engine2.connectors) == 1

    def test_undo_redo(self):
        engine = DiagramEngine()

        shape = engine.add_shape("basic_rectangle", Point(100, 100))
        assert len(engine.shapes) == 1

        assert engine.can_undo()

        engine.undo()
        assert len(engine.shapes) == 0

        assert engine.can_redo()

        engine.redo()
        assert len(engine.shapes) == 1

    def test_statistics(self):
        engine = DiagramEngine()

        engine.add_shape("flowchart_process", Point(100, 100))
        engine.add_shape("flowchart_decision", Point(100, 200))

        stats = engine.get_statistics()

        assert stats["total_shapes"] == 2
        assert stats["total_connectors"] == 0
        assert stats["total_layers"] >= 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
