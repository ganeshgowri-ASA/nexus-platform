<<<<<<< HEAD
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
=======
"""Main API router that aggregates all module routers"""
from fastapi import APIRouter
from app.modules.ocr.router import router as ocr_router
from app.modules.translation.router import router as translation_router

api_router = APIRouter()

# Include module routers
api_router.include_router(ocr_router, prefix="/ocr", tags=["OCR"])
api_router.include_router(translation_router, prefix="/translation", tags=["Translation"])
>>>>>>> origin/claude/ocr-translation-modules-01Kv1eeHRaW9ea224g8V59NS
