"""FastAPI logging example for NEXUS platform.

This example demonstrates:
- Request logging middleware
- Error tracking in API endpoints
- Structured logging in FastAPI
"""

from pathlib import Path

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from nexus.logging import get_logger, setup_logging, ErrorTracker, LogLevel
from nexus.logging.config import LogConfig
from nexus.middleware import RequestLoggingMiddleware


# Set up logging
config = LogConfig(
    log_dir=Path("logs"),
    log_level=LogLevel.INFO,
)
setup_logging(config)

# Create FastAPI app
app = FastAPI(title="NEXUS Example API")

# Add request logging middleware
app.add_middleware(RequestLoggingMiddleware)

# Get logger and error tracker
logger = get_logger("example.api")
error_tracker = ErrorTracker()


class UserCreate(BaseModel):
    """User creation model."""

    name: str
    email: str


class User(BaseModel):
    """User model."""

    id: int
    name: str
    email: str


# In-memory database
users_db: dict[int, User] = {}
next_id = 1


@app.get("/")
async def root() -> dict[str, str]:
    """Root endpoint."""
    logger.info("root_endpoint_accessed")
    return {"message": "Welcome to NEXUS API"}


@app.post("/users", response_model=User)
async def create_user(user: UserCreate) -> User:
    """Create a new user.

    Args:
        user: User data

    Returns:
        Created user
    """
    global next_id

    logger.info(
        "creating_user",
        name=user.name,
        email=user.email,
    )

    try:
        new_user = User(
            id=next_id,
            name=user.name,
            email=user.email,
        )
        users_db[next_id] = new_user
        next_id += 1

        logger.info(
            "user_created",
            user_id=new_user.id,
            name=new_user.name,
        )

        return new_user

    except Exception as e:
        error_tracker.track_error(
            error=e,
            context={"operation": "create_user", "user_data": user.dict()},
            severity="error",
        )
        raise HTTPException(status_code=500, detail="Failed to create user")


@app.get("/users/{user_id}", response_model=User)
async def get_user(user_id: int) -> User:
    """Get a user by ID.

    Args:
        user_id: User ID

    Returns:
        User data

    Raises:
        HTTPException: If user not found
    """
    logger.info("fetching_user", user_id=user_id)

    if user_id not in users_db:
        logger.warning("user_not_found", user_id=user_id)
        error_tracker.track_http_error(
            status_code=404,
            method="GET",
            url=f"/users/{user_id}",
            error_message="User not found",
        )
        raise HTTPException(status_code=404, detail="User not found")

    user = users_db[user_id]
    logger.info("user_fetched", user_id=user_id, name=user.name)

    return user


@app.get("/error-example")
async def error_example() -> dict[str, str]:
    """Endpoint that demonstrates error tracking.

    Raises:
        HTTPException: Always raises an error
    """
    try:
        # Simulate an error
        result = 1 / 0
    except Exception as e:
        error_tracker.track_error(
            error=e,
            context={"endpoint": "/error-example"},
            severity="error",
        )
        raise HTTPException(status_code=500, detail="Internal server error")


if __name__ == "__main__":
    import uvicorn

    logger.info("starting_api_server", host="0.0.0.0", port=8000)
    uvicorn.run(app, host="0.0.0.0", port=8000)
