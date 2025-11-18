"""Main FastAPI application for A/B testing module."""

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

from modules.ab_testing.api.experiments import router as experiments_router
from modules.ab_testing.api.metrics import router as metrics_router
from modules.ab_testing.api.variants import router as variants_router
from modules.ab_testing.config import get_settings
from modules.ab_testing.models.base import close_db, init_db


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator:
    """
    Application lifespan manager.

    Handles startup and shutdown events.
    """
    # Startup
    logger.info("Starting A/B Testing API")
    await init_db()
    logger.info("Database initialized")

    yield

    # Shutdown
    logger.info("Shutting down A/B Testing API")
    await close_db()
    logger.info("Database connections closed")


# Create FastAPI app
settings = get_settings()

app = FastAPI(
    title="NEXUS A/B Testing API",
    description="Production-ready A/B testing module for NEXUS platform",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
    lifespan=lifespan,
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(experiments_router, prefix="/api/v1")
app.include_router(variants_router, prefix="/api/v1")
app.include_router(metrics_router, prefix="/api/v1")


@app.get("/health", tags=["Health"])
async def health_check() -> dict:
    """
    Health check endpoint.

    Returns:
        dict: Health status
    """
    return {
        "status": "healthy",
        "service": "ab-testing",
        "version": "1.0.0",
    }


@app.get("/", tags=["Root"])
async def root() -> dict:
    """
    Root endpoint.

    Returns:
        dict: API information
    """
    return {
        "name": "NEXUS A/B Testing API",
        "version": "1.0.0",
        "docs": "/api/docs",
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "modules.ab_testing.api.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.api_reload,
        workers=1 if settings.api_reload else settings.api_workers,
        log_level=settings.log_level.lower(),
    )
