"""
NEXUS Infographics Designer Module

A comprehensive infographics design tool with 100+ templates, 10k+ icons,
advanced charting, data visualization, animations, and multi-format export.

Main Features:
- 100+ professional templates (business, education, marketing, data reports, social media)
- 10,000+ icon library organized by categories
- Advanced charts with data binding (bar, pie, line, scatter, donut, funnel, etc.)
- Design tools (drag-drop, alignment, grouping, layering, flip/rotate)
- Data import from CSV, Excel, JSON with auto-chart generation
- Animation effects and transitions
- Export to PNG, PDF, SVG, GIF, video, and HTML

Usage:
    from modules.infographics import InfographicDesigner, ElementFactory, TemplateLibrary

    # Create designer
    designer = InfographicDesigner()

    # Add elements
    text = ElementFactory.create_text("Hello World", x=100, y=100)
    designer.add_element(text)

    # Export
    from modules.infographics import InfographicExporter, ExportConfig, ExportFormat
    exporter = InfographicExporter(designer)
    config = ExportConfig(format=ExportFormat.PNG)
    exporter.export(config, "output.png")
"""

# Elements
from .elements import (
    ElementType, ShapeType, LineStyle, ArrowType, TextAlign, VerticalAlign,
    Position, Style, TextStyle,
    BaseElement, TextElement, ShapeElement, IconElement, ImageElement,
    LineElement, GroupElement,
    ElementFactory, ElementPresets
)

# Templates
from .templates import (
    TemplateCategory, TemplateStyle, SocialMediaFormat,
    TemplateMetadata, Template,
    TemplateGenerator, TemplateLibrary,
    EducationTemplates, MarketingTemplates
)

# Charts
from .charts import (
    ChartType, LegendPosition,
    DataSeries, ChartConfig, AxisConfig, ChartElement,
    ChartFactory, ChartStyler, ChartDataTransformer
)

# Icons
from .icons import (
    IconCategory, IconStyle,
    Icon, IconSet, IconLibrary,
    IconGenerator, IconPackManager, IconCustomizer
)

# Data Visualization
from .data_viz import (
    DataSourceType, DataType,
    DataColumn, DataTable,
    DataImporter, ChartGenerator, DataTableElement, DataAnalyzer
)

# Animations
from .animations import (
    AnimationType, AnimationDirection, EasingFunction, TriggerType,
    AnimationConfig, Animation,
    AnimationPresets, AnimationSequence, TransitionEffect,
    InteractiveEffect, AnimationTimeline, AnimationBuilder
)

# Designer
from .designer import (
    AlignmentType, DistributionType, FlipDirection,
    CanvasConfig, HistoryEntry, InfographicDesigner
)

# Export
from .export import (
    ExportFormat, ImageQuality, ExportConfig,
    InfographicExporter, BatchExporter, PrintExporter, AnimationExporter
)

# UI
from .streamlit_ui import InfographicsUI


__version__ = "1.0.0"
__author__ = "NEXUS"


__all__ = [
    # Elements
    'ElementType', 'ShapeType', 'LineStyle', 'ArrowType', 'TextAlign', 'VerticalAlign',
    'Position', 'Style', 'TextStyle',
    'BaseElement', 'TextElement', 'ShapeElement', 'IconElement', 'ImageElement',
    'LineElement', 'GroupElement',
    'ElementFactory', 'ElementPresets',

    # Templates
    'TemplateCategory', 'TemplateStyle', 'SocialMediaFormat',
    'TemplateMetadata', 'Template',
    'TemplateGenerator', 'TemplateLibrary',
    'EducationTemplates', 'MarketingTemplates',

    # Charts
    'ChartType', 'LegendPosition',
    'DataSeries', 'ChartConfig', 'AxisConfig', 'ChartElement',
    'ChartFactory', 'ChartStyler', 'ChartDataTransformer',

    # Icons
    'IconCategory', 'IconStyle',
    'Icon', 'IconSet', 'IconLibrary',
    'IconGenerator', 'IconPackManager', 'IconCustomizer',

    # Data Visualization
    'DataSourceType', 'DataType',
    'DataColumn', 'DataTable',
    'DataImporter', 'ChartGenerator', 'DataTableElement', 'DataAnalyzer',

    # Animations
    'AnimationType', 'AnimationDirection', 'EasingFunction', 'TriggerType',
    'AnimationConfig', 'Animation',
    'AnimationPresets', 'AnimationSequence', 'TransitionEffect',
    'InteractiveEffect', 'AnimationTimeline', 'AnimationBuilder',

    # Designer
    'AlignmentType', 'DistributionType', 'FlipDirection',
    'CanvasConfig', 'HistoryEntry', 'InfographicDesigner',

    # Export
    'ExportFormat', 'ImageQuality', 'ExportConfig',
    'InfographicExporter', 'BatchExporter', 'PrintExporter', 'AnimationExporter',

    # UI
    'InfographicsUI'
]
