"""Main Streamlit application for Nexus Platform."""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from nexus.core.database import init_db
from nexus.core.logger import get_logger, setup_logging
from nexus.modules.notes.ui.streamlit_ui import render_notes_app

logger = get_logger(__name__)


def main():
    """Main application entry point."""
    # Setup logging
    setup_logging()

    # Initialize database
    try:
        init_db()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")

    # Render the notes app
    render_notes_app()


if __name__ == "__main__":
    main()
