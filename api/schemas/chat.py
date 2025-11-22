"""
Chat and messaging-related Pydantic schemas
"""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict


class MessageBase(BaseModel):
    """Base message schema"""

    content: str = Field(..., min_length=1, max_length=4000)
    message_type: str = Field(
        default="text", description="Message type: text, image, file, system"
    )


class MessageCreate(MessageBase):
    """Schema for message creation"""

    room_id: int
    parent_id: Optional[int] = Field(
        None, description="Parent message ID for threaded conversations"
    )


class MessageResponse(BaseModel):
    """Schema for message response"""

    id: int
    content: str
    message_type: str
    room_id: int
    user_id: int
    username: str
    parent_id: Optional[int]
    is_edited: bool = False
    is_deleted: bool = False
    created_at: datetime
    updated_at: Optional[datetime]

    model_config = ConfigDict(from_attributes=True)


class ChatRoomBase(BaseModel):
    """Base chat room schema"""

    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    is_private: bool = False
    room_type: str = Field(
        default="group", description="Room type: direct, group, channel"
    )


class ChatRoomCreate(ChatRoomBase):
    """Schema for chat room creation"""

    participant_ids: List[int] = Field(
        default_factory=list, description="Initial participant user IDs"
    )


class ChatRoomUpdate(BaseModel):
    """Schema for chat room update"""

    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    is_private: Optional[bool] = None


class ChatRoomResponse(BaseModel):
    """Schema for chat room response"""

    id: int
    name: str
    description: Optional[str]
    is_private: bool
    room_type: str
    owner_id: int
    participant_count: int
    last_message_at: Optional[datetime]
    created_at: datetime
    updated_at: Optional[datetime]

    model_config = ConfigDict(from_attributes=True)


class ChatRoomParticipant(BaseModel):
    """Schema for chat room participant"""

    user_id: int
    username: str
    joined_at: datetime
    role: str = Field(
        default="member", description="Participant role: owner, admin, member"
    )

    model_config = ConfigDict(from_attributes=True)
