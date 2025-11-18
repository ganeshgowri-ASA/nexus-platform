"""
OpenAI Client (GPT-4)

Client wrapper for OpenAI's models with support for:
- GPT-4, GPT-4-Turbo, GPT-3.5-Turbo
- Streaming responses
- Vision support (GPT-4V)
- Function calling
- JSON mode
"""

import asyncio
from typing import Dict, List, Optional, Any, AsyncIterator
import os
import base64
from pathlib import Path

try:
    from openai import AsyncOpenAI, OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

try:
    import tiktoken
    TIKTOKEN_AVAILABLE = True
except ImportError:
    TIKTOKEN_AVAILABLE = False


class OpenAIClient:
    """
    Client for OpenAI's GPT models.

    Features:
    - Multiple model support (GPT-4, GPT-4-Turbo, GPT-3.5)
    - Streaming and non-streaming responses
    - Vision capabilities (GPT-4V)
    - Function calling
    - JSON mode
    - Token counting with tiktoken
    - Retry logic
    - Error handling
    """

    # Available models
    GPT_4 = "gpt-4"
    GPT_4_TURBO = "gpt-4-turbo-preview"
    GPT_4O = "gpt-4o"
    GPT_35_TURBO = "gpt-3.5-turbo"

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize OpenAI client.

        Args:
            api_key: OpenAI API key (uses OPENAI_API_KEY env var if not provided)
        """
        if not OPENAI_AVAILABLE:
            raise ImportError(
                "openai package not installed. "
                "Install with: pip install openai"
            )

        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError(
                "OpenAI API key required. Set OPENAI_API_KEY environment "
                "variable or pass api_key parameter."
            )

        self.client = OpenAI(api_key=self.api_key)
        self.async_client = AsyncOpenAI(api_key=self.api_key)

    async def generate(
        self,
        prompt: str,
        model: str = GPT_4O,
        system_prompt: Optional[str] = None,
        temperature: float = 1.0,
        max_tokens: Optional[int] = None,
        conversation_history: Optional[List[Dict]] = None,
        functions: Optional[List[Dict]] = None,
        response_format: Optional[Dict] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Generate a response from OpenAI.

        Args:
            prompt: User prompt/message
            model: Model to use
            system_prompt: System prompt for context
            temperature: Randomness (0.0 to 2.0)
            max_tokens: Maximum response tokens
            conversation_history: Previous messages
            functions: Function definitions for function calling
            response_format: Response format (e.g., {"type": "json_object"})
            **kwargs: Additional parameters

        Returns:
            Dictionary with response and metadata
        """
        try:
            # Build messages list
            messages = []

            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})

            if conversation_history:
                messages.extend(conversation_history)

            messages.append({"role": "user", "content": prompt})

            # Prepare API call parameters
            params = {
                "model": model,
                "messages": messages,
                "temperature": temperature,
            }

            if max_tokens:
                params["max_tokens"] = max_tokens

            if functions:
                params["functions"] = functions
                params["function_call"] = kwargs.get("function_call", "auto")

            if response_format:
                params["response_format"] = response_format

            # Add optional parameters
            if "top_p" in kwargs:
                params["top_p"] = kwargs["top_p"]
            if "frequency_penalty" in kwargs:
                params["frequency_penalty"] = kwargs["frequency_penalty"]
            if "presence_penalty" in kwargs:
                params["presence_penalty"] = kwargs["presence_penalty"]

            # Make API call
            response = await self.async_client.chat.completions.create(**params)

            # Extract response
            choice = response.choices[0]
            message = choice.message

            result = {
                "content": message.content,
                "role": message.role,
                "model": response.model,
                "finish_reason": choice.finish_reason,
                "usage": {
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens,
                },
            }

            # Add function call if present
            if hasattr(message, "function_call") and message.function_call:
                result["function_call"] = {
                    "name": message.function_call.name,
                    "arguments": message.function_call.arguments,
                }

            return result

        except Exception as e:
            return {
                "error": str(e),
                "error_type": type(e).__name__,
            }

    async def generate_stream(
        self,
        prompt: str,
        model: str = GPT_4O,
        system_prompt: Optional[str] = None,
        temperature: float = 1.0,
        max_tokens: Optional[int] = None,
        conversation_history: Optional[List[Dict]] = None,
        **kwargs
    ) -> AsyncIterator[str]:
        """
        Generate streaming response from OpenAI.

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
            # Build messages
            messages = []

            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})

            if conversation_history:
                messages.extend(conversation_history)

            messages.append({"role": "user", "content": prompt})

            # Prepare parameters
            params = {
                "model": model,
                "messages": messages,
                "temperature": temperature,
                "stream": True,
            }

            if max_tokens:
                params["max_tokens"] = max_tokens

            # Stream response
            stream = await self.async_client.chat.completions.create(**params)

            async for chunk in stream:
                if chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content

        except Exception as e:
            yield f"[Error: {str(e)}]"

    async def analyze_image(
        self,
        image_path: str,
        prompt: str,
        model: str = GPT_4O,
        detail: str = "auto",
        **kwargs
    ) -> Dict[str, Any]:
        """
        Analyze an image with GPT-4 Vision.

        Args:
            image_path: Path to image file or URL
            prompt: Question about the image
            model: Model to use (must support vision)
            detail: Image detail level (low, high, auto)
            **kwargs: Additional parameters

        Returns:
            Dictionary with analysis and metadata
        """
        try:
            # Prepare image content
            if image_path.startswith(("http://", "https://")):
                # URL
                image_content = {
                    "type": "image_url",
                    "image_url": {
                        "url": image_path,
                        "detail": detail,
                    },
                }
            else:
                # Local file - encode to base64
                image_data = self._encode_image(image_path)
                media_type = self._get_media_type(image_path)

                image_content = {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:{media_type};base64,{image_data}",
                        "detail": detail,
                    },
                }

            # Build message with image
            messages = [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        image_content,
                    ],
                }
            ]

            # Make API call
            response = await self.async_client.chat.completions.create(
                model=model,
                messages=messages,
                max_tokens=kwargs.get("max_tokens", 4096),
            )

            choice = response.choices[0]

            return {
                "content": choice.message.content,
                "model": response.model,
                "finish_reason": choice.finish_reason,
                "usage": {
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens,
                },
            }

        except Exception as e:
            return {
                "error": str(e),
                "error_type": type(e).__name__,
            }

    async def generate_json(
        self,
        prompt: str,
        model: str = GPT_4O,
        system_prompt: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Generate JSON response using JSON mode.

        Args:
            prompt: User prompt
            model: Model to use
            system_prompt: System prompt
            **kwargs: Additional parameters

        Returns:
            Dictionary with JSON response
        """
        # Add JSON instruction to system prompt
        json_system_prompt = (
            system_prompt or ""
        ) + "\n\nRespond with valid JSON only."

        return await self.generate(
            prompt=prompt,
            model=model,
            system_prompt=json_system_prompt,
            response_format={"type": "json_object"},
            **kwargs
        )

    async def use_functions(
        self,
        prompt: str,
        functions: List[Dict],
        model: str = GPT_4O,
        system_prompt: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Use OpenAI with function calling.

        Args:
            prompt: User prompt
            functions: List of function definitions
            model: Model to use
            system_prompt: System prompt
            **kwargs: Additional parameters

        Returns:
            Dictionary with response and function calls
        """
        return await self.generate(
            prompt=prompt,
            model=model,
            system_prompt=system_prompt,
            functions=functions,
            **kwargs
        )

    def count_tokens(self, text: str, model: str = GPT_4O) -> int:
        """
        Count tokens using tiktoken.

        Args:
            text: Text to count tokens for
            model: Model to count for

        Returns:
            Token count
        """
        if not TIKTOKEN_AVAILABLE:
            # Fallback: rough estimate (1 token ≈ 4 characters)
            return len(text) // 4

        try:
            encoding = tiktoken.encoding_for_model(model)
            return len(encoding.encode(text))
        except Exception:
            # Fallback to cl100k_base encoding (used by GPT-4)
            encoding = tiktoken.get_encoding("cl100k_base")
            return len(encoding.encode(text))

    def count_messages_tokens(
        self,
        messages: List[Dict],
        model: str = GPT_4O
    ) -> int:
        """
        Count tokens in a list of messages.

        Args:
            messages: List of message dictionaries
            model: Model to count for

        Returns:
            Total token count
        """
        if not TIKTOKEN_AVAILABLE:
            # Fallback estimate
            total_chars = sum(len(msg.get("content", "")) for msg in messages)
            return total_chars // 4

        try:
            encoding = tiktoken.encoding_for_model(model)
        except Exception:
            encoding = tiktoken.get_encoding("cl100k_base")

        tokens_per_message = 3  # every message follows <im_start>{role/name}\n{content}<im_end>\n
        tokens_per_name = 1  # if there's a name, the role is omitted

        num_tokens = 0
        for message in messages:
            num_tokens += tokens_per_message
            for key, value in message.items():
                num_tokens += len(encoding.encode(str(value)))
                if key == "name":
                    num_tokens += tokens_per_name

        num_tokens += 3  # every reply is primed with <im_start>assistant

        return num_tokens

    def _encode_image(self, image_path: str) -> str:
        """Encode image file to base64."""
        with open(image_path, "rb") as f:
            return base64.standard_b64encode(f.read()).decode("utf-8")

    def _get_media_type(self, image_path: str) -> str:
        """Get media type from file extension."""
        extension = Path(image_path).suffix.lower()
        media_types = {
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".png": "image/png",
            ".gif": "image/gif",
            ".webp": "image/webp",
        }
        return media_types.get(extension, "image/jpeg")

    def get_model_info(self, model: str) -> Dict[str, Any]:
        """
        Get information about a model.

        Args:
            model: Model name

        Returns:
            Dictionary with model information
        """
        model_info = {
            self.GPT_4: {
                "name": "GPT-4",
                "context_window": 8192,
                "max_output": 4096,
                "supports_vision": False,
                "supports_functions": True,
                "description": "Most capable GPT-4 model",
            },
            self.GPT_4_TURBO: {
                "name": "GPT-4 Turbo",
                "context_window": 128000,
                "max_output": 4096,
                "supports_vision": False,
                "supports_functions": True,
                "description": "Faster, cheaper GPT-4 with larger context",
            },
            self.GPT_4O: {
                "name": "GPT-4o",
                "context_window": 128000,
                "max_output": 4096,
                "supports_vision": True,
                "supports_functions": True,
                "description": "Multimodal GPT-4 optimized for speed",
            },
            self.GPT_35_TURBO: {
                "name": "GPT-3.5 Turbo",
                "context_window": 16385,
                "max_output": 4096,
                "supports_vision": False,
                "supports_functions": True,
                "description": "Fast and cost-effective",
            },
        }

        return model_info.get(model, {})
