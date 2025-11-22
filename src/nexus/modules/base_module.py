"""
Base module class for all Nexus sessions
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict, List, Optional
from loguru import logger

from ..core.claude_client import ClaudeClient
from ..core.cache import CacheManager


@dataclass
class ModuleConfig:
    """Configuration for a module"""
    session: int
    name: str
    icon: str
    description: str
    version: str
    features: List[str]
    enabled: bool = True


class BaseModule(ABC):
    """Abstract base class for all Nexus modules"""

    def __init__(
        self,
        config: ModuleConfig,
        claude_client: ClaudeClient,
        cache_manager: Optional[CacheManager] = None
    ):
        self.config = config
        self.claude = claude_client
        self.cache = cache_manager or CacheManager()
        self.state: Dict[str, Any] = {}
        logger.info(f"Initialized module: {self.config.name} (Session {self.config.session})")

    @abstractmethod
    def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Main processing method for the module

        Args:
            input_data: Input data dictionary

        Returns:
            Processed result dictionary
        """
        pass

    @abstractmethod
    def validate_input(self, input_data: Dict[str, Any]) -> bool:
        """
        Validate input data

        Args:
            input_data: Input to validate

        Returns:
            True if valid, False otherwise
        """
        pass

    def get_system_prompt(self) -> str:
        """Get system prompt for Claude"""
        return f"""You are an AI assistant specialized in {self.config.name}.
Your capabilities include: {', '.join(self.config.features)}.
Provide accurate, helpful, and production-ready responses."""

    def format_output(self, data: Any, format_type: str = "json") -> Any:
        """
        Format output data

        Args:
            data: Data to format
            format_type: Output format (json, text, etc.)

        Returns:
            Formatted data
        """
        if format_type == "json":
            return data
        elif format_type == "text":
            return str(data)
        else:
            return data

    def log_operation(self, operation: str, metadata: Optional[Dict] = None):
        """Log module operation"""
        log_data = {
            "module": self.config.name,
            "session": self.config.session,
            "operation": operation,
            "metadata": metadata or {}
        }
        logger.info(f"Module operation: {log_data}")

    def handle_error(self, error: Exception, context: Optional[str] = None) -> Dict[str, Any]:
        """
        Handle and format errors

        Args:
            error: Exception that occurred
            context: Optional context information

        Returns:
            Error response dictionary
        """
        error_msg = str(error)
        logger.error(f"Module error in {self.config.name}: {error_msg}", exc_info=True)

        return {
            "success": False,
            "error": error_msg,
            "module": self.config.name,
            "session": self.config.session,
            "context": context
        }

    def get_cache_key(self, operation: str, params: Dict[str, Any]) -> str:
        """Generate cache key for operation"""
        import hashlib
        import json
        key_data = {
            "module": self.config.name,
            "operation": operation,
            "params": params
        }
        key_str = json.dumps(key_data, sort_keys=True, default=str)
        return hashlib.md5(key_str.encode()).hexdigest()

    async def aprocess(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Async version of process method"""
        # Default implementation calls sync version
        # Override in subclasses for true async processing
        return self.process(input_data)

    def get_status(self) -> Dict[str, Any]:
        """Get module status"""
        return {
            "module": self.config.name,
            "session": self.config.session,
            "version": self.config.version,
            "enabled": self.config.enabled,
            "features": self.config.features,
            "state": self.state
        }

    def reset(self):
        """Reset module state"""
        self.state = {}
        logger.info(f"Reset module: {self.config.name}")
