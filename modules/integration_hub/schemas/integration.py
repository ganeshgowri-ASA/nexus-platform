"""Integration schemas."""
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime


class IntegrationBase(BaseModel):
    """Base integration schema."""

    name: str
    slug: str
    description: Optional[str] = None
    provider: str
    category: str
    logo_url: Optional[str] = None
    auth_type: str
    auth_config: Dict[str, Any]
    supports_webhooks: bool = False
    supports_sync: bool = False
    supported_actions: Optional[List[str]] = None
    is_public: bool = True
    is_verified: bool = False


class IntegrationCreate(IntegrationBase):
    """Schema for creating an integration."""

    pass


class IntegrationResponse(IntegrationBase):
    """Schema for integration response."""

    id: str
    install_count: int = 0
    rating: int = 0
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True
