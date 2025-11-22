"""
<<<<<<< HEAD
NEXUS Platform - Backend API
Main FastAPI application
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from backend.database import init_db
from backend.routers import notifications

# Create FastAPI app
app = FastAPI(
    title="NEXUS Platform API",
    description="Multi-channel notification system with email, SMS, push, and in-app notifications",
    version="1.0.0",
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
app.include_router(notifications.router)


@app.on_event("startup")
async def startup_event():
    """Initialize database on startup"""
    init_db()
    print("✓ Database initialized")
    print("✓ NEXUS Platform API started")


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "NEXUS Platform API",
        "version": "1.0.0",
        "status": "running",
        "features": [
            "Multi-channel notifications (email, SMS, push, in-app)",
            "Notification templates",
            "Scheduling",
            "Delivery tracking",
            "User preferences",
            "Unsubscribe management",
            "Firebase Cloud Messaging ready"
        ]
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}


if __name__ == "__main__":
=======
NEXUS Platform FastAPI Application.

This is the main entry point for the FastAPI backend server.
"""

import time
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from backend.api.v1.router import api_router
from backend.core.config import get_settings
from backend.core.exceptions import NEXUSException
from backend.core.logging import get_logger, setup_logging
from backend.database import create_tables, engine

# Setup logging first
setup_logging()

settings = get_settings()
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator:
    """
    Lifespan context manager for startup and shutdown events.

    Args:
        app: FastAPI application instance

    Yields:
        None
    """
    # Startup
    logger.info("application_starting", app_name=settings.APP_NAME)

    # Create database tables
    try:
        create_tables()
        logger.info("database_tables_created")
    except Exception as e:
        logger.error("database_initialization_failed", error=str(e))

    # Additional startup tasks
    logger.info("application_started", version=settings.APP_VERSION)

    yield

    # Shutdown
    logger.info("application_shutting_down")

    # Close database connections
    engine.dispose()
    logger.info("database_connections_closed")

    logger.info("application_shutdown_complete")


# Create FastAPI application
app = FastAPI(
    title=settings.APP_NAME,
    description="Unified AI-powered productivity platform with document management",
    version=settings.APP_VERSION,
    openapi_url=f"{settings.API_V1_PREFIX}/openapi.json" if not settings.is_production else None,
    docs_url=f"{settings.API_V1_PREFIX}/docs" if settings.DEBUG else None,
    redoc_url=f"{settings.API_V1_PREFIX}/redoc" if settings.DEBUG else None,
    lifespan=lifespan,
)


# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Total-Count", "X-Page", "X-Per-Page"],
)


# Gzip Compression Middleware
app.add_middleware(GZipMiddleware, minimum_size=1000)


# Request Logging Middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """
    Log all HTTP requests with timing information.

    Args:
        request: HTTP request
        call_next: Next middleware in chain

    Returns:
        Response: HTTP response
    """
    start_time = time.time()
    request_id = request.headers.get("X-Request-ID", "unknown")

    logger.info(
        "request_started",
        method=request.method,
        url=str(request.url),
        client=request.client.host if request.client else None,
        request_id=request_id,
    )

    try:
        response = await call_next(request)

        process_time = time.time() - start_time

        logger.info(
            "request_completed",
            method=request.method,
            url=str(request.url),
            status_code=response.status_code,
            duration_ms=round(process_time * 1000, 2),
            request_id=request_id,
        )

        response.headers["X-Process-Time"] = str(process_time)
        response.headers["X-Request-ID"] = request_id

        return response

    except Exception as e:
        process_time = time.time() - start_time

        logger.error(
            "request_failed",
            method=request.method,
            url=str(request.url),
            error=str(e),
            duration_ms=round(process_time * 1000, 2),
            request_id=request_id,
        )
        raise


# Exception Handlers


@app.exception_handler(NEXUSException)
async def nexus_exception_handler(request: Request, exc: NEXUSException):
    """
    Handle custom NEXUS exceptions.

    Args:
        request: HTTP request
        exc: NEXUS exception

    Returns:
        JSONResponse: Error response
    """
    logger.warning(
        "nexus_exception",
        exception_type=exc.__class__.__name__,
        message=exc.message,
        status_code=exc.status_code,
        url=str(request.url),
    )

    return JSONResponse(
        status_code=exc.status_code,
        content=exc.to_dict(),
    )


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    """
    Handle HTTP exceptions.

    Args:
        request: HTTP request
        exc: HTTP exception

    Returns:
        JSONResponse: Error response
    """
    logger.warning(
        "http_exception",
        status_code=exc.status_code,
        detail=exc.detail,
        url=str(request.url),
    )

    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": "HTTPException",
            "message": exc.detail,
            "status_code": exc.status_code,
        },
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """
    Handle request validation errors.

    Args:
        request: HTTP request
        exc: Validation error

    Returns:
        JSONResponse: Error response
    """
    logger.warning(
        "validation_error",
        errors=exc.errors(),
        url=str(request.url),
    )

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": "ValidationError",
            "message": "Request validation failed",
            "status_code": status.HTTP_422_UNPROCESSABLE_ENTITY,
            "details": exc.errors(),
        },
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """
    Handle unexpected exceptions.

    Args:
        request: HTTP request
        exc: Exception

    Returns:
        JSONResponse: Error response
    """
    logger.error(
        "unexpected_exception",
        exception_type=exc.__class__.__name__,
        error=str(exc),
        url=str(request.url),
        exc_info=True,
    )

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "InternalServerError",
            "message": "An unexpected error occurred",
            "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
        },
    )


# Include API routers
app.include_router(api_router, prefix=settings.API_V1_PREFIX)


# Root endpoint
@app.get("/", tags=["root"])
async def root():
    """Root endpoint with API information."""
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "running",
        "docs_url": f"{settings.API_V1_PREFIX}/docs" if settings.DEBUG else None,
        "api_version": "v1",
    }


# Health check endpoint
@app.get("/health", tags=["health"])
async def health():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT,
    }


if __name__ == "__main__":
    import uvicorn

>>>>>>> origin/claude/build-dms-module-01NEqPB75CF7J7XEDr4aawai
    uvicorn.run(
        "backend.main:app",
        host="0.0.0.0",
        port=8000,
<<<<<<< HEAD
        reload=True
=======
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower(),
>>>>>>> origin/claude/build-dms-module-01NEqPB75CF7J7XEDr4aawai
    )
