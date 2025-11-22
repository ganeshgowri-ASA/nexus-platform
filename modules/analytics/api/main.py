"""
FastAPI Application

Main FastAPI application for analytics API.
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from modules.analytics.api.middleware import AnalyticsMiddleware, RateLimitMiddleware
from modules.analytics.api.routes import (
    ab_tests,
    cohorts,
    dashboards,
    events,
    exports,
    funnels,
    goals,
    metrics,
    sessions,
    users,
)
from modules.analytics.storage.cache import CacheConfig, init_cache
from modules.analytics.storage.database import DatabaseConfig, init_database

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup
    logger.info("Starting analytics API...")

    # Initialize database
    db_config = DatabaseConfig(
        database_url="postgresql://localhost/nexus_analytics"
    )
    db = init_database(db_config)

    # Initialize cache
    cache_config = CacheConfig(host="localhost")
    cache = init_cache(cache_config)

    # Health checks
    if not db.health_check():
        logger.error("Database health check failed")
    if not cache.health_check():
        logger.error("Cache health check failed")

    logger.info("Analytics API started successfully")

    yield

    # Shutdown
    logger.info("Shutting down analytics API...")
    db.dispose()
    cache.close()
    logger.info("Analytics API shutdown complete")


def create_app() -> FastAPI:
    """
    Create and configure FastAPI application.

    Returns:
        FastAPI application
    """
    app = FastAPI(
        title="NEXUS Analytics API",
        description="Advanced analytics and insights API",
        version="1.0.0",
        lifespan=lifespan,
    )

    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Configure appropriately for production
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Custom middleware
    app.add_middleware(AnalyticsMiddleware)
    app.add_middleware(RateLimitMiddleware)

    # Include routers
    app.include_router(events.router, prefix="/api/v1/events", tags=["Events"])
    app.include_router(metrics.router, prefix="/api/v1/metrics", tags=["Metrics"])
    app.include_router(sessions.router, prefix="/api/v1/sessions", tags=["Sessions"])
    app.include_router(users.router, prefix="/api/v1/users", tags=["Users"])
    app.include_router(funnels.router, prefix="/api/v1/funnels", tags=["Funnels"])
    app.include_router(cohorts.router, prefix="/api/v1/cohorts", tags=["Cohorts"])
    app.include_router(goals.router, prefix="/api/v1/goals", tags=["Goals"])
    app.include_router(ab_tests.router, prefix="/api/v1/ab-tests", tags=["A/B Tests"])
    app.include_router(dashboards.router, prefix="/api/v1/dashboards", tags=["Dashboards"])
    app.include_router(exports.router, prefix="/api/v1/exports", tags=["Exports"])

    # Health check endpoint
    @app.get("/health")
    async def health_check():
        """Health check endpoint."""
        return {"status": "healthy", "service": "analytics"}

    # Root endpoint
    @app.get("/")
    async def root():
        """Root endpoint."""
        return {
            "service": "NEXUS Analytics API",
            "version": "1.0.0",
            "status": "running"
        }

    # Exception handlers
    @app.exception_handler(Exception)
    async def global_exception_handler(request, exc):
        """Global exception handler."""
        logger.error(f"Unhandled exception: {exc}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={"detail": "Internal server error"}
        )

    logger.info("FastAPI application created")
    return app


# Create app instance
app = create_app()
