"""
RPA Actions - Individual automation action executors
"""
from typing import Dict, Any
import asyncio
import re
from datetime import datetime

try:
    import pyautogui
    import cv2
    import numpy as np
    from PIL import Image
    DESKTOP_AUTOMATION_AVAILABLE = True
except ImportError:
    DESKTOP_AUTOMATION_AVAILABLE = False

from src.utils.logger import get_logger

logger = get_logger(__name__)


class ActionExecutor:
    """Executes individual automation actions"""

    def __init__(self):
        self.action_map = {
            "click": self.click_action,
            "type": self.type_action,
            "wait": self.wait_action,
            "condition": self.condition_action,
            "loop": self.loop_action,
            "set_variable": self.set_variable_action,
            "get_variable": self.get_variable_action,
            "log": self.log_action,
            "http_request": self.http_request_action,
            "data_manipulation": self.data_manipulation_action,
            "screenshot": self.screenshot_action,
        }

    async def execute_action(
        self, action_type: str, config: Dict[str, Any], context: Dict[str, Any]
    ):
        """
        Execute an action

        Args:
            action_type: Type of action to execute
            config: Action configuration
            context: Execution context with variables

        Raises:
            ValueError: If action type is not supported
        """
        action_func = self.action_map.get(action_type)
        if not action_func:
            raise ValueError(f"Unsupported action type: {action_type}")

        logger.info(f"Executing action: {action_type}")
        await action_func(config, context)

    async def click_action(self, config: Dict[str, Any], context: Dict[str, Any]):
        """Click action - simulates mouse click"""
        if not DESKTOP_AUTOMATION_AVAILABLE:
            logger.warning("Desktop automation libraries not available")
            return

        x = config.get("x")
        y = config.get("y")
        clicks = config.get("clicks", 1)
        button = config.get("button", "left")

        # Resolve variables if present
        x = self._resolve_value(x, context)
        y = self._resolve_value(y, context)

        logger.info(f"Clicking at ({x}, {y}) with {button} button")

        if x is not None and y is not None:
            pyautogui.click(x, y, clicks=clicks, button=button)
        else:
            logger.warning("Click coordinates not provided")

    async def type_action(self, config: Dict[str, Any], context: Dict[str, Any]):
        """Type action - simulates keyboard typing"""
        if not DESKTOP_AUTOMATION_AVAILABLE:
            logger.warning("Desktop automation libraries not available")
            return

        text = config.get("text", "")
        interval = config.get("interval", 0.1)

        # Resolve variables in text
        text = self._resolve_value(text, context)

        logger.info(f"Typing text: {text[:50]}...")
        pyautogui.write(str(text), interval=interval)

    async def wait_action(self, config: Dict[str, Any], context: Dict[str, Any]):
        """Wait action - pauses execution"""
        duration = config.get("duration", 1)
        duration = self._resolve_value(duration, context)

        logger.info(f"Waiting for {duration} seconds")
        await asyncio.sleep(float(duration))

    async def condition_action(self, config: Dict[str, Any], context: Dict[str, Any]):
        """Condition action - evaluates a condition"""
        condition = config.get("condition")
        operator = config.get("operator", "==")
        left = self._resolve_value(config.get("left"), context)
        right = self._resolve_value(config.get("right"), context)

        result = self._evaluate_condition(left, operator, right)
        logger.info(f"Condition {left} {operator} {right} = {result}")

        # Store result in context
        if config.get("store_as"):
            context["variables"][config["store_as"]] = result

    async def loop_action(self, config: Dict[str, Any], context: Dict[str, Any]):
        """Loop action - iterates over a collection"""
        items = config.get("items", [])
        items = self._resolve_value(items, context)

        if not isinstance(items, list):
            items = list(range(int(items)))

        variable_name = config.get("variable", "item")

        logger.info(f"Looping over {len(items)} items")

        for i, item in enumerate(items):
            context["variables"][variable_name] = item
            context["variables"][f"{variable_name}_index"] = i

    async def set_variable_action(
        self, config: Dict[str, Any], context: Dict[str, Any]
    ):
        """Set variable action - sets a variable value"""
        name = config.get("name")
        value = self._resolve_value(config.get("value"), context)

        logger.info(f"Setting variable {name} = {value}")
        context["variables"][name] = value

    async def get_variable_action(
        self, config: Dict[str, Any], context: Dict[str, Any]
    ):
        """Get variable action - retrieves a variable value"""
        name = config.get("name")
        value = context["variables"].get(name)

        logger.info(f"Getting variable {name} = {value}")

        if config.get("store_as"):
            context["variables"][config["store_as"]] = value

    async def log_action(self, config: Dict[str, Any], context: Dict[str, Any]):
        """Log action - logs a message"""
        message = self._resolve_value(config.get("message", ""), context)
        level = config.get("level", "INFO")

        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": level,
            "message": message,
        }

        context["logs"].append(log_entry)
        logger.info(f"Log: {message}")

    async def http_request_action(
        self, config: Dict[str, Any], context: Dict[str, Any]
    ):
        """HTTP request action - makes an HTTP request"""
        import httpx

        url = self._resolve_value(config.get("url"), context)
        method = config.get("method", "GET").upper()
        headers = config.get("headers", {})
        data = self._resolve_value(config.get("data"), context)

        logger.info(f"Making {method} request to {url}")

        async with httpx.AsyncClient() as client:
            response = await client.request(
                method, url, headers=headers, json=data
            )

            result = {
                "status_code": response.status_code,
                "headers": dict(response.headers),
                "body": response.text,
            }

            if config.get("store_as"):
                context["variables"][config["store_as"]] = result

    async def data_manipulation_action(
        self, config: Dict[str, Any], context: Dict[str, Any]
    ):
        """Data manipulation action - transforms data"""
        operation = config.get("operation")
        data = self._resolve_value(config.get("data"), context)

        if operation == "parse_json":
            import json

            result = json.loads(data)
        elif operation == "to_json":
            import json

            result = json.dumps(data)
        elif operation == "split":
            delimiter = config.get("delimiter", ",")
            result = str(data).split(delimiter)
        elif operation == "join":
            delimiter = config.get("delimiter", ",")
            result = delimiter.join(map(str, data))
        elif operation == "uppercase":
            result = str(data).upper()
        elif operation == "lowercase":
            result = str(data).lower()
        elif operation == "trim":
            result = str(data).strip()
        else:
            result = data

        if config.get("store_as"):
            context["variables"][config["store_as"]] = result

    async def screenshot_action(
        self, config: Dict[str, Any], context: Dict[str, Any]
    ):
        """Screenshot action - captures screen"""
        if not DESKTOP_AUTOMATION_AVAILABLE:
            logger.warning("Desktop automation libraries not available")
            return

        filename = config.get("filename", "screenshot.png")
        filename = self._resolve_value(filename, context)

        logger.info(f"Taking screenshot: {filename}")
        screenshot = pyautogui.screenshot()
        screenshot.save(filename)

        if config.get("store_as"):
            context["variables"][config["store_as"]] = filename

    def _resolve_value(self, value: Any, context: Dict[str, Any]) -> Any:
        """Resolve a value, replacing variable references"""
        if isinstance(value, str):
            # Replace variable references like {{variable_name}}
            pattern = r"\{\{(\w+)\}\}"
            matches = re.findall(pattern, value)

            for var_name in matches:
                var_value = context["variables"].get(var_name, "")
                value = value.replace(f"{{{{{var_name}}}}}", str(var_value))

            # If the entire value is just a variable reference, return the actual value
            if value.startswith("{{") and value.endswith("}}"):
                var_name = value[2:-2]
                return context["variables"].get(var_name)

        return value

    def _evaluate_condition(self, left: Any, operator: str, right: Any) -> bool:
        """Evaluate a condition"""
        operators = {
            "==": lambda l, r: l == r,
            "!=": lambda l, r: l != r,
            ">": lambda l, r: l > r,
            "<": lambda l, r: l < r,
            ">=": lambda l, r: l >= r,
            "<=": lambda l, r: l <= r,
            "in": lambda l, r: l in r,
            "not in": lambda l, r: l not in r,
            "contains": lambda l, r: r in l,
        }

        op_func = operators.get(operator)
        if not op_func:
            raise ValueError(f"Unsupported operator: {operator}")

        return op_func(left, right)
