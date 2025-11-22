"""
<<<<<<< HEAD
NEXUS Platform - Main FastAPI Application
"""
=======
NEXUS Platform - Main FastAPI Application.

This is the entry point for the NEXUS Platform backend API.
"""

>>>>>>> origin/claude/build-campaign-manager-01KFpVYVNSuz2bfrpAMAZpwp
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
<<<<<<< HEAD
from sqlalchemy.exc import SQLAlchemyError

from backend.app.core.config import settings
from backend.app.core.exceptions import NEXUSException
from backend.app.api.v1.api import api_router
=======
import logging

from app.config import settings
from app.database import engine, Base
from app.api.v1.router import api_router
from app.core.exceptions import NexusException

# Configure logging
logging.basicConfig(
    level=settings.LOG_LEVEL,
    format=settings.LOG_FORMAT
)
logger = logging.getLogger(__name__)
>>>>>>> origin/claude/build-campaign-manager-01KFpVYVNSuz2bfrpAMAZpwp


# Create FastAPI application
app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
<<<<<<< HEAD
    description="NEXUS - Unified AI-powered productivity platform",
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url=f"{settings.API_V1_STR}/docs",
    redoc_url=f"{settings.API_V1_STR}/redoc",
)

# Configure CORS
=======
    description=settings.DESCRIPTION,
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
)


# CORS Configuration
>>>>>>> origin/claude/build-campaign-manager-01KFpVYVNSuz2bfrpAMAZpwp
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


<<<<<<< HEAD
# Exception handlers
@app.exception_handler(NEXUSException)
async def nexus_exception_handler(request: Request, exc: NEXUSException):
=======
# Exception Handlers
@app.exception_handler(NexusException)
async def nexus_exception_handler(request: Request, exc: NexusException):
>>>>>>> origin/claude/build-campaign-manager-01KFpVYVNSuz2bfrpAMAZpwp
    """Handle custom NEXUS exceptions."""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.message,
            "details": exc.details,
<<<<<<< HEAD
            "path": str(request.url),
        },
=======
        }
>>>>>>> origin/claude/build-campaign-manager-01KFpVYVNSuz2bfrpAMAZpwp
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle request validation errors."""
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": "Validation error",
            "details": exc.errors(),
<<<<<<< HEAD
            "path": str(request.url),
        },
    )


@app.exception_handler(SQLAlchemyError)
async def sqlalchemy_exception_handler(request: Request, exc: SQLAlchemyError):
    """Handle SQLAlchemy database errors."""
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "Database error",
            "details": {"message": str(exc)},
            "path": str(request.url),
        },
    )


# Health check endpoint
@app.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "environment": settings.ENVIRONMENT,
    }
=======
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle uncaught exceptions."""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "Internal server error",
            "details": str(exc) if settings.DEBUG else "An unexpected error occurred",
        }
    )


# Startup and Shutdown Events
@app.on_event("startup")
async def startup_event():
    """Initialize application on startup."""
    logger.info("Starting NEXUS Platform API...")

    # Create database tables (in production, use Alembic migrations)
    if settings.DEBUG:
        logger.info("Creating database tables...")
        Base.metadata.create_all(bind=engine)

    logger.info("NEXUS Platform API started successfully")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on application shutdown."""
    logger.info("Shutting down NEXUS Platform API...")
>>>>>>> origin/claude/build-campaign-manager-01KFpVYVNSuz2bfrpAMAZpwp


# Include API routers
app.include_router(api_router, prefix=settings.API_V1_STR)


<<<<<<< HEAD
# Startup event
@app.on_event("startup")
async def startup_event():
    """Execute on application startup."""
    print(f"Starting {settings.PROJECT_NAME} v{settings.VERSION}")
    print(f"Environment: {settings.ENVIRONMENT}")
    print(f"Debug mode: {settings.DEBUG}")
    print(f"API docs: http://localhost:8000{settings.API_V1_STR}/docs")


# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    """Execute on application shutdown."""
    print(f"Shutting down {settings.PROJECT_NAME}")
=======
# Root endpoint
@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "name": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "description": settings.DESCRIPTION,
        "docs_url": "/api/docs",
        "status": "running"
    }


# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint for monitoring."""
    return {
        "status": "healthy",
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION
    }
>>>>>>> origin/claude/build-campaign-manager-01KFpVYVNSuz2bfrpAMAZpwp


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
<<<<<<< HEAD
        "backend.app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
        log_level="debug" if settings.DEBUG else "info",
=======
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower()
>>>>>>> origin/claude/build-campaign-manager-01KFpVYVNSuz2bfrpAMAZpwp
    )
