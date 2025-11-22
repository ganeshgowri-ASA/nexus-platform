"""
Chatbot service for lead capture using AI/LLM.
"""
from datetime import datetime
from typing import Dict, Any, Optional, List
from uuid import UUID

import anthropic
from loguru import logger
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from config import get_settings
from modules.lead_generation.models import ChatbotConversation, Lead, LeadSource

settings = get_settings()


class ChatbotService:
    """Service for managing chatbot conversations."""

    def __init__(self):
        """Initialize chatbot service."""
        self.client = None
        if settings.anthropic_api_key:
            self.client = anthropic.Anthropic(api_key=settings.anthropic_api_key)

    async def create_conversation(self, db: AsyncSession) -> ChatbotConversation:
        """
        Create a new chatbot conversation.

        Args:
            db: Database session

        Returns:
            Created conversation
        """
        try:
            conversation = ChatbotConversation(
                messages=[],
                context={},
                is_active=True
            )

            db.add(conversation)
            await db.commit()
            await db.refresh(conversation)

            logger.info(f"Chatbot conversation created: {conversation.id}")
            return conversation
        except Exception as e:
            await db.rollback()
            logger.error(f"Error creating conversation: {e}")
            raise

    async def send_message(
        self,
        db: AsyncSession,
        conversation_id: UUID,
        message: str,
        sender: str = "user"
    ) -> Dict[str, Any]:
        """
        Send a message in the conversation.

        Args:
            db: Database session
            conversation_id: Conversation ID
            message: Message text
            sender: Sender (user or bot)

        Returns:
            Response with bot reply
        """
        try:
            # Get conversation
            result = await db.execute(
                select(ChatbotConversation).where(
                    ChatbotConversation.id == conversation_id
                )
            )
            conversation = result.scalar_one_or_none()

            if not conversation:
                logger.error(f"Conversation not found: {conversation_id}")
                raise ValueError("Conversation not found")

            # Add user message
            user_msg = {
                "role": sender,
                "content": message,
                "timestamp": datetime.utcnow().isoformat()
            }
            conversation.messages.append(user_msg)

            # Generate bot response
            bot_response = await self._generate_response(conversation)

            # Add bot message
            bot_msg = {
                "role": "bot",
                "content": bot_response["content"],
                "timestamp": datetime.utcnow().isoformat()
            }
            conversation.messages.append(bot_msg)

            # Update context
            if "context_update" in bot_response:
                conversation.context.update(bot_response["context_update"])

            # Check if lead info is captured
            if self._has_lead_info(conversation.context):
                if not conversation.lead_captured:
                    await self._create_lead_from_conversation(db, conversation)

            await db.commit()
            await db.refresh(conversation)

            logger.info(f"Message processed in conversation: {conversation_id}")

            return {
                "conversation_id": conversation_id,
                "message": bot_response["content"],
                "context": conversation.context,
                "lead_captured": conversation.lead_captured
            }

        except Exception as e:
            await db.rollback()
            logger.error(f"Error sending message: {e}")
            raise

    async def _generate_response(
        self,
        conversation: ChatbotConversation
    ) -> Dict[str, Any]:
        """
        Generate bot response using Claude AI.

        Args:
            conversation: Conversation object

        Returns:
            Response with content and context updates
        """
        if not self.client:
            logger.warning("Anthropic API not configured, using fallback")
            return self._fallback_response(conversation)

        try:
            # Build system prompt
            system_prompt = """You are a helpful lead capture chatbot for NEXUS platform.
Your goal is to naturally engage visitors and collect their contact information
(name, email, company, job title) in a conversational way.

Be friendly, helpful, and don't be too pushy. Ask questions one at a time.
If the user provides information, acknowledge it and ask for the next piece naturally.

Extract any information provided and include it in your response metadata."""

            # Build message history for Claude
            messages = []
            for msg in conversation.messages:
                if msg["role"] == "user":
                    messages.append({
                        "role": "user",
                        "content": msg["content"]
                    })
                elif msg["role"] == "bot":
                    messages.append({
                        "role": "assistant",
                        "content": msg["content"]
                    })

            # Call Claude API
            response = self.client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=500,
                system=system_prompt,
                messages=messages
            )

            content = response.content[0].text

            # Extract any lead info from the conversation
            context_update = self._extract_lead_info(content, conversation.messages)

            return {
                "content": content,
                "context_update": context_update
            }

        except Exception as e:
            logger.error(f"Error generating AI response: {e}")
            return self._fallback_response(conversation)

    def _fallback_response(
        self,
        conversation: ChatbotConversation
    ) -> Dict[str, Any]:
        """
        Fallback response when AI is not available.

        Args:
            conversation: Conversation object

        Returns:
            Fallback response
        """
        message_count = len(conversation.messages)
        context = conversation.context

        responses = {
            0: "Hi! Welcome to NEXUS. I'm here to help. What brings you here today?",
            1: "That's great! To better assist you, may I have your name?",
            2: "Nice to meet you! What's your email address?",
            3: "Thanks! Which company do you work for?",
            4: "Great! What's your role there?",
        }

        content = responses.get(message_count, "Thank you for the information!")

        return {
            "content": content,
            "context_update": {}
        }

    def _extract_lead_info(
        self,
        content: str,
        messages: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Extract lead information from conversation.

        Args:
            content: Bot response content
            messages: Conversation messages

        Returns:
            Extracted lead info
        """
        # Simple extraction (can be enhanced with NER/LLM)
        info = {}

        # Look for email pattern in recent messages
        import re
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'

        for msg in reversed(messages[-5:]):  # Check last 5 messages
            if msg["role"] == "user":
                # Extract email
                email_match = re.search(email_pattern, msg["content"])
                if email_match:
                    info["email"] = email_match.group()

        return info

    def _has_lead_info(self, context: Dict[str, Any]) -> bool:
        """
        Check if conversation has enough lead info.

        Args:
            context: Conversation context

        Returns:
            True if has required info
        """
        return "email" in context

    async def _create_lead_from_conversation(
        self,
        db: AsyncSession,
        conversation: ChatbotConversation
    ) -> Optional[Lead]:
        """
        Create lead from chatbot conversation.

        Args:
            db: Database session
            conversation: Conversation object

        Returns:
            Created lead or None
        """
        try:
            context = conversation.context

            if "email" not in context:
                return None

            # Create lead
            lead = Lead(
                email=context["email"],
                first_name=context.get("first_name"),
                last_name=context.get("last_name"),
                company=context.get("company"),
                job_title=context.get("job_title"),
                source=LeadSource.CHATBOT,
                custom_fields={"chatbot_conversation_id": str(conversation.id)}
            )

            db.add(lead)
            conversation.lead_id = lead.id
            conversation.lead_captured = True

            await db.commit()
            await db.refresh(lead)

            logger.info(f"Lead created from chatbot: {lead.id}")
            return lead

        except Exception as e:
            logger.error(f"Error creating lead from conversation: {e}")
            return None
