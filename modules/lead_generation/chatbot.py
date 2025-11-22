"""
Chatbot lead capture for conversational lead generation.

This module provides chatbot functionality for lead qualification,
scheduling, and conversational data collection.
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
from sqlalchemy.orm import Session

from .capture import LeadCapture
from .lead_types import LeadCreate, LeadStatus
from config.logging_config import get_logger
from config.settings import settings

logger = get_logger(__name__)


class ChatbotLeadCapture:
    """Chatbot lead capture service."""

    def __init__(self, db: Session):
        """
        Initialize chatbot lead capture.

        Args:
            db: Database session.
        """
        self.db = db
        self.lead_capture = LeadCapture(db)

    async def process_conversation(
        self,
        conversation: List[Dict[str, str]],
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Process chatbot conversation and extract lead information.

        Args:
            conversation: List of conversation messages.
            metadata: Additional metadata.

        Returns:
            Extracted lead data and qualification info.
        """
        try:
            # Extract information from conversation using AI/LLM
            extracted_data = await self._extract_lead_info(conversation)

            # Qualify lead based on conversation
            qualification = await self._qualify_lead(conversation, extracted_data)

            result = {
                "lead_data": extracted_data,
                "qualification": qualification,
                "conversation": conversation,
            }

            logger.info(f"Chatbot conversation processed: {extracted_data.get('email')}")

            return result

        except Exception as e:
            logger.error(f"Error processing chatbot conversation: {e}")
            raise

    async def capture_from_conversation(
        self,
        email: str,
        conversation: List[Dict[str, str]],
        extracted_data: Optional[Dict[str, Any]] = None,
    ) -> Any:
        """
        Capture lead from chatbot conversation.

        Args:
            email: Lead email address.
            conversation: Conversation history.
            extracted_data: Pre-extracted lead data.

        Returns:
            Created lead object.
        """
        try:
            if not extracted_data:
                extracted_data = await self._extract_lead_info(conversation)

            lead = await self.lead_capture.capture_chatbot_lead(
                email=email,
                conversation_data=extracted_data,
                metadata={"conversation_length": len(conversation)},
            )

            logger.info(f"Lead captured from chatbot: {email}")

            return lead

        except Exception as e:
            logger.error(f"Error capturing lead from conversation: {e}")
            raise

    async def _extract_lead_info(
        self,
        conversation: List[Dict[str, str]],
    ) -> Dict[str, Any]:
        """
        Extract lead information from conversation using AI.

        Args:
            conversation: Conversation messages.

        Returns:
            Extracted lead data.
        """
        # Combine conversation into a single text
        conversation_text = "\n".join([
            f"{msg['role']}: {msg['content']}"
            for msg in conversation
        ])

        # Use LLM to extract structured data (implement based on your AI provider)
        extracted = {
            "email": None,
            "first_name": None,
            "last_name": None,
            "company": None,
            "phone": None,
            "intent": None,
            "pain_points": [],
            "interests": [],
        }

        # Simple pattern matching for email (replace with LLM extraction)
        import re
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        emails = re.findall(email_pattern, conversation_text)
        if emails:
            extracted["email"] = emails[0]

        # Add more sophisticated extraction logic using LLM here

        return extracted

    async def _qualify_lead(
        self,
        conversation: List[Dict[str, str]],
        extracted_data: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Qualify lead based on conversation.

        Args:
            conversation: Conversation messages.
            extracted_data: Extracted lead data.

        Returns:
            Qualification results.
        """
        qualification = {
            "is_qualified": False,
            "score": 0,
            "reasons": [],
            "next_steps": [],
        }

        # Check if key information is provided
        if extracted_data.get("email"):
            qualification["score"] += 20
        if extracted_data.get("company"):
            qualification["score"] += 20
        if extracted_data.get("phone"):
            qualification["score"] += 10

        # Check engagement level
        engagement_score = len(conversation) * 5
        qualification["score"] += min(engagement_score, 30)

        # Determine if qualified
        qualification["is_qualified"] = qualification["score"] >= 50

        # Add reasons
        if qualification["is_qualified"]:
            qualification["reasons"].append("Provided contact information")
            qualification["reasons"].append("Engaged in conversation")
        else:
            qualification["reasons"].append("Insufficient information provided")

        # Suggest next steps
        if qualification["is_qualified"]:
            qualification["next_steps"].append("Schedule demo call")
            qualification["next_steps"].append("Send product information")
        else:
            qualification["next_steps"].append("Send nurture email")
            qualification["next_steps"].append("Request more information")

        return qualification


class ChatbotFlow:
    """Chatbot conversation flow builder."""

    def __init__(self):
        """Initialize chatbot flow."""
        self.steps = []

    def add_step(
        self,
        step_id: str,
        message: str,
        question_type: str = "text",
        options: Optional[List[str]] = None,
        validation: Optional[Dict[str, Any]] = None,
    ) -> "ChatbotFlow":
        """
        Add step to chatbot flow.

        Args:
            step_id: Step identifier.
            message: Message to display.
            question_type: Type of question (text, email, phone, choice).
            options: Options for choice questions.
            validation: Validation rules.

        Returns:
            Self for chaining.
        """
        self.steps.append({
            "id": step_id,
            "message": message,
            "type": question_type,
            "options": options,
            "validation": validation,
        })
        return self

    def build(self) -> List[Dict[str, Any]]:
        """
        Build chatbot flow.

        Returns:
            List of flow steps.
        """
        return self.steps


class ChatbotScheduling:
    """Chatbot scheduling integration for booking meetings."""

    async def check_availability(
        self,
        date: str,
        time_slot: str,
    ) -> bool:
        """
        Check if time slot is available.

        Args:
            date: Date string (YYYY-MM-DD).
            time_slot: Time slot (e.g., "10:00-11:00").

        Returns:
            True if available.
        """
        # Implement calendar integration here
        # For now, return True
        return True

    async def schedule_meeting(
        self,
        lead_email: str,
        date: str,
        time_slot: str,
        meeting_type: str = "demo",
    ) -> Dict[str, Any]:
        """
        Schedule meeting with lead.

        Args:
            lead_email: Lead email address.
            date: Date string.
            time_slot: Time slot.
            meeting_type: Type of meeting.

        Returns:
            Meeting details.
        """
        try:
            # Create meeting (integrate with calendar API)
            meeting = {
                "id": f"meeting-{datetime.utcnow().timestamp()}",
                "lead_email": lead_email,
                "date": date,
                "time_slot": time_slot,
                "type": meeting_type,
                "status": "scheduled",
                "meeting_link": f"https://meet.nexus.com/{lead_email}",
            }

            logger.info(f"Meeting scheduled: {lead_email} on {date} {time_slot}")

            return meeting

        except Exception as e:
            logger.error(f"Error scheduling meeting: {e}")
            raise


# Pre-built chatbot flows
DEFAULT_LEAD_CAPTURE_FLOW = ChatbotFlow() \
    .add_step("greeting", "Hi! I'm here to help. What's your name?", "text") \
    .add_step("email", "Great to meet you! What's your email address?", "email") \
    .add_step("company", "Which company do you work for?", "text") \
    .add_step("interest", "What are you interested in?", "choice",
              options=["Product Demo", "Pricing", "Support", "Other"]) \
    .add_step("thank_you", "Thank you! We'll be in touch soon.", "info") \
    .build()

QUALIFICATION_FLOW = ChatbotFlow() \
    .add_step("greeting", "Hi! Let's see if we're a good fit.", "text") \
    .add_step("email", "What's your work email?", "email") \
    .add_step("role", "What's your role?", "choice",
              options=["Executive", "Manager", "Developer", "Other"]) \
    .add_step("company_size", "How large is your company?", "choice",
              options=["1-10", "11-50", "51-200", "201-1000", "1000+"]) \
    .add_step("budget", "What's your approximate budget?", "choice",
              options=["< $1k", "$1k-$10k", "$10k-$50k", "$50k+"]) \
    .add_step("timeline", "When are you looking to get started?", "choice",
              options=["Immediately", "This month", "This quarter", "Just exploring"]) \
    .build()
