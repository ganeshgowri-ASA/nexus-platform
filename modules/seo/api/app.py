"""
FastAPI application setup.

Main application factory for the SEO tools API.
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from loguru import logger

from modules.seo.config.database import db_manager
from modules.seo.config.logging import setup_logging
from modules.seo.config.redis import redis_manager
from modules.seo.config.settings import get_settings
from modules.seo.utils.exceptions import SEOException

# Import routers
from .routers import (
    keywords,
    rankings,
    audit,
    backlinks,
    competitors,
    content,
    technical,
    schema,
    sitemap,
    meta_tags,
    links,
    reports,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup
    setup_logging()
    logger.info("Starting NEXUS SEO Tools API")

    # Initialize database
    try:
        await db_manager.create_tables()
        logger.info("Database initialized")
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")

    yield

    # Shutdown
    logger.info("Shutting down NEXUS SEO Tools API")
    await db_manager.close()
    await redis_manager.close()


def create_app() -> FastAPI:
    """
    Create and configure FastAPI application.

    Returns:
        FastAPI: Configured application instance
    """
    settings = get_settings()

    app = FastAPI(
        title="NEXUS SEO Tools API",
        description="Production-ready SEO tools API with comprehensive features",
        version="1.0.0",
        lifespan=lifespan,
        docs_url="/docs",
        redoc_url="/redoc",
    )

    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Exception handler
    @app.exception_handler(SEOException)
    async def seo_exception_handler(request, exc: SEOException):
        return JSONResponse(
            status_code=400,
            content={
                "error": exc.message,
                "details": exc.details,
            },
        )

    # Health check
    @app.get("/health")
    async def health_check():
        """Health check endpoint."""
        return {
            "status": "healthy",
            "service": "NEXUS SEO Tools API",
            "version": "1.0.0",
        }

    # Include routers
    app.include_router(keywords.router, prefix="/api/v1/keywords", tags=["Keywords"])
    app.include_router(rankings.router, prefix="/api/v1/rankings", tags=["Rankings"])
    app.include_router(audit.router, prefix="/api/v1/audit", tags=["Site Audit"])
    app.include_router(backlinks.router, prefix="/api/v1/backlinks", tags=["Backlinks"])
    app.include_router(competitors.router, prefix="/api/v1/competitors", tags=["Competitors"])
    app.include_router(content.router, prefix="/api/v1/content", tags=["Content"])
    app.include_router(technical.router, prefix="/api/v1/technical", tags=["Technical SEO"])
    app.include_router(schema.router, prefix="/api/v1/schema", tags=["Schema Markup"])
    app.include_router(sitemap.router, prefix="/api/v1/sitemap", tags=["Sitemap"])
    app.include_router(meta_tags.router, prefix="/api/v1/meta-tags", tags=["Meta Tags"])
    app.include_router(links.router, prefix="/api/v1/links", tags=["Link Building"])
    app.include_router(reports.router, prefix="/api/v1/reports", tags=["Reports"])

    logger.info("FastAPI application created successfully")
    return app


# Create app instance
app = create_app()
