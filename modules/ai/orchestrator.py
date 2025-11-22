"""
AI Orchestrator - Smart Model Router

Intelligently routes requests to Claude, GPT-4, or Gemini based on:
- Task type and complexity
- Response quality requirements
- Speed requirements
- Cost optimization
- Context window size

Features:
- Automatic model selection
- Fallback handling
- Load balancing
- A/B testing support
- Cost tracking
- Response caching
"""

import asyncio
from typing import Dict, List, Optional, Any, AsyncIterator
from enum import Enum
from datetime import datetime
import random

from .claude_client import ClaudeClient
from .openai_client import OpenAIClient
from .gemini_client import GeminiClient
from .cost_tracker import cost_tracker
from .cache_manager import cache_manager
from .context_manager import context_manager
from .prompt_templates import prompt_builder


class TaskType(str, Enum):
    """Task types for model selection."""
    WRITING = "writing"
    CODING = "coding"
    ANALYSIS = "analysis"
    CHAT = "chat"
    TRANSLATION = "translation"
    SUMMARIZATION = "summarization"
    IMAGE_ANALYSIS = "image_analysis"
    DATA_PROCESSING = "data_processing"
    LONG_DOCUMENT = "long_document"


class QualityLevel(str, Enum):
    """Quality requirements for responses."""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class SpeedRequirement(str, Enum):
    """Speed requirements for responses."""
    FAST = "fast"
    BALANCED = "balanced"
    QUALITY = "quality"


class CostOptimization(str, Enum):
    """Cost optimization strategies."""
    MINIMIZE = "minimize"
    BALANCED = "balanced"
    QUALITY = "quality"


class AIOrchestrator:
    """
    Intelligent AI orchestration system.

    Routes requests to the optimal model based on multiple factors,
    handles fallbacks, caching, and cost tracking.
    """

    def __init__(
        self,
        claude_api_key: Optional[str] = None,
        openai_api_key: Optional[str] = None,
        google_api_key: Optional[str] = None,
    ):
        """
        Initialize orchestrator with AI clients.

        Args:
            claude_api_key: Anthropic API key
            openai_api_key: OpenAI API key
            google_api_key: Google API key
        """
        # Initialize clients (lazy loading - only create if API key provided)
        self.claude_client = None
        self.openai_client = None
        self.gemini_client = None

        try:
            if claude_api_key or True:  # Try with env var
                self.claude_client = ClaudeClient(claude_api_key)
        except Exception:
            pass

        try:
            if openai_api_key or True:
                self.openai_client = OpenAIClient(openai_api_key)
        except Exception:
            pass

        try:
            if google_api_key or True:
                self.gemini_client = GeminiClient(google_api_key)
        except Exception:
            pass

        # Model selection rules
        self.model_rules = self._initialize_model_rules()

        # A/B testing configuration
        self.ab_test_enabled = False
        self.ab_test_split = 0.5  # 50/50 split

    def _initialize_model_rules(self) -> Dict:
        """
        Initialize model selection rules.

        Returns:
            Dictionary of task types to recommended models
        """
        return {
            # Quick chat, simple Q&A -> GPT-3.5-turbo (fast, cheap)
            (TaskType.CHAT, QualityLevel.LOW, SpeedRequirement.FAST): {
                "primary": ("openai", OpenAIClient.GPT_35_TURBO),
                "fallback": ("claude", ClaudeClient.HAIKU),
            },

            # Writing, creative content -> Claude Sonnet (quality)
            (TaskType.WRITING, QualityLevel.HIGH, SpeedRequirement.QUALITY): {
                "primary": ("claude", ClaudeClient.SONNET),
                "fallback": ("openai", OpenAIClient.GPT_4O),
            },

            # Complex reasoning -> Claude Opus (best quality)
            (TaskType.ANALYSIS, QualityLevel.HIGH, SpeedRequirement.QUALITY): {
                "primary": ("claude", ClaudeClient.OPUS),
                "fallback": ("openai", OpenAIClient.GPT_4_TURBO),
            },

            # Code generation -> GPT-4 (strong at code)
            (TaskType.CODING, QualityLevel.HIGH, SpeedRequirement.BALANCED): {
                "primary": ("openai", OpenAIClient.GPT_4O),
                "fallback": ("claude", ClaudeClient.SONNET),
            },

            # Long document analysis -> Gemini Pro (2M context)
            (TaskType.LONG_DOCUMENT, QualityLevel.MEDIUM, SpeedRequirement.BALANCED): {
                "primary": ("gemini", GeminiClient.GEMINI_1_5_PRO),
                "fallback": ("claude", ClaudeClient.SONNET),
            },

            # Image analysis -> GPT-4V or Claude
            (TaskType.IMAGE_ANALYSIS, QualityLevel.HIGH, SpeedRequirement.BALANCED): {
                "primary": ("openai", OpenAIClient.GPT_4O),
                "fallback": ("claude", ClaudeClient.SONNET),
            },

            # Real-time chat -> Claude Haiku (fastest)
            (TaskType.CHAT, QualityLevel.MEDIUM, SpeedRequirement.FAST): {
                "primary": ("claude", ClaudeClient.HAIKU),
                "fallback": ("openai", OpenAIClient.GPT_35_TURBO),
            },

            # Translation -> Gemini Pro (good multilingual)
            (TaskType.TRANSLATION, QualityLevel.MEDIUM, SpeedRequirement.FAST): {
                "primary": ("gemini", GeminiClient.GEMINI_PRO),
                "fallback": ("claude", ClaudeClient.HAIKU),
            },
        }

    def select_model(
        self,
        task_type: TaskType,
        quality: QualityLevel = QualityLevel.MEDIUM,
        speed: SpeedRequirement = SpeedRequirement.BALANCED,
        cost_optimization: CostOptimization = CostOptimization.BALANCED,
        context_size: Optional[int] = None,
    ) -> tuple:
        """
        Select the optimal model based on requirements.

        Args:
            task_type: Type of task
            quality: Required quality level
            speed: Speed requirement
            cost_optimization: Cost optimization strategy
            context_size: Estimated context size in tokens

        Returns:
            Tuple of (provider, model_name)
        """
        # Check for exact match in rules
        rule_key = (task_type, quality, speed)
        if rule_key in self.model_rules:
            return self.model_rules[rule_key]["primary"]

        # Cost optimization override
        if cost_optimization == CostOptimization.MINIMIZE:
            if self.openai_client:
                return ("openai", OpenAIClient.GPT_35_TURBO)
            if self.claude_client:
                return ("claude", ClaudeClient.HAIKU)

        # Context size considerations
        if context_size and context_size > 100000:
            # Need large context window
            if self.gemini_client:
                return ("gemini", GeminiClient.GEMINI_1_5_PRO)
            if self.claude_client:
                return ("claude", ClaudeClient.SONNET)

        # Default selection based on task type
        task_defaults = {
            TaskType.WRITING: ("claude", ClaudeClient.SONNET),
            TaskType.CODING: ("openai", OpenAIClient.GPT_4O),
            TaskType.ANALYSIS: ("claude", ClaudeClient.SONNET),
            TaskType.CHAT: ("openai", OpenAIClient.GPT_35_TURBO),
            TaskType.TRANSLATION: ("gemini", GeminiClient.GEMINI_PRO),
            TaskType.SUMMARIZATION: ("claude", ClaudeClient.HAIKU),
            TaskType.IMAGE_ANALYSIS: ("openai", OpenAIClient.GPT_4O),
            TaskType.DATA_PROCESSING: ("openai", OpenAIClient.GPT_4O),
            TaskType.LONG_DOCUMENT: ("gemini", GeminiClient.GEMINI_1_5_PRO),
        }

        provider, model = task_defaults.get(
            task_type,
            ("claude", ClaudeClient.SONNET)  # Default fallback
        )

        # Ensure provider is available
        if provider == "claude" and not self.claude_client:
            provider, model = ("openai", OpenAIClient.GPT_4O)
        if provider == "openai" and not self.openai_client:
            provider, model = ("claude", ClaudeClient.SONNET)
        if provider == "gemini" and not self.gemini_client:
            provider, model = ("claude", ClaudeClient.SONNET)

        return (provider, model)

    async def generate(
        self,
        prompt: str,
        task_type: TaskType = TaskType.CHAT,
        module: str = "chat",
        user_id: Optional[int] = None,
        conversation_id: Optional[str] = None,
        quality: QualityLevel = QualityLevel.MEDIUM,
        speed: SpeedRequirement = SpeedRequirement.BALANCED,
        cost_optimization: CostOptimization = CostOptimization.BALANCED,
        system_prompt: Optional[str] = None,
        temperature: float = 1.0,
        max_tokens: Optional[int] = None,
        use_cache: bool = True,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Generate AI response with intelligent model selection.

        Args:
            prompt: User prompt
            task_type: Type of task
            module: Module making the request
            user_id: User ID
            conversation_id: Conversation ID for history
            quality: Quality requirement
            speed: Speed requirement
            cost_optimization: Cost optimization strategy
            system_prompt: System prompt
            temperature: Model temperature
            max_tokens: Maximum tokens
            use_cache: Whether to use caching
            **kwargs: Additional parameters

        Returns:
            Dictionary with response and metadata
        """
        start_time = datetime.utcnow()

        # Check cache first
        if use_cache and cache_manager.should_cache(
            "auto",
            task_type.value,
            temperature
        ):
            cached_response = cache_manager.get(
                model="auto",
                prompt=prompt,
                system_prompt=system_prompt,
                temperature=temperature,
                max_tokens=max_tokens,
            )

            if cached_response:
                # Track cache hit (zero cost)
                if user_id:
                    cost_tracker.track_request(
                        user_id=user_id,
                        model="cached",
                        input_tokens=0,
                        output_tokens=0,
                        task_type=task_type.value,
                        module=module,
                        cached=True,
                        cache_savings=cached_response.get("estimated_cost", 0),
                    )

                return {
                    **cached_response,
                    "cached": True,
                    "response_time": (datetime.utcnow() - start_time).total_seconds(),
                }

        # Get conversation history if conversation_id provided
        conversation_history = None
        if conversation_id:
            conversation_history = context_manager.get_messages(
                conversation_id,
                include_system=False
            )

        # Estimate context size
        context_size = len(prompt) // 4
        if conversation_history:
            context_size += sum(len(msg.get("content", "")) for msg in conversation_history) // 4

        # Select optimal model
        provider, model = self.select_model(
            task_type=task_type,
            quality=quality,
            speed=speed,
            cost_optimization=cost_optimization,
            context_size=context_size,
        )

        # A/B testing override
        if self.ab_test_enabled and random.random() < self.ab_test_split:
            # Use alternative model for testing
            provider, model = self._get_ab_test_model(provider, model)

        # Generate response
        response = await self._generate_with_fallback(
            provider=provider,
            model=model,
            prompt=prompt,
            system_prompt=system_prompt,
            temperature=temperature,
            max_tokens=max_tokens,
            conversation_history=conversation_history,
            **kwargs
        )

        # Track usage and costs
        if user_id and "usage" in response:
            usage = response["usage"]
            cost = cost_tracker.calculate_cost(
                model=response.get("model", model),
                input_tokens=usage.get("input_tokens", usage.get("prompt_tokens", 0)),
                output_tokens=usage.get("output_tokens", usage.get("completion_tokens", 0)),
            )

            cost_tracker.track_request(
                user_id=user_id,
                model=response.get("model", model),
                input_tokens=usage.get("input_tokens", usage.get("prompt_tokens", 0)),
                output_tokens=usage.get("output_tokens", usage.get("completion_tokens", 0)),
                task_type=task_type.value,
                module=module,
                cached=False,
            )

            response["estimated_cost"] = float(cost)

        # Cache successful response
        if use_cache and "content" in response and "error" not in response:
            ttl = cache_manager.get_ttl_for_task(task_type.value)
            cache_manager.set(
                model=model,
                prompt=prompt,
                response=response,
                system_prompt=system_prompt,
                temperature=temperature,
                max_tokens=max_tokens,
                ttl=ttl,
            )

        # Update conversation history
        if conversation_id and "content" in response:
            context_manager.add_message(
                conversation_id=conversation_id,
                role="user",
                content=prompt,
            )
            context_manager.add_message(
                conversation_id=conversation_id,
                role="assistant",
                content=response["content"],
                metadata={
                    "model": response.get("model", model),
                    "provider": provider,
                },
            )

        # Add metadata
        response["provider"] = provider
        response["selected_model"] = model
        response["task_type"] = task_type.value
        response["response_time"] = (datetime.utcnow() - start_time).total_seconds()
        response["cached"] = False

        return response

    async def _generate_with_fallback(
        self,
        provider: str,
        model: str,
        prompt: str,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Generate with automatic fallback on failure.

        Args:
            provider: Primary provider (claude, openai, gemini)
            model: Primary model
            prompt: User prompt
            **kwargs: Additional parameters

        Returns:
            Response dictionary
        """
        # Try primary model
        try:
            response = await self._call_provider(provider, model, prompt, **kwargs)

            if "error" not in response:
                return response
        except Exception as e:
            pass  # Fall through to fallback

        # Try fallback models
        fallback_options = [
            ("claude", ClaudeClient.SONNET),
            ("openai", OpenAIClient.GPT_4O),
            ("gemini", GeminiClient.GEMINI_1_5_PRO),
        ]

        for fallback_provider, fallback_model in fallback_options:
            if fallback_provider == provider and fallback_model == model:
                continue  # Skip primary model

            try:
                response = await self._call_provider(
                    fallback_provider,
                    fallback_model,
                    prompt,
                    **kwargs
                )

                if "error" not in response:
                    response["fallback_used"] = True
                    response["original_provider"] = provider
                    response["original_model"] = model
                    return response
            except Exception:
                continue

        # All models failed
        return {
            "error": "All models failed to generate response",
            "provider": provider,
            "model": model,
        }

    async def _call_provider(
        self,
        provider: str,
        model: str,
        prompt: str,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Call specific AI provider.

        Args:
            provider: Provider name
            model: Model name
            prompt: User prompt
            **kwargs: Additional parameters

        Returns:
            Response dictionary
        """
        if provider == "claude" and self.claude_client:
            return await self.claude_client.generate(
                prompt=prompt,
                model=model,
                **kwargs
            )
        elif provider == "openai" and self.openai_client:
            return await self.openai_client.generate(
                prompt=prompt,
                model=model,
                **kwargs
            )
        elif provider == "gemini" and self.gemini_client:
            return await self.gemini_client.generate(
                prompt=prompt,
                model=model,
                **kwargs
            )
        else:
            return {
                "error": f"Provider {provider} not available",
            }

    async def generate_stream(
        self,
        prompt: str,
        task_type: TaskType = TaskType.CHAT,
        quality: QualityLevel = QualityLevel.MEDIUM,
        speed: SpeedRequirement = SpeedRequirement.FAST,
        **kwargs
    ) -> AsyncIterator[str]:
        """
        Generate streaming response.

        Args:
            prompt: User prompt
            task_type: Task type
            quality: Quality level
            speed: Speed requirement
            **kwargs: Additional parameters

        Yields:
            Response chunks
        """
        # Select model
        provider, model = self.select_model(
            task_type=task_type,
            quality=quality,
            speed=speed,
        )

        # Stream from provider
        if provider == "claude" and self.claude_client:
            async for chunk in self.claude_client.generate_stream(
                prompt=prompt,
                model=model,
                **kwargs
            ):
                yield chunk
        elif provider == "openai" and self.openai_client:
            async for chunk in self.openai_client.generate_stream(
                prompt=prompt,
                model=model,
                **kwargs
            ):
                yield chunk
        elif provider == "gemini" and self.gemini_client:
            async for chunk in self.gemini_client.generate_stream(
                prompt=prompt,
                model=model,
                **kwargs
            ):
                yield chunk
        else:
            yield f"[Error: Provider {provider} not available]"

    def _get_ab_test_model(self, provider: str, model: str) -> tuple:
        """Get alternative model for A/B testing."""
        alternatives = {
            ("claude", ClaudeClient.SONNET): ("openai", OpenAIClient.GPT_4O),
            ("openai", OpenAIClient.GPT_4O): ("claude", ClaudeClient.SONNET),
            ("claude", ClaudeClient.HAIKU): ("openai", OpenAIClient.GPT_35_TURBO),
        }
        return alternatives.get((provider, model), (provider, model))

    def get_statistics(self, user_id: Optional[int] = None) -> Dict[str, Any]:
        """
        Get orchestrator statistics.

        Args:
            user_id: User ID (optional, for user-specific stats)

        Returns:
            Dictionary with statistics
        """
        stats = {
            "cache": cache_manager.get_statistics(),
            "available_providers": {
                "claude": self.claude_client is not None,
                "openai": self.openai_client is not None,
                "gemini": self.gemini_client is not None,
            },
        }

        if user_id:
            stats["user_usage"] = cost_tracker.get_user_usage(user_id, period="month")
            stats["optimization_suggestions"] = cost_tracker.get_optimization_suggestions(user_id)

        return stats


# Global orchestrator instance (initialized lazily)
_orchestrator: Optional[AIOrchestrator] = None


def get_orchestrator() -> AIOrchestrator:
    """Get or create global orchestrator instance."""
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = AIOrchestrator()
    return _orchestrator
