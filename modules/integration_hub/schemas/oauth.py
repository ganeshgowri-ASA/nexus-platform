"""OAuth schemas."""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class OAuthInitRequest(BaseModel):
    """Schema for initiating OAuth flow."""

    integration_id: str
    redirect_uri: str
    scopes: Optional[List[str]] = None
    state: Optional[str] = None


class OAuthCallbackRequest(BaseModel):
    """Schema for OAuth callback."""

    code: str
    state: Optional[str] = None


class OAuthConnectionResponse(BaseModel):
    """Schema for OAuth connection response."""

    id: str
    integration_id: str
    name: str
    user_id: Optional[str] = None
    token_type: str
    scopes: Optional[List[str]] = None
    expires_at: Optional[datetime] = None
    provider_user_id: Optional[str] = None
    provider_user_info: Optional[dict] = None
    is_active: bool
    last_used: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True
