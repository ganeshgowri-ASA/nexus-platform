"""Pipeline module implementation."""

from typing import List
from core.base_module import BaseModule


class PipelineModule(BaseModule):
    """Pipeline module for visual pipeline building and orchestration."""

    MODULE_NAME = "pipeline"
    MODULE_ICON = "⚙️"
    MODULE_DESCRIPTION = "Visual pipeline builder with ETL workflows, stream processing, and monitoring"
    MODULE_VERSION = "1.0.0"

    def render_ui(self):
        """Render Streamlit UI for pipeline module."""
        from .ui import PipelineUI
        return PipelineUI.render()

    def get_routes(self):
        """Return FastAPI router for pipeline endpoints."""
        from .api import router
        return router

    def get_models(self) -> List:
        """Return SQLAlchemy models for pipeline module."""
        from .models import (
            Pipeline,
            PipelineStep,
            PipelineExecution,
            StepExecution,
            Connector,
            Schedule
        )
        return [
            Pipeline,
            PipelineStep,
            PipelineExecution,
            StepExecution,
            Connector,
            Schedule
        ]

    def initialize(self):
        """Initialize pipeline module."""
        from .services import PipelineService
        # Initialize default connectors, transformations, etc.
        pass
