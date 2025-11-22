"""
Goals API Routes
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from modules.analytics.api.dependencies import get_db_session
from modules.analytics.models.goal import GoalCreate, GoalQuery
from modules.analytics.storage.repositories import GoalRepository

router = APIRouter()
goal_repo = GoalRepository()


@router.post("/")
def create_goal(goal: GoalCreate, db: Session = Depends(get_db_session)):
    """Create a new goal."""
    return goal_repo.create(db, **goal.model_dump())


@router.get("/{goal_id}")
def get_goal(goal_id: str, db: Session = Depends(get_db_session)):
    """Get goal by ID."""
    goal = goal_repo.get_by_id(db, goal_id)
    if not goal:
        raise HTTPException(status_code=404, detail="Goal not found")
    return goal


@router.get("/")
def list_goals(db: Session = Depends(get_db_session)):
    """List all goals."""
    goals = goal_repo.get_all(db)
    return {"goals": goals}
