"""Context manager for maintaining conversation state."""

from typing import Dict, List, Optional
from datetime import datetime
from collections import deque
import json


class ContextManager:
    """Manages conversation context and history."""

    def __init__(self, max_history: int = 10):
        """
        Initialize context manager.

        Args:
            max_history: Maximum number of interactions to keep in memory
        """
        self.max_history = max_history
        self.sessions = {}  # session_id -> session context

    def create_session(self, session_id: str, user_id: str) -> Dict:
        """
        Create a new conversation session.

        Args:
            session_id: Unique session identifier
            user_id: User identifier

        Returns:
            Session context
        """
        self.sessions[session_id] = {
            "session_id": session_id,
            "user_id": user_id,
            "created_at": datetime.utcnow().isoformat(),
            "last_activity": datetime.utcnow().isoformat(),
            "history": deque(maxlen=self.max_history),
            "variables": {},  # Store extracted variables across conversation
            "current_intent": None,
            "pending_confirmations": [],
            "module_context": None  # Current NEXUS module being used
        }
        return self.sessions[session_id]

    def get_session(self, session_id: str) -> Optional[Dict]:
        """
        Get session context.

        Args:
            session_id: Session identifier

        Returns:
            Session context or None
        """
        return self.sessions.get(session_id)

    def add_interaction(
        self,
        session_id: str,
        user_input: str,
        transcript: str,
        intent: str,
        entities: Dict,
        response: str,
        action_taken: Optional[Dict] = None
    ):
        """
        Add an interaction to the session history.

        Args:
            session_id: Session identifier
            user_input: Original user input
            transcript: Transcribed text
            intent: Detected intent
            entities: Extracted entities
            response: System response
            action_taken: Action that was performed
        """
        session = self.sessions.get(session_id)
        if not session:
            return

        interaction = {
            "timestamp": datetime.utcnow().isoformat(),
            "user_input": user_input,
            "transcript": transcript,
            "intent": intent,
            "entities": entities,
            "response": response,
            "action_taken": action_taken
        }

        session["history"].append(interaction)
        session["last_activity"] = datetime.utcnow().isoformat()
        session["current_intent"] = intent

        # Update session variables with extracted entities
        if entities:
            session["variables"].update(entities)

    def get_conversation_history(
        self,
        session_id: str,
        limit: Optional[int] = None
    ) -> List[Dict]:
        """
        Get conversation history for a session.

        Args:
            session_id: Session identifier
            limit: Maximum number of interactions to return

        Returns:
            List of interactions
        """
        session = self.sessions.get(session_id)
        if not session:
            return []

        history = list(session["history"])
        if limit:
            history = history[-limit:]

        return history

    def get_context_for_intent(self, session_id: str) -> Dict:
        """
        Get relevant context for intent recognition.

        Args:
            session_id: Session identifier

        Returns:
            Context dictionary
        """
        session = self.sessions.get(session_id)
        if not session:
            return {}

        # Get last few interactions
        recent_history = list(session["history"])[-3:]

        return {
            "recent_intents": [h["intent"] for h in recent_history],
            "current_module": session.get("module_context"),
            "variables": session.get("variables", {}),
            "last_intent": session.get("current_intent"),
            "recent_entities": self._merge_recent_entities(recent_history)
        }

    def _merge_recent_entities(self, history: List[Dict]) -> Dict:
        """Merge entities from recent history."""
        merged = {}
        for interaction in history:
            if interaction.get("entities"):
                merged.update(interaction["entities"])
        return merged

    def set_module_context(self, session_id: str, module_name: str):
        """
        Set the current module context.

        Args:
            session_id: Session identifier
            module_name: Name of the NEXUS module
        """
        session = self.sessions.get(session_id)
        if session:
            session["module_context"] = module_name

    def add_pending_confirmation(
        self,
        session_id: str,
        action: str,
        details: Dict
    ):
        """
        Add a pending confirmation.

        Args:
            session_id: Session identifier
            action: Action requiring confirmation
            details: Action details
        """
        session = self.sessions.get(session_id)
        if session:
            session["pending_confirmations"].append({
                "action": action,
                "details": details,
                "added_at": datetime.utcnow().isoformat()
            })

    def get_pending_confirmations(self, session_id: str) -> List[Dict]:
        """Get pending confirmations."""
        session = self.sessions.get(session_id)
        return session.get("pending_confirmations", []) if session else []

    def clear_pending_confirmations(self, session_id: str):
        """Clear all pending confirmations."""
        session = self.sessions.get(session_id)
        if session:
            session["pending_confirmations"] = []

    def set_variable(self, session_id: str, key: str, value):
        """
        Set a session variable.

        Args:
            session_id: Session identifier
            key: Variable name
            value: Variable value
        """
        session = self.sessions.get(session_id)
        if session:
            session["variables"][key] = value

    def get_variable(self, session_id: str, key: str, default=None):
        """
        Get a session variable.

        Args:
            session_id: Session identifier
            key: Variable name
            default: Default value if not found

        Returns:
            Variable value or default
        """
        session = self.sessions.get(session_id)
        if session:
            return session["variables"].get(key, default)
        return default

    def clear_session(self, session_id: str):
        """Clear a session."""
        if session_id in self.sessions:
            del self.sessions[session_id]

    def get_summary(self, session_id: str) -> str:
        """
        Get a summary of the conversation.

        Args:
            session_id: Session identifier

        Returns:
            Summary text
        """
        session = self.sessions.get(session_id)
        if not session:
            return "No active session"

        history = list(session["history"])
        if not history:
            return "No conversation history"

        summary_parts = [
            f"Session started at: {session['created_at']}",
            f"Total interactions: {len(history)}",
            f"Current module: {session.get('module_context', 'None')}",
            "\nRecent intents:"
        ]

        for interaction in history[-5:]:
            summary_parts.append(
                f"  - {interaction['intent']}: {interaction['transcript'][:50]}..."
            )

        return "\n".join(summary_parts)

    def export_session(self, session_id: str) -> str:
        """
        Export session data as JSON.

        Args:
            session_id: Session identifier

        Returns:
            JSON string
        """
        session = self.sessions.get(session_id)
        if not session:
            return "{}"

        # Convert deque to list for JSON serialization
        export_data = {
            **session,
            "history": list(session["history"])
        }

        return json.dumps(export_data, indent=2)
