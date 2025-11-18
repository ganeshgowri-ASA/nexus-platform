"""
Example usage of NEXUS Infographics Designer.

This script demonstrates basic usage of the infographics module.
"""

from modules.infographics import (
    InfographicDesigner,
    ElementFactory,
    ElementPresets,
    ChartFactory,
    DataImporter,
    ChartGenerator,
    TemplateLibrary,
    TemplateCategory,
    InfographicExporter,
    ExportConfig,
    ExportFormat,
    ImageQuality,
    ShapeType,
    AnimationPresets,
    Animation
)


def example_basic():
    """Basic example: Create simple infographic."""
    print("Example 1: Basic Infographic")

    # Create designer
    designer = InfographicDesigner()

    # Add title
    title = ElementPresets.heading("Welcome to NEXUS", x=100, y=50)
    designer.add_element(title)

    # Add subtitle
    subtitle = ElementPresets.subheading("Infographics Designer", x=100, y=120)
    designer.add_element(subtitle)

    # Add a shape
    circle = ElementFactory.create_shape(ShapeType.CIRCLE, 400, 200, 100, 100)
    circle.style.fill_color = "#3498DB"
    designer.add_element(circle)

    # Add text inside circle
    text = ElementFactory.create_text("100+", x=420, y=235, font_size=24)
    text.style.fill_color = "#FFFFFF"
    designer.add_element(text)

    # Save design
    designer.save_to_file("example_basic.json")
    print("✓ Saved to example_basic.json")


def example_charts():
    """Chart example: Create infographic with charts."""
    print("\nExample 2: Charts and Data")

    designer = InfographicDesigner()

    # Add title
    title = ElementPresets.heading("Sales Dashboard", x=100, y=50)
    designer.add_element(title)

    # Create bar chart
    bar_chart = ChartFactory.create_bar_chart(
        categories=["Q1", "Q2", "Q3", "Q4"],
        data=[45000, 52000, 61000, 73000],
        title="Quarterly Sales"
    )
    bar_chart.position.x = 100
    bar_chart.position.y = 150
    designer.add_element(bar_chart)

    # Create pie chart
    pie_chart = ChartFactory.create_pie_chart(
        labels=["Product A", "Product B", "Product C"],
        data=[35, 45, 20],
        title="Market Share"
    )
    pie_chart.position.x = 900
    pie_chart.position.y = 150
    designer.add_element(pie_chart)

    # Save
    designer.save_to_file("example_charts.json")
    print("✓ Saved to example_charts.json")


def example_data_import():
    """Data import example: Import CSV and auto-generate chart."""
    print("\nExample 3: Data Import")

    designer = InfographicDesigner()

    # Sample CSV data
    csv_data = """Category,Value,Percentage
Electronics,125000,35%
Clothing,95000,27%
Home & Garden,75000,21%
Sports,60000,17%"""

    # Import data
    table = DataImporter.import_csv(csv_data)
    print(f"✓ Imported {table.get_row_count()} rows, {table.get_column_count()} columns")

    # Auto-generate chart
    chart = ChartGenerator.auto_generate_chart(table)
    chart.position.x = 100
    chart.position.y = 100
    designer.add_element(chart)

    # Save
    designer.save_to_file("example_data_import.json")
    print("✓ Saved to example_data_import.json")


def example_templates():
    """Template example: Use existing templates."""
    print("\nExample 4: Using Templates")

    # Load template library
    library = TemplateLibrary()

    # Get business templates
    templates = library.get_templates_by_category(TemplateCategory.BUSINESS)
    print(f"✓ Found {len(templates)} business templates")

    if templates:
        designer = InfographicDesigner()
        designer.load_template(templates[0])
        print(f"✓ Loaded template: {templates[0].metadata.name}")

        # Save
        designer.save_to_file("example_template.json")
        print("✓ Saved to example_template.json")


def example_animations():
    """Animation example: Add animations to elements."""
    print("\nExample 5: Animations")

    designer = InfographicDesigner()

    # Add text
    text = ElementPresets.heading("Animated Text", x=300, y=200)
    designer.add_element(text)

    # Add fade-in animation
    fade_in = AnimationPresets.fade_in(duration=1000)
    animation = Animation(
        element_id=text.id,
        name="Fade In",
        config=fade_in
    )
    designer.animations.append(animation)

    # Add shape with bounce animation
    circle = ElementFactory.create_shape(ShapeType.CIRCLE, 500, 300, 80, 80)
    designer.add_element(circle)

    bounce_in = AnimationPresets.bounce_in(duration=1500)
    bounce_animation = Animation(
        element_id=circle.id,
        name="Bounce In",
        config=bounce_in
    )
    designer.animations.append(bounce_animation)

    # Save
    designer.save_to_file("example_animations.json")
    print("✓ Saved to example_animations.json")
    print(f"✓ Added {len(designer.animations)} animations")


def example_export():
    """Export example: Export to different formats."""
    print("\nExample 6: Export Formats")

    designer = InfographicDesigner()

    # Create simple design
    title = ElementPresets.heading("Export Example", x=400, y=300)
    designer.add_element(title)

    # Export to different formats
    exporter = InfographicExporter(designer)

    # Export PNG
    png_config = ExportConfig(
        format=ExportFormat.PNG,
        quality=ImageQuality.HIGH
    )
    exporter.export(png_config, "example_export.png")
    print("✓ Exported to PNG")

    # Export SVG
    svg_config = ExportConfig(format=ExportFormat.SVG)
    exporter.export(svg_config, "example_export.svg")
    print("✓ Exported to SVG")

    # Export PDF
    pdf_config = ExportConfig(
        format=ExportFormat.PDF,
        quality=ImageQuality.HIGH
    )
    exporter.export(pdf_config, "example_export.pdf")
    print("✓ Exported to PDF")

    # Get embed code
    embed_code = exporter.get_embed_code(width=800, height=600)
    print("✓ Generated embed code")


def main():
    """Run all examples."""
    print("=" * 60)
    print("NEXUS Infographics Designer - Examples")
    print("=" * 60)

    try:
        example_basic()
        example_charts()
        example_data_import()
        example_templates()
        example_animations()
        example_export()

        print("\n" + "=" * 60)
        print("All examples completed successfully!")
        print("=" * 60)

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
