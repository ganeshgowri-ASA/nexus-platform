"""
Authentication router - login, register, token management
"""

from datetime import timedelta
from typing import Any
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from api.dependencies import (
    get_db,
    get_password_hash,
    verify_password,
    create_access_token,
    create_refresh_token,
    decode_token,
    get_current_user,
    ACCESS_TOKEN_EXPIRE_MINUTES,
)
from api.schemas.user import (
    UserCreate,
    UserResponse,
    Token,
    LoginRequest,
    PasswordReset,
)
from api.schemas.common import MessageResponse

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(
    user_data: UserCreate,
    db: Session = Depends(get_db)
) -> Any:
    """
    Register a new user

    - **email**: Valid email address
    - **username**: Unique username (3-50 characters)
    - **password**: Strong password (min 8 characters)
    - **full_name**: Optional full name
    """
    # TODO: Implement actual user creation when DB is connected
    # Check if user exists
    # existing_user = db.query(User).filter(
    #     (User.email == user_data.email) | (User.username == user_data.username)
    # ).first()
    # if existing_user:
    #     raise HTTPException(
    #         status_code=status.HTTP_400_BAD_REQUEST,
    #         detail="Email or username already registered"
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

    # Placeholder response
    from datetime import datetime
    return {
        "id": 1,
        "email": user_data.email,
        "username": user_data.username,
        "full_name": user_data.full_name,
        "is_active": True,
        "is_superuser": False,
        "created_at": datetime.utcnow(),
        "updated_at": None,
    }


@router.post("/login", response_model=Token)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
) -> Any:
    """
    OAuth2 compatible token login

    - **username**: Username or email
    - **password**: User password

    Returns access token for authentication
    """
    # TODO: Implement actual user authentication when DB is connected
    # Authenticate user
    # user = db.query(User).filter(
    #     (User.username == form_data.username) | (User.email == form_data.username)
    # ).first()

    # if not user or not verify_password(form_data.password, user.hashed_password):
    #     raise HTTPException(
    #         status_code=status.HTTP_401_UNAUTHORIZED,
    #         detail="Incorrect username or password",
    #         headers={"WWW-Authenticate": "Bearer"},
    #     )

    # if not user.is_active:
    #     raise HTTPException(
    #         status_code=status.HTTP_403_FORBIDDEN,
    #         detail="Inactive user account"
    #     )

    # Placeholder: Create access token
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={
            "sub": 1,  # user.id
            "username": form_data.username,
            "email": "user@example.com",  # user.email
        },
        expires_delta=access_token_expires
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    }


@router.post("/token", response_model=Token)
async def login_json(
    login_data: LoginRequest,
    db: Session = Depends(get_db)
) -> Any:
    """
    JSON-based login endpoint (alternative to OAuth2 form)

    - **username**: Username or email
    - **password**: User password

    Returns access token for authentication
    """
    # TODO: Implement actual user authentication when DB is connected
    # Similar to /login but accepts JSON instead of form data

    # Placeholder: Create access token
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={
            "sub": 1,
            "username": login_data.username,
            "email": "user@example.com",
        },
        expires_delta=access_token_expires
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    }


@router.post("/refresh", response_model=Token)
async def refresh_token(
    refresh_token: str,
    db: Session = Depends(get_db)
) -> Any:
    """
    Refresh access token using refresh token

    - **refresh_token**: Valid refresh token

    Returns new access token
    """
    # Decode and validate refresh token
    try:
        token_data = decode_token(refresh_token)
    except HTTPException:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
        )

    # TODO: Verify user still exists and is active when DB is connected

    # Create new access token
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={
            "sub": token_data.user_id,
            "username": token_data.username,
            "email": token_data.email,
        },
        expires_delta=access_token_expires
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    }


@router.post("/logout", response_model=MessageResponse)
async def logout(
    current_user = Depends(get_current_user)
) -> Any:
    """
    Logout current user

    Note: With JWT tokens, logout is typically handled client-side by
    removing the token. For production, consider implementing token
    blacklisting or using a token revocation mechanism.
    """
    # TODO: Implement token blacklisting if needed
    return {
        "message": "Successfully logged out",
        "detail": "Token should be removed from client storage",
    }


@router.post("/reset-password", response_model=MessageResponse)
async def reset_password(
    password_data: PasswordReset,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Reset user password

    - **old_password**: Current password
    - **new_password**: New password (min 8 characters)

    Requires authentication
    """
    # TODO: Implement password reset when DB is connected
    # user = db.query(User).filter(User.id == current_user.user_id).first()

    # if not verify_password(password_data.old_password, user.hashed_password):
    #     raise HTTPException(
    #         status_code=status.HTTP_400_BAD_REQUEST,
    #         detail="Incorrect password"
    #     )

    # user.hashed_password = get_password_hash(password_data.new_password)
    # db.commit()

    return {
        "message": "Password reset successfully",
        "detail": "Please login with your new password",
    }


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Get current authenticated user information
    """
    # TODO: Fetch full user data from DB when connected
    # user = db.query(User).filter(User.id == current_user.user_id).first()

    from datetime import datetime
    return {
        "id": current_user.user_id or 1,
        "email": current_user.email or "user@example.com",
        "username": current_user.username or "testuser",
        "full_name": "Test User",
        "is_active": True,
        "is_superuser": False,
        "created_at": datetime.utcnow(),
        "updated_at": None,
    }


@router.post("/verify-token", response_model=MessageResponse)
async def verify_token_endpoint(
    current_user = Depends(get_current_user)
) -> Any:
    """
    Verify if the provided token is valid

    Returns success if token is valid and user is authenticated
    """
    return {
        "message": "Token is valid",
        "data": {
            "user_id": current_user.user_id,
            "username": current_user.username,
        },
    }
