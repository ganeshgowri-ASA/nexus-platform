"""Tests for command registry."""

import pytest
from modules.voice.utils.command_registry import CommandRegistry


def test_registry_initialization():
    """Test registry initializes with default commands."""
    registry = CommandRegistry()
    commands = registry.get_all_commands()

    assert len(commands) > 0
    assert any(cmd['name'] == 'create_document' for cmd in commands)


def test_register_command():
    """Test registering a new command."""
    registry = CommandRegistry()

    registry.register_command(
        name="test_command",
        intent="test_intent",
        category="test",
        patterns=["test pattern"],
        description="Test command",
        module="test",
        handler="test_handler",
        params=["param1"],
        examples=["Test example"]
    )

    cmd = registry.get_command("test_command")
    assert cmd is not None
    assert cmd['name'] == "test_command"
    assert cmd['intent'] == "test_intent"


def test_get_command_by_intent():
    """Test getting command by intent."""
    registry = CommandRegistry()

    cmd = registry.get_command_by_intent("create_document")
    assert cmd is not None
    assert cmd['intent'] == "create_document"


def test_get_commands_by_category():
    """Test getting commands by category."""
    registry = CommandRegistry()

    commands = registry.get_commands_by_category("productivity")
    assert len(commands) > 0
    assert all(cmd['category'] == 'productivity' for cmd in commands)


def test_disable_enable_command():
    """Test disabling and enabling commands."""
    registry = CommandRegistry()

    # Disable command
    registry.disable_command("create_document")
    cmd = registry.get_command("create_document")
    assert cmd['is_active'] is False

    # Enable command
    registry.enable_command("create_document")
    cmd = registry.get_command("create_document")
    assert cmd['is_active'] is True


def test_search_commands():
    """Test searching commands."""
    registry = CommandRegistry()

    results = registry.search_commands("document")
    assert len(results) > 0
    assert any("document" in cmd['name'].lower() for cmd in results)


def test_update_priority():
    """Test updating command priority."""
    registry = CommandRegistry()

    registry.update_command_priority("create_document", 100)
    cmd = registry.get_command("create_document")
    assert cmd['priority'] == 100


def test_get_help_text():
    """Test getting help text."""
    registry = CommandRegistry()

    help_text = registry.get_help_text()
    assert len(help_text) > 0
    assert "create_document" in help_text.lower()

    # Category-specific help
    help_text = registry.get_help_text("productivity")
    assert len(help_text) > 0
