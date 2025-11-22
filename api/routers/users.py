"""
Users router - CRUD operations for user management
"""

from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from api.dependencies import (
    get_db,
    get_current_user,
    get_current_superuser,
    get_pagination_params,
    get_sort_params,
    get_password_hash,
    PaginationParams,
    SortParams,
)
from api.schemas.user import UserCreate, UserUpdate, UserResponse
from api.schemas.common import PaginatedResponse, MessageResponse

router = APIRouter(prefix="/users", tags=["Users"])


@router.get("", response_model=PaginatedResponse[UserResponse])
async def list_users(
    pagination: PaginationParams = Depends(get_pagination_params),
    sort: SortParams = Depends(get_sort_params),
    search: str = Query(None, description="Search by username or email"),
    is_active: bool = Query(None, description="Filter by active status"),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),
) -> Any:
    """
    List all users with pagination, filtering, and sorting

    - **page**: Page number (default: 1)
    - **page_size**: Items per page (default: 20, max: 100)
    - **sort_by**: Field to sort by (e.g., username, created_at)
    - **sort_order**: Sort order (asc or desc)
    - **search**: Search term for username or email
    - **is_active**: Filter by active status
    """
    # TODO: Implement actual database query when DB is connected
    # query = db.query(User)

    # Apply filters
    # if search:
    #     query = query.filter(
    #         (User.username.ilike(f"%{search}%")) | (User.email.ilike(f"%{search}%"))
    #     )
    # if is_active is not None:
    #     query = query.filter(User.is_active == is_active)

    # Get total count
    # total = query.count()

    # Apply sorting
    # if sort.sort_by:
    #     order_column = getattr(User, sort.sort_by, User.created_at)
    #     if sort.sort_order == "desc":
    #         query = query.order_by(order_column.desc())
    #     else:
    #         query = query.order_by(order_column.asc())

    # Apply pagination
    # users = query.offset(pagination.skip).limit(pagination.limit).all()

    # Placeholder data
    from datetime import datetime
    users = [
        {
            "id": i,
            "email": f"user{i}@example.com",
            "username": f"user{i}",
            "full_name": f"User {i}",
            "is_active": True,
            "is_superuser": False,
            "created_at": datetime.utcnow(),
            "updated_at": None,
        }
        for i in range(1, min(pagination.page_size + 1, 6))
    ]

    total = 5
    total_pages = (total + pagination.page_size - 1) // pagination.page_size

    return {
        "items": users,
        "total": total,
        "page": pagination.page,
        "page_size": pagination.page_size,
        "total_pages": total_pages,
    }


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),
) -> Any:
    """
    Get user by ID

    - **user_id**: User ID to retrieve
    """
    # TODO: Implement actual database query when DB is connected
    # user = db.query(User).filter(User.id == user_id).first()
    # if not user:
    #     raise HTTPException(
    #         status_code=status.HTTP_404_NOT_FOUND,
    #         detail="User not found"
    #     )

    from datetime import datetime
    return {
        "id": user_id,
        "email": f"user{user_id}@example.com",
        "username": f"user{user_id}",
        "full_name": f"User {user_id}",
        "is_active": True,
        "is_superuser": False,
        "created_at": datetime.utcnow(),
        "updated_at": None,
    }


@router.post("", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    user_data: UserCreate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_superuser),
) -> Any:
    """
    Create a new user (Admin only)

    - **email**: Valid email address
    - **username**: Unique username
    - **password**: User password
    - **full_name**: Optional full name

    Requires superuser permissions
    """
    # TODO: Implement actual user creation when DB is connected
    # Check if user exists
    # existing = db.query(User).filter(
    #     (User.email == user_data.email) | (User.username == user_data.username)
    # ).first()
    # if existing:
    #     raise HTTPException(
    #         status_code=status.HTTP_400_BAD_REQUEST,
    #         detail="Email or username already exists"
    #     )

    # Hash password
    hashed_password = get_password_hash(user_data.password)

    # Create user
    # db_user = User(
    #     email=user_data.email,
    #     username=user_data.username,
    #     hashed_password=hashed_password,
    #     full_name=user_data.full_name,
    # )
    # db.add(db_user)
    # db.commit()
    # db.refresh(db_user)

    from datetime import datetime
    return {
        "id": 99,
        "email": user_data.email,
        "username": user_data.username,
        "full_name": user_data.full_name,
        "is_active": True,
        "is_superuser": False,
        "created_at": datetime.utcnow(),
        "updated_at": None,
    }


@router.put("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: int,
    user_data: UserUpdate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),
) -> Any:
    """
    Update user information

    - **user_id**: User ID to update
    - **email**: New email (optional)
    - **username**: New username (optional)
    - **full_name**: New full name (optional)
    - **password**: New password (optional)
    - **is_active**: Active status (optional)

    Users can update their own profile, admins can update any user
    """
    # TODO: Implement actual user update when DB is connected
    # user = db.query(User).filter(User.id == user_id).first()
    # if not user:
    #     raise HTTPException(
    #         status_code=status.HTTP_404_NOT_FOUND,
    #         detail="User not found"
    #     )

    # Check permissions
    # if current_user.user_id != user_id and not current_user.is_superuser:
    #     raise HTTPException(
    #         status_code=status.HTTP_403_FORBIDDEN,
    #         detail="Not enough permissions"
    #     )

    # Update fields
    # if user_data.email:
    #     user.email = user_data.email
    # if user_data.username:
    #     user.username = user_data.username
    # if user_data.full_name is not None:
    #     user.full_name = user_data.full_name
    # if user_data.password:
    #     user.hashed_password = get_password_hash(user_data.password)
    # if user_data.is_active is not None:
    #     user.is_active = user_data.is_active

    # db.commit()
    # db.refresh(user)

    from datetime import datetime
    return {
        "id": user_id,
        "email": user_data.email or f"user{user_id}@example.com",
        "username": user_data.username or f"user{user_id}",
        "full_name": user_data.full_name or f"User {user_id}",
        "is_active": user_data.is_active if user_data.is_active is not None else True,
        "is_superuser": False,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
    }


@router.delete("/{user_id}", response_model=MessageResponse)
async def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_superuser),
) -> Any:
    """
    Delete a user (Admin only)

    - **user_id**: User ID to delete

    Requires superuser permissions
    """
    # TODO: Implement actual user deletion when DB is connected
    # user = db.query(User).filter(User.id == user_id).first()
    # if not user:
    #     raise HTTPException(
    #         status_code=status.HTTP_404_NOT_FOUND,
    #         detail="User not found"
    #     )

    # Prevent self-deletion
    # if user.id == current_user.user_id:
    #     raise HTTPException(
    #         status_code=status.HTTP_400_BAD_REQUEST,
    #         detail="Cannot delete your own account"
    #     )

    # db.delete(user)
    # db.commit()

    return {
        "message": "User deleted successfully",
        "detail": f"User with ID {user_id} has been removed",
    }


@router.post("/{user_id}/activate", response_model=UserResponse)
async def activate_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_superuser),
) -> Any:
    """
    Activate a user account (Admin only)

    - **user_id**: User ID to activate

    Requires superuser permissions
    """
    # TODO: Implement when DB is connected
    # user = db.query(User).filter(User.id == user_id).first()
    # if not user:
    #     raise HTTPException(status_code=404, detail="User not found")
    # user.is_active = True
    # db.commit()
    # db.refresh(user)

    from datetime import datetime
    return {
        "id": user_id,
        "email": f"user{user_id}@example.com",
        "username": f"user{user_id}",
        "full_name": f"User {user_id}",
        "is_active": True,
        "is_superuser": False,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
    }


@router.post("/{user_id}/deactivate", response_model=UserResponse)
async def deactivate_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_superuser),
) -> Any:
    """
    Deactivate a user account (Admin only)

    - **user_id**: User ID to deactivate

    Requires superuser permissions
    """
    # TODO: Implement when DB is connected
    # user = db.query(User).filter(User.id == user_id).first()
    # if not user:
    #     raise HTTPException(status_code=404, detail="User not found")
    # user.is_active = False
    # db.commit()
    # db.refresh(user)

    from datetime import datetime
    return {
        "id": user_id,
        "email": f"user{user_id}@example.com",
        "username": f"user{user_id}",
        "full_name": f"User {user_id}",
        "is_active": False,
        "is_superuser": False,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
    }
