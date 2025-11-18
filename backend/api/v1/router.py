"""
API v1 Router configuration.

This module aggregates all v1 API endpoints.
"""

from fastapi import APIRouter

from backend.api.v1 import documents

api_router = APIRouter()

# Include all routers
api_router.include_router(
    documents.router,
    prefix="/documents",
    tags=["documents"],
)

# Health check endpoint
@api_router.get("/health", tags=["health"])
async def health_check() -> dict:
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "NEXUS Platform API",
        "version": "1.0.0",
    }
