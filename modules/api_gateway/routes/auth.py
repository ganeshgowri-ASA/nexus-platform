from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from datetime import datetime, timedelta
import jwt

from modules.api_gateway.config import settings

router = APIRouter(prefix="/auth", tags=["Authentication"])


class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


@router.post("/login", response_model=TokenResponse)
def login(credentials: LoginRequest):
    """
    Login and get JWT tokens.

    This is a simplified implementation. In production, you should:
    - Validate against a user database
    - Hash and compare passwords securely (bcrypt)
    - Implement proper user management
    """

    # Simple validation (replace with real auth in production)
    if credentials.username == settings.ADMIN_USERNAME and credentials.password == settings.ADMIN_PASSWORD:
        user_id = "admin"
        scopes = ["admin"]
    else:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password"
        )

    # Generate access token
    access_token_expires = timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_jwt_token(
        data={"sub": user_id, "scopes": scopes},
        expires_delta=access_token_expires
    )

    # Generate refresh token
    refresh_token_expires = timedelta(days=settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS)
    refresh_token = create_jwt_token(
        data={"sub": user_id, "type": "refresh"},
        expires_delta=refresh_token_expires
    )

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "expires_in": int(access_token_expires.total_seconds())
    }


@router.post("/refresh", response_model=TokenResponse)
def refresh_token(refresh_token: str):
    """Refresh access token using refresh token"""

    try:
        # Decode refresh token
        payload = jwt.decode(
            refresh_token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM]
        )

        if payload.get("type") != "refresh":
            raise HTTPException(status_code=400, detail="Invalid token type")

        user_id = payload.get("sub")

        # Generate new access token
        access_token_expires = timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_jwt_token(
            data={"sub": user_id},
            expires_delta=access_token_expires
        )

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,  # Keep same refresh token
            "token_type": "bearer",
            "expires_in": int(access_token_expires.total_seconds())
        }

    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Refresh token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid refresh token")


def create_jwt_token(data: dict, expires_delta: timedelta) -> str:
    """Create a JWT token"""

    to_encode = data.copy()
    expire = datetime.utcnow() + expires_delta
    to_encode.update({"exp": expire})

    encoded_jwt = jwt.encode(
        to_encode,
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM
    )

    return encoded_jwt
