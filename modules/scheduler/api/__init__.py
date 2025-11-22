"""API routes for scheduler"""
from fastapi import APIRouter
from .jobs import router as jobs_router
from .cron import router as cron_router

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(jobs_router)
api_router.include_router(cron_router)

__all__ = ["api_router"]
