"""
Sessions API Routes
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from modules.analytics.api.dependencies import get_db_session
from modules.analytics.models.session import SessionCreate, SessionQuery, Session as SessionModel
from modules.analytics.storage.repositories import SessionRepository

router = APIRouter()
session_repo = SessionRepository()


@router.post("/")
def create_session(session_data: SessionCreate, db: Session = Depends(get_db_session)):
    """Create a new session."""
    return session_repo.create(db, **session_data.model_dump())


@router.get("/{session_id}", response_model=SessionModel)
def get_session(session_id: str, db: Session = Depends(get_db_session)):
    """Get session by ID."""
    session_obj = session_repo.get_by_id(db, session_id)
    if not session_obj:
        raise HTTPException(status_code=404, detail="Session not found")
    return session_obj


@router.post("/query")
def query_sessions(query: SessionQuery, db: Session = Depends(get_db_session)):
    """Query sessions."""
    sessions = session_repo.get_all(db, skip=(query.page - 1) * query.page_size, limit=query.page_size)
    return {"sessions": sessions}
