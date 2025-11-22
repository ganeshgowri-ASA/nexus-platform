<<<<<<< HEAD
"""
NEXUS Platform - FastAPI Main Application

Production-ready REST API with:
- Auto-generated OpenAPI documentation
- JWT authentication
- Rate limiting
- CORS middleware
- Request/response logging
- Comprehensive error handling
- API versioning
- WebSocket support preparation
"""

import os
import logging
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.middleware.gzip import GZipMiddleware
from starlette.exceptions import HTTPException as StarletteHTTPException

from api.middleware import setup_cors, RateLimitMiddleware, LoggingMiddleware
from api.routers import (
    auth_router,
    users_router,
    documents_router,
    emails_router,
    chat_router,
    projects_router,
    tasks_router,
    files_router,
    ai_router,
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


# Lifespan context manager for startup and shutdown events
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for startup and shutdown events
    """
    # Startup
    logger.info("Starting NEXUS Platform API...")
    logger.info("API Version: 1.0.0")
    logger.info("Environment: %s", os.getenv("ENVIRONMENT", "development"))

    # TODO: Initialize database connection pool
    # TODO: Initialize Redis connection for caching
    # TODO: Load AI model configurations
    # TODO: Setup background task workers

    yield

    # Shutdown
    logger.info("Shutting down NEXUS Platform API...")

    # TODO: Close database connections
    # TODO: Close Redis connections
    # TODO: Cleanup resources


# Create FastAPI application
app = FastAPI(
    title="NEXUS Platform API",
    description="""
    **NEXUS Platform** - Comprehensive REST API for enterprise productivity platform.

    ## Features

    * **Authentication & Authorization** - JWT-based authentication with role-based access control
    * **User Management** - Complete user CRUD operations with profile management
    * **Document Management** - Create, edit, version, and search documents
    * **Email Integration** - Send, receive, and manage emails
    * **Real-time Chat** - WebSocket-ready chat rooms and messaging
    * **Project Management** - Projects, tasks, team collaboration
    * **File Storage** - Upload, download, and manage files
    * **AI Integration** - AI completions, image generation, embeddings

    ## Authentication

    Most endpoints require authentication. Use the `/api/v1/auth/login` endpoint to obtain an access token.

    Include the token in the `Authorization` header:
    ```
    Authorization: Bearer <your_access_token>
    ```

    ## Rate Limiting

    API requests are rate limited:
    - 60 requests per minute
    - 1000 requests per hour

    Rate limit information is included in response headers.

    ## Pagination

    List endpoints support pagination with query parameters:
    - `page`: Page number (default: 1)
    - `page_size`: Items per page (default: 20, max: 100)

    ## Filtering & Sorting

    Many endpoints support filtering and sorting:
    - `sort_by`: Field name to sort by
    - `sort_order`: `asc` or `desc`
    - Additional filter parameters vary by endpoint

    ## WebSocket Support

    Real-time features are available via WebSocket connections at `/api/v1/chat/ws/{room_id}`.
    """,
    version="1.0.0",
    contact={
        "name": "NEXUS Platform Team",
        "email": "support@nexus-platform.com",
    },
    license_info={
        "name": "Proprietary",
    },
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)


# Add middleware
# Note: Middleware is executed in reverse order of addition

# 1. Logging middleware (first to log everything)
app.add_middleware(LoggingMiddleware)

# 2. Rate limiting middleware
if os.getenv("ENABLE_RATE_LIMITING", "true").lower() == "true":
    app.add_middleware(
        RateLimitMiddleware,
        requests_per_minute=int(os.getenv("RATE_LIMIT_PER_MINUTE", "60")),
        requests_per_hour=int(os.getenv("RATE_LIMIT_PER_HOUR", "1000")),
    )

# 3. CORS middleware
setup_cors(
    app,
    allowed_origins=os.getenv("ALLOWED_ORIGINS", "*").split(","),
)

# 4. GZip compression middleware
app.add_middleware(GZipMiddleware, minimum_size=1000)


# Global exception handlers
@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    """Handle HTTP exceptions"""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.detail,
            "status_code": exc.status_code,
            "path": str(request.url),
        },
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """Handle request validation errors"""
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": "Validation error",
            "detail": exc.errors(),
            "status_code": status.HTTP_422_UNPROCESSABLE_ENTITY,
            "path": str(request.url),
        },
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle unexpected exceptions"""
    logger.error(f"Unexpected error: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "Internal server error",
            "detail": str(exc) if os.getenv("DEBUG", "false").lower() == "true" else "An unexpected error occurred",
            "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
            "path": str(request.url),
        },
    )


# Root endpoint
@app.get("/", tags=["Root"])
async def root() -> dict[str, Any]:
    """
    API root endpoint

    Returns basic API information and available endpoints
    """
    return {
        "name": "NEXUS Platform API",
        "version": "1.0.0",
        "status": "operational",
        "documentation": {
            "swagger": "/docs",
            "redoc": "/redoc",
            "openapi": "/openapi.json",
        },
        "endpoints": {
            "auth": "/api/v1/auth",
            "users": "/api/v1/users",
            "documents": "/api/v1/documents",
            "emails": "/api/v1/emails",
            "chat": "/api/v1/chat",
            "projects": "/api/v1/projects",
            "tasks": "/api/v1/tasks",
            "files": "/api/v1/files",
            "ai": "/api/v1/ai",
        },
    }


# Health check endpoint
@app.get("/health", tags=["Health"])
async def health_check() -> dict[str, Any]:
    """
    Health check endpoint

    Returns API health status and system information
    """
    # TODO: Add actual health checks for:
    # - Database connectivity
    # - Redis connectivity
    # - External service availability
    # - Disk space
    # - Memory usage

    return {
        "status": "healthy",
        "version": "1.0.0",
        "environment": os.getenv("ENVIRONMENT", "development"),
        "checks": {
            "database": "ok",  # TODO: Actual DB check
            "redis": "ok",     # TODO: Actual Redis check
            "storage": "ok",   # TODO: Actual storage check
        },
    }


# API version prefix
API_V1_PREFIX = "/api/v1"

# Include routers with API versioning
app.include_router(auth_router, prefix=API_V1_PREFIX, tags=["Authentication"])
app.include_router(users_router, prefix=API_V1_PREFIX, tags=["Users"])
app.include_router(documents_router, prefix=API_V1_PREFIX, tags=["Documents"])
app.include_router(emails_router, prefix=API_V1_PREFIX, tags=["Emails"])
app.include_router(chat_router, prefix=API_V1_PREFIX, tags=["Chat"])
app.include_router(projects_router, prefix=API_V1_PREFIX, tags=["Projects"])
app.include_router(tasks_router, prefix=API_V1_PREFIX, tags=["Tasks"])
app.include_router(files_router, prefix=API_V1_PREFIX, tags=["Files"])
app.include_router(ai_router, prefix=API_V1_PREFIX, tags=["AI"])


# Development server runner
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "api.main:app",
        host=os.getenv("HOST", "0.0.0.0"),
        port=int(os.getenv("PORT", "8000")),
        reload=os.getenv("RELOAD", "true").lower() == "true",
        log_level=os.getenv("LOG_LEVEL", "info"),
=======
"""Main FastAPI application for NEXUS Platform."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from core.config import settings
from core.logging import setup_logging
from database.connection import engine
from database.models import Base
from modules.batch_processing.routes import router as batch_router

# Setup logging
setup_logging()

# Create FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    description="NEXUS Platform - 24 Integrated Modules for Complete Productivity",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
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
    """Run on application startup."""
    # Create database tables
    Base.metadata.create_all(bind=engine)
    print("🚀 NEXUS Platform started successfully!")
    print(f"📊 API Documentation: http://localhost:8000/docs")
    print(f"🎨 Streamlit UI: http://localhost:8501")
    print(f"🌺 Flower (Celery): http://localhost:5555")


@app.on_event("shutdown")
async def shutdown_event():
    """Run on application shutdown."""
    print("👋 NEXUS Platform shutting down...")


# Health check
@app.get("/")
def root():
    """Root endpoint."""
    return {
        "name": settings.APP_NAME,
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs"
    }


@app.get("/health")
def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "api",
        "version": "1.0.0"
    }


# Include routers
app.include_router(batch_router, prefix="", tags=["Batch Processing"])


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG
>>>>>>> origin/claude/batch-processing-module-01PCraqtfpn2xgwyYUuEev97
    )
