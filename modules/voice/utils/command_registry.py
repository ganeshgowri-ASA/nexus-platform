"""Command registry for voice commands."""

from typing import Dict, List, Callable, Optional
import json
from pathlib import Path


class CommandRegistry:
    """Registry for voice commands and their handlers."""

    def __init__(self):
        """Initialize command registry."""
        self.commands = {}
        self._initialize_default_commands()

    def _initialize_default_commands(self):
        """Initialize default NEXUS commands."""
        default_commands = [
            {
                "name": "create_document",
                "intent": "create_document",
                "category": "productivity",
                "patterns": [
                    "create (a )?(new )?document",
                    "new document",
                    "start (a )?document"
                ],
                "description": "Create a new document",
                "module": "word",
                "handler": "create_new_document",
                "params": ["title"],
                "examples": [
                    "Create a new document",
                    "Create a document called Project Report"
                ]
            },
            {
                "name": "create_spreadsheet",
                "intent": "create_spreadsheet",
                "category": "productivity",
                "patterns": [
                    "create (a )?(new )?spreadsheet",
                    "new spreadsheet",
                    "open excel"
                ],
                "description": "Create a new spreadsheet",
                "module": "excel",
                "handler": "create_new_spreadsheet",
                "params": ["title"],
                "examples": [
                    "Create a new spreadsheet",
                    "Create a spreadsheet for budget tracking"
                ]
            },
            {
                "name": "create_presentation",
                "intent": "create_presentation",
                "category": "productivity",
                "patterns": [
                    "create (a )?(new )?presentation",
                    "new presentation",
                    "start powerpoint"
                ],
                "description": "Create a new presentation",
                "module": "powerpoint",
                "handler": "create_new_presentation",
                "params": ["title"],
                "examples": [
                    "Create a new presentation",
                    "Create a presentation about quarterly results"
                ]
            },
            {
                "name": "send_email",
                "intent": "send_email",
                "category": "communication",
                "patterns": [
                    "send (an? )?email",
                    "compose email",
                    "write email"
                ],
                "description": "Send an email",
                "module": "email",
                "handler": "compose_email",
                "params": ["to", "subject", "body"],
                "examples": [
                    "Send an email to john@example.com",
                    "Compose an email about the meeting"
                ]
            },
            {
                "name": "schedule_meeting",
                "intent": "schedule_meeting",
                "category": "productivity",
                "patterns": [
                    "schedule (a )?meeting",
                    "create (a )?meeting",
                    "book (a )?meeting"
                ],
                "description": "Schedule a meeting",
                "module": "meetings",
                "handler": "create_meeting",
                "params": ["title", "date", "time", "duration"],
                "examples": [
                    "Schedule a meeting for tomorrow at 2pm",
                    "Book a meeting called Team Sync"
                ]
            },
            {
                "name": "open_module",
                "intent": "open_module",
                "category": "navigation",
                "patterns": [
                    "open (\\w+) module",
                    "go to (\\w+)",
                    "switch to (\\w+)",
                    "show (\\w+)"
                ],
                "description": "Open a NEXUS module",
                "module": "system",
                "handler": "navigate_to_module",
                "params": ["module_name"],
                "examples": [
                    "Open email module",
                    "Go to calendar",
                    "Show analytics"
                ]
            },
            {
                "name": "search",
                "intent": "search",
                "category": "query",
                "patterns": [
                    "search for (.+)",
                    "find (.+)",
                    "look for (.+)"
                ],
                "description": "Search for content",
                "module": "search",
                "handler": "perform_search",
                "params": ["query"],
                "examples": [
                    "Search for project files",
                    "Find emails from last week"
                ]
            },
            {
                "name": "create_task",
                "intent": "create_task",
                "category": "productivity",
                "patterns": [
                    "create (a )?(new )?task",
                    "add task",
                    "new task"
                ],
                "description": "Create a new task",
                "module": "projects",
                "handler": "create_task",
                "params": ["title", "due_date", "priority"],
                "examples": [
                    "Create a task to review the proposal",
                    "Add a task for tomorrow"
                ]
            },
            {
                "name": "show_analytics",
                "intent": "show_analytics",
                "category": "query",
                "patterns": [
                    "show analytics",
                    "display (\\w+) analytics",
                    "analytics for (.+)"
                ],
                "description": "Show analytics dashboard",
                "module": "analytics",
                "handler": "show_analytics",
                "params": ["metric_type"],
                "examples": [
                    "Show analytics",
                    "Display sales analytics"
                ]
            },
            {
                "name": "help",
                "intent": "help",
                "category": "system",
                "patterns": [
                    "help",
                    "what can you do",
                    "show commands"
                ],
                "description": "Show help information",
                "module": "system",
                "handler": "show_help",
                "params": [],
                "examples": [
                    "Help",
                    "What can you do?"
                ]
            }
        ]

        for cmd in default_commands:
            self.register_command(**cmd)

    def register_command(
        self,
        name: str,
        intent: str,
        category: str,
        patterns: List[str],
        description: str,
        module: str,
        handler: str,
        params: List[str],
        examples: List[str],
        requires_confirmation: bool = False,
        priority: int = 0
    ):
        """
        Register a voice command.

        Args:
            name: Command name
            intent: Associated intent
            category: Command category
            patterns: List of regex patterns that trigger this command
            description: Command description
            module: NEXUS module that handles this command
            handler: Handler function name
            params: Required parameters
            examples: Example phrases
            requires_confirmation: Whether command requires confirmation
            priority: Command priority (higher = checked first)
        """
        self.commands[name] = {
            "name": name,
            "intent": intent,
            "category": category,
            "patterns": patterns,
            "description": description,
            "module": module,
            "handler": handler,
            "params": params,
            "examples": examples,
            "requires_confirmation": requires_confirmation,
            "priority": priority,
            "is_active": True
        }

    def get_command(self, name: str) -> Optional[Dict]:
        """Get command by name."""
        return self.commands.get(name)

    def get_command_by_intent(self, intent: str) -> Optional[Dict]:
        """Get command by intent."""
        for cmd in self.commands.values():
            if cmd["intent"] == intent and cmd["is_active"]:
                return cmd
        return None

    def get_commands_by_category(self, category: str) -> List[Dict]:
        """Get all commands in a category."""
        return [
            cmd for cmd in self.commands.values()
            if cmd["category"] == category and cmd["is_active"]
        ]

    def get_all_commands(self) -> List[Dict]:
        """Get all active commands."""
        return [cmd for cmd in self.commands.values() if cmd["is_active"]]

    def disable_command(self, name: str):
        """Disable a command."""
        if name in self.commands:
            self.commands[name]["is_active"] = False

    def enable_command(self, name: str):
        """Enable a command."""
        if name in self.commands:
            self.commands[name]["is_active"] = True

    def update_command_priority(self, name: str, priority: int):
        """Update command priority."""
        if name in self.commands:
            self.commands[name]["priority"] = priority

    def search_commands(self, query: str) -> List[Dict]:
        """
        Search for commands by name, description, or examples.

        Args:
            query: Search query

        Returns:
            List of matching commands
        """
        query_lower = query.lower()
        matches = []

        for cmd in self.commands.values():
            if not cmd["is_active"]:
                continue

            # Check name
            if query_lower in cmd["name"].lower():
                matches.append(cmd)
                continue

            # Check description
            if query_lower in cmd["description"].lower():
                matches.append(cmd)
                continue

            # Check examples
            if any(query_lower in ex.lower() for ex in cmd["examples"]):
                matches.append(cmd)
                continue

        return matches

    def get_help_text(self, category: Optional[str] = None) -> str:
        """
        Get help text for commands.

        Args:
            category: Optional category filter

        Returns:
            Formatted help text
        """
        if category:
            commands = self.get_commands_by_category(category)
            header = f"Commands in category: {category}"
        else:
            commands = self.get_all_commands()
            header = "All available voice commands"

        if not commands:
            return "No commands available"

        # Group by category
        by_category = {}
        for cmd in commands:
            cat = cmd["category"]
            if cat not in by_category:
                by_category[cat] = []
            by_category[cat].append(cmd)

        lines = [header, "=" * len(header), ""]

        for cat, cmds in sorted(by_category.items()):
            lines.append(f"\n{cat.upper()}:")
            for cmd in sorted(cmds, key=lambda x: x["name"]):
                lines.append(f"\n  {cmd['name']}")
                lines.append(f"    Description: {cmd['description']}")
                lines.append(f"    Examples: {', '.join(cmd['examples'][:2])}")

        return "\n".join(lines)

    def export_to_json(self, file_path: str):
        """Export commands to JSON file."""
        with open(file_path, 'w') as f:
            json.dump(self.commands, f, indent=2)

    def import_from_json(self, file_path: str):
        """Import commands from JSON file."""
        with open(file_path, 'r') as f:
            commands = json.load(f)
            for name, cmd in commands.items():
                self.commands[name] = cmd
