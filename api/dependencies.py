"""
API dependencies for authentication, database sessions, and common utilities
"""

import os
from datetime import datetime, timedelta
from typing import Optional, Generator, Any
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer, HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from api.schemas.user import TokenData

# Configuration
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "7"))

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# OAuth2 scheme
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")
http_bearer = HTTPBearer()


# Database dependency (placeholder - will be connected to actual DB in future sessions)
def get_db() -> Generator[Any, None, None]:
    """
    Get database session

    NOTE: This is a placeholder. Will be connected to actual SQLAlchemy
    database session in a future session when the database layer is integrated.
    """
    # TODO: Implement actual database session management
    # from database.session import SessionLocal
    # db = SessionLocal()
    # try:
    #     yield db
    # finally:
    #     db.close()

    # Placeholder for now
    yield None


# Password utilities
def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against a hash"""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Hash a password"""
    return pwd_context.hash(password)


# JWT token utilities
def create_access_token(
    data: dict,
    expires_delta: Optional[timedelta] = None
) -> str:
    """
    Create a JWT access token

    Args:
        data: Dictionary containing token claims
        expires_delta: Token expiration time delta

    Returns:
        Encoded JWT token
    """
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({
        "exp": expire,
        "iat": datetime.utcnow(),
        "type": "access"
    })

    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def create_refresh_token(data: dict) -> str:
    """
    Create a JWT refresh token

    Args:
        data: Dictionary containing token claims

    Returns:
        Encoded JWT refresh token
    """
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)

    to_encode.update({
        "exp": expire,
        "iat": datetime.utcnow(),
        "type": "refresh"
    })

    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def decode_token(token: str) -> TokenData:
    """
    Decode and validate a JWT token

    Args:
        token: JWT token string

    Returns:
        TokenData object with user information

    Raises:
        HTTPException: If token is invalid or expired
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: int = payload.get("sub")
        username: str = payload.get("username")
        email: str = payload.get("email")

        if user_id is None:
            raise credentials_exception

        token_data = TokenData(
            user_id=user_id,
            username=username,
            email=email
        )
        return token_data

    except JWTError:
        raise credentials_exception


# Authentication dependencies
async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> TokenData:
    """
    Get current authenticated user from JWT token

    Args:
        token: JWT token from Authorization header
        db: Database session

    Returns:
        TokenData with user information

    Raises:
        HTTPException: If authentication fails
    """
    token_data = decode_token(token)

    # TODO: Fetch user from database and verify they exist and are active
    # user = db.query(User).filter(User.id == token_data.user_id).first()
    # if user is None or not user.is_active:
    #     raise HTTPException(
    #         status_code=status.HTTP_401_UNAUTHORIZED,
    #         detail="User not found or inactive"
    #     )

    return token_data


async def get_current_active_user(
    current_user: TokenData = Depends(get_current_user)
) -> TokenData:
    """
    Get current active user

    Args:
        current_user: Current user from get_current_user dependency

    Returns:
        TokenData with user information
    """
    # TODO: Add additional checks when DB is connected
    return current_user


async def get_current_superuser(
    current_user: TokenData = Depends(get_current_user)
) -> TokenData:
    """
    Get current superuser (admin)

    Args:
        current_user: Current user from get_current_user dependency

    Returns:
        TokenData with superuser information

    Raises:
        HTTPException: If user is not a superuser
    """
    # TODO: Check if user is superuser from database
    # if not current_user.is_superuser:
    #     raise HTTPException(
    #         status_code=status.HTTP_403_FORBIDDEN,
    #         detail="Not enough permissions"
    #     )

    return current_user


# Optional authentication (for endpoints that work with or without auth)
async def get_current_user_optional(
    token: Optional[str] = Depends(oauth2_scheme)
) -> Optional[TokenData]:
    """
    Get current user if token is provided, otherwise return None

    Args:
        token: Optional JWT token from Authorization header

    Returns:
        TokenData if authenticated, None otherwise
    """
    if token is None:
        return None

    try:
        return decode_token(token)
    except HTTPException:
        return None


# Pagination dependency
class PaginationParams:
    """Pagination parameters for list endpoints"""

    def __init__(
        self,
        page: int = 1,
        page_size: int = 20,
        max_page_size: int = 100
    ):
        self.page = max(1, page)
        self.page_size = min(max(1, page_size), max_page_size)
        self.skip = (self.page - 1) * self.page_size
        self.limit = self.page_size


def get_pagination_params(
    page: int = 1,
    page_size: int = 20
) -> PaginationParams:
    """
    Get pagination parameters from query string

    Args:
        page: Page number (1-indexed)
        page_size: Number of items per page

    Returns:
        PaginationParams object
    """
    return PaginationParams(page=page, page_size=page_size)


# Sorting and filtering utilities
class SortParams:
    """Sorting parameters for list endpoints"""

    def __init__(
        self,
        sort_by: Optional[str] = None,
        sort_order: str = "asc"
    ):
        self.sort_by = sort_by
        self.sort_order = sort_order.lower() if sort_order.lower() in ["asc", "desc"] else "asc"


def get_sort_params(
    sort_by: Optional[str] = None,
    sort_order: str = "asc"
) -> SortParams:
    """
    Get sorting parameters from query string

    Args:
        sort_by: Field name to sort by
        sort_order: Sort order (asc or desc)

    Returns:
        SortParams object
    """
    return SortParams(sort_by=sort_by, sort_order=sort_order)
