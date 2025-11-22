"""
AI Chatbot Module

AI-powered chatbot for instant answers from KB content.
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4

from sqlalchemy.orm import Session

from .kb_types import Language
from .models import ChatMessage, ChatSession

logger = logging.getLogger(__name__)


class ChatbotManager:
    """Manager for AI-powered KB chatbot."""

    def __init__(
        self,
        db_session: Session,
        llm_client: Optional[Any] = None,
        search_engine: Optional[Any] = None,
    ):
        self.db = db_session
        self.llm = llm_client
        self.search = search_engine

    async def create_session(
        self,
        user_id: Optional[UUID] = None,
        language: Language = Language.EN,
    ) -> ChatSession:
        """Create a new chat session."""
        try:
            session = ChatSession(
                user_id=user_id,
                session_id=str(uuid4()),
                language=language.value,
            )

            self.db.add(session)
            self.db.commit()
            self.db.refresh(session)

            return session

        except Exception as e:
            self.db.rollback()
            logger.error(f"Error creating chat session: {str(e)}")
            raise

    async def send_message(
        self,
        session_id: UUID,
        message: str,
    ) -> Dict:
        """Send a message and get AI response."""
        try:
            session = (
                self.db.query(ChatSession)
                .filter(ChatSession.id == session_id)
                .first()
            )

            if not session:
                raise ValueError(f"Session {session_id} not found")

            # Save user message
            user_message = ChatMessage(
                session_id=session_id,
                role="user",
                content=message,
            )
            self.db.add(user_message)

            # Search KB for relevant content
            relevant_articles = []
            if self.search:
                search_results = await self.search.search(message, limit=3)
                relevant_articles = search_results.get("results", [])

            # Generate AI response
            response_content = await self._generate_response(
                message,
                relevant_articles,
                session,
            )

            # Save assistant message
            assistant_message = ChatMessage(
                session_id=session_id,
                role="assistant",
                content=response_content,
                suggested_articles=[
                    a.get("id") for a in relevant_articles if a.get("id")
                ],
            )
            self.db.add(assistant_message)

            session.last_message_at = datetime.utcnow()
            self.db.commit()

            return {
                "message": response_content,
                "suggested_articles": relevant_articles,
            }

        except Exception as e:
            self.db.rollback()
            logger.error(f"Error sending message: {str(e)}")
            raise

    async def _generate_response(
        self,
        query: str,
        articles: List[Dict],
        session: ChatSession,
    ) -> str:
        """Generate AI response using LLM."""
        if not self.llm:
            # Fallback response
            if articles:
                return f"I found some relevant articles that might help: {articles[0].get('title', '')}"
            return "I'm here to help! Could you provide more details?"

        # Build context from articles
        context = "\n\n".join(
            [f"Title: {a.get('title')}\n{a.get('snippet', '')}" for a in articles]
        )

        prompt = f"""
        You are a helpful KB assistant. Answer the user's question based on the following information:

        {context}

        User question: {query}

        Provide a helpful, concise answer.
        """

        # Call LLM (simplified)
        # response = await self.llm.complete(prompt)

        # Placeholder
        return "Based on our knowledge base, here's what I found..."

    async def get_conversation_history(
        self,
        session_id: UUID,
        limit: int = 50,
    ) -> List[ChatMessage]:
        """Get conversation history."""
        try:
            messages = (
                self.db.query(ChatMessage)
                .filter(ChatMessage.session_id == session_id)
                .order_by(ChatMessage.timestamp)
                .limit(limit)
                .all()
            )

            return messages

        except Exception as e:
            logger.error(f"Error getting conversation history: {str(e)}")
            return []
