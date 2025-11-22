"""Tests for context manager."""

import pytest
from modules.voice.nlp.context_manager import ContextManager


def test_create_session():
    """Test creating a session."""
    manager = ContextManager()

    session = manager.create_session("session123", "user456")

    assert session['session_id'] == "session123"
    assert session['user_id'] == "user456"
    assert len(session['history']) == 0


def test_get_session():
    """Test getting a session."""
    manager = ContextManager()

    manager.create_session("session123", "user456")
    session = manager.get_session("session123")

    assert session is not None
    assert session['session_id'] == "session123"


def test_add_interaction():
    """Test adding interactions."""
    manager = ContextManager()
    manager.create_session("session123", "user456")

    manager.add_interaction(
        session_id="session123",
        user_input="test input",
        transcript="test input",
        intent="test_intent",
        entities={},
        response="test response"
    )

    history = manager.get_conversation_history("session123")
    assert len(history) == 1
    assert history[0]['intent'] == "test_intent"


def test_get_conversation_history():
    """Test getting conversation history."""
    manager = ContextManager()
    manager.create_session("session123", "user456")

    # Add multiple interactions
    for i in range(5):
        manager.add_interaction(
            session_id="session123",
            user_input=f"input {i}",
            transcript=f"input {i}",
            intent=f"intent_{i}",
            entities={},
            response=f"response {i}"
        )

    history = manager.get_conversation_history("session123")
    assert len(history) == 5

    # Test limit
    history = manager.get_conversation_history("session123", limit=3)
    assert len(history) == 3


def test_set_module_context():
    """Test setting module context."""
    manager = ContextManager()
    manager.create_session("session123", "user456")

    manager.set_module_context("session123", "email")

    session = manager.get_session("session123")
    assert session['module_context'] == "email"


def test_session_variables():
    """Test session variables."""
    manager = ContextManager()
    manager.create_session("session123", "user456")

    manager.set_variable("session123", "key1", "value1")
    value = manager.get_variable("session123", "key1")

    assert value == "value1"

    # Test default value
    value = manager.get_variable("session123", "nonexistent", "default")
    assert value == "default"


def test_pending_confirmations():
    """Test pending confirmations."""
    manager = ContextManager()
    manager.create_session("session123", "user456")

    manager.add_pending_confirmation(
        session_id="session123",
        action="delete_file",
        details={"file": "important.txt"}
    )

    confirmations = manager.get_pending_confirmations("session123")
    assert len(confirmations) == 1
    assert confirmations[0]['action'] == "delete_file"

    manager.clear_pending_confirmations("session123")
    confirmations = manager.get_pending_confirmations("session123")
    assert len(confirmations) == 0


def test_clear_session():
    """Test clearing a session."""
    manager = ContextManager()
    manager.create_session("session123", "user456")

    manager.clear_session("session123")
    session = manager.get_session("session123")

    assert session is None


def test_get_context_for_intent():
    """Test getting context for intent recognition."""
    manager = ContextManager()
    manager.create_session("session123", "user456")

    manager.add_interaction(
        session_id="session123",
        user_input="create document",
        transcript="create document",
        intent="create_document",
        entities={"title": "Report"},
        response="Creating document"
    )

    context = manager.get_context_for_intent("session123")

    assert 'recent_intents' in context
    assert 'create_document' in context['recent_intents']
    assert 'recent_entities' in context
    assert context['recent_entities'].get('title') == "Report"
