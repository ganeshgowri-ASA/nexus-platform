"""
LLM Client for Claude AI integration.

This module provides a unified interface for interacting with Claude AI
for content generation, personalization, and other AI-powered features.
"""
from typing import Optional, Dict, Any, List
import anthropic
from anthropic import Anthropic, AsyncAnthropic

from config.settings import settings
from config.logging_config import get_logger
from src.core.exceptions import LLMError

logger = get_logger(__name__)


class LLMClient:
    """
    Client for interacting with Claude AI.

    Provides methods for content generation, personalization, and AI-powered
    marketing automation features.
    """

    def __init__(self, api_key: Optional[str] = None) -> None:
        """
        Initialize LLM client.

        Args:
            api_key: Anthropic API key (defaults to settings.anthropic_api_key)
        """
        self.api_key = api_key or settings.anthropic_api_key
        self.model = settings.llm_default_model
        self.max_tokens = settings.llm_max_tokens
        self.temperature = settings.llm_temperature

        # Initialize sync and async clients
        self.client = Anthropic(api_key=self.api_key)
        self.async_client = AsyncAnthropic(api_key=self.api_key)

        logger.info("LLM client initialized", model=self.model)

    async def generate_text(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
    ) -> str:
        """
        Generate text using Claude AI.

        Args:
            prompt: User prompt
            system_prompt: System prompt for context
            max_tokens: Maximum tokens to generate
            temperature: Temperature for sampling

        Returns:
            Generated text

        Raises:
            LLMError: If generation fails
        """
        try:
            messages = [{"role": "user", "content": prompt}]

            response = await self.async_client.messages.create(
                model=self.model,
                max_tokens=max_tokens or self.max_tokens,
                temperature=temperature or self.temperature,
                system=system_prompt or "You are a helpful AI assistant.",
                messages=messages,
            )

            generated_text = response.content[0].text
            logger.info(
                "Text generated successfully",
                prompt_length=len(prompt),
                response_length=len(generated_text)
            )
            return generated_text

        except anthropic.APIError as e:
            logger.error("LLM API error", error=str(e))
            raise LLMError(f"Failed to generate text: {str(e)}")
        except Exception as e:
            logger.error("Unexpected error in text generation", error=str(e))
            raise LLMError(f"Unexpected error: {str(e)}")

    async def generate_email_content(
        self,
        campaign_goal: str,
        target_audience: str,
        key_points: List[str],
        tone: str = "professional",
        include_cta: bool = True,
    ) -> Dict[str, str]:
        """
        Generate email content for a campaign.

        Args:
            campaign_goal: Goal of the campaign
            target_audience: Description of target audience
            key_points: Key points to include
            tone: Tone of the email (professional, casual, friendly, etc.)
            include_cta: Whether to include a call-to-action

        Returns:
            Dictionary with 'subject' and 'body' keys

        Raises:
            LLMError: If generation fails
        """
        key_points_str = "\n".join(f"- {point}" for point in key_points)
        cta_instruction = "Include a clear call-to-action." if include_cta else ""

        prompt = f"""Generate an email for a marketing campaign with the following details:

Campaign Goal: {campaign_goal}
Target Audience: {target_audience}
Tone: {tone}

Key Points to Include:
{key_points_str}

{cta_instruction}

Please provide:
1. An engaging subject line
2. The email body in HTML format

Format your response as:
SUBJECT: [subject line]
BODY:
[HTML body content]
"""

        try:
            response = await self.generate_text(
                prompt=prompt,
                system_prompt="You are an expert email marketing copywriter. Create compelling, conversion-focused email content."
            )

            # Parse response
            parts = response.split("BODY:", 1)
            subject = parts[0].replace("SUBJECT:", "").strip()
            body = parts[1].strip() if len(parts) > 1 else response

            return {"subject": subject, "body": body}

        except Exception as e:
            logger.error("Failed to generate email content", error=str(e))
            raise LLMError(f"Failed to generate email content: {str(e)}")

    async def personalize_content(
        self,
        template: str,
        contact_data: Dict[str, Any],
        personalization_level: str = "medium",
    ) -> str:
        """
        Personalize content using AI based on contact data.

        Args:
            template: Content template
            contact_data: Contact information and attributes
            personalization_level: Level of personalization (low, medium, high)

        Returns:
            Personalized content

        Raises:
            LLMError: If personalization fails
        """
        prompt = f"""Personalize the following email template for the recipient:

Template:
{template}

Recipient Information:
{', '.join(f'{k}: {v}' for k, v in contact_data.items())}

Personalization Level: {personalization_level}

Instructions:
- For 'low': Only substitute basic fields like name
- For 'medium': Add context-aware personalization based on recipient data
- For 'high': Deeply personalize content, tone, and recommendations

Provide the personalized email content in HTML format.
"""

        try:
            return await self.generate_text(
                prompt=prompt,
                system_prompt="You are an AI personalization engine for email marketing. Create highly personalized content that resonates with recipients."
            )
        except Exception as e:
            logger.error("Failed to personalize content", error=str(e))
            raise LLMError(f"Failed to personalize content: {str(e)}")

    async def generate_subject_line_variations(
        self,
        base_subject: str,
        num_variations: int = 3,
    ) -> List[str]:
        """
        Generate subject line variations for A/B testing.

        Args:
            base_subject: Base subject line
            num_variations: Number of variations to generate

        Returns:
            List of subject line variations

        Raises:
            LLMError: If generation fails
        """
        prompt = f"""Generate {num_variations} creative variations of this email subject line for A/B testing:

Base Subject: {base_subject}

Requirements:
- Each variation should test a different approach (e.g., urgency, curiosity, benefit-focused)
- Keep them concise (under 60 characters)
- Make them compelling and click-worthy

Provide only the subject lines, one per line.
"""

        try:
            response = await self.generate_text(
                prompt=prompt,
                system_prompt="You are an expert email marketing copywriter specializing in high-converting subject lines."
            )

            # Parse variations (one per line)
            variations = [line.strip() for line in response.split("\n") if line.strip()]
            return variations[:num_variations]

        except Exception as e:
            logger.error("Failed to generate subject line variations", error=str(e))
            raise LLMError(f"Failed to generate subject line variations: {str(e)}")

    async def analyze_campaign_performance(
        self,
        campaign_data: Dict[str, Any],
    ) -> str:
        """
        Analyze campaign performance and provide insights.

        Args:
            campaign_data: Campaign metrics and data

        Returns:
            Analysis and recommendations

        Raises:
            LLMError: If analysis fails
        """
        prompt = f"""Analyze this email campaign performance and provide insights:

Campaign Data:
{', '.join(f'{k}: {v}' for k, v in campaign_data.items())}

Please provide:
1. Performance assessment (open rate, click rate, conversion rate)
2. Key strengths and weaknesses
3. Specific recommendations for improvement
4. A/B test suggestions
"""

        try:
            return await self.generate_text(
                prompt=prompt,
                system_prompt="You are a marketing analytics expert. Provide data-driven insights and actionable recommendations."
            )
        except Exception as e:
            logger.error("Failed to analyze campaign performance", error=str(e))
            raise LLMError(f"Failed to analyze campaign performance: {str(e)}")

    async def generate_segment_criteria(
        self,
        campaign_goal: str,
        available_attributes: List[str],
    ) -> Dict[str, Any]:
        """
        Generate intelligent segment criteria based on campaign goal.

        Args:
            campaign_goal: Goal of the campaign
            available_attributes: Available contact attributes

        Returns:
            Suggested segment criteria

        Raises:
            LLMError: If generation fails
        """
        attributes_str = ", ".join(available_attributes)

        prompt = f"""Suggest audience segmentation criteria for this campaign:

Campaign Goal: {campaign_goal}
Available Contact Attributes: {attributes_str}

Provide segmentation criteria that would make this campaign most effective.
Format as JSON with conditions.
"""

        try:
            response = await self.generate_text(
                prompt=prompt,
                system_prompt="You are an audience segmentation expert. Provide data-driven segmentation strategies."
            )

            # In a production system, you'd parse this as JSON
            # For now, returning as-is
            return {"criteria": response}

        except Exception as e:
            logger.error("Failed to generate segment criteria", error=str(e))
            raise LLMError(f"Failed to generate segment criteria: {str(e)}")


# Global LLM client instance
llm_client = LLMClient()
