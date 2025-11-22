"""
Wiki AI Assistant Service

AI-powered features for the NEXUS Wiki System including:
- Content summarization and improvement suggestions
- Auto-linking suggestions based on content analysis
- Question answering over wiki content
- Automatic tag suggestions
- Related page recommendations
- Content outline generation
- Grammar and style checking
- Translation support
- Smart search query expansion
- Integration with Claude and GPT-4 models

Author: NEXUS Platform Team
"""

import re
import json
import hashlib
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set, Tuple, Any
from collections import defaultdict
from functools import lru_cache
from sqlalchemy import and_, or_, func, desc
from sqlalchemy.orm import Session, joinedload
from sqlalchemy.exc import SQLAlchemyError

from app.utils import get_logger
from app.config import settings
from modules.wiki.models import WikiPage, WikiTag, WikiLink, WikiCategory
from modules.wiki.wiki_types import (
    PageStatus, ContentFormat, LinkType,
    WikiPage as WikiPageSchema
)

logger = get_logger(__name__)


# ============================================================================
# TYPE DEFINITIONS
# ============================================================================

class AIModel:
    """Supported AI models."""
    CLAUDE_SONNET = "claude-3-5-sonnet-20241022"
    CLAUDE_HAIKU = "claude-3-5-haiku-20241022"
    GPT4 = "gpt-4"
    GPT4_TURBO = "gpt-4-turbo"


class AITaskType:
    """Types of AI tasks."""
    SUMMARIZE = "summarize"
    SUGGEST_LINKS = "suggest_links"
    SUGGEST_TAGS = "suggest_tags"
    IMPROVE_CONTENT = "improve_content"
    ANSWER_QUESTION = "answer_question"
    GENERATE_OUTLINE = "generate_outline"
    CHECK_GRAMMAR = "check_grammar"
    TRANSLATE = "translate"
    FIND_RELATED = "find_related"
    EXPAND_QUERY = "expand_query"


# ============================================================================
# AI ASSISTANT SERVICE
# ============================================================================

class AIAssistant:
    """
    AI-powered assistant for wiki content analysis and enhancement.

    Provides intelligent features including content summarization, auto-linking,
    tag suggestions, question answering, and more using Claude/GPT-4 models.
    """

    def __init__(self, db: Session, model: str = AIModel.CLAUDE_SONNET):
        """
        Initialize AIAssistant.

        Args:
            db: SQLAlchemy database session
            model: AI model to use (default: Claude Sonnet)

        Example:
            >>> assistant = AIAssistant(db)
            >>> summary = assistant.summarize_content(page_id=123)
        """
        self.db = db
        self.model = model
        self._response_cache: Dict[str, Tuple[Any, datetime]] = {}
        self._cache_ttl = timedelta(hours=24)

    # ========================================================================
    # CONTENT SUMMARIZATION
    # ========================================================================

    def summarize_content(
        self,
        page_id: Optional[int] = None,
        content: Optional[str] = None,
        max_length: int = 500,
        use_cache: bool = True
    ) -> Optional[str]:
        """
        Generate a concise summary of wiki page content.

        Args:
            page_id: Wiki page ID to summarize
            content: Direct content to summarize (if page_id not provided)
            max_length: Maximum summary length in characters
            use_cache: Whether to use cached responses

        Returns:
            Summary text or None if failed

        Example:
            >>> assistant = AIAssistant(db)
            >>> summary = assistant.summarize_content(page_id=123, max_length=200)
            >>> print(summary)
            "This page covers the basics of Python programming..."
        """
        try:
            # Get content
            if page_id:
                page = self.db.query(WikiPage).filter(WikiPage.id == page_id).first()
                if not page:
                    logger.warning(f"Page {page_id} not found for summarization")
                    return None
                content = page.content
                title = page.title
            else:
                title = "Content"

            if not content or len(content.strip()) < 50:
                logger.warning("Content too short for summarization")
                return None

            # Check cache
            cache_key = self._get_cache_key(AITaskType.SUMMARIZE, content, max_length)
            if use_cache:
                cached = self._get_cached_response(cache_key)
                if cached:
                    return cached

            # Build prompt
            prompt = f"""Summarize the following wiki page content in {max_length} characters or less.
Focus on the main points and key information.

Title: {title}

Content:
{content[:5000]}  # Limit content length for API

Provide a concise, informative summary:"""

            # Call AI model
            summary = self._call_ai_model(prompt, max_tokens=500)

            if summary:
                # Cache response
                self._cache_response(cache_key, summary)
                logger.info(f"Generated summary for content (length: {len(summary)})")
                return summary.strip()

            return None

        except Exception as e:
            logger.error(f"Error summarizing content: {str(e)}", exc_info=True)
            return None

    # ========================================================================
    # AUTO-LINKING SUGGESTIONS
    # ========================================================================

    def suggest_links(
        self,
        page_id: int,
        min_confidence: float = 0.7,
        max_suggestions: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Analyze content and suggest internal links to other pages.

        Args:
            page_id: Wiki page ID to analyze
            min_confidence: Minimum confidence score (0.0-1.0)
            max_suggestions: Maximum number of suggestions

        Returns:
            List of link suggestions with confidence scores

        Example:
            >>> assistant = AIAssistant(db)
            >>> suggestions = assistant.suggest_links(page_id=123, min_confidence=0.8)
            >>> for link in suggestions:
            ...     print(f"{link['text']} -> {link['target_page']} ({link['confidence']})")
        """
        try:
            # Get source page
            page = self.db.query(WikiPage).filter(
                WikiPage.id == page_id,
                WikiPage.is_deleted == False
            ).first()

            if not page:
                logger.warning(f"Page {page_id} not found for link suggestions")
                return []

            # Get all potential target pages (same namespace or public)
            potential_targets = self.db.query(WikiPage).filter(
                WikiPage.id != page_id,
                WikiPage.is_deleted == False,
                WikiPage.status == PageStatus.PUBLISHED,
                or_(
                    WikiPage.namespace == page.namespace,
                    WikiPage.namespace.is_(None)
                )
            ).all()

            if not potential_targets:
                return []

            # Build context for AI
            context = {
                "source_title": page.title,
                "source_content": page.content[:3000],
                "potential_links": [
                    {
                        "id": p.id,
                        "title": p.title,
                        "summary": p.summary or p.content[:200]
                    }
                    for p in potential_targets[:50]  # Limit to 50 candidates
                ]
            }

            # Build prompt
            prompt = f"""Analyze the following wiki page and suggest relevant internal links.

Source Page: {context['source_title']}
Content: {context['source_content']}

Available pages to link to:
{json.dumps(context['potential_links'], indent=2)}

For each suggestion, provide:
1. The exact text in the source content to link
2. The target page ID
3. A confidence score (0.0-1.0)
4. Brief reasoning

Return as JSON array:
[
  {{
    "text": "machine learning",
    "target_page_id": 45,
    "confidence": 0.9,
    "reason": "Directly related topic mentioned in context"
  }}
]

Only suggest links with confidence >= {min_confidence}. Maximum {max_suggestions} suggestions.
"""

            # Call AI model
            response = self._call_ai_model(prompt, max_tokens=2000)

            if not response:
                return []

            # Parse JSON response
            try:
                suggestions = json.loads(self._extract_json(response))

                # Validate and enrich suggestions
                validated_suggestions = []
                for sugg in suggestions[:max_suggestions]:
                    if sugg.get("confidence", 0) >= min_confidence:
                        # Get target page details
                        target = next(
                            (p for p in potential_targets if p.id == sugg["target_page_id"]),
                            None
                        )
                        if target:
                            validated_suggestions.append({
                                "text": sugg["text"],
                                "target_page_id": target.id,
                                "target_title": target.title,
                                "target_slug": target.slug,
                                "confidence": sugg["confidence"],
                                "reason": sugg.get("reason", ""),
                                "position": page.content.find(sugg["text"])
                            })

                logger.info(f"Generated {len(validated_suggestions)} link suggestions for page {page_id}")
                return validated_suggestions

            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse AI response as JSON: {str(e)}")
                return []

        except Exception as e:
            logger.error(f"Error generating link suggestions: {str(e)}", exc_info=True)
            return []

    # ========================================================================
    # TAG SUGGESTIONS
    # ========================================================================

    def suggest_tags(
        self,
        page_id: Optional[int] = None,
        content: Optional[str] = None,
        title: Optional[str] = None,
        max_tags: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Suggest relevant tags based on content analysis.

        Args:
            page_id: Wiki page ID to analyze
            content: Direct content to analyze (if page_id not provided)
            title: Page title (if page_id not provided)
            max_tags: Maximum number of tag suggestions

        Returns:
            List of tag suggestions with confidence scores

        Example:
            >>> assistant = AIAssistant(db)
            >>> tags = assistant.suggest_tags(page_id=123, max_tags=5)
            >>> for tag in tags:
            ...     print(f"{tag['name']} ({tag['confidence']})")
        """
        try:
            # Get content
            if page_id:
                page = self.db.query(WikiPage).filter(WikiPage.id == page_id).first()
                if not page:
                    logger.warning(f"Page {page_id} not found for tag suggestions")
                    return []
                content = page.content
                title = page.title
            elif not content:
                logger.warning("No content provided for tag suggestions")
                return []

            # Get existing tags for reference
            existing_tags = self.db.query(WikiTag).order_by(
                desc(WikiTag.usage_count)
            ).limit(100).all()

            existing_tag_names = [tag.name for tag in existing_tags]

            # Build prompt
            prompt = f"""Analyze the following wiki page and suggest {max_tags} relevant tags.

Title: {title}
Content: {content[:3000]}

Existing popular tags in the system:
{', '.join(existing_tag_names[:30])}

Suggest tags that:
1. Accurately describe the content
2. Are concise (1-3 words)
3. Use existing tags when appropriate
4. Create new tags when existing ones don't fit

Return as JSON array:
[
  {{
    "name": "python",
    "confidence": 0.95,
    "is_new": false,
    "reason": "Main programming language discussed"
  }}
]

Maximum {max_tags} tags, ordered by relevance.
"""

            # Call AI model
            response = self._call_ai_model(prompt, max_tokens=1000)

            if not response:
                return []

            # Parse JSON response
            try:
                suggestions = json.loads(self._extract_json(response))

                validated_suggestions = []
                for sugg in suggestions[:max_tags]:
                    tag_name = sugg["name"].lower().strip()
                    validated_suggestions.append({
                        "name": tag_name,
                        "confidence": sugg.get("confidence", 0.5),
                        "is_new": sugg.get("is_new", True),
                        "reason": sugg.get("reason", "")
                    })

                logger.info(f"Generated {len(validated_suggestions)} tag suggestions")
                return validated_suggestions

            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse AI response as JSON: {str(e)}")
                return []

        except Exception as e:
            logger.error(f"Error generating tag suggestions: {str(e)}", exc_info=True)
            return []

    # ========================================================================
    # CONTENT IMPROVEMENT
    # ========================================================================

    def suggest_improvements(
        self,
        page_id: int,
        focus_areas: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Analyze content and suggest improvements.

        Args:
            page_id: Wiki page ID to analyze
            focus_areas: Specific areas to focus on (structure, clarity, completeness, etc.)

        Returns:
            Dictionary of improvement suggestions

        Example:
            >>> assistant = AIAssistant(db)
            >>> improvements = assistant.suggest_improvements(
            ...     page_id=123,
            ...     focus_areas=['structure', 'clarity']
            ... )
            >>> print(improvements['overall_score'])
            >>> for item in improvements['suggestions']:
            ...     print(f"- {item['title']}: {item['description']}")
        """
        try:
            page = self.db.query(WikiPage).filter(WikiPage.id == page_id).first()
            if not page:
                logger.warning(f"Page {page_id} not found for improvement suggestions")
                return {}

            focus = focus_areas or ['structure', 'clarity', 'completeness', 'formatting']

            # Build prompt
            prompt = f"""Analyze the following wiki page and suggest improvements.

Title: {page.title}
Content: {page.content}

Focus areas: {', '.join(focus)}

Provide analysis and suggestions in JSON format:
{{
  "overall_score": 7.5,
  "strengths": ["Well-structured", "Clear examples"],
  "suggestions": [
    {{
      "category": "structure",
      "priority": "high",
      "title": "Add table of contents",
      "description": "The page would benefit from a TOC for better navigation",
      "example": "Use the {{toc}} macro at the beginning"
    }}
  ],
  "missing_elements": ["code examples", "diagrams"],
  "readability_score": 8.0,
  "seo_keywords": ["python", "tutorial", "beginners"]
}}

Provide actionable, specific suggestions.
"""

            # Call AI model
            response = self._call_ai_model(prompt, max_tokens=2000)

            if not response:
                return {}

            # Parse JSON response
            try:
                improvements = json.loads(self._extract_json(response))
                logger.info(f"Generated improvement suggestions for page {page_id}")
                return improvements

            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse AI response as JSON: {str(e)}")
                return {}

        except Exception as e:
            logger.error(f"Error generating improvement suggestions: {str(e)}", exc_info=True)
            return {}

    # ========================================================================
    # QUESTION ANSWERING
    # ========================================================================

    def answer_question(
        self,
        question: str,
        page_id: Optional[int] = None,
        search_all: bool = False,
        max_pages: int = 5
    ) -> Dict[str, Any]:
        """
        Answer questions about wiki content using AI.

        Args:
            question: User's question
            page_id: Specific page to search (optional)
            search_all: Search all pages for relevant content
            max_pages: Maximum pages to consider when search_all=True

        Returns:
            Answer with source references

        Example:
            >>> assistant = AIAssistant(db)
            >>> answer = assistant.answer_question(
            ...     question="How do I install Python?",
            ...     search_all=True
            ... )
            >>> print(answer['answer'])
            >>> print(f"Sources: {answer['sources']}")
        """
        try:
            context_pages = []

            if page_id:
                # Answer from specific page
                page = self.db.query(WikiPage).filter(WikiPage.id == page_id).first()
                if page:
                    context_pages.append(page)
            elif search_all:
                # Search for relevant pages
                # Simple keyword-based search (could be enhanced with semantic search)
                keywords = self._extract_keywords(question)

                query = self.db.query(WikiPage).filter(
                    WikiPage.is_deleted == False,
                    WikiPage.status == PageStatus.PUBLISHED
                )

                # Add text search filter
                search_conditions = []
                for keyword in keywords:
                    search_conditions.append(
                        or_(
                            WikiPage.title.ilike(f"%{keyword}%"),
                            WikiPage.content.ilike(f"%{keyword}%"),
                            WikiPage.summary.ilike(f"%{keyword}%")
                        )
                    )

                if search_conditions:
                    query = query.filter(or_(*search_conditions))

                context_pages = query.limit(max_pages).all()

            if not context_pages:
                return {
                    "answer": "I don't have enough information to answer this question.",
                    "confidence": 0.0,
                    "sources": []
                }

            # Build context
            context = "\n\n---\n\n".join([
                f"Page: {page.title}\n{page.content[:2000]}"
                for page in context_pages
            ])

            # Build prompt
            prompt = f"""Answer the following question based on the wiki content provided.

Question: {question}

Context:
{context}

Provide a clear, accurate answer based on the information available. If the context doesn't contain enough information, say so. Include references to the source pages when possible.

Answer:"""

            # Call AI model
            response = self._call_ai_model(prompt, max_tokens=1000)

            if response:
                return {
                    "answer": response.strip(),
                    "confidence": 0.8,  # Could implement confidence scoring
                    "sources": [
                        {
                            "page_id": page.id,
                            "title": page.title,
                            "slug": page.slug
                        }
                        for page in context_pages
                    ],
                    "question": question
                }

            return {
                "answer": "Unable to generate an answer at this time.",
                "confidence": 0.0,
                "sources": []
            }

        except Exception as e:
            logger.error(f"Error answering question: {str(e)}", exc_info=True)
            return {
                "answer": f"Error: {str(e)}",
                "confidence": 0.0,
                "sources": []
            }

    # ========================================================================
    # RELATED PAGE SUGGESTIONS
    # ========================================================================

    def find_related_pages(
        self,
        page_id: int,
        max_results: int = 10,
        min_relevance: float = 0.6
    ) -> List[Dict[str, Any]]:
        """
        Find pages related to the given page based on content similarity.

        Args:
            page_id: Source page ID
            max_results: Maximum number of related pages
            min_relevance: Minimum relevance score (0.0-1.0)

        Returns:
            List of related pages with relevance scores

        Example:
            >>> assistant = AIAssistant(db)
            >>> related = assistant.find_related_pages(page_id=123, max_results=5)
            >>> for page in related:
            ...     print(f"{page['title']} - Relevance: {page['relevance']}")
        """
        try:
            # Get source page
            page = self.db.query(WikiPage).filter(WikiPage.id == page_id).first()
            if not page:
                logger.warning(f"Page {page_id} not found for related pages")
                return []

            # Get candidate pages (same category or namespace)
            candidates = self.db.query(WikiPage).filter(
                WikiPage.id != page_id,
                WikiPage.is_deleted == False,
                WikiPage.status == PageStatus.PUBLISHED,
                or_(
                    WikiPage.category_id == page.category_id,
                    WikiPage.namespace == page.namespace
                )
            ).limit(50).all()

            if not candidates:
                return []

            # Use AI to determine relevance
            prompt = f"""Analyze the source page and rank the candidate pages by relevance.

Source Page:
Title: {page.title}
Content: {page.content[:2000]}

Candidate Pages:
{json.dumps([
    {"id": p.id, "title": p.title, "summary": p.summary or p.content[:200]}
    for p in candidates
], indent=2)}

Return JSON array of related pages with relevance scores (0.0-1.0):
[
  {{
    "page_id": 45,
    "relevance": 0.85,
    "reason": "Discusses related concepts"
  }}
]

Only include pages with relevance >= {min_relevance}. Maximum {max_results} results.
"""

            # Call AI model
            response = self._call_ai_model(prompt, max_tokens=2000)

            if not response:
                return []

            # Parse response
            try:
                results = json.loads(self._extract_json(response))

                related_pages = []
                for result in results[:max_results]:
                    candidate = next(
                        (p for p in candidates if p.id == result["page_id"]),
                        None
                    )
                    if candidate and result["relevance"] >= min_relevance:
                        related_pages.append({
                            "page_id": candidate.id,
                            "title": candidate.title,
                            "slug": candidate.slug,
                            "summary": candidate.summary,
                            "relevance": result["relevance"],
                            "reason": result.get("reason", "")
                        })

                logger.info(f"Found {len(related_pages)} related pages for page {page_id}")
                return related_pages

            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse AI response as JSON: {str(e)}")
                return []

        except Exception as e:
            logger.error(f"Error finding related pages: {str(e)}", exc_info=True)
            return []

    # ========================================================================
    # CONTENT OUTLINE GENERATION
    # ========================================================================

    def generate_outline(
        self,
        topic: str,
        target_audience: str = "general",
        depth: int = 2,
        include_examples: bool = True
    ) -> Dict[str, Any]:
        """
        Generate a content outline for a new page.

        Args:
            topic: Topic for the page
            target_audience: Target audience (general, technical, beginner, etc.)
            depth: Outline depth (1-3 levels)
            include_examples: Whether to include example content

        Returns:
            Structured outline with sections and subsections

        Example:
            >>> assistant = AIAssistant(db)
            >>> outline = assistant.generate_outline(
            ...     topic="Python Data Analysis",
            ...     target_audience="beginner",
            ...     depth=2
            ... )
            >>> print(json.dumps(outline, indent=2))
        """
        try:
            prompt = f"""Generate a comprehensive wiki page outline for the following topic.

Topic: {topic}
Target Audience: {target_audience}
Depth: {depth} levels
Include Examples: {include_examples}

Return a structured outline in JSON format:
{{
  "title": "Page Title",
  "summary": "Brief summary",
  "sections": [
    {{
      "title": "Introduction",
      "content_hints": "What to cover in this section",
      "subsections": [
        {{
          "title": "Subsection",
          "content_hints": "Details"
        }}
      ]
    }}
  ],
  "suggested_tags": ["tag1", "tag2"],
  "prerequisites": ["Link to prerequisite pages"],
  "next_steps": ["Link to follow-up topics"]
}}

Create a well-structured, comprehensive outline.
"""

            # Call AI model
            response = self._call_ai_model(prompt, max_tokens=2000)

            if not response:
                return {}

            # Parse response
            try:
                outline = json.loads(self._extract_json(response))
                logger.info(f"Generated outline for topic: {topic}")
                return outline

            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse AI response as JSON: {str(e)}")
                return {}

        except Exception as e:
            logger.error(f"Error generating outline: {str(e)}", exc_info=True)
            return {}

    # ========================================================================
    # GRAMMAR AND STYLE CHECKING
    # ========================================================================

    def check_grammar_and_style(
        self,
        content: str,
        style_guide: str = "technical"
    ) -> Dict[str, Any]:
        """
        Check content for grammar, spelling, and style issues.

        Args:
            content: Content to check
            style_guide: Style guide to follow (technical, casual, formal)

        Returns:
            List of issues with suggestions

        Example:
            >>> assistant = AIAssistant(db)
            >>> results = assistant.check_grammar_and_style(
            ...     content="This are a test.",
            ...     style_guide="technical"
            ... )
            >>> for issue in results['issues']:
            ...     print(f"{issue['type']}: {issue['message']}")
        """
        try:
            prompt = f"""Check the following content for grammar, spelling, and style issues.

Style Guide: {style_guide}

Content:
{content[:4000]}

Return issues in JSON format:
{{
  "overall_quality": 8.5,
  "issues": [
    {{
      "type": "grammar",
      "severity": "high",
      "line": 5,
      "original": "This are a test",
      "suggestion": "This is a test",
      "message": "Subject-verb agreement error"
    }}
  ],
  "style_suggestions": [
    {{
      "message": "Consider using active voice",
      "examples": ["Change 'was written' to 'wrote'"]
    }}
  ],
  "readability_score": 7.5
}}

Focus on actionable improvements.
"""

            # Call AI model
            response = self._call_ai_model(prompt, max_tokens=2000)

            if not response:
                return {}

            # Parse response
            try:
                results = json.loads(self._extract_json(response))
                logger.info(f"Checked grammar and style, found {len(results.get('issues', []))} issues")
                return results

            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse AI response as JSON: {str(e)}")
                return {}

        except Exception as e:
            logger.error(f"Error checking grammar and style: {str(e)}", exc_info=True)
            return {}

    # ========================================================================
    # TRANSLATION
    # ========================================================================

    def translate_content(
        self,
        page_id: Optional[int] = None,
        content: Optional[str] = None,
        target_language: str = "es",
        preserve_formatting: bool = True
    ) -> Optional[str]:
        """
        Translate content to another language.

        Args:
            page_id: Page ID to translate
            content: Direct content to translate
            target_language: Target language code (es, fr, de, etc.)
            preserve_formatting: Preserve markdown formatting

        Returns:
            Translated content

        Example:
            >>> assistant = AIAssistant(db)
            >>> translated = assistant.translate_content(
            ...     page_id=123,
            ...     target_language="es"
            ... )
            >>> print(translated)
        """
        try:
            # Get content
            if page_id:
                page = self.db.query(WikiPage).filter(WikiPage.id == page_id).first()
                if not page:
                    logger.warning(f"Page {page_id} not found for translation")
                    return None
                content = page.content
            elif not content:
                logger.warning("No content provided for translation")
                return None

            prompt = f"""Translate the following content to {target_language}.

{"Preserve all markdown formatting (headers, links, code blocks, etc.)." if preserve_formatting else ""}

Content:
{content[:4000]}

Provide only the translated content, maintaining the same structure:"""

            # Call AI model
            response = self._call_ai_model(prompt, max_tokens=4000)

            if response:
                logger.info(f"Translated content to {target_language}")
                return response.strip()

            return None

        except Exception as e:
            logger.error(f"Error translating content: {str(e)}", exc_info=True)
            return None

    # ========================================================================
    # SEARCH QUERY EXPANSION
    # ========================================================================

    def expand_search_query(
        self,
        query: str,
        max_expansions: int = 5
    ) -> List[str]:
        """
        Expand a search query with synonyms and related terms.

        Args:
            query: Original search query
            max_expansions: Maximum number of expanded queries

        Returns:
            List of expanded query variations

        Example:
            >>> assistant = AIAssistant(db)
            >>> expansions = assistant.expand_search_query("python tutorial")
            >>> print(expansions)
            ['python guide', 'python learning', 'python introduction', ...]
        """
        try:
            prompt = f"""Expand the following search query with synonyms and related terms.

Original Query: {query}

Generate {max_expansions} alternative search queries that would find similar or related content.
Return as JSON array:
["alternative query 1", "alternative query 2", ...]

Focus on practical variations that maintain the original intent.
"""

            # Call AI model
            response = self._call_ai_model(prompt, max_tokens=500)

            if not response:
                return []

            # Parse response
            try:
                expansions = json.loads(self._extract_json(response))
                logger.info(f"Expanded query '{query}' into {len(expansions)} variations")
                return expansions[:max_expansions]

            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse AI response as JSON: {str(e)}")
                return []

        except Exception as e:
            logger.error(f"Error expanding search query: {str(e)}", exc_info=True)
            return []

    # ========================================================================
    # AI MODEL INTEGRATION
    # ========================================================================

    def _call_ai_model(
        self,
        prompt: str,
        max_tokens: int = 1000,
        temperature: float = 0.7
    ) -> Optional[str]:
        """
        Call the configured AI model (Claude or GPT-4).

        Args:
            prompt: Prompt to send to the model
            max_tokens: Maximum tokens in response
            temperature: Model temperature (0.0-1.0)

        Returns:
            Model response text
        """
        try:
            if self.model.startswith("claude"):
                return self._call_claude(prompt, max_tokens, temperature)
            elif self.model.startswith("gpt"):
                return self._call_gpt4(prompt, max_tokens, temperature)
            else:
                logger.error(f"Unsupported model: {self.model}")
                return None

        except Exception as e:
            logger.error(f"Error calling AI model: {str(e)}", exc_info=True)
            return None

    def _call_claude(
        self,
        prompt: str,
        max_tokens: int,
        temperature: float
    ) -> Optional[str]:
        """Call Anthropic Claude API."""
        try:
            # This is a placeholder - actual implementation would use Anthropic SDK
            # Example implementation:
            # from anthropic import Anthropic
            # client = Anthropic(api_key=settings.anthropic.api_key)
            # response = client.messages.create(
            #     model=self.model,
            #     max_tokens=max_tokens,
            #     temperature=temperature,
            #     messages=[{"role": "user", "content": prompt}]
            # )
            # return response.content[0].text

            logger.warning("Claude API integration not implemented - returning mock response")
            return None

        except Exception as e:
            logger.error(f"Error calling Claude API: {str(e)}", exc_info=True)
            return None

    def _call_gpt4(
        self,
        prompt: str,
        max_tokens: int,
        temperature: float
    ) -> Optional[str]:
        """Call OpenAI GPT-4 API."""
        try:
            # This is a placeholder - actual implementation would use OpenAI SDK
            # Example implementation:
            # from openai import OpenAI
            # client = OpenAI(api_key=settings.openai.api_key)
            # response = client.chat.completions.create(
            #     model=self.model,
            #     max_tokens=max_tokens,
            #     temperature=temperature,
            #     messages=[{"role": "user", "content": prompt}]
            # )
            # return response.choices[0].message.content

            logger.warning("GPT-4 API integration not implemented - returning mock response")
            return None

        except Exception as e:
            logger.error(f"Error calling GPT-4 API: {str(e)}", exc_info=True)
            return None

    # ========================================================================
    # UTILITY METHODS
    # ========================================================================

    def _get_cache_key(self, task_type: str, *args) -> str:
        """Generate cache key for AI responses."""
        content = f"{task_type}:{'|'.join(str(arg) for arg in args)}"
        return hashlib.sha256(content.encode()).hexdigest()

    def _get_cached_response(self, cache_key: str) -> Optional[Any]:
        """Get cached AI response if still valid."""
        if cache_key in self._response_cache:
            response, timestamp = self._response_cache[cache_key]
            if datetime.utcnow() - timestamp < self._cache_ttl:
                logger.debug(f"Cache hit for key: {cache_key[:16]}...")
                return response
            else:
                # Remove expired cache entry
                del self._response_cache[cache_key]
        return None

    def _cache_response(self, cache_key: str, response: Any) -> None:
        """Cache AI response with timestamp."""
        self._response_cache[cache_key] = (response, datetime.utcnow())
        logger.debug(f"Cached response for key: {cache_key[:16]}...")

    def _extract_json(self, text: str) -> str:
        """Extract JSON from AI response text."""
        # Try to find JSON in markdown code blocks
        json_match = re.search(r'```(?:json)?\s*(\{[\s\S]*?\}|\[[\s\S]*?\])\s*```', text)
        if json_match:
            return json_match.group(1)

        # Try to find raw JSON
        json_match = re.search(r'(\{[\s\S]*\}|\[[\s\S]*\])', text)
        if json_match:
            return json_match.group(1)

        return text

    def _extract_keywords(self, text: str, max_keywords: int = 5) -> List[str]:
        """Extract keywords from text for search."""
        # Simple keyword extraction (could use more sophisticated NLP)
        # Remove common words
        stop_words = {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
            'of', 'with', 'by', 'from', 'is', 'are', 'was', 'were', 'how', 'what',
            'when', 'where', 'why', 'who', 'which', 'do', 'does', 'did'
        }

        words = re.findall(r'\b\w+\b', text.lower())
        keywords = [w for w in words if w not in stop_words and len(w) > 2]

        # Return unique keywords
        return list(dict.fromkeys(keywords))[:max_keywords]

    def clear_cache(self) -> None:
        """Clear the response cache."""
        self._response_cache.clear()
        logger.info("AI response cache cleared")

    def get_cache_stats(self) -> Dict[str, int]:
        """Get cache statistics."""
        total = len(self._response_cache)
        expired = sum(
            1 for _, timestamp in self._response_cache.values()
            if datetime.utcnow() - timestamp >= self._cache_ttl
        )
        return {
            "total_entries": total,
            "expired_entries": expired,
            "active_entries": total - expired
        }
