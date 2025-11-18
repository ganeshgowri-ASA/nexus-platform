"""
Email-related Pydantic schemas
"""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, EmailStr, Field, ConfigDict


class EmailBase(BaseModel):
    """Base email schema"""

    subject: str = Field(..., min_length=1, max_length=255)
    body: str = Field(..., description="Email body content")
    is_html: bool = False


class EmailCreate(EmailBase):
    """Schema for storing received emails"""

    sender: EmailStr
    recipients: List[EmailStr]
    cc: Optional[List[EmailStr]] = Field(default_factory=list)
    bcc: Optional[List[EmailStr]] = Field(default_factory=list)


class EmailSend(EmailBase):
    """Schema for sending emails"""

    to: List[EmailStr] = Field(..., min_items=1)
    cc: Optional[List[EmailStr]] = Field(default_factory=list)
    bcc: Optional[List[EmailStr]] = Field(default_factory=list)
    attachments: Optional[List[str]] = Field(
        default_factory=list, description="List of file paths or URLs"
    )
    reply_to: Optional[EmailStr] = None


class EmailResponse(BaseModel):
    """Schema for email response"""

    id: int
    subject: str
    body: str
    is_html: bool
    sender: EmailStr
    recipients: List[EmailStr]
    cc: List[EmailStr]
    bcc: List[EmailStr]
    status: str = Field(
        ..., description="Email status: draft, sent, failed, received"
    )
    user_id: int
    created_at: datetime
    sent_at: Optional[datetime]
    read_at: Optional[datetime]

    model_config = ConfigDict(from_attributes=True)


class EmailFilter(BaseModel):
    """Schema for filtering emails"""

    sender: Optional[EmailStr] = None
    status: Optional[str] = None
    is_read: Optional[bool] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
