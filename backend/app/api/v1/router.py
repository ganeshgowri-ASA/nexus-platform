"""
Main API router for NEXUS Platform API v1.

This module combines all API endpoint routers.
"""

from fastapi import APIRouter

from app.api.v1.endpoints import auth
from app.modules.campaign_manager import router as campaign_router


api_router = APIRouter()

# Include authentication endpoints
api_router.include_router(auth.router)

# Include campaign manager module
api_router.include_router(campaign_router)


@api_router.get("/health")
def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "NEXUS Platform API"
    }
