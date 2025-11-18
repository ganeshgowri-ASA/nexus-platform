"""
AI assistant integration for document management using Claude.

This module provides AI-powered features including:
- Document summarization
- Entity extraction
- Content classification
- Tag suggestions
- Content recommendations
- Smart search assistance
"""

import json
import re
from typing import Any, Dict, List, Optional, Set, Tuple

import anthropic
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.config import get_settings
from backend.core.exceptions import (
    AIException,
    AIQuotaExceededException,
    AIServiceUnavailableException,
    ConfigurationException,
    DocumentNotFoundException,
)
from backend.core.logging import get_logger
from backend.models.document import Document

logger = get_logger(__name__)
settings = get_settings()


class AIAssistantException(AIException):
    """Exception raised for AI assistant errors."""

    def __init__(self, message: str = "AI assistant error", **kwargs: Any) -> None:
        super().__init__(message, **kwargs)


class DocumentAIAssistant:
    """
    AI assistant service using Claude for document intelligence.

    Provides AI-powered features for document analysis, classification,
    and content understanding.
    """

    def __init__(self, db_session: AsyncSession, api_key: Optional[str] = None) -> None:
        """
        Initialize AI assistant.

        Args:
            db_session: Database session
            api_key: Anthropic API key (defaults to settings)

        Raises:
            ConfigurationException: If API key is not configured
        """
        self.db = db_session
        self.api_key = api_key or settings.ANTHROPIC_API_KEY

        if not self.api_key:
            raise ConfigurationException(
                "Anthropic API key not configured. Set ANTHROPIC_API_KEY environment variable."
            )

        self.client = anthropic.Anthropic(api_key=self.api_key)
        self.model = settings.ANTHROPIC_MODEL
        self.max_tokens = settings.ANTHROPIC_MAX_TOKENS
        self.temperature = settings.ANTHROPIC_TEMPERATURE

    async def summarize_document(
        self,
        content: str,
        max_length: int = 200,
        style: str = "concise",
    ) -> Dict[str, Any]:
        """
        Generate a summary of document content.

        Args:
            content: Document content to summarize
            max_length: Maximum length of summary in words
            style: Summary style ('concise', 'detailed', 'bullet_points')

        Returns:
            Dict containing:
                - summary: Generated summary text
                - key_points: List of key points
                - word_count: Number of words in summary

        Raises:
            AIServiceUnavailableException: If API is unavailable
            AIQuotaExceededException: If quota is exceeded
        """
        if not settings.AI_SUMMARIZATION_ENABLED:
            raise AIAssistantException("AI summarization is disabled in settings")

        logger.info(
            "Generating document summary",
            content_length=len(content),
            max_length=max_length,
            style=style,
        )

        # Prepare prompt based on style
        style_instructions = {
            "concise": "Provide a concise, single-paragraph summary.",
            "detailed": "Provide a detailed summary with key points and context.",
            "bullet_points": "Provide a summary as a list of bullet points.",
        }

        prompt = f"""Please analyze the following document and provide a summary.

Style: {style_instructions.get(style, style_instructions['concise'])}
Maximum length: approximately {max_length} words

Document content:
{content[:10000]}  # Limit content to avoid token limits

Please provide:
1. A summary following the specified style
2. A list of 3-5 key points from the document

Format your response as JSON with the following structure:
{{
    "summary": "your summary here",
    "key_points": ["point 1", "point 2", "point 3"]
}}"""

        try:
            response = await self._call_claude(prompt)
            result = self._parse_json_response(response)

            # Add metadata
            result["word_count"] = len(result.get("summary", "").split())
            result["style"] = style

            logger.info(
                "Document summary generated",
                word_count=result["word_count"],
                key_points_count=len(result.get("key_points", [])),
            )

            return result

        except anthropic.APIError as e:
            return self._handle_api_error(e)

    async def extract_entities(
        self,
        content: str,
        entity_types: Optional[List[str]] = None,
    ) -> Dict[str, List[str]]:
        """
        Extract named entities from document content.

        Args:
            content: Document content
            entity_types: Types of entities to extract
                (default: people, organizations, locations, dates, money)

        Returns:
            Dict mapping entity types to lists of extracted entities

        Raises:
            AIServiceUnavailableException: If API is unavailable
        """
        if not settings.AI_ENTITY_EXTRACTION_ENABLED:
            raise AIAssistantException("AI entity extraction is disabled in settings")

        logger.info("Extracting entities", content_length=len(content))

        if entity_types is None:
            entity_types = ["people", "organizations", "locations", "dates", "money", "products"]

        prompt = f"""Please extract named entities from the following document content.

Entity types to extract: {', '.join(entity_types)}

Document content:
{content[:10000]}

Please provide the extracted entities as JSON with the following structure:
{{
    "people": ["person 1", "person 2"],
    "organizations": ["org 1", "org 2"],
    "locations": ["location 1"],
    "dates": ["date 1"],
    "money": ["amount 1"],
    "products": ["product 1"]
}}

Only include entity types that are found in the document."""

        try:
            response = await self._call_claude(prompt)
            entities = self._parse_json_response(response)

            # Filter to requested entity types
            filtered_entities = {
                k: v for k, v in entities.items() if k in entity_types
            }

            total_entities = sum(len(v) for v in filtered_entities.values())
            logger.info(
                "Entities extracted",
                total_count=total_entities,
                types=list(filtered_entities.keys()),
            )

            return filtered_entities

        except anthropic.APIError as e:
            return self._handle_api_error(e)

    async def classify_document(
        self,
        content: str,
        categories: Optional[List[str]] = None,
        include_confidence: bool = True,
    ) -> Dict[str, Any]:
        """
        Classify document into categories.

        Args:
            content: Document content
            categories: List of possible categories (if None, Claude suggests categories)
            include_confidence: Whether to include confidence scores

        Returns:
            Dict containing:
                - primary_category: Main category
                - categories: List of all applicable categories
                - confidence_scores: Dict mapping categories to confidence (0-1)
                - reasoning: Explanation of classification

        Raises:
            AIServiceUnavailableException: If API is unavailable
        """
        if not settings.AI_CLASSIFICATION_ENABLED:
            raise AIAssistantException("AI classification is disabled in settings")

        logger.info("Classifying document", content_length=len(content))

        if categories:
            category_instruction = f"Choose from these categories: {', '.join(categories)}"
        else:
            category_instruction = "Suggest appropriate categories based on the content"

        prompt = f"""Please classify the following document.

{category_instruction}

Document content:
{content[:10000]}

Please provide classification results as JSON:
{{
    "primary_category": "main category",
    "categories": ["category 1", "category 2"],
    "confidence_scores": {{"category 1": 0.95, "category 2": 0.75}},
    "reasoning": "explanation of why these categories apply"
}}"""

        try:
            response = await self._call_claude(prompt)
            classification = self._parse_json_response(response)

            if not include_confidence:
                classification.pop("confidence_scores", None)

            logger.info(
                "Document classified",
                primary_category=classification.get("primary_category"),
                categories_count=len(classification.get("categories", [])),
            )

            return classification

        except anthropic.APIError as e:
            return self._handle_api_error(e)

    async def suggest_tags(
        self,
        content: str,
        title: Optional[str] = None,
        existing_tags: Optional[List[str]] = None,
        max_tags: int = 10,
    ) -> List[str]:
        """
        Suggest relevant tags for a document.

        Args:
            content: Document content
            title: Document title (optional)
            existing_tags: Already existing tags in the system
            max_tags: Maximum number of tags to suggest

        Returns:
            List of suggested tags

        Raises:
            AIServiceUnavailableException: If API is unavailable
        """
        logger.info("Suggesting tags", content_length=len(content))

        title_context = f"Title: {title}\n\n" if title else ""
        existing_context = (
            f"Existing tags in system: {', '.join(existing_tags[:50])}\n\n"
            if existing_tags
            else ""
        )

        prompt = f"""Please suggest relevant tags for the following document.

{title_context}{existing_context}Document content:
{content[:10000]}

Provide {max_tags} relevant, concise tags that describe the document's content, topics, and themes.
Return the tags as a JSON array of strings:
["tag1", "tag2", "tag3"]

Keep tags short (1-3 words) and use lowercase."""

        try:
            response = await self._call_claude(prompt)
            tags = self._parse_json_response(response)

            if isinstance(tags, dict) and "tags" in tags:
                tags = tags["tags"]

            # Ensure we have a list
            if not isinstance(tags, list):
                tags = []

            # Normalize tags
            tags = [tag.lower().strip() for tag in tags if tag]
            tags = tags[:max_tags]

            logger.info("Tags suggested", count=len(tags))

            return tags

        except anthropic.APIError as e:
            return self._handle_api_error(e)

    async def generate_content_recommendations(
        self,
        content: str,
        all_documents: List[Dict[str, Any]],
        max_recommendations: int = 5,
    ) -> List[Dict[str, Any]]:
        """
        Generate recommendations for related documents.

        Args:
            content: Current document content
            all_documents: List of other documents with their metadata
            max_recommendations: Maximum number of recommendations

        Returns:
            List of recommended documents with relevance scores

        Raises:
            AIServiceUnavailableException: If API is unavailable
        """
        logger.info(
            "Generating content recommendations",
            content_length=len(content),
            candidate_count=len(all_documents),
        )

        # Create document summaries for comparison
        doc_summaries = []
        for i, doc in enumerate(all_documents[:50]):  # Limit to avoid token limits
            doc_summaries.append(
                f"{i}. {doc.get('title', 'Untitled')} - {doc.get('description', '')[:200]}"
            )

        summaries_text = "\n".join(doc_summaries)

        prompt = f"""Please analyze the following document and recommend related documents from the list.

Current document content:
{content[:5000]}

Available documents:
{summaries_text}

Please recommend up to {max_recommendations} most relevant documents and explain why they are related.

Return as JSON:
{{
    "recommendations": [
        {{
            "document_index": 0,
            "relevance_score": 0.95,
            "reason": "explanation of relevance"
        }}
    ]
}}"""

        try:
            response = await self._call_claude(prompt)
            result = self._parse_json_response(response)

            recommendations = []
            for rec in result.get("recommendations", [])[:max_recommendations]:
                idx = rec.get("document_index")
                if idx is not None and 0 <= idx < len(all_documents):
                    recommendations.append(
                        {
                            "document": all_documents[idx],
                            "relevance_score": rec.get("relevance_score", 0.5),
                            "reason": rec.get("reason", ""),
                        }
                    )

            logger.info("Recommendations generated", count=len(recommendations))

            return recommendations

        except anthropic.APIError as e:
            return self._handle_api_error(e)

    async def analyze_document_quality(
        self,
        content: str,
        check_grammar: bool = True,
        check_readability: bool = True,
        check_structure: bool = True,
    ) -> Dict[str, Any]:
        """
        Analyze document quality and provide improvement suggestions.

        Args:
            content: Document content
            check_grammar: Whether to check grammar
            check_readability: Whether to check readability
            check_structure: Whether to check structure

        Returns:
            Dict containing quality analysis and suggestions

        Raises:
            AIServiceUnavailableException: If API is unavailable
        """
        logger.info("Analyzing document quality", content_length=len(content))

        checks = []
        if check_grammar:
            checks.append("grammar and spelling")
        if check_readability:
            checks.append("readability and clarity")
        if check_structure:
            checks.append("document structure and organization")

        checks_text = ", ".join(checks)

        prompt = f"""Please analyze the quality of the following document.

Check for: {checks_text}

Document content:
{content[:10000]}

Provide analysis as JSON:
{{
    "overall_quality": "excellent|good|fair|poor",
    "quality_score": 0.85,
    "issues": [
        {{"type": "grammar", "severity": "minor", "description": "issue description"}},
        {{"type": "readability", "severity": "major", "description": "issue description"}}
    ],
    "suggestions": [
        "suggestion 1",
        "suggestion 2"
    ],
    "strengths": [
        "strength 1",
        "strength 2"
    ]
}}"""

        try:
            response = await self._call_claude(prompt)
            analysis = self._parse_json_response(response)

            logger.info(
                "Document quality analyzed",
                overall_quality=analysis.get("overall_quality"),
                issues_count=len(analysis.get("issues", [])),
            )

            return analysis

        except anthropic.APIError as e:
            return self._handle_api_error(e)

    async def answer_question_about_document(
        self,
        content: str,
        question: str,
    ) -> Dict[str, Any]:
        """
        Answer a specific question about document content.

        Args:
            content: Document content
            question: User's question

        Returns:
            Dict containing:
                - answer: Answer to the question
                - confidence: Confidence level (low, medium, high)
                - relevant_excerpts: Relevant parts of the document

        Raises:
            AIServiceUnavailableException: If API is unavailable
        """
        logger.info(
            "Answering question about document",
            content_length=len(content),
            question=question,
        )

        prompt = f"""Please answer the following question based on the document content.

Document content:
{content[:10000]}

Question: {question}

Provide your answer as JSON:
{{
    "answer": "your answer here",
    "confidence": "high|medium|low",
    "relevant_excerpts": ["excerpt 1", "excerpt 2"],
    "explanation": "brief explanation of how you arrived at this answer"
}}

If the answer cannot be found in the document, indicate this clearly."""

        try:
            response = await self._call_claude(prompt)
            result = self._parse_json_response(response)

            logger.info(
                "Question answered",
                confidence=result.get("confidence"),
                has_answer=bool(result.get("answer")),
            )

            return result

        except anthropic.APIError as e:
            return self._handle_api_error(e)

    async def _call_claude(self, prompt: str) -> str:
        """
        Call Claude API with the given prompt.

        Args:
            prompt: Prompt to send to Claude

        Returns:
            str: Response text from Claude

        Raises:
            AIServiceUnavailableException: If API call fails
        """
        try:
            message = self.client.messages.create(
                model=self.model,
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                messages=[{"role": "user", "content": prompt}],
            )

            # Extract text from response
            response_text = ""
            for block in message.content:
                if hasattr(block, "text"):
                    response_text += block.text

            return response_text

        except anthropic.APIConnectionError as e:
            logger.exception("Claude API connection error", error=str(e))
            raise AIServiceUnavailableException("Failed to connect to Claude API")

        except anthropic.APIError as e:
            logger.exception("Claude API error", error=str(e))
            raise

    def _parse_json_response(self, response: str) -> Dict[str, Any]:
        """
        Parse JSON from Claude's response.

        Args:
            response: Response text from Claude

        Returns:
            Dict: Parsed JSON data

        Raises:
            AIAssistantException: If JSON parsing fails
        """
        try:
            # Try to find JSON in the response
            # Claude sometimes wraps JSON in markdown code blocks
            json_match = re.search(r"```json\s*(.*?)\s*```", response, re.DOTALL)
            if json_match:
                json_str = json_match.group(1)
            else:
                # Try to find raw JSON
                json_match = re.search(r"\{.*\}", response, re.DOTALL)
                if json_match:
                    json_str = json_match.group(0)
                else:
                    json_str = response

            return json.loads(json_str)

        except json.JSONDecodeError as e:
            logger.exception("Failed to parse JSON response", error=str(e), response=response)
            raise AIAssistantException(f"Failed to parse AI response: {str(e)}")

    def _handle_api_error(self, error: anthropic.APIError) -> None:
        """
        Handle API errors and raise appropriate exceptions.

        Args:
            error: API error from Anthropic

        Raises:
            AIQuotaExceededException: If quota exceeded
            AIServiceUnavailableException: For other API errors
        """
        if isinstance(error, anthropic.RateLimitError):
            logger.error("Claude API rate limit exceeded", error=str(error))
            raise AIQuotaExceededException("AI service quota exceeded. Please try again later.")

        logger.exception("Claude API error", error=str(error))
        raise AIServiceUnavailableException(f"AI service error: {str(error)}")


class BatchAIProcessor:
    """
    Batch processor for AI operations on multiple documents.

    Handles efficient batch processing of AI operations with
    rate limiting and error handling.
    """

    def __init__(
        self,
        db_session: AsyncSession,
        ai_assistant: DocumentAIAssistant,
        batch_size: int = 10,
    ) -> None:
        """
        Initialize batch processor.

        Args:
            db_session: Database session
            ai_assistant: AI assistant instance
            batch_size: Number of documents to process in parallel
        """
        self.db = db_session
        self.ai_assistant = ai_assistant
        self.batch_size = batch_size

    async def batch_summarize(
        self,
        document_contents: List[Tuple[int, str]],
    ) -> Dict[int, Dict[str, Any]]:
        """
        Generate summaries for multiple documents.

        Args:
            document_contents: List of (document_id, content) tuples

        Returns:
            Dict mapping document IDs to summaries
        """
        logger.info("Starting batch summarization", count=len(document_contents))

        results = {}
        errors = {}

        for doc_id, content in document_contents:
            try:
                summary = await self.ai_assistant.summarize_document(content)
                results[doc_id] = summary
            except Exception as e:
                logger.exception("Failed to summarize document", doc_id=doc_id, error=str(e))
                errors[doc_id] = str(e)

        logger.info(
            "Batch summarization completed",
            success_count=len(results),
            error_count=len(errors),
        )

        return results

    async def batch_classify(
        self,
        document_contents: List[Tuple[int, str]],
        categories: Optional[List[str]] = None,
    ) -> Dict[int, Dict[str, Any]]:
        """
        Classify multiple documents.

        Args:
            document_contents: List of (document_id, content) tuples
            categories: List of possible categories

        Returns:
            Dict mapping document IDs to classifications
        """
        logger.info("Starting batch classification", count=len(document_contents))

        results = {}
        errors = {}

        for doc_id, content in document_contents:
            try:
                classification = await self.ai_assistant.classify_document(
                    content, categories=categories
                )
                results[doc_id] = classification
            except Exception as e:
                logger.exception("Failed to classify document", doc_id=doc_id, error=str(e))
                errors[doc_id] = str(e)

        logger.info(
            "Batch classification completed",
            success_count=len(results),
            error_count=len(errors),
        )

        return results

    async def batch_extract_entities(
        self,
        document_contents: List[Tuple[int, str]],
        entity_types: Optional[List[str]] = None,
    ) -> Dict[int, Dict[str, List[str]]]:
        """
        Extract entities from multiple documents.

        Args:
            document_contents: List of (document_id, content) tuples
            entity_types: Types of entities to extract

        Returns:
            Dict mapping document IDs to extracted entities
        """
        logger.info("Starting batch entity extraction", count=len(document_contents))

        results = {}
        errors = {}

        for doc_id, content in document_contents:
            try:
                entities = await self.ai_assistant.extract_entities(
                    content, entity_types=entity_types
                )
                results[doc_id] = entities
            except Exception as e:
                logger.exception("Failed to extract entities", doc_id=doc_id, error=str(e))
                errors[doc_id] = str(e)

        logger.info(
            "Batch entity extraction completed",
            success_count=len(results),
            error_count=len(errors),
        )

        return results
