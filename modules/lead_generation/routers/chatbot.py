"""
Chatbot API router.
"""
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from modules.lead_generation.schemas import (
    ChatbotMessageCreate, ChatbotConversationResponse
)
from modules.lead_generation.services.chatbot_service import ChatbotService

router = APIRouter()
chatbot_service = ChatbotService()


@router.post("/conversations", response_model=ChatbotConversationResponse, status_code=201)
async def create_conversation(db: AsyncSession = Depends(get_db)):
    """Create a new chatbot conversation."""
    conversation = await chatbot_service.create_conversation(db)
    return conversation


@router.post("/conversations/{conversation_id}/messages")
async def send_message(
    conversation_id: UUID,
    message_data: ChatbotMessageCreate,
    db: AsyncSession = Depends(get_db)
):
    """Send a message in a conversation."""
    try:
        response = await chatbot_service.send_message(
            db,
            conversation_id,
            message_data.message,
            message_data.sender
        )
        return response
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
