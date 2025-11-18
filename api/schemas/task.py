"""
Task-related Pydantic schemas
"""

from datetime import datetime, date
from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict


class TaskBase(BaseModel):
    """Base task schema"""

    title: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=2000)
    status: str = Field(
        default="todo",
        description="Task status: todo, in_progress, review, completed, cancelled",
    )
    priority: str = Field(
        default="medium", description="Task priority: low, medium, high, critical"
    )
    due_date: Optional[date] = None
    estimated_hours: Optional[float] = Field(None, ge=0)
    actual_hours: Optional[float] = Field(None, ge=0)


class TaskCreate(TaskBase):
    """Schema for task creation"""

    project_id: int
    assigned_to_id: Optional[int] = Field(
        None, description="User ID to assign the task to"
    )
    parent_task_id: Optional[int] = Field(
        None, description="Parent task ID for subtasks"
    )
    tags: List[str] = Field(default_factory=list)


class TaskUpdate(BaseModel):
    """Schema for task update"""

    title: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=2000)
    status: Optional[str] = None
    priority: Optional[str] = None
    due_date: Optional[date] = None
    estimated_hours: Optional[float] = Field(None, ge=0)
    actual_hours: Optional[float] = Field(None, ge=0)
    assigned_to_id: Optional[int] = None
    tags: Optional[List[str]] = None


class TaskResponse(BaseModel):
    """Schema for task response"""

    id: int
    title: str
    description: Optional[str]
    status: str
    priority: str
    due_date: Optional[date]
    estimated_hours: Optional[float]
    actual_hours: Optional[float]
    project_id: int
    project_name: str
    created_by_id: int
    assigned_to_id: Optional[int]
    assigned_to_username: Optional[str]
    parent_task_id: Optional[int]
    subtask_count: int = 0
    is_overdue: bool = False
    tags: List[str]
    created_at: datetime
    updated_at: Optional[datetime]
    completed_at: Optional[datetime]

    model_config = ConfigDict(from_attributes=True)


class TaskFilter(BaseModel):
    """Schema for filtering tasks"""

    project_id: Optional[int] = None
    status: Optional[str] = None
    priority: Optional[str] = None
    assigned_to_id: Optional[int] = None
    created_by_id: Optional[int] = None
    is_overdue: Optional[bool] = None
    tags: Optional[List[str]] = None


class TaskComment(BaseModel):
    """Schema for task comments"""

    id: int
    task_id: int
    user_id: int
    username: str
    content: str
    created_at: datetime
    updated_at: Optional[datetime]

    model_config = ConfigDict(from_attributes=True)
