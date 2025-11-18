from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime

from modules.api_gateway.database import get_db
from modules.api_gateway.models.api_key import APIKey

router = APIRouter(prefix="/admin/api-keys", tags=["API Keys"])


class APIKeyCreate(BaseModel):
    name: str
    user_id: str = None
    email: str = None
    scopes: List[str] = []
    allowed_routes: List[str] = []
    rate_limit: int = 1000
    rate_limit_window: int = 3600
    expires_at: Optional[datetime] = None
    description: str = None
    metadata: dict = {}


class APIKeyUpdate(BaseModel):
    name: str = None
    active: bool = None
    scopes: List[str] = None
    allowed_routes: List[str] = None
    rate_limit: int = None
    rate_limit_window: int = None
    expires_at: Optional[datetime] = None
    description: str = None
    metadata: dict = None


@router.get("/", response_model=List[dict])
def list_api_keys(
    skip: int = 0,
    limit: int = 100,
    active_only: bool = False,
    db: Session = Depends(get_db)
):
    """List all API keys"""
    query = db.query(APIKey)

    if active_only:
        query = query.filter(APIKey.active == True)

    keys = query.offset(skip).limit(limit).all()

    return [
        {
            "id": k.id,
            "key": k.key[:16] + "...",  # Mask the key
            "name": k.name,
            "user_id": k.user_id,
            "email": k.email,
            "active": k.active,
            "scopes": k.scopes,
            "rate_limit": k.rate_limit,
            "total_requests": k.total_requests,
            "last_used_at": k.last_used_at,
            "expires_at": k.expires_at,
            "created_at": k.created_at,
        }
        for k in keys
    ]


@router.get("/{key_id}")
def get_api_key(key_id: int, db: Session = Depends(get_db)):
    """Get a specific API key"""
    api_key = db.query(APIKey).filter(APIKey.id == key_id).first()
    if not api_key:
        raise HTTPException(status_code=404, detail="API key not found")

    return {
        "id": api_key.id,
        "key": api_key.key,  # Show full key only on individual fetch
        "name": api_key.name,
        "user_id": api_key.user_id,
        "email": api_key.email,
        "active": api_key.active,
        "scopes": api_key.scopes,
        "allowed_routes": api_key.allowed_routes,
        "rate_limit": api_key.rate_limit,
        "rate_limit_window": api_key.rate_limit_window,
        "total_requests": api_key.total_requests,
        "last_used_at": api_key.last_used_at,
        "expires_at": api_key.expires_at,
        "description": api_key.description,
        "metadata": api_key.metadata,
        "created_at": api_key.created_at,
        "updated_at": api_key.updated_at,
    }


@router.post("/", status_code=status.HTTP_201_CREATED)
def create_api_key(key_data: APIKeyCreate, db: Session = Depends(get_db)):
    """Create a new API key"""

    # Generate API key
    key_value = APIKey.generate_key()

    api_key = APIKey(
        key=key_value,
        **key_data.model_dump()
    )

    db.add(api_key)
    db.commit()
    db.refresh(api_key)

    return {
        "id": api_key.id,
        "key": api_key.key,
        "name": api_key.name,
        "message": "API key created successfully. Save this key - it won't be shown again!"
    }


@router.put("/{key_id}")
def update_api_key(key_id: int, key_data: APIKeyUpdate, db: Session = Depends(get_db)):
    """Update an API key"""

    api_key = db.query(APIKey).filter(APIKey.id == key_id).first()
    if not api_key:
        raise HTTPException(status_code=404, detail="API key not found")

    # Update fields
    update_data = key_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(api_key, field, value)

    db.commit()
    db.refresh(api_key)

    return {"id": api_key.id, "name": api_key.name, "message": "API key updated successfully"}


@router.delete("/{key_id}")
def delete_api_key(key_id: int, db: Session = Depends(get_db)):
    """Delete an API key"""

    api_key = db.query(APIKey).filter(APIKey.id == key_id).first()
    if not api_key:
        raise HTTPException(status_code=404, detail="API key not found")

    db.delete(api_key)
    db.commit()

    return {"message": "API key deleted successfully"}


@router.post("/{key_id}/rotate")
def rotate_api_key(key_id: int, db: Session = Depends(get_db)):
    """Rotate an API key (generate new key value)"""

    api_key = db.query(APIKey).filter(APIKey.id == key_id).first()
    if not api_key:
        raise HTTPException(status_code=404, detail="API key not found")

    # Generate new key
    new_key = APIKey.generate_key()
    api_key.key = new_key

    db.commit()
    db.refresh(api_key)

    return {
        "id": api_key.id,
        "key": api_key.key,
        "name": api_key.name,
        "message": "API key rotated successfully. Save this new key!"
    }
