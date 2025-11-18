"""Claude AI client wrapper for all AI operations"""
from anthropic import Anthropic
from config.settings import settings
from typing import List, Dict, Optional

class ClaudeClient:
    """Wrapper for Claude AI API"""

    def __init__(self, api_key: Optional[str] = None):
        """Initialize Claude client"""
        self.api_key = api_key or settings.ANTHROPIC_API_KEY
        if not self.api_key:
            raise ValueError("ANTHROPIC_API_KEY not set. Please configure it in .env file")
        self.client = Anthropic(api_key=self.api_key)
        self.model = settings.CLAUDE_MODEL

    def chat(
        self,
        messages: List[Dict[str, str]],
        system: Optional[str] = None,
        max_tokens: int = 4096,
        temperature: float = 1.0
    ) -> str:
        """
        Send a chat message to Claude

        Args:
            messages: List of message dicts with 'role' and 'content'
            system: System prompt
            max_tokens: Maximum tokens in response
            temperature: Randomness (0-1)

        Returns:
            Claude's response text
        """
        params = {
            "model": self.model,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "messages": messages
        }

        if system:
            params["system"] = system

        response = self.client.messages.create(**params)
        return response.content[0].text

    def generate_slide_content(self, topic: str, num_slides: int = 5) -> Dict:
        """Generate presentation content for a given topic"""
        system = "You are a professional presentation designer. Create engaging, well-structured slide content."

        messages = [{
            "role": "user",
            "content": f"Create {num_slides} slides about '{topic}'. For each slide, provide a title and bullet points. Return as JSON with structure: {{'slides': [{{'title': '...', 'content': ['point1', 'point2', ...]}}]}}"
        }]

        response = self.chat(messages, system=system)
        # Parse and return the response
        import json
        try:
            return json.loads(response)
        except:
            # Fallback if JSON parsing fails
            return {"slides": [{"title": topic, "content": [response]}]}

    def generate_email_reply(self, original_email: str, context: str = "") -> str:
        """Generate smart email reply"""
        system = "You are a professional email assistant. Generate appropriate, concise email replies."

        messages = [{
            "role": "user",
            "content": f"Generate a professional reply to this email:\n\n{original_email}\n\nContext: {context}"
        }]

        return self.chat(messages, system=system, max_tokens=1024)

    def summarize_note(self, note_content: str, max_length: int = 200) -> str:
        """Generate AI summary of a note"""
        system = "You are a helpful assistant that creates concise summaries."

        messages = [{
            "role": "user",
            "content": f"Summarize the following note in {max_length} characters or less:\n\n{note_content}"
        }]

        return self.chat(messages, system=system, max_tokens=512)

    def suggest_project_tasks(self, project_description: str) -> List[str]:
        """Suggest tasks for a project"""
        system = "You are a project management expert. Break down projects into actionable tasks."

        messages = [{
            "role": "user",
            "content": f"Break down this project into 5-10 specific, actionable tasks:\n\n{project_description}\n\nReturn as a JSON array of task titles."
        }]

        response = self.chat(messages, system=system, max_tokens=1024)
        import json
        try:
            return json.loads(response)
        except:
            # Fallback
            return response.split('\n')

    def analyze_email_sentiment(self, email_content: str) -> str:
        """Analyze sentiment of email"""
        system = "You are an email analyst. Classify emails as: Positive, Neutral, Negative, or Urgent."

        messages = [{
            "role": "user",
            "content": f"Classify the sentiment of this email in one word:\n\n{email_content}"
        }]

        return self.chat(messages, system=system, max_tokens=50).strip()

    def generate_meeting_agenda(self, meeting_topic: str, duration_minutes: int) -> str:
        """Generate meeting agenda"""
        system = "You are a meeting facilitator. Create structured meeting agendas."

        messages = [{
            "role": "user",
            "content": f"Create a detailed agenda for a {duration_minutes}-minute meeting about: {meeting_topic}"
        }]

        return self.chat(messages, system=system, max_tokens=1024)

    def suggest_crm_next_steps(self, contact_info: str, deal_stage: str) -> List[str]:
        """Suggest next steps for CRM contact"""
        system = "You are a sales expert. Suggest next steps for moving deals forward."

        messages = [{
            "role": "user",
            "content": f"Contact: {contact_info}\nDeal Stage: {deal_stage}\n\nSuggest 3-5 next steps to move this deal forward. Return as JSON array."
        }]

        response = self.chat(messages, system=system, max_tokens=512)
        import json
        try:
            return json.loads(response)
        except:
            return response.split('\n')
