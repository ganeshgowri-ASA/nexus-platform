"""
NEXUS AI/LLM Orchestration Module

Intelligent AI orchestration system that routes requests to Claude, GPT-4,
and Gemini based on task complexity, cost, and speed requirements.

Main Components:
- AIOrchestrator: Smart model routing and request handling
- ClaudeClient: Anthropic Claude integration
- OpenAIClient: OpenAI GPT-4 integration
- GeminiClient: Google Gemini integration
- CostTracker: Usage analytics and cost tracking
- CacheManager: Response caching with LRU
- ContextManager: Conversation history management
- PromptTemplates: Module-specific prompt templates

Usage:
    from modules.ai import get_orchestrator, TaskType, QualityLevel

    orchestrator = get_orchestrator()

    response = await orchestrator.generate(
        prompt="Write a professional email...",
        task_type=TaskType.WRITING,
        module="email",
        user_id=123,
    )
"""

# Main orchestrator
from .orchestrator import (
    AIOrchestrator,
    get_orchestrator,
    TaskType,
    QualityLevel,
    SpeedRequirement,
    CostOptimization,
)

# Individual clients
from .claude_client import ClaudeClient
from .openai_client import OpenAIClient
from .gemini_client import GeminiClient

# Supporting components
from .cost_tracker import CostTracker, cost_tracker
from .cache_manager import CacheManager, cache_manager
from .context_manager import ContextManager, context_manager
from .prompt_templates import (
    PromptTemplates,
    PromptBuilder,
    prompt_templates,
    prompt_builder,
)

# Version
__version__ = "1.0.0"

# Exports
__all__ = [
    # Main orchestrator
    "AIOrchestrator",
    "get_orchestrator",

    # Enums
    "TaskType",
    "QualityLevel",
    "SpeedRequirement",
    "CostOptimization",

    # Clients
    "ClaudeClient",
    "OpenAIClient",
    "GeminiClient",

    # Components
    "CostTracker",
    "cost_tracker",
    "CacheManager",
    "cache_manager",
    "ContextManager",
    "context_manager",
    "PromptTemplates",
    "PromptBuilder",
    "prompt_templates",
    "prompt_builder",
]
