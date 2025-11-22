"""
Google Gemini Client

Client wrapper for Google's Gemini models with support for:
- Gemini Pro, Gemini Pro Vision, Gemini 1.5 Pro
- Streaming responses
- Multimodal support (text, images, video)
- Large context window (up to 2M tokens)
"""

import asyncio
from typing import Dict, List, Optional, Any, AsyncIterator
import os
from pathlib import Path

try:
    import google.generativeai as genai
    from google.generativeai.types import GenerationConfig
    GENAI_AVAILABLE = True
except ImportError:
    GENAI_AVAILABLE = False


class GeminiClient:
    """
    Client for Google's Gemini models.

    Features:
    - Multiple model support (Pro, Pro Vision, 1.5 Pro)
    - Streaming and non-streaming responses
    - Multimodal capabilities
    - Huge context window (2M tokens for 1.5 Pro)
    - Safety settings
    - Error handling
    """

    # Available models
    GEMINI_PRO = "gemini-pro"
    GEMINI_PRO_VISION = "gemini-pro-vision"
    GEMINI_1_5_PRO = "gemini-1.5-pro"

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize Gemini client.

        Args:
            api_key: Google API key (uses GOOGLE_API_KEY env var if not provided)
        """
        if not GENAI_AVAILABLE:
            raise ImportError(
                "google-generativeai package not installed. "
                "Install with: pip install google-generativeai"
            )

        self.api_key = api_key or os.getenv("GOOGLE_API_KEY")
        if not self.api_key:
            raise ValueError(
                "Google API key required. Set GOOGLE_API_KEY environment "
                "variable or pass api_key parameter."
            )

        # Configure the API
        genai.configure(api_key=self.api_key)

    async def generate(
        self,
        prompt: str,
        model: str = GEMINI_1_5_PRO,
        system_prompt: Optional[str] = None,
        temperature: float = 1.0,
        max_tokens: Optional[int] = None,
        conversation_history: Optional[List[Dict]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Generate a response from Gemini.

        Args:
            prompt: User prompt/message
            model: Model to use
            system_prompt: System prompt (prepended to conversation)
            temperature: Randomness (0.0 to 2.0)
            max_tokens: Maximum response tokens
            conversation_history: Previous messages
            **kwargs: Additional parameters

        Returns:
            Dictionary with response and metadata
        """
        try:
            # Create model instance
            genai_model = genai.GenerativeModel(model)

            # Build generation config
            generation_config = GenerationConfig(
                temperature=temperature,
                max_output_tokens=max_tokens,
                top_p=kwargs.get("top_p"),
                top_k=kwargs.get("top_k"),
            )

            # Build conversation context
            full_prompt = prompt
            if system_prompt:
                full_prompt = f"{system_prompt}\n\n{prompt}"

            if conversation_history:
                # Format conversation history
                context_parts = []
                for msg in conversation_history:
                    role = msg.get("role", "user")
                    content = msg.get("content", "")
                    if role == "user":
                        context_parts.append(f"User: {content}")
                    elif role == "assistant" or role == "model":
                        context_parts.append(f"Assistant: {content}")

                context = "\n".join(context_parts)
                full_prompt = f"{context}\n\nUser: {prompt}"

            # Generate response
            response = await asyncio.to_thread(
                genai_model.generate_content,
                full_prompt,
                generation_config=generation_config,
                safety_settings=kwargs.get("safety_settings"),
            )

            # Extract content
            content = response.text if response.text else ""

            # Get usage metadata if available
            usage = {}
            if hasattr(response, "usage_metadata"):
                usage = {
                    "prompt_tokens": response.usage_metadata.prompt_token_count,
                    "completion_tokens": response.usage_metadata.candidates_token_count,
                    "total_tokens": response.usage_metadata.total_token_count,
                }

            return {
                "content": content,
                "model": model,
                "finish_reason": self._get_finish_reason(response),
                "usage": usage,
                "safety_ratings": self._get_safety_ratings(response),
            }

        except Exception as e:
            return {
                "error": str(e),
                "error_type": type(e).__name__,
            }

    async def generate_stream(
        self,
        prompt: str,
        model: str = GEMINI_1_5_PRO,
        system_prompt: Optional[str] = None,
        temperature: float = 1.0,
        max_tokens: Optional[int] = None,
        conversation_history: Optional[List[Dict]] = None,
        **kwargs
    ) -> AsyncIterator[str]:
        """
        Generate streaming response from Gemini.

        Args:
            prompt: User prompt
            model: Model to use
            system_prompt: System prompt
            temperature: Randomness
            max_tokens: Maximum tokens
            conversation_history: Previous messages
            **kwargs: Additional parameters

        Yields:
            Response chunks as they arrive
        """
        try:
            # Create model instance
            genai_model = genai.GenerativeModel(model)

            # Build generation config
            generation_config = GenerationConfig(
                temperature=temperature,
                max_output_tokens=max_tokens,
                top_p=kwargs.get("top_p"),
                top_k=kwargs.get("top_k"),
            )

            # Build full prompt
            full_prompt = prompt
            if system_prompt:
                full_prompt = f"{system_prompt}\n\n{prompt}"

            if conversation_history:
                context_parts = []
                for msg in conversation_history:
                    role = msg.get("role", "user")
                    content = msg.get("content", "")
                    if role == "user":
                        context_parts.append(f"User: {content}")
                    elif role == "assistant" or role == "model":
                        context_parts.append(f"Assistant: {content}")

                context = "\n".join(context_parts)
                full_prompt = f"{context}\n\nUser: {prompt}"

            # Stream response
            response_stream = await asyncio.to_thread(
                genai_model.generate_content,
                full_prompt,
                generation_config=generation_config,
                stream=True,
            )

            for chunk in response_stream:
                if chunk.text:
                    yield chunk.text

        except Exception as e:
            yield f"[Error: {str(e)}]"

    async def analyze_image(
        self,
        image_path: str,
        prompt: str,
        model: str = GEMINI_PRO_VISION,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Analyze an image with Gemini's vision capabilities.

        Args:
            image_path: Path to image file
            prompt: Question about the image
            model: Model to use (must support vision)
            **kwargs: Additional parameters

        Returns:
            Dictionary with analysis and metadata
        """
        try:
            # Create vision model
            genai_model = genai.GenerativeModel(model)

            # Load image
            image = self._load_image(image_path)

            # Build generation config
            generation_config = GenerationConfig(
                temperature=kwargs.get("temperature", 0.4),
                max_output_tokens=kwargs.get("max_tokens", 4096),
            )

            # Generate response
            response = await asyncio.to_thread(
                genai_model.generate_content,
                [prompt, image],
                generation_config=generation_config,
            )

            content = response.text if response.text else ""

            # Get usage
            usage = {}
            if hasattr(response, "usage_metadata"):
                usage = {
                    "prompt_tokens": response.usage_metadata.prompt_token_count,
                    "completion_tokens": response.usage_metadata.candidates_token_count,
                    "total_tokens": response.usage_metadata.total_token_count,
                }

            return {
                "content": content,
                "model": model,
                "usage": usage,
                "safety_ratings": self._get_safety_ratings(response),
            }

        except Exception as e:
            return {
                "error": str(e),
                "error_type": type(e).__name__,
            }

    async def chat(
        self,
        messages: List[Dict],
        model: str = GEMINI_1_5_PRO,
        temperature: float = 1.0,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Start a chat session with Gemini.

        Args:
            messages: List of message dictionaries
            model: Model to use
            temperature: Randomness
            **kwargs: Additional parameters

        Returns:
            Dictionary with response
        """
        try:
            # Create model
            genai_model = genai.GenerativeModel(model)

            # Start chat session
            chat = genai_model.start_chat(history=[])

            # Build generation config
            generation_config = GenerationConfig(
                temperature=temperature,
                max_output_tokens=kwargs.get("max_tokens"),
            )

            # Send messages
            last_response = None
            for msg in messages:
                if msg.get("role") == "user":
                    last_response = await asyncio.to_thread(
                        chat.send_message,
                        msg.get("content", ""),
                        generation_config=generation_config,
                    )

            if last_response:
                content = last_response.text if last_response.text else ""

                usage = {}
                if hasattr(last_response, "usage_metadata"):
                    usage = {
                        "prompt_tokens": last_response.usage_metadata.prompt_token_count,
                        "completion_tokens": last_response.usage_metadata.candidates_token_count,
                        "total_tokens": last_response.usage_metadata.total_token_count,
                    }

                return {
                    "content": content,
                    "model": model,
                    "usage": usage,
                }

            return {"error": "No response generated"}

        except Exception as e:
            return {
                "error": str(e),
                "error_type": type(e).__name__,
            }

    def _load_image(self, image_path: str):
        """Load image for Gemini vision."""
        from PIL import Image

        if not Path(image_path).exists():
            raise FileNotFoundError(f"Image not found: {image_path}")

        return Image.open(image_path)

    def _get_finish_reason(self, response) -> str:
        """Extract finish reason from response."""
        try:
            if hasattr(response, "candidates") and response.candidates:
                candidate = response.candidates[0]
                if hasattr(candidate, "finish_reason"):
                    return str(candidate.finish_reason)
        except Exception:
            pass
        return "unknown"

    def _get_safety_ratings(self, response) -> List[Dict]:
        """Extract safety ratings from response."""
        try:
            if hasattr(response, "candidates") and response.candidates:
                candidate = response.candidates[0]
                if hasattr(candidate, "safety_ratings"):
                    return [
                        {
                            "category": str(rating.category),
                            "probability": str(rating.probability),
                        }
                        for rating in candidate.safety_ratings
                    ]
        except Exception:
            pass
        return []

    async def count_tokens(self, text: str, model: str = GEMINI_1_5_PRO) -> int:
        """
        Count tokens for text.

        Args:
            text: Text to count
            model: Model to count for

        Returns:
            Token count
        """
        try:
            genai_model = genai.GenerativeModel(model)
            result = await asyncio.to_thread(
                genai_model.count_tokens,
                text
            )
            return result.total_tokens
        except Exception:
            # Fallback estimate
            return len(text) // 4

    def get_model_info(self, model: str) -> Dict[str, Any]:
        """
        Get information about a model.

        Args:
            model: Model name

        Returns:
            Dictionary with model information
        """
        model_info = {
            self.GEMINI_PRO: {
                "name": "Gemini Pro",
                "context_window": 32768,
                "max_output": 8192,
                "supports_vision": False,
                "supports_multimodal": False,
                "description": "Fast and versatile performance",
            },
            self.GEMINI_PRO_VISION: {
                "name": "Gemini Pro Vision",
                "context_window": 32768,
                "max_output": 8192,
                "supports_vision": True,
                "supports_multimodal": True,
                "description": "Multimodal understanding",
            },
            self.GEMINI_1_5_PRO: {
                "name": "Gemini 1.5 Pro",
                "context_window": 2000000,  # 2M tokens!
                "max_output": 8192,
                "supports_vision": True,
                "supports_multimodal": True,
                "description": "Most capable with huge context window",
            },
        }

        return model_info.get(model, {})

    def get_available_models(self) -> List[str]:
        """
        Get list of available models.

        Returns:
            List of model names
        """
        try:
            models = genai.list_models()
            return [m.name for m in models if "generateContent" in m.supported_generation_methods]
        except Exception:
            return [self.GEMINI_PRO, self.GEMINI_PRO_VISION, self.GEMINI_1_5_PRO]
