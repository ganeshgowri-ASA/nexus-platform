"""${router^} API router."""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from modules.seo.config.database import get_db_session

router = APIRouter()

@router.get("/")
async def list_items(session: AsyncSession = Depends(get_db_session)):
    """List items."""
    return {"items": []}

@router.post("/")
async def create_item(session: AsyncSession = Depends(get_db_session)):
    """Create item."""
    return {"id": 1}
