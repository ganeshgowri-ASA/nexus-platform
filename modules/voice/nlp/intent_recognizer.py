"""Intent recognition using AI/LLM."""

import re
import json
from typing import Dict, List, Optional, Tuple
from datetime import datetime


class IntentRecognizer:
    """Recognizes user intents from text using AI/LLM."""

    def __init__(self, llm_provider: str = "anthropic", api_key: Optional[str] = None):
        """
        Initialize intent recognizer.

        Args:
            llm_provider: 'anthropic' or 'openai'
            api_key: API key for the LLM provider
        """
        self.llm_provider = llm_provider
        self.api_key = api_key
        self._client = None
        self._initialize_client()

        # Define intent categories
        self.intent_categories = {
            "productivity": [
                "create_document", "edit_document", "open_document",
                "create_spreadsheet", "create_presentation",
                "schedule_meeting", "send_email", "create_task"
            ],
            "navigation": [
                "open_module", "go_to_page", "switch_tab",
                "show_dashboard", "open_settings"
            ],
            "query": [
                "search", "find", "get_info", "calculate",
                "summarize", "analyze"
            ],
            "system": [
                "help", "settings", "logout", "cancel",
                "undo", "redo", "save", "export"
            ],
            "communication": [
                "send_message", "make_call", "start_chat",
                "share_document", "invite_user"
            ]
        }

    def _initialize_client(self):
        """Initialize the LLM client."""
        if self.llm_provider == "anthropic":
            try:
                import anthropic
                self._client = anthropic.Anthropic(api_key=self.api_key)
            except ImportError:
                raise ImportError(
                    "Anthropic SDK not installed. "
                    "Install with: pip install anthropic"
                )
        elif self.llm_provider == "openai":
            try:
                import openai
                self._client = openai.OpenAI(api_key=self.api_key)
            except ImportError:
                raise ImportError(
                    "OpenAI SDK not installed. "
                    "Install with: pip install openai"
                )

    def recognize_intent(
        self,
        text: str,
        context: Optional[Dict] = None,
        available_commands: Optional[List[str]] = None
    ) -> Dict:
        """
        Recognize intent from text.

        Args:
            text: User input text
            context: Conversation context
            available_commands: List of available command names

        Returns:
            Dict with intent, confidence, entities, and metadata
        """
        # First try rule-based matching for common patterns
        rule_based_result = self._rule_based_recognition(text)

        if rule_based_result['confidence'] > 0.8:
            return rule_based_result

        # Fall back to LLM-based recognition
        llm_result = self._llm_based_recognition(text, context, available_commands)

        # Combine results (prefer higher confidence)
        if rule_based_result['confidence'] > llm_result['confidence']:
            return rule_based_result
        else:
            return llm_result

    def _rule_based_recognition(self, text: str) -> Dict:
        """Simple rule-based intent recognition."""
        text_lower = text.lower().strip()

        # Define patterns
        patterns = {
            "create_document": [
                r"create\s+(a\s+)?(new\s+)?document",
                r"new\s+document",
                r"start\s+(a\s+)?document"
            ],
            "create_spreadsheet": [
                r"create\s+(a\s+)?(new\s+)?spreadsheet",
                r"new\s+spreadsheet",
                r"open\s+excel"
            ],
            "send_email": [
                r"send\s+(an?\s+)?email",
                r"compose\s+email",
                r"write\s+email"
            ],
            "schedule_meeting": [
                r"schedule\s+(a\s+)?meeting",
                r"create\s+(a\s+)?meeting",
                r"book\s+(a\s+)?meeting"
            ],
            "search": [
                r"search\s+for",
                r"find\s+",
                r"look\s+for"
            ],
            "help": [
                r"^help$",
                r"what\s+can\s+you\s+do",
                r"how\s+do\s+i"
            ],
            "open_module": [
                r"open\s+(\w+)\s+module",
                r"go\s+to\s+(\w+)",
                r"switch\s+to\s+(\w+)"
            ]
        }

        for intent, pattern_list in patterns.items():
            for pattern in pattern_list:
                match = re.search(pattern, text_lower)
                if match:
                    # Extract any captured groups as entities
                    entities = {}
                    if match.groups():
                        entities['target'] = match.group(1)

                    return {
                        "intent": intent,
                        "confidence": 0.85,
                        "category": self._get_category(intent),
                        "entities": entities,
                        "method": "rule_based"
                    }

        return {
            "intent": "unknown",
            "confidence": 0.0,
            "category": "unknown",
            "entities": {},
            "method": "rule_based"
        }

    def _llm_based_recognition(
        self,
        text: str,
        context: Optional[Dict],
        available_commands: Optional[List[str]]
    ) -> Dict:
        """Use LLM to recognize intent."""
        # Prepare prompt
        intent_list = []
        for category, intents in self.intent_categories.items():
            intent_list.extend(intents)

        commands_str = ""
        if available_commands:
            commands_str = f"\n\nAvailable commands: {', '.join(available_commands)}"

        context_str = ""
        if context:
            context_str = f"\n\nContext: {json.dumps(context, indent=2)}"

        prompt = f"""Analyze this user input and identify the intent.

User input: "{text}"{commands_str}{context_str}

Available intent categories and types:
{json.dumps(self.intent_categories, indent=2)}

Respond with a JSON object containing:
- intent: the specific intent name (use one from the list above, or create a descriptive one)
- confidence: confidence score from 0.0 to 1.0
- category: the category this intent belongs to
- entities: any extracted entities (e.g., names, dates, numbers)
- reasoning: brief explanation of your analysis

Example response:
{{
  "intent": "create_document",
  "confidence": 0.95,
  "category": "productivity",
  "entities": {{"title": "Project Report"}},
  "reasoning": "User wants to create a new document titled 'Project Report'"
}}

Respond with only the JSON object, no additional text."""

        try:
            if self.llm_provider == "anthropic":
                response = self._client.messages.create(
                    model="claude-3-sonnet-20240229",
                    max_tokens=500,
                    messages=[{
                        "role": "user",
                        "content": prompt
                    }]
                )
                result_text = response.content[0].text

            elif self.llm_provider == "openai":
                response = self._client.chat.completions.create(
                    model="gpt-4",
                    messages=[{
                        "role": "user",
                        "content": prompt
                    }],
                    max_tokens=500
                )
                result_text = response.choices[0].message.content

            # Parse JSON response
            result = json.loads(result_text.strip())
            result['method'] = 'llm_based'

            return result

        except Exception as e:
            return {
                "intent": "unknown",
                "confidence": 0.0,
                "category": "unknown",
                "entities": {},
                "method": "llm_based",
                "error": str(e)
            }

    def _get_category(self, intent: str) -> str:
        """Get category for an intent."""
        for category, intents in self.intent_categories.items():
            if intent in intents:
                return category
        return "unknown"

    def add_custom_intent(self, intent_name: str, category: str, patterns: List[str]):
        """
        Add a custom intent with patterns.

        Args:
            intent_name: Name of the intent
            category: Category to add it to
            patterns: List of regex patterns
        """
        if category not in self.intent_categories:
            self.intent_categories[category] = []

        if intent_name not in self.intent_categories[category]:
            self.intent_categories[category].append(intent_name)

    def get_intent_suggestions(self, partial_text: str) -> List[Dict]:
        """
        Get intent suggestions based on partial input.

        Args:
            partial_text: Partial user input

        Returns:
            List of suggested intents with examples
        """
        suggestions = []

        # Use LLM to generate suggestions
        prompt = f"""Given this partial user input, suggest 3-5 possible intents they might want to complete.

Partial input: "{partial_text}"

For each suggestion, provide:
- intent: the intent name
- completion: how they might complete the sentence
- category: intent category

Respond with JSON array only."""

        try:
            if self.llm_provider == "anthropic":
                response = self._client.messages.create(
                    model="claude-3-sonnet-20240229",
                    max_tokens=300,
                    messages=[{"role": "user", "content": prompt}]
                )
                suggestions = json.loads(response.content[0].text.strip())

        except Exception:
            pass

        return suggestions
