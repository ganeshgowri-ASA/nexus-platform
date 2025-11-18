"""
Main entry point for NEXUS SEO Tools.

Run FastAPI server: python -m modules.seo.main
"""

import uvicorn
from modules.seo.config.settings import get_settings


def main():
    """Run the application."""
    settings = get_settings()

    uvicorn.run(
        "modules.seo.api.app:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.api_reload,
        workers=settings.api_workers if not settings.api_reload else 1,
        log_level=settings.log_level.lower(),
    )


if __name__ == "__main__":
    main()
