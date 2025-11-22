"""
Mind Map Module - Usage Examples

This file demonstrates various ways to use the mind map module.
"""

from modules.mindmap import (
    MindMapEngine,
    LayoutType,
    ExportFormat,
    ThemeName,
    ConnectionType,
    User,
    Task,
    Priority,
)


def example_basic_mindmap():
    """Example 1: Create a basic mind map."""
    print("Example 1: Basic Mind Map")
    print("-" * 50)

    # Create engine
    engine = MindMapEngine()
    engine.title = "Product Launch Plan"

    # Create root node
    root_id = engine.create_root_node("Product Launch")

    # Add main branches
    marketing_id = engine.create_node("Marketing Strategy", parent_id=root_id)
    dev_id = engine.create_node("Development", parent_id=root_id)
    sales_id = engine.create_node("Sales Plan", parent_id=root_id)

    # Add sub-branches
    engine.create_node("Social Media Campaign", parent_id=marketing_id)
    engine.create_node("Email Marketing", parent_id=marketing_id)
    engine.create_node("Content Creation", parent_id=marketing_id)

    engine.create_node("Backend API", parent_id=dev_id)
    engine.create_node("Frontend UI", parent_id=dev_id)
    engine.create_node("Testing", parent_id=dev_id)

    # Apply layout
    engine.apply_layout(LayoutType.MIND_MAP)

    # Apply theme
    engine.apply_theme(ThemeName.PROFESSIONAL.value)

    # Get statistics
    stats = engine.get_statistics()
    print(f"Created mind map with {stats['total_nodes']} nodes")
    print(f"Max depth: {stats['max_depth']}")

    # Export
    markdown = engine.export(ExportFormat.MARKDOWN)
    print("\nMarkdown Export Preview:")
    print(markdown.decode('utf-8')[:200] + "...")

    return engine


def example_with_tasks():
    """Example 2: Mind map with tasks and priorities."""
    print("\n\nExample 2: Mind Map with Tasks")
    print("-" * 50)

    engine = MindMapEngine()
    root_id = engine.create_root_node("Project Tasks")

    # Create node with tasks
    research_id = engine.create_node("Research Phase", parent_id=root_id)
    research_node = engine.get_node(research_id)

    # Add tasks
    task1 = Task(
        description="Conduct market research",
        priority=Priority.HIGH,
    )
    task2 = Task(
        description="Analyze competitors",
        priority=Priority.MEDIUM,
    )
    task3 = Task(
        description="Identify target audience",
        priority=Priority.HIGH,
    )

    research_node.add_task(task1)
    research_node.add_task(task2)
    research_node.add_task(task3)

    # Complete a task
    research_node.toggle_task(task2.id)

    # Check completion rate
    completion = research_node.get_completion_rate()
    print(f"Task completion rate: {completion:.1%}")

    return engine


def example_ai_generation():
    """Example 3: Generate mind map from text using AI."""
    print("\n\nExample 3: AI-Powered Generation")
    print("-" * 50)

    text = """
    Website Redesign Project

    Planning Phase:
    - Define goals and objectives
    - Identify target audience
    - Competitive analysis
    - Budget planning

    Design Phase:
    - Wireframes and mockups
    - User experience design
    - Visual design
    - Design system creation

    Development Phase:
    - Frontend development
    - Backend development
    - Content management system
    - Testing and QA

    Launch:
    - Deployment
    - Marketing campaign
    - Analytics setup
    - Monitoring and maintenance
    """

    engine = MindMapEngine()
    engine.generate_from_text(text, root_text="Website Redesign")
    engine.apply_layout(LayoutType.TREE)

    stats = engine.get_statistics()
    print(f"Generated {stats['total_nodes']} nodes from text")
    print(f"Depth: {stats['max_depth']} levels")

    return engine


def example_ai_suggestions():
    """Example 4: Get AI suggestions for nodes."""
    print("\n\nExample 4: AI Suggestions")
    print("-" * 50)

    engine = MindMapEngine()
    root_id = engine.create_root_node("Business Strategy")
    marketing_id = engine.create_node("Marketing", parent_id=root_id)

    # Get AI suggestions
    suggestions = engine.suggest_ideas_for_node(marketing_id, count=5)

    print("AI Suggestions for 'Marketing':")
    for i, suggestion in enumerate(suggestions, 1):
        print(f"  {i}. {suggestion}")

    return engine


def example_collaboration():
    """Example 5: Collaborative editing."""
    print("\n\nExample 5: Collaboration")
    print("-" * 50)

    engine = MindMapEngine()
    root_id = engine.create_root_node("Team Project")

    # Start collaboration
    session_id = engine.start_collaboration()
    print(f"Collaboration session started: {session_id}")

    # Add users
    user1 = User(
        id="user1",
        name="Alice",
        email="alice@example.com",
        color="#FF0000"
    )
    user2 = User(
        id="user2",
        name="Bob",
        email="bob@example.com",
        color="#0000FF"
    )

    engine.add_collaborator(user1)
    engine.add_collaborator(user2)

    print(f"Added {len(engine.collaboration_session.users)} collaborators")

    # Lock a node
    success = engine.collaboration_session.lock_node(root_id, user1.id)
    print(f"Node locked by {user1.name}: {success}")

    # Try to lock same node with different user
    success = engine.collaboration_session.lock_node(root_id, user2.id)
    print(f"Attempted lock by {user2.name}: {success}")

    return engine


def example_custom_branches():
    """Example 6: Custom branch connections."""
    print("\n\nExample 6: Custom Branches")
    print("-" * 50)

    engine = MindMapEngine()
    root_id = engine.create_root_node("Software Architecture")

    # Create components
    frontend_id = engine.create_node("Frontend", parent_id=root_id)
    backend_id = engine.create_node("Backend", parent_id=root_id)
    database_id = engine.create_node("Database", parent_id=root_id)
    api_id = engine.create_node("API Gateway", parent_id=root_id)

    # Create custom associations
    engine.create_branch(frontend_id, api_id, ConnectionType.DEPENDENCY)
    engine.create_branch(api_id, backend_id, ConnectionType.DEPENDENCY)
    engine.create_branch(backend_id, database_id, ConnectionType.DEPENDENCY)

    # Create reference connections
    engine.create_branch(frontend_id, backend_id, ConnectionType.REFERENCE)

    print(f"Created {len(engine.branch_manager.branches)} branches")
    print(f"Branch types: {engine.branch_manager.get_statistics()}")

    return engine


def example_themes():
    """Example 7: Applying different themes."""
    print("\n\nExample 7: Themes")
    print("-" * 50)

    engine = MindMapEngine()
    root_id = engine.create_root_node("Themed Mind Map")

    for i in range(3):
        engine.create_node(f"Branch {i+1}", parent_id=root_id)

    # List available themes
    themes = engine.theme_manager.list_themes()
    print(f"Available themes: {len(themes)}")

    # Apply different themes
    for theme_name in [ThemeName.CLASSIC.value, ThemeName.DARK.value, ThemeName.OCEANIC.value]:
        engine.apply_theme(theme_name)
        print(f"Applied theme: {theme_name}")

    return engine


def example_export_formats():
    """Example 8: Export to various formats."""
    print("\n\nExample 8: Export Formats")
    print("-" * 50)

    engine = MindMapEngine()
    engine.title = "Export Demo"
    root_id = engine.create_root_node("Main Topic")

    for i in range(3):
        child_id = engine.create_node(f"Subtopic {i+1}", parent_id=root_id)
        for j in range(2):
            engine.create_node(f"Detail {i+1}.{j+1}", parent_id=child_id)

    engine.apply_layout(LayoutType.MIND_MAP)

    # Export to different formats
    formats = [
        ExportFormat.JSON,
        ExportFormat.MARKDOWN,
        ExportFormat.HTML,
        ExportFormat.TEXT_OUTLINE,
    ]

    for fmt in formats:
        data = engine.export(fmt)
        print(f"{fmt.value}: {len(data)} bytes")

    return engine


def example_search_and_filter():
    """Example 9: Search and filter nodes."""
    print("\n\nExample 9: Search and Filter")
    print("-" * 50)

    engine = MindMapEngine()
    root_id = engine.create_root_node("Knowledge Base")

    # Create nodes with different content
    engine.create_node("Python Programming", parent_id=root_id)
    engine.create_node("JavaScript Development", parent_id=root_id)
    engine.create_node("Python Libraries", parent_id=root_id)
    engine.create_node("Web Development", parent_id=root_id)

    # Search for nodes
    results = engine.search_nodes("python")
    print(f"Found {len(results)} nodes matching 'python':")
    for node in results:
        print(f"  - {node.text}")

    return engine


def example_auto_organize():
    """Example 10: Auto-organize with AI."""
    print("\n\nExample 10: Auto-Organize")
    print("-" * 50)

    engine = MindMapEngine()
    root_id = engine.create_root_node("Random Ideas")

    # Create various types of nodes
    engine.create_node("TODO: Write documentation", parent_id=root_id)
    engine.create_node("What is the deadline?", parent_id=root_id)
    engine.create_node("New feature idea: Dark mode", parent_id=root_id)
    engine.create_node("Link to resources", parent_id=root_id)
    engine.create_node("How can we improve performance?", parent_id=root_id)

    # Get organization suggestions
    suggestions = engine.auto_organize()

    print("Organization Suggestions:")
    print(f"Categories: {list(suggestions['categories'].keys())}")
    print(f"Total nodes: {suggestions['analysis']['total_nodes']}")
    print(f"Recommendations: {suggestions['recommendations']}")

    return engine


def run_all_examples():
    """Run all examples."""
    print("=" * 50)
    print("MIND MAP MODULE - USAGE EXAMPLES")
    print("=" * 50)

    examples = [
        example_basic_mindmap,
        example_with_tasks,
        example_ai_generation,
        example_ai_suggestions,
        example_collaboration,
        example_custom_branches,
        example_themes,
        example_export_formats,
        example_search_and_filter,
        example_auto_organize,
    ]

    for example in examples:
        try:
            example()
        except Exception as e:
            print(f"Error in {example.__name__}: {e}")

    print("\n" + "=" * 50)
    print("All examples completed!")
    print("=" * 50)


if __name__ == "__main__":
    run_all_examples()
