"""Main application entry point.

This module sets up and runs the NEXUS platform FastAPI application
with all modules integrated.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import structlog

from config import settings
from shared.database import init_db
from modules.contracts.api import router as contracts_router

# Configure structured logging
structlog.configure(
    processors=[
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.JSONRenderer()
    ]
)

logger = structlog.get_logger(__name__)

# Create FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="NEXUS: Unified AI-powered productivity platform with integrated modules",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup_event():
    """Application startup event handler."""
    logger.info("Starting NEXUS platform", version=settings.APP_VERSION)

    # Initialize database
    try:
        init_db()
        logger.info("Database initialized")
    except Exception as e:
        logger.error("Failed to initialize database", error=str(e))


@app.on_event("shutdown")
async def shutdown_event():
    """Application shutdown event handler."""
    logger.info("Shutting down NEXUS platform")


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "running",
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}


# Include routers
app.include_router(contracts_router)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower(),
    )
