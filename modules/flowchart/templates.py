"""
Pre-built diagram templates for common use cases.
Includes templates for flowcharts, org charts, network diagrams, and more.
"""

from typing import Dict, List, Any
from .diagram_engine import DiagramEngine
from .shapes import Point, ShapeStyle, ShapeCategory
from .connectors import ConnectorType, ConnectorStyle, ArrowType


class DiagramTemplate:
    """Base class for diagram templates."""

    def __init__(self, name: str, description: str, category: str):
        self.name = name
        self.description = description
        self.category = category

    def create(self) -> DiagramEngine:
        """Create a new diagram from this template."""
        raise NotImplementedError


class BasicFlowchartTemplate(DiagramTemplate):
    """Simple flowchart template."""

    def __init__(self):
        super().__init__(
            "Basic Flowchart",
            "Simple flowchart with start, process, decision, and end",
            "flowchart"
        )

    def create(self) -> DiagramEngine:
        engine = DiagramEngine()
        engine.metadata.title = self.name

        # Start
        start = engine.add_shape(
            "flowchart_terminator",
            Point(300, 50),
            "Start",
            ShapeStyle(fill_color="#90EE90")
        )

        # Process 1
        process1 = engine.add_shape(
            "flowchart_process",
            Point(270, 150),
            "Process Data",
            ShapeStyle(fill_color="#87CEEB")
        )

        # Decision
        decision = engine.add_shape(
            "flowchart_decision",
            Point(270, 270),
            "Valid?",
            ShapeStyle(fill_color="#FFD700")
        )

        # Process 2
        process2 = engine.add_shape(
            "flowchart_process",
            Point(270, 400),
            "Save Result",
            ShapeStyle(fill_color="#87CEEB")
        )

        # End
        end = engine.add_shape(
            "flowchart_terminator",
            Point(300, 500),
            "End",
            ShapeStyle(fill_color="#FFB6C1")
        )

        # Error handling
        error = engine.add_shape(
            "flowchart_process",
            Point(500, 270),
            "Handle Error",
            ShapeStyle(fill_color="#FFA07A")
        )

        # Connectors
        if start and process1:
            engine.add_connector(ConnectorType.STRAIGHT, start.id, process1.id)
        if process1 and decision:
            engine.add_connector(ConnectorType.STRAIGHT, process1.id, decision.id)
        if decision and process2:
            conn = engine.add_connector(ConnectorType.STRAIGHT, decision.id, process2.id)
            if conn:
                conn.labels.append(type('Label', (), {"text": "Yes", "position": 0.5, "offset_x": -20, "offset_y": 0})())
        if decision and error:
            conn = engine.add_connector(ConnectorType.ELBOW, decision.id, error.id)
            if conn:
                conn.labels.append(type('Label', (), {"text": "No", "position": 0.5, "offset_x": 0, "offset_y": -10})())
        if process2 and end:
            engine.add_connector(ConnectorType.STRAIGHT, process2.id, end.id)
        if error and end:
            engine.add_connector(ConnectorType.ELBOW, error.id, end.id)

        return engine


class OrgChartTemplate(DiagramTemplate):
    """Organization chart template."""

    def __init__(self):
        super().__init__(
            "Organization Chart",
            "Corporate organizational hierarchy",
            "org_chart"
        )

    def create(self) -> DiagramEngine:
        engine = DiagramEngine()
        engine.metadata.title = self.name

        # CEO
        ceo = engine.add_shape(
            "org_executive",
            Point(300, 50),
            "CEO",
            ShapeStyle(fill_color="#4A90E2", font_color="#FFFFFF")
        )

        # VPs
        vp_ops = engine.add_shape(
            "org_manager",
            Point(100, 180),
            "VP Operations",
            ShapeStyle(fill_color="#7ED321")
        )

        vp_eng = engine.add_shape(
            "org_manager",
            Point(320, 180),
            "VP Engineering",
            ShapeStyle(fill_color="#7ED321")
        )

        vp_sales = engine.add_shape(
            "org_manager",
            Point(540, 180),
            "VP Sales",
            ShapeStyle(fill_color="#7ED321")
        )

        # Managers
        mgr1 = engine.add_shape(
            "org_employee",
            Point(50, 300),
            "Manager 1",
            ShapeStyle(fill_color="#F8E71C")
        )

        mgr2 = engine.add_shape(
            "org_employee",
            Point(200, 300),
            "Manager 2",
            ShapeStyle(fill_color="#F8E71C")
        )

        mgr3 = engine.add_shape(
            "org_employee",
            Point(300, 300),
            "Manager 3",
            ShapeStyle(fill_color="#F8E71C")
        )

        mgr4 = engine.add_shape(
            "org_employee",
            Point(450, 300),
            "Manager 4",
            ShapeStyle(fill_color="#F8E71C")
        )

        # Connectors
        if ceo:
            for vp in [vp_ops, vp_eng, vp_sales]:
                if vp:
                    engine.add_connector(ConnectorType.STRAIGHT, ceo.id, vp.id)

        if vp_ops:
            for mgr in [mgr1, mgr2]:
                if mgr:
                    engine.add_connector(ConnectorType.STRAIGHT, vp_ops.id, mgr.id)

        if vp_eng and mgr3:
            engine.add_connector(ConnectorType.STRAIGHT, vp_eng.id, mgr3.id)

        if vp_sales and mgr4:
            engine.add_connector(ConnectorType.STRAIGHT, vp_sales.id, mgr4.id)

        return engine


class NetworkDiagramTemplate(DiagramTemplate):
    """Network architecture template."""

    def __init__(self):
        super().__init__(
            "Network Diagram",
            "Basic network infrastructure layout",
            "network"
        )

    def create(self) -> DiagramEngine:
        engine = DiagramEngine()
        engine.metadata.title = self.name

        # Internet
        internet = engine.add_shape(
            "network_cloud",
            Point(300, 50),
            "Internet",
            ShapeStyle(fill_color="#E0E0E0")
        )

        # Firewall
        firewall = engine.add_shape(
            "network_firewall",
            Point(310, 180),
            "Firewall",
            ShapeStyle(fill_color="#FF6B6B")
        )

        # Router
        router = engine.add_shape(
            "network_router",
            Point(300, 310),
            "Router",
            ShapeStyle(fill_color="#4ECDC4")
        )

        # Switch
        switch = engine.add_shape(
            "network_switch",
            Point(300, 440),
            "Switch",
            ShapeStyle(fill_color="#95E1D3")
        )

        # Servers
        server1 = engine.add_shape(
            "network_server",
            Point(150, 570),
            "Web Server",
            ShapeStyle(fill_color="#87CEEB")
        )

        server2 = engine.add_shape(
            "network_server",
            Point(350, 570),
            "Database",
            ShapeStyle(fill_color="#87CEEB")
        )

        # Workstation
        workstation = engine.add_shape(
            "network_workstation",
            Point(550, 570),
            "Workstation",
            ShapeStyle(fill_color="#FFE66D")
        )

        # Connectors
        connections = [
            (internet, firewall),
            (firewall, router),
            (router, switch),
            (switch, server1),
            (switch, server2),
            (switch, workstation)
        ]

        for source, target in connections:
            if source and target:
                engine.add_connector(ConnectorType.STRAIGHT, source.id, target.id)

        return engine


class CloudArchitectureTemplate(DiagramTemplate):
    """Cloud architecture (AWS) template."""

    def __init__(self):
        super().__init__(
            "Cloud Architecture",
            "AWS cloud infrastructure diagram",
            "cloud"
        )

    def create(self) -> DiagramEngine:
        engine = DiagramEngine()
        engine.metadata.title = self.name

        # Load Balancer
        lb = engine.add_shape(
            "basic_rectangle",
            Point(300, 50),
            "Load Balancer",
            ShapeStyle(fill_color="#FF9900", font_color="#FFFFFF")
        )

        # EC2 Instances
        ec2_1 = engine.add_shape(
            "cloud_aws_ec2",
            Point(150, 180),
            "EC2 Instance 1",
            ShapeStyle(fill_color="#FF9900")
        )

        ec2_2 = engine.add_shape(
            "cloud_aws_ec2",
            Point(400, 180),
            "EC2 Instance 2",
            ShapeStyle(fill_color="#FF9900")
        )

        # RDS Database
        rds = engine.add_shape(
            "cloud_aws_rds",
            Point(270, 340),
            "RDS Database",
            ShapeStyle(fill_color="#3B48CC")
        )

        # S3 Storage
        s3 = engine.add_shape(
            "cloud_aws_s3",
            Point(550, 340),
            "S3 Storage",
            ShapeStyle(fill_color="#569A31")
        )

        # Lambda
        lambda_fn = engine.add_shape(
            "cloud_aws_lambda",
            Point(100, 340),
            "Lambda Function",
            ShapeStyle(fill_color="#FF9900")
        )

        # Connectors
        if lb:
            for ec2 in [ec2_1, ec2_2]:
                if ec2:
                    engine.add_connector(ConnectorType.STRAIGHT, lb.id, ec2.id)

        if rds:
            for ec2 in [ec2_1, ec2_2]:
                if ec2:
                    engine.add_connector(ConnectorType.ELBOW, ec2.id, rds.id)

        if s3 and ec2_1:
            engine.add_connector(ConnectorType.CURVED, ec2_1.id, s3.id)

        if lambda_fn and rds:
            engine.add_connector(ConnectorType.ELBOW, lambda_fn.id, rds.id)

        return engine


class UMLClassDiagramTemplate(DiagramTemplate):
    """UML Class diagram template."""

    def __init__(self):
        super().__init__(
            "UML Class Diagram",
            "Object-oriented class structure",
            "uml"
        )

    def create(self) -> DiagramEngine:
        engine = DiagramEngine()
        engine.metadata.title = self.name

        # Base class
        base_class = engine.add_shape(
            "uml_class",
            Point(280, 50),
            "BaseClass\n---\n+id: int\n+name: string\n---\n+getId()\n+setName()",
            ShapeStyle(fill_color="#E8F4F8")
        )

        # Derived classes
        derived1 = engine.add_shape(
            "uml_class",
            Point(100, 250),
            "DerivedA\n---\n+extra: bool\n---\n+process()",
            ShapeStyle(fill_color="#D4E6F1")
        )

        derived2 = engine.add_shape(
            "uml_class",
            Point(400, 250),
            "DerivedB\n---\n+count: int\n---\n+calculate()",
            ShapeStyle(fill_color="#D4E6F1")
        )

        # Interface
        interface = engine.add_shape(
            "uml_interface",
            Point(280, 400),
            "<<interface>>\nIService\n---\n+execute()",
            ShapeStyle(fill_color="#FCF3CF")
        )

        # Connectors (inheritance)
        if base_class:
            for derived in [derived1, derived2]:
                if derived:
                    style = ConnectorStyle(end_arrow=ArrowType.HOLLOW)
                    engine.add_connector(
                        ConnectorType.STRAIGHT,
                        derived.id,
                        base_class.id,
                        style=style
                    )

        # Implementation
        if interface and derived1:
            style = ConnectorStyle(
                end_arrow=ArrowType.HOLLOW,
                line_style=type('LineStyle', (), {"DASHED": "dashed"})().DASHED
            )
            engine.add_connector(
                ConnectorType.STRAIGHT,
                derived1.id,
                interface.id,
                style=style
            )

        return engine


class WireframeTemplate(DiagramTemplate):
    """Web page wireframe template."""

    def __init__(self):
        super().__init__(
            "Web Wireframe",
            "Basic web page layout wireframe",
            "wireframe"
        )

    def create(self) -> DiagramEngine:
        engine = DiagramEngine()
        engine.metadata.title = self.name

        # Browser window
        browser = engine.add_shape(
            "wireframe_browser",
            Point(50, 50),
            "",
            ShapeStyle(fill_color="#FFFFFF", stroke_color="#333333")
        )

        # Header
        header = engine.add_shape(
            "basic_rectangle",
            Point(70, 110),
            "Header / Navigation",
            ShapeStyle(fill_color="#34495E", font_color="#FFFFFF")
        )

        # Sidebar
        sidebar = engine.add_shape(
            "basic_rectangle",
            Point(70, 180),
            "Sidebar",
            ShapeStyle(fill_color="#ECF0F1")
        )

        # Main content
        content = engine.add_shape(
            "basic_rectangle",
            Point(180, 180),
            "Main Content Area",
            ShapeStyle(fill_color="#FFFFFF", stroke_color="#BDC3C7")
        )

        # Footer
        footer = engine.add_shape(
            "basic_rectangle",
            Point(70, 400),
            "Footer",
            ShapeStyle(fill_color="#34495E", font_color="#FFFFFF")
        )

        return engine


class BPMNProcessTemplate(DiagramTemplate):
    """BPMN business process template."""

    def __init__(self):
        super().__init__(
            "BPMN Process",
            "Business process workflow",
            "bpmn"
        )

    def create(self) -> DiagramEngine:
        engine = DiagramEngine()
        engine.metadata.title = self.name

        # Start event
        start = engine.add_shape(
            "bpmn_event_start",
            Point(50, 140),
            "",
            ShapeStyle(fill_color="#90EE90", stroke_color="#2E7D32", stroke_width=3)
        )

        # Task 1
        task1 = engine.add_shape(
            "bpmn_task",
            Point(150, 120),
            "Review Request",
            ShapeStyle(fill_color="#E3F2FD")
        )

        # Gateway
        gateway = engine.add_shape(
            "bpmn_gateway",
            Point(330, 130),
            "×",
            ShapeStyle(fill_color="#FFF9C4", stroke_width=2)
        )

        # Task 2a
        task2a = engine.add_shape(
            "bpmn_task",
            Point(450, 50),
            "Approve",
            ShapeStyle(fill_color="#C8E6C9")
        )

        # Task 2b
        task2b = engine.add_shape(
            "bpmn_task",
            Point(450, 180),
            "Reject",
            ShapeStyle(fill_color="#FFCDD2")
        )

        # Task 3
        task3 = engine.add_shape(
            "bpmn_task",
            Point(620, 120),
            "Notify User",
            ShapeStyle(fill_color="#E3F2FD")
        )

        # End event
        end = engine.add_shape(
            "bpmn_event_end",
            Point(780, 140),
            "",
            ShapeStyle(fill_color="#FFB6C1", stroke_color="#C62828", stroke_width=4)
        )

        # Connectors
        connections = [
            (start, task1),
            (task1, gateway),
            (gateway, task2a),
            (gateway, task2b),
            (task2a, task3),
            (task2b, task3),
            (task3, end)
        ]

        for source, target in connections:
            if source and target:
                engine.add_connector(ConnectorType.STRAIGHT, source.id, target.id)

        return engine


class TemplateLibrary:
    """Library of diagram templates."""

    def __init__(self):
        self.templates: Dict[str, DiagramTemplate] = {}
        self._initialize_templates()

    def _initialize_templates(self):
        """Initialize all templates."""
        templates = [
            BasicFlowchartTemplate(),
            OrgChartTemplate(),
            NetworkDiagramTemplate(),
            CloudArchitectureTemplate(),
            UMLClassDiagramTemplate(),
            WireframeTemplate(),
            BPMNProcessTemplate()
        ]

        for template in templates:
            self.templates[template.name] = template

    def get_template(self, name: str) -> DiagramTemplate:
        """Get a template by name."""
        return self.templates.get(name)

    def get_all_templates(self) -> List[DiagramTemplate]:
        """Get all available templates."""
        return list(self.templates.values())

    def get_templates_by_category(self, category: str) -> List[DiagramTemplate]:
        """Get templates in a specific category."""
        return [t for t in self.templates.values() if t.category == category]

    def create_from_template(self, name: str) -> DiagramEngine:
        """Create a new diagram from a template."""
        template = self.get_template(name)
        if not template:
            raise ValueError(f"Template not found: {name}")
        return template.create()


# Global template library instance
template_library = TemplateLibrary()
