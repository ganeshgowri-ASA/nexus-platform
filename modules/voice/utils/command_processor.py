"""Voice command processor."""

import time
from typing import Dict, Optional, Any
from datetime import datetime

from ..nlp.intent_recognizer import IntentRecognizer
from ..nlp.entity_extractor import EntityExtractor
from ..nlp.context_manager import ContextManager
from .command_registry import CommandRegistry


class CommandProcessor:
    """Process voice commands and execute actions."""

    def __init__(
        self,
        intent_recognizer: IntentRecognizer,
        entity_extractor: EntityExtractor,
        context_manager: ContextManager,
        command_registry: CommandRegistry
    ):
        """
        Initialize command processor.

        Args:
            intent_recognizer: Intent recognition service
            entity_extractor: Entity extraction service
            context_manager: Context management service
            command_registry: Command registry
        """
        self.intent_recognizer = intent_recognizer
        self.entity_extractor = entity_extractor
        self.context_manager = context_manager
        self.command_registry = command_registry

    def process_command(
        self,
        transcript: str,
        session_id: str,
        user_id: str
    ) -> Dict:
        """
        Process a voice command.

        Args:
            transcript: Transcribed text
            session_id: Session identifier
            user_id: User identifier

        Returns:
            Dict with processing results
        """
        start_time = time.time()

        # Get or create session
        session = self.context_manager.get_session(session_id)
        if not session:
            session = self.context_manager.create_session(session_id, user_id)

        # Get context for intent recognition
        context = self.context_manager.get_context_for_intent(session_id)

        # Extract entities
        entities = self.entity_extractor.extract_entities(transcript)

        # Get available commands
        available_commands = [
            cmd["name"] for cmd in self.command_registry.get_all_commands()
        ]

        # Recognize intent
        intent_result = self.intent_recognizer.recognize_intent(
            transcript,
            context=context,
            available_commands=available_commands
        )

        intent = intent_result.get("intent")
        confidence = intent_result.get("confidence", 0.0)

        # Check if we have a matching command
        command = self.command_registry.get_command_by_intent(intent)

        if not command:
            response = self._handle_unknown_command(transcript, intent_result)
            action_result = None
        elif confidence < 0.5:
            response = self._handle_low_confidence(transcript, intent_result, command)
            action_result = None
        else:
            # Execute command
            action_result = self._execute_command(
                command,
                entities,
                session_id,
                transcript
            )
            response = action_result.get("response", "Command executed")

        # Add to context
        self.context_manager.add_interaction(
            session_id=session_id,
            user_input=transcript,
            transcript=transcript,
            intent=intent,
            entities=entities,
            response=response,
            action_taken=action_result
        )

        processing_time = (time.time() - start_time) * 1000

        return {
            "transcript": transcript,
            "intent": intent,
            "confidence": confidence,
            "entities": entities,
            "command": command["name"] if command else None,
            "response": response,
            "action_result": action_result,
            "processing_time_ms": processing_time,
            "session_id": session_id
        }

    def _execute_command(
        self,
        command: Dict,
        entities: Dict,
        session_id: str,
        transcript: str
    ) -> Dict:
        """
        Execute a command.

        Args:
            command: Command definition
            entities: Extracted entities
            session_id: Session identifier
            transcript: Original transcript

        Returns:
            Execution result
        """
        # Check if command requires confirmation
        if command.get("requires_confirmation"):
            # Add to pending confirmations
            self.context_manager.add_pending_confirmation(
                session_id,
                command["name"],
                {"entities": entities, "transcript": transcript}
            )

            return {
                "status": "pending_confirmation",
                "response": f"Are you sure you want to {command['description'].lower()}?",
                "command": command["name"]
            }

        # Extract required parameters
        params = self._extract_parameters(command, entities, transcript)

        # Check if all required parameters are present
        missing_params = [
            p for p in command.get("params", [])
            if p not in params
        ]

        if missing_params:
            return {
                "status": "missing_parameters",
                "response": f"I need more information: {', '.join(missing_params)}",
                "missing": missing_params,
                "command": command["name"]
            }

        # Update module context
        self.context_manager.set_module_context(session_id, command["module"])

        # Execute the command
        # In a real implementation, this would call the actual handler
        result = self._call_handler(
            command["module"],
            command["handler"],
            params
        )

        return {
            "status": "success",
            "response": result.get("message", f"Successfully executed {command['name']}"),
            "command": command["name"],
            "module": command["module"],
            "result": result
        }

    def _extract_parameters(
        self,
        command: Dict,
        entities: Dict,
        transcript: str
    ) -> Dict:
        """
        Extract command parameters from entities and transcript.

        Args:
            command: Command definition
            entities: Extracted entities
            transcript: Original transcript

        Returns:
            Dict of parameters
        """
        params = {}

        # Map entities to parameters
        param_mapping = {
            "title": ["transcript"],  # Use transcript as title if not found
            "to": ["emails"],
            "subject": ["transcript"],
            "body": ["transcript"],
            "date": ["dates"],
            "time": ["times"],
            "duration": ["durations"],
            "query": ["transcript"],
            "module_name": ["transcript"],
            "metric_type": ["transcript"]
        }

        for param in command.get("params", []):
            # Check if we have a mapping
            if param in param_mapping:
                sources = param_mapping[param]

                for source in sources:
                    if source == "transcript":
                        # Extract from transcript based on parameter type
                        value = self._extract_from_transcript(param, transcript)
                        if value:
                            params[param] = value
                            break
                    elif source in entities and entities[source]:
                        # Use first entity of this type
                        entity_value = entities[source]
                        if isinstance(entity_value, list) and entity_value:
                            params[param] = entity_value[0]
                        else:
                            params[param] = entity_value
                        break

        return params

    def _extract_from_transcript(self, param: str, transcript: str) -> Optional[str]:
        """Extract parameter value from transcript."""
        import re

        if param == "title":
            # Try to extract text after "called", "named", "titled"
            patterns = [
                r'(?:called|named|titled)\s+["\']?([^"\']+)["\']?',
                r'create\s+(?:a\s+)?(?:new\s+)?(?:document|spreadsheet|presentation)\s+(.+)',
            ]
            for pattern in patterns:
                match = re.search(pattern, transcript, re.IGNORECASE)
                if match:
                    return match.group(1).strip()

            # Fall back to using part of transcript
            return transcript[:50]

        elif param == "module_name":
            # Extract module name from phrases like "open X module", "go to X"
            patterns = [
                r'(?:open|go to|show|switch to)\s+(\w+)',
            ]
            for pattern in patterns:
                match = re.search(pattern, transcript, re.IGNORECASE)
                if match:
                    return match.group(1).strip()

        elif param == "query":
            # Extract search query
            patterns = [
                r'(?:search for|find|look for)\s+(.+)',
            ]
            for pattern in patterns:
                match = re.search(pattern, transcript, re.IGNORECASE)
                if match:
                    return match.group(1).strip()

        return None

    def _call_handler(self, module: str, handler: str, params: Dict) -> Dict:
        """
        Call the command handler.

        This is a placeholder - in a real implementation,
        this would route to the actual module handlers.

        Args:
            module: Module name
            handler: Handler function name
            params: Parameters

        Returns:
            Handler result
        """
        # Placeholder implementation
        return {
            "success": True,
            "message": f"Executed {handler} in {module} module",
            "params": params,
            "timestamp": datetime.utcnow().isoformat()
        }

    def _handle_unknown_command(self, transcript: str, intent_result: Dict) -> str:
        """Handle unknown commands."""
        suggestions = self.command_registry.search_commands(transcript)

        if suggestions:
            cmd_names = [cmd["name"] for cmd in suggestions[:3]]
            return f"I'm not sure what you want to do. Did you mean: {', '.join(cmd_names)}?"
        else:
            return "I didn't understand that command. Say 'help' to see available commands."

    def _handle_low_confidence(
        self,
        transcript: str,
        intent_result: Dict,
        command: Dict
    ) -> str:
        """Handle low confidence intent recognition."""
        return (
            f"I'm not sure I understood correctly. "
            f"Did you want to {command['description'].lower()}? "
            f"Please confirm or rephrase your request."
        )

    def confirm_command(self, session_id: str, confirmed: bool) -> Dict:
        """
        Confirm or cancel a pending command.

        Args:
            session_id: Session identifier
            confirmed: Whether user confirmed

        Returns:
            Result dictionary
        """
        pending = self.context_manager.get_pending_confirmations(session_id)

        if not pending:
            return {
                "status": "error",
                "response": "No pending commands to confirm"
            }

        # Get the most recent pending command
        pending_cmd = pending[-1]

        if confirmed:
            # Execute the command
            command = self.command_registry.get_command(pending_cmd["action"])
            if command:
                result = self._execute_command(
                    command,
                    pending_cmd["details"].get("entities", {}),
                    session_id,
                    pending_cmd["details"].get("transcript", "")
                )
                self.context_manager.clear_pending_confirmations(session_id)
                return result
        else:
            # Cancel the command
            self.context_manager.clear_pending_confirmations(session_id)
            return {
                "status": "cancelled",
                "response": "Command cancelled"
            }

    def get_help(self, category: Optional[str] = None) -> str:
        """Get help text."""
        return self.command_registry.get_help_text(category)
