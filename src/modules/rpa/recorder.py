"""
Process Recorder - Records user actions to create automation workflows
"""
from typing import List, Dict, Any, Optional
import time
from datetime import datetime
import json

try:
    from pynput import mouse, keyboard
    import pyautogui
    RECORDING_AVAILABLE = True
except ImportError:
    RECORDING_AVAILABLE = False

from src.utils.logger import get_logger
from src.utils.helpers import generate_id

logger = get_logger(__name__)


class ProcessRecorder:
    """Records user interactions to create automation workflows"""

    def __init__(self):
        self.is_recording = False
        self.recorded_actions = []
        self.start_time = None
        self.mouse_listener = None
        self.keyboard_listener = None
        self.last_mouse_position = None

    def start_recording(self):
        """Start recording user actions"""
        if not RECORDING_AVAILABLE:
            logger.error("Recording libraries not available")
            raise RuntimeError("Recording libraries not installed")

        if self.is_recording:
            logger.warning("Recording is already in progress")
            return

        self.is_recording = True
        self.recorded_actions = []
        self.start_time = time.time()

        logger.info("Started recording")

        # Start mouse listener
        self.mouse_listener = mouse.Listener(
            on_click=self._on_click, on_scroll=self._on_scroll
        )
        self.mouse_listener.start()

        # Start keyboard listener
        self.keyboard_listener = keyboard.Listener(on_press=self._on_key_press)
        self.keyboard_listener.start()

    def stop_recording(self) -> List[Dict[str, Any]]:
        """Stop recording and return recorded actions"""
        if not self.is_recording:
            logger.warning("No recording in progress")
            return []

        self.is_recording = False

        # Stop listeners
        if self.mouse_listener:
            self.mouse_listener.stop()
        if self.keyboard_listener:
            self.keyboard_listener.stop()

        logger.info(f"Stopped recording. Recorded {len(self.recorded_actions)} actions")

        return self.recorded_actions

    def _on_click(self, x, y, button, pressed):
        """Handle mouse click events"""
        if not self.is_recording:
            return

        if pressed:
            timestamp = time.time() - self.start_time

            action = {
                "id": generate_id(),
                "type": "click",
                "timestamp": timestamp,
                "config": {
                    "x": x,
                    "y": y,
                    "button": str(button).split(".")[-1].lower(),
                },
            }

            self.recorded_actions.append(action)
            logger.debug(f"Recorded click at ({x}, {y})")

    def _on_scroll(self, x, y, dx, dy):
        """Handle mouse scroll events"""
        if not self.is_recording:
            return

        timestamp = time.time() - self.start_time

        action = {
            "id": generate_id(),
            "type": "scroll",
            "timestamp": timestamp,
            "config": {"x": x, "y": y, "dx": dx, "dy": dy},
        }

        self.recorded_actions.append(action)
        logger.debug(f"Recorded scroll at ({x}, {y})")

    def _on_key_press(self, key):
        """Handle keyboard press events"""
        if not self.is_recording:
            return

        timestamp = time.time() - self.start_time

        try:
            key_char = key.char
            action_type = "type"
        except AttributeError:
            key_char = str(key).split(".")[-1]
            action_type = "key_press"

        action = {
            "id": generate_id(),
            "type": action_type,
            "timestamp": timestamp,
            "config": {"key": key_char},
        }

        self.recorded_actions.append(action)
        logger.debug(f"Recorded key press: {key_char}")

    def convert_to_workflow(
        self, actions: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Convert recorded actions to workflow definition

        Args:
            actions: List of recorded actions

        Returns:
            Workflow definition with nodes and edges
        """
        nodes = []
        edges = []

        # Group consecutive type actions
        grouped_actions = self._group_type_actions(actions)

        for i, action in enumerate(grouped_actions):
            node_id = action.get("id") or f"node_{i}"

            node = {
                "id": node_id,
                "type": action["type"],
                "name": f"{action['type'].title()} Action {i + 1}",
                "config": action.get("config", {}),
                "position": {"x": 100, "y": i * 100},
            }

            nodes.append(node)

            # Create edge to next node
            if i > 0:
                edge = {
                    "id": f"edge_{i - 1}_{i}",
                    "source": grouped_actions[i - 1].get("id") or f"node_{i - 1}",
                    "target": node_id,
                }
                edges.append(edge)

        return {"nodes": nodes, "edges": edges, "variables": {}}

    def _group_type_actions(
        self, actions: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Group consecutive typing actions together"""
        grouped = []
        current_text = ""
        last_timestamp = None

        for action in actions:
            if action["type"] == "type":
                if current_text == "":
                    last_timestamp = action["timestamp"]

                current_text += action["config"]["key"]
            else:
                # Save accumulated text if any
                if current_text:
                    grouped.append(
                        {
                            "id": generate_id(),
                            "type": "type",
                            "timestamp": last_timestamp,
                            "config": {"text": current_text},
                        }
                    )
                    current_text = ""

                # Add non-type action
                grouped.append(action)

        # Save any remaining text
        if current_text:
            grouped.append(
                {
                    "id": generate_id(),
                    "type": "type",
                    "timestamp": last_timestamp,
                    "config": {"text": current_text},
                }
            )

        return grouped

    def save_recording(
        self, filename: str, actions: List[Dict[str, Any]]
    ) -> bool:
        """Save recorded actions to a file"""
        try:
            with open(filename, "w") as f:
                json.dump(
                    {
                        "recorded_at": datetime.utcnow().isoformat(),
                        "actions": actions,
                    },
                    f,
                    indent=2,
                )
            logger.info(f"Saved recording to {filename}")
            return True
        except Exception as e:
            logger.error(f"Failed to save recording: {str(e)}")
            return False

    def load_recording(self, filename: str) -> Optional[List[Dict[str, Any]]]:
        """Load recorded actions from a file"""
        try:
            with open(filename, "r") as f:
                data = json.load(f)
                return data.get("actions", [])
        except Exception as e:
            logger.error(f"Failed to load recording: {str(e)}")
            return None
