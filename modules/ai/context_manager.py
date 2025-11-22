"""
Conversation Context Management

Manages conversation history, context window limits, system prompts,
and multi-turn conversations across different AI models.
"""

from datetime import datetime
from typing import List, Dict, Optional, Any, Tuple
from collections import defaultdict
import json


class ContextManager:
    """
    Manages conversation context and history for AI interactions.

    Features:
    - Conversation history storage
    - Context window management (auto-truncation)
    - System prompt injection
    - User preference integration
    - Multi-turn conversation support
    - Message role management (system, user, assistant)
    """

    # Context window limits per model (in tokens)
    CONTEXT_LIMITS = {
        # Claude models
        "claude-3-opus-20240229": 200000,
        "claude-3-5-sonnet-20241022": 200000,
        "claude-3-haiku-20240307": 200000,

        # OpenAI models
        "gpt-4-turbo-preview": 128000,
        "gpt-4": 8192,
        "gpt-3.5-turbo": 16385,
        "gpt-4o": 128000,

        # Google Gemini models
        "gemini-pro": 32768,
        "gemini-pro-vision": 32768,
        "gemini-1.5-pro": 2000000,  # 2M tokens!
    }

    def __init__(self):
        """Initialize context manager with empty conversations."""
        # Store conversations by conversation_id
        self.conversations: Dict[str, List[Dict]] = defaultdict(list)

        # Store system prompts by conversation_id
        self.system_prompts: Dict[str, str] = {}

        # Store user preferences by user_id
        self.user_preferences: Dict[int, Dict] = defaultdict(dict)

    def create_conversation(
        self,
        conversation_id: str,
        system_prompt: Optional[str] = None,
        user_id: Optional[int] = None,
        metadata: Optional[Dict] = None
    ) -> Dict:
        """
        Create a new conversation.

        Args:
            conversation_id: Unique conversation identifier
            system_prompt: System prompt to use
            user_id: User ID (optional)
            metadata: Additional metadata (optional)

        Returns:
            Conversation initialization info
        """
        self.conversations[conversation_id] = []

        if system_prompt:
            self.system_prompts[conversation_id] = system_prompt

        return {
            "conversation_id": conversation_id,
            "created_at": datetime.utcnow().isoformat(),
            "user_id": user_id,
            "system_prompt": system_prompt,
            "metadata": metadata or {},
        }

    def add_message(
        self,
        conversation_id: str,
        role: str,
        content: str,
        metadata: Optional[Dict] = None
    ) -> Dict:
        """
        Add a message to the conversation history.

        Args:
            conversation_id: Conversation identifier
            role: Message role (system, user, assistant)
            content: Message content
            metadata: Additional metadata (model used, tokens, etc.)

        Returns:
            Message entry
        """
        message = {
            "role": role,
            "content": content,
            "timestamp": datetime.utcnow().isoformat(),
            "metadata": metadata or {},
        }

        self.conversations[conversation_id].append(message)

        return message

    def get_messages(
        self,
        conversation_id: str,
        limit: Optional[int] = None,
        include_system: bool = True
    ) -> List[Dict]:
        """
        Get messages from a conversation.

        Args:
            conversation_id: Conversation identifier
            limit: Maximum number of messages to return (most recent)
            include_system: Whether to include system prompt

        Returns:
            List of messages
        """
        messages = []

        # Add system prompt if exists and requested
        if include_system and conversation_id in self.system_prompts:
            messages.append({
                "role": "system",
                "content": self.system_prompts[conversation_id],
            })

        # Add conversation messages
        conv_messages = self.conversations[conversation_id]

        if limit:
            # Get last N messages
            conv_messages = conv_messages[-limit:]

        messages.extend([
            {"role": msg["role"], "content": msg["content"]}
            for msg in conv_messages
        ])

        return messages

    def truncate_to_fit(
        self,
        conversation_id: str,
        model: str,
        new_message: str,
        safety_margin: float = 0.8
    ) -> List[Dict]:
        """
        Truncate conversation history to fit within model's context window.

        Strategy:
        1. Keep system prompt
        2. Keep most recent messages
        3. Remove oldest messages until within limit

        Args:
            conversation_id: Conversation identifier
            model: Model name to check limits against
            new_message: New message to be added
            safety_margin: Use only this fraction of context (default 80%)

        Returns:
            Truncated message list ready for API
        """
        # Get context limit for model
        context_limit = self.CONTEXT_LIMITS.get(model, 8192)
        effective_limit = int(context_limit * safety_margin)

        # Get all messages
        messages = self.get_messages(conversation_id, include_system=True)

        # Add new message to estimate
        messages.append({"role": "user", "content": new_message})

        # Estimate token count (rough: 1 token ≈ 4 characters)
        def estimate_tokens(msgs: List[Dict]) -> int:
            total = 0
            for msg in msgs:
                # Count content + overhead (role, formatting)
                total += len(msg["content"]) // 4 + 10
            return total

        current_tokens = estimate_tokens(messages)

        # If within limit, return as-is
        if current_tokens <= effective_limit:
            return messages

        # Truncate from the middle (keep system + recent messages)
        system_messages = [m for m in messages if m["role"] == "system"]
        non_system_messages = [m for m in messages if m["role"] != "system"]

        # Always keep system prompt and last message
        result = system_messages + non_system_messages[-1:]

        # Add messages from end until we hit limit
        for msg in reversed(non_system_messages[:-1]):
            result_with_msg = system_messages + [msg] + non_system_messages[-1:]

            if estimate_tokens(result_with_msg) <= effective_limit:
                result = result_with_msg
            else:
                break

        # Re-sort to maintain chronological order
        return sorted(result, key=lambda m: messages.index(m))

    def set_user_preferences(
        self,
        user_id: int,
        preferences: Dict[str, Any]
    ):
        """
        Set user preferences for AI interactions.

        Preferences can include:
        - tone: formal, casual, friendly, professional
        - verbosity: concise, balanced, detailed
        - language: en, es, fr, de, etc.
        - temperature: 0.0 - 2.0
        - max_tokens: integer

        Args:
            user_id: User ID
            preferences: Dictionary of preferences
        """
        self.user_preferences[user_id].update(preferences)

    def get_user_preferences(self, user_id: int) -> Dict[str, Any]:
        """
        Get user preferences.

        Args:
            user_id: User ID

        Returns:
            Dictionary of user preferences
        """
        return self.user_preferences.get(user_id, {})

    def build_system_prompt(
        self,
        base_prompt: str,
        user_id: Optional[int] = None,
        additional_instructions: Optional[str] = None
    ) -> str:
        """
        Build a complete system prompt with user preferences.

        Args:
            base_prompt: Base system prompt template
            user_id: User ID to fetch preferences
            additional_instructions: Extra instructions to append

        Returns:
            Complete system prompt
        """
        prompt_parts = [base_prompt]

        # Add user preferences
        if user_id:
            prefs = self.get_user_preferences(user_id)

            if prefs.get("tone"):
                prompt_parts.append(f"\nTone: {prefs['tone']}")

            if prefs.get("verbosity"):
                prompt_parts.append(f"Response style: {prefs['verbosity']}")

            if prefs.get("language") and prefs["language"] != "en":
                prompt_parts.append(f"Respond in {prefs['language']}")

        # Add additional instructions
        if additional_instructions:
            prompt_parts.append(f"\n{additional_instructions}")

        return "\n".join(prompt_parts)

    def get_conversation_summary(self, conversation_id: str) -> Dict:
        """
        Get summary statistics for a conversation.

        Args:
            conversation_id: Conversation identifier

        Returns:
            Dictionary with conversation statistics
        """
        messages = self.conversations.get(conversation_id, [])

        user_messages = [m for m in messages if m["role"] == "user"]
        assistant_messages = [m for m in messages if m["role"] == "assistant"]

        # Estimate total tokens
        total_chars = sum(len(m["content"]) for m in messages)
        estimated_tokens = total_chars // 4

        return {
            "conversation_id": conversation_id,
            "total_messages": len(messages),
            "user_messages": len(user_messages),
            "assistant_messages": len(assistant_messages),
            "estimated_tokens": estimated_tokens,
            "has_system_prompt": conversation_id in self.system_prompts,
            "created_at": messages[0]["timestamp"] if messages else None,
            "last_updated": messages[-1]["timestamp"] if messages else None,
        }

    def clear_conversation(self, conversation_id: str):
        """
        Clear all messages in a conversation.

        Args:
            conversation_id: Conversation identifier
        """
        if conversation_id in self.conversations:
            self.conversations[conversation_id] = []

    def delete_conversation(self, conversation_id: str):
        """
        Delete a conversation entirely.

        Args:
            conversation_id: Conversation identifier
        """
        if conversation_id in self.conversations:
            del self.conversations[conversation_id]

        if conversation_id in self.system_prompts:
            del self.system_prompts[conversation_id]

    def export_conversation(
        self,
        conversation_id: str,
        format: str = "json"
    ) -> str:
        """
        Export conversation in specified format.

        Args:
            conversation_id: Conversation identifier
            format: Export format (json, markdown, text)

        Returns:
            Formatted conversation string
        """
        messages = self.conversations.get(conversation_id, [])

        if format == "json":
            return json.dumps({
                "conversation_id": conversation_id,
                "system_prompt": self.system_prompts.get(conversation_id),
                "messages": messages,
            }, indent=2)

        elif format == "markdown":
            lines = [f"# Conversation: {conversation_id}\n"]

            if conversation_id in self.system_prompts:
                lines.append(f"**System**: {self.system_prompts[conversation_id]}\n")

            for msg in messages:
                role = msg["role"].capitalize()
                content = msg["content"]
                timestamp = msg["timestamp"]
                lines.append(f"**{role}** ({timestamp}):\n{content}\n")

            return "\n".join(lines)

        else:  # text format
            lines = []

            if conversation_id in self.system_prompts:
                lines.append(f"SYSTEM: {self.system_prompts[conversation_id]}\n")

            for msg in messages:
                role = msg["role"].upper()
                content = msg["content"]
                lines.append(f"{role}: {content}\n")

            return "\n".join(lines)

    def get_active_conversations(self, user_id: Optional[int] = None) -> List[str]:
        """
        Get list of active conversation IDs.

        Args:
            user_id: Filter by user ID (optional)

        Returns:
            List of conversation IDs
        """
        # For now, return all conversation IDs
        # In production, would filter by user_id from metadata
        return list(self.conversations.keys())


# Global context manager instance
context_manager = ContextManager()
