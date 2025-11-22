"""
Project-related Pydantic schemas
"""

from datetime import datetime, date
from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict


class ProjectBase(BaseModel):
    """Base project schema"""

    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    status: str = Field(
        default="planning",
        description="Project status: planning, active, on_hold, completed, cancelled",
    )
    priority: str = Field(
        default="medium", description="Project priority: low, medium, high, critical"
    )
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    budget: Optional[float] = Field(None, ge=0)


class ProjectCreate(ProjectBase):
    """Schema for project creation"""

    team_member_ids: List[int] = Field(
        default_factory=list, description="Initial team member user IDs"
    )


class ProjectUpdate(BaseModel):
    """Schema for project update"""

    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    status: Optional[str] = None
    priority: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    budget: Optional[float] = Field(None, ge=0)


class ProjectResponse(BaseModel):
    """Schema for project response"""

    id: int
    name: str
    description: Optional[str]
    status: str
    priority: str
    start_date: Optional[date]
    end_date: Optional[date]
    budget: Optional[float]
    owner_id: int
    team_member_count: int
    task_count: int
    completed_task_count: int
    progress_percentage: float = Field(
        default=0.0, ge=0, le=100, description="Project completion percentage"
    )
    created_at: datetime
    updated_at: Optional[datetime]

    model_config = ConfigDict(from_attributes=True)


class ProjectMember(BaseModel):
    """Schema for project team member"""

    user_id: int
    username: str
    role: str = Field(
        default="member", description="Member role: owner, manager, member, viewer"
    )
    joined_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ProjectStats(BaseModel):
    """Schema for project statistics"""

    total_tasks: int
    completed_tasks: int
    in_progress_tasks: int
    overdue_tasks: int
    team_size: int
    budget_spent: Optional[float] = None
    days_remaining: Optional[int] = None
