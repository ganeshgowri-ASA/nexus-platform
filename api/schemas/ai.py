"""
AI-related Pydantic schemas
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, ConfigDict


class AICompletionRequest(BaseModel):
    """Schema for AI completion request"""

    prompt: str = Field(..., min_length=1, max_length=10000)
    model: str = Field(
        default="gpt-3.5-turbo",
        description="AI model to use: gpt-3.5-turbo, gpt-4, claude-3, etc.",
    )
    max_tokens: int = Field(default=1000, ge=1, le=8000)
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    top_p: float = Field(default=1.0, ge=0.0, le=1.0)
    frequency_penalty: float = Field(default=0.0, ge=-2.0, le=2.0)
    presence_penalty: float = Field(default=0.0, ge=-2.0, le=2.0)
    system_message: Optional[str] = Field(
        None, description="System message to set context"
    )
    conversation_history: Optional[List[Dict[str, str]]] = Field(
        default_factory=list, description="Previous messages in conversation"
    )
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)


class AICompletionResponse(BaseModel):
    """Schema for AI completion response"""

    id: str = Field(..., description="Unique completion ID")
    completion: str = Field(..., description="AI-generated response")
    model: str
    usage: Dict[str, int] = Field(
        ..., description="Token usage: prompt_tokens, completion_tokens, total_tokens"
    )
    finish_reason: str = Field(
        ..., description="Completion finish reason: stop, length, content_filter"
    )
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AIModelInfo(BaseModel):
    """Schema for AI model information"""

    model_id: str
    name: str
    provider: str = Field(..., description="Model provider: openai, anthropic, etc.")
    description: Optional[str]
    max_tokens: int
    supports_streaming: bool = False
    cost_per_1k_tokens: Optional[float] = None

    model_config = ConfigDict(from_attributes=True)


class AIConversationCreate(BaseModel):
    """Schema for creating AI conversation"""

    title: Optional[str] = Field(None, max_length=200)
    model: str = Field(default="gpt-3.5-turbo")
    system_message: Optional[str] = None


class AIConversationResponse(BaseModel):
    """Schema for AI conversation response"""

    id: int
    title: Optional[str]
    model: str
    system_message: Optional[str]
    user_id: int
    message_count: int = 0
    total_tokens_used: int = 0
    created_at: datetime
    updated_at: Optional[datetime]

    model_config = ConfigDict(from_attributes=True)


class AIImageGenerationRequest(BaseModel):
    """Schema for AI image generation request"""

    prompt: str = Field(..., min_length=1, max_length=4000)
    model: str = Field(default="dall-e-3", description="Image generation model")
    size: str = Field(
        default="1024x1024", description="Image size: 256x256, 512x512, 1024x1024"
    )
    quality: str = Field(default="standard", description="Quality: standard, hd")
    n: int = Field(default=1, ge=1, le=10, description="Number of images to generate")


class AIImageGenerationResponse(BaseModel):
    """Schema for AI image generation response"""

    id: str
    prompt: str
    model: str
    image_urls: List[str]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
