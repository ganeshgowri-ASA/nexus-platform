"""
Base module class for all NEXUS modules.
"""
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
import streamlit as st


class BaseModule(ABC):
    """Abstract base class for all NEXUS modules."""

    def __init__(self):
        """Initialize the module."""
        self.module_name: str = "Base Module"
        self.icon: str = "📄"
        self.description: str = "Base module description"
        self.version: str = "1.0.0"

    @abstractmethod
    def render(self) -> None:
        """
        Render the module UI using Streamlit.
        Must be implemented by subclasses.
        """
        pass

    def initialize_session_state(self, defaults: Dict[str, Any]) -> None:
        """
        Initialize Streamlit session state with default values.

        Args:
            defaults: Dictionary of default values for session state
        """
        for key, value in defaults.items():
            if key not in st.session_state:
                st.session_state[key] = value

    def get_session_state(self, key: str, default: Any = None) -> Any:
        """
        Get value from Streamlit session state.

        Args:
            key: Session state key
            default: Default value if key doesn't exist

        Returns:
            Session state value
        """
        return st.session_state.get(key, default)

    def set_session_state(self, key: str, value: Any) -> None:
        """
        Set value in Streamlit session state.

        Args:
            key: Session state key
            value: Value to set
        """
        st.session_state[key] = value

    def clear_session_state(self) -> None:
        """Clear all session state for this module."""
        keys_to_remove = [
            key for key in st.session_state.keys()
            if key.startswith(f"{self.module_name.lower().replace(' ', '_')}_")
        ]
        for key in keys_to_remove:
            del st.session_state[key]

    def show_header(self) -> None:
        """Display module header."""
        st.title(f"{self.icon} {self.module_name}")
        st.caption(self.description)
        st.divider()

    def show_error(self, message: str) -> None:
        """
        Display error message.

        Args:
            message: Error message
        """
        st.error(f"❌ {message}")

    def show_success(self, message: str) -> None:
        """
        Display success message.

        Args:
            message: Success message
        """
        st.success(f"✅ {message}")

    def show_warning(self, message: str) -> None:
        """
        Display warning message.

        Args:
            message: Warning message
        """
        st.warning(f"⚠️ {message}")

    def show_info(self, message: str) -> None:
        """
        Display info message.

        Args:
            message: Info message
        """
        st.info(f"ℹ️ {message}")

    @abstractmethod
    def handle_user_input(self, input_data: Any) -> Dict[str, Any]:
        """
        Process user input and return results.
        Must be implemented by subclasses.

        Args:
            input_data: User input data

        Returns:
            Dictionary with processing results
        """
        pass

    def export_data(self, data: Any, format: str = "json") -> bytes:
        """
        Export module data in specified format.
        Can be overridden by subclasses.

        Args:
            data: Data to export
            format: Export format

        Returns:
            Exported data as bytes
        """
        raise NotImplementedError("Export functionality not implemented for this module")

    def import_data(self, data: bytes, format: str = "json") -> Any:
        """
        Import data into module.
        Can be overridden by subclasses.

        Args:
            data: Data to import
            format: Data format

        Returns:
            Imported data
        """
        raise NotImplementedError("Import functionality not implemented for this module")

    def get_module_info(self) -> Dict[str, str]:
        """
        Get module information.

        Returns:
            Dictionary with module info
        """
        return {
            "name": self.module_name,
            "icon": self.icon,
            "description": self.description,
            "version": self.version,
        }
