"""
Users API Routes
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from modules.analytics.api.dependencies import get_db_session
from modules.analytics.models.user import UserCreate, UserQuery, User
from modules.analytics.storage.repositories import UserRepository

router = APIRouter()
user_repo = UserRepository()


@router.post("/")
def create_user(user: UserCreate, db: Session = Depends(get_db_session)):
    """Create a new user."""
    return user_repo.create(db, **user.model_dump())


@router.get("/{user_id}", response_model=User)
def get_user(user_id: str, db: Session = Depends(get_db_session)):
    """Get user by ID."""
    user = user_repo.get_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.post("/query")
def query_users(query: UserQuery, db: Session = Depends(get_db_session)):
    """Query users."""
    users = user_repo.get_all(db, skip=(query.page - 1) * query.page_size, limit=query.page_size)
    return {"users": users}
