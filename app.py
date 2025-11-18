"""
FastAPI application for NEXUS Platform.

This is the main entry point for the marketing automation API.
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from config.settings import settings
from config.logging_config import get_logger, configure_logging
from src.core.database import init_db, close_db
from src.api.v1.marketing import campaigns, contacts, automations
from src.schemas.common import HealthCheckResponse

# Configure logging
configure_logging()
logger = get_logger(__name__)

# Create FastAPI app
app = FastAPI(
    title="NEXUS Marketing Automation API",
    description="Production-ready marketing automation platform with AI-powered features",
    version="0.1.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup_event():
    """Initialize application on startup."""
    logger.info("Starting NEXUS Platform API", environment=settings.environment)

    # Initialize database (in production, use Alembic migrations)
    # init_db()


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown."""
    logger.info("Shutting down NEXUS Platform API")
    await close_db()


@app.get("/", tags=["root"])
async def root():
    """Root endpoint."""
    return {
        "message": "NEXUS Marketing Automation API",
        "version": "0.1.0",
        "docs": "/api/docs"
    }


@app.get("/health", response_model=HealthCheckResponse, tags=["health"])
async def health_check():
    """Health check endpoint."""
    from datetime import datetime
    from src.core.database import DatabaseHealthCheck

    db_status = "healthy" if await DatabaseHealthCheck.check() else "unhealthy"

    return HealthCheckResponse(
        status="healthy" if db_status == "healthy" else "degraded",
        version="0.1.0",
        timestamp=datetime.utcnow().isoformat(),
        database=db_status,
        redis="not_configured",  # Add Redis health check in production
    )


# Include routers
app.include_router(
    campaigns.router,
    prefix="/api/v1/marketing",
)

app.include_router(
    contacts.router,
    prefix="/api/v1/marketing",
)

app.include_router(
    automations.router,
    prefix="/api/v1/marketing",
)


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Handle uncaught exceptions."""
    logger.error("Unhandled exception", error=str(exc), path=request.url.path)

    return JSONResponse(
        status_code=500,
        content={
            "error": "internal_server_error",
            "message": "An unexpected error occurred",
            "details": str(exc) if settings.debug else None,
        }
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug,
        log_level=settings.log_level.lower(),
    )
