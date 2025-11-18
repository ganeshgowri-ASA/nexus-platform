"""Main API router that aggregates all module routers"""
from fastapi import APIRouter
from app.modules.ocr.router import router as ocr_router
from app.modules.translation.router import router as translation_router

api_router = APIRouter()

# Include module routers
api_router.include_router(ocr_router, prefix="/ocr", tags=["OCR"])
api_router.include_router(translation_router, prefix="/translation", tags=["Translation"])
