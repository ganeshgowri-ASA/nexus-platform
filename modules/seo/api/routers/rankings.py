"""Rankings API router."""

from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from modules.seo.config.database import get_db_session

router = APIRouter()


class RankingResponse(BaseModel):
    """Ranking response."""
    id: int
    keyword_id: int
    domain: str
    position: Optional[int]
    previous_position: Optional[int]
    position_change: Optional[int]
    search_engine: str = "google"
    device: str = "desktop"


@router.get("/", response_model=List[RankingResponse])
async def list_rankings(
    domain: str = Query(...),
    search_engine: str = Query("google"),
    device: str = Query("desktop"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    session: AsyncSession = Depends(get_db_session),
):
    """List current rankings for domain."""
    return []


@router.post("/track")
async def track_ranking(
    keyword_id: int,
    domain: str,
    search_engine: str = "google",
    device: str = "desktop",
    location: Optional[str] = None,
    session: AsyncSession = Depends(get_db_session),
):
    """Track keyword ranking."""
    return {"status": "tracking_started", "keyword_id": keyword_id}


@router.get("/{ranking_id}/history")
async def get_ranking_history(
    ranking_id: int,
    days: int = Query(30, ge=1, le=365),
    session: AsyncSession = Depends(get_db_session),
):
    """Get ranking history."""
    return {"ranking_id": ranking_id, "history": []}
