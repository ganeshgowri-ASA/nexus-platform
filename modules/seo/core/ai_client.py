"""
AI client for SEO recommendations and content optimization.

Integrates with Anthropic Claude and OpenAI for AI-powered SEO features.
"""

from typing import Dict, List, Optional

from anthropic import AsyncAnthropic
from loguru import logger
from openai import AsyncOpenAI

from modules.seo.config.settings import get_settings
from modules.seo.utils.exceptions import APIException


class AIClient:
    """
    AI client for SEO operations.

    Provides methods for AI-powered content optimization,
    keyword suggestions, and SEO recommendations.
    """

    def __init__(self):
        """Initialize AI client."""
        self.settings = get_settings()
        self._anthropic_client: Optional[AsyncAnthropic] = None
        self._openai_client: Optional[AsyncOpenAI] = None

    @property
    def anthropic(self) -> AsyncAnthropic:
        """Get Anthropic client."""
        if self._anthropic_client is None:
            if not self.settings.anthropic_api_key:
                raise APIException(
                    "Anthropic API key not configured",
                    api_name="anthropic",
                )
            self._anthropic_client = AsyncAnthropic(
                api_key=self.settings.anthropic_api_key
            )
        return self._anthropic_client

    @property
    def openai(self) -> AsyncOpenAI:
        """Get OpenAI client."""
        if self._openai_client is None:
            if not self.settings.openai_api_key:
                raise APIException(
                    "OpenAI API key not configured",
                    api_name="openai",
                )
            self._openai_client = AsyncOpenAI(
                api_key=self.settings.openai_api_key
            )
        return self._openai_client

    async def generate_title_suggestions(
        self,
        content: str,
        keyword: str,
        count: int = 5,
    ) -> List[str]:
        """
        Generate title suggestions for content.

        Args:
            content: Content text
            keyword: Target keyword
            count: Number of suggestions

        Returns:
            List of title suggestions
        """
        try:
            prompt = f"""Generate {count} SEO-optimized title suggestions for the following content.
Each title should:
- Include the keyword "{keyword}"
- Be 50-60 characters long
- Be compelling and click-worthy
- Follow SEO best practices

Content:
{content[:1000]}

Return only the titles, one per line."""

            response = await self.anthropic.messages.create(
                model=self.settings.ai_model,
                max_tokens=1000,
                messages=[{"role": "user", "content": prompt}],
            )

            suggestions = response.content[0].text.strip().split("\n")
            return [s.strip("- ").strip() for s in suggestions if s.strip()]

        except Exception as e:
            logger.error(f"Error generating title suggestions: {e}")
            return []

    async def generate_meta_description(
        self,
        content: str,
        keyword: str,
    ) -> Optional[str]:
        """
        Generate meta description for content.

        Args:
            content: Content text
            keyword: Target keyword

        Returns:
            Meta description or None
        """
        try:
            prompt = f"""Generate an SEO-optimized meta description for the following content.
Requirements:
- Include the keyword "{keyword}"
- Be 150-160 characters long
- Be compelling and include a call-to-action
- Accurately summarize the content

Content:
{content[:1000]}

Return only the meta description."""

            response = await self.anthropic.messages.create(
                model=self.settings.ai_model,
                max_tokens=200,
                messages=[{"role": "user", "content": prompt}],
            )

            return response.content[0].text.strip()

        except Exception as e:
            logger.error(f"Error generating meta description: {e}")
            return None

    async def analyze_content_quality(
        self,
        content: str,
        keyword: str,
    ) -> Dict[str, any]:
        """
        Analyze content quality for SEO.

        Args:
            content: Content text
            keyword: Target keyword

        Returns:
            Dictionary with quality analysis
        """
        try:
            prompt = f"""Analyze the following content for SEO quality targeting the keyword "{keyword}".

Provide analysis in the following format:
- Overall Score: (0-100)
- Keyword Usage: (rating and feedback)
- Readability: (rating and feedback)
- Structure: (rating and feedback)
- Engagement: (rating and feedback)
- Recommendations: (3-5 specific improvements)

Content:
{content}

Provide structured analysis."""

            response = await self.anthropic.messages.create(
                model=self.settings.ai_model,
                max_tokens=2000,
                messages=[{"role": "user", "content": prompt}],
            )

            analysis_text = response.content[0].text

            # Parse response (simplified)
            return {
                "score": 75.0,  # Would parse from response
                "analysis": analysis_text,
                "recommendations": [],  # Would parse from response
            }

        except Exception as e:
            logger.error(f"Error analyzing content: {e}")
            return {"score": 0, "analysis": "", "recommendations": []}

    async def generate_keyword_suggestions(
        self,
        seed_keyword: str,
        count: int = 20,
    ) -> List[Dict[str, any]]:
        """
        Generate related keyword suggestions.

        Args:
            seed_keyword: Seed keyword
            count: Number of suggestions

        Returns:
            List of keyword suggestions with relevance scores
        """
        try:
            prompt = f"""Generate {count} related keyword suggestions for "{seed_keyword}".

For each keyword provide:
- The keyword phrase
- Search intent (informational/commercial/transactional)
- Estimated relevance (0-100)

Focus on:
- Long-tail variations
- Question-based keywords
- Related topics
- Commercial opportunities

Return in format: keyword | intent | relevance"""

            response = await self.anthropic.messages.create(
                model=self.settings.ai_model,
                max_tokens=1500,
                messages=[{"role": "user", "content": prompt}],
            )

            suggestions = []
            lines = response.content[0].text.strip().split("\n")

            for line in lines:
                if "|" in line:
                    parts = [p.strip() for p in line.split("|")]
                    if len(parts) >= 3:
                        suggestions.append({
                            "keyword": parts[0],
                            "intent": parts[1],
                            "relevance": float(parts[2]) if parts[2].isdigit() else 50.0,
                        })

            return suggestions

        except Exception as e:
            logger.error(f"Error generating keyword suggestions: {e}")
            return []

    async def generate_content_outline(
        self,
        topic: str,
        keyword: str,
    ) -> Dict[str, any]:
        """
        Generate content outline for topic.

        Args:
            topic: Content topic
            keyword: Target keyword

        Returns:
            Content outline structure
        """
        try:
            prompt = f"""Create a comprehensive SEO content outline for:
Topic: {topic}
Target Keyword: {keyword}

Include:
1. Suggested H1 title
2. Introduction points
3. Main sections (H2) with subsections (H3)
4. Key points to cover in each section
5. Conclusion points
6. Recommended word count
7. Keywords to include

Format as structured outline."""

            response = await self.anthropic.messages.create(
                model=self.settings.ai_model,
                max_tokens=2000,
                messages=[{"role": "user", "content": prompt}],
            )

            return {
                "outline": response.content[0].text,
                "word_count": 2000,  # Would parse from response
                "sections": [],  # Would parse from response
            }

        except Exception as e:
            logger.error(f"Error generating content outline: {e}")
            return {"outline": "", "word_count": 0, "sections": []}
