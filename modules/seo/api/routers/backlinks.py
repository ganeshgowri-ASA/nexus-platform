"""Backlinks API router."""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from modules.seo.config.database import get_db_session

router = APIRouter()

@router.get("/")
async def list_backlinks(
    target_domain: str = Query(...),
    is_active: bool = Query(True),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    session: AsyncSession = Depends(get_db_session),
):
    """List backlinks for domain."""
    return {"target_domain": target_domain, "backlinks": []}

@router.post("/analyze")
async def analyze_backlinks(
    domain: str,
    session: AsyncSession = Depends(get_db_session),
):
    """Analyze backlink profile."""
    return {"domain": domain, "status": "analysis_started"}

@router.get("/lost")
async def get_lost_backlinks(
    domain: str = Query(...),
    days: int = Query(30, ge=1, le=365),
    session: AsyncSession = Depends(get_db_session),
):
    """Get lost backlinks."""
    return {"domain": domain, "lost_backlinks": []}
