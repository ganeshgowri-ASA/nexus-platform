"""
NEXUS Platform - API Router Aggregation
"""
from fastapi import APIRouter

from backend.app.api.v1.endpoints import attribution


# Create main API router
api_router = APIRouter()

# Include module routers
api_router.include_router(
    attribution.router,
    prefix="/attribution",
    tags=["Attribution"]
)
