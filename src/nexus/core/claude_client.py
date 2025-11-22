"""
Claude AI client for Nexus Platform
"""
import asyncio
from typing import Any, Dict, List, Optional, Union
from anthropic import Anthropic, AsyncAnthropic
from loguru import logger
from tenacity import retry, stop_after_attempt, wait_exponential


class ClaudeClient:
    """Centralized Claude AI client with streaming and vision support"""

    def __init__(self, api_key: str, model: str = "claude-3-5-sonnet-20241022"):
        self.api_key = api_key
        self.model = model
        self.client = Anthropic(api_key=api_key)
        self.async_client = AsyncAnthropic(api_key=api_key)
        self.max_tokens = 4096

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10)
    )
    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        max_tokens: Optional[int] = None,
        temperature: float = 1.0,
        **kwargs
    ) -> str:
        """
        Generate text completion from Claude

        Args:
            prompt: User prompt
            system_prompt: Optional system prompt
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            **kwargs: Additional parameters

        Returns:
            Generated text response
        """
        try:
            messages = [{"role": "user", "content": prompt}]

            params = {
                "model": self.model,
                "messages": messages,
                "max_tokens": max_tokens or self.max_tokens,
                "temperature": temperature,
            }

            if system_prompt:
                params["system"] = system_prompt

            params.update(kwargs)

            response = self.client.messages.create(**params)
            return response.content[0].text

        except Exception as e:
            logger.error(f"Error generating completion: {e}")
            raise

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10)
    )
    async def agenerate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        max_tokens: Optional[int] = None,
        temperature: float = 1.0,
        **kwargs
    ) -> str:
        """Async version of generate"""
        try:
            messages = [{"role": "user", "content": prompt}]

            params = {
                "model": self.model,
                "messages": messages,
                "max_tokens": max_tokens or self.max_tokens,
                "temperature": temperature,
            }

            if system_prompt:
                params["system"] = system_prompt

            params.update(kwargs)

            response = await self.async_client.messages.create(**params)
            return response.content[0].text

        except Exception as e:
            logger.error(f"Error generating async completion: {e}")
            raise

    def generate_with_vision(
        self,
        prompt: str,
        images: List[Dict[str, Any]],
        system_prompt: Optional[str] = None,
        **kwargs
    ) -> str:
        """
        Generate text with vision analysis

        Args:
            prompt: Text prompt
            images: List of image dicts with source/data
            system_prompt: Optional system prompt
            **kwargs: Additional parameters

        Returns:
            Generated response
        """
        try:
            content = []

            # Add images
            for image in images:
                content.append({
                    "type": "image",
                    "source": image
                })

            # Add text prompt
            content.append({
                "type": "text",
                "text": prompt
            })

            messages = [{"role": "user", "content": content}]

            params = {
                "model": self.model,
                "messages": messages,
                "max_tokens": self.max_tokens,
            }

            if system_prompt:
                params["system"] = system_prompt

            params.update(kwargs)

            response = self.client.messages.create(**params)
            return response.content[0].text

        except Exception as e:
            logger.error(f"Error generating vision completion: {e}")
            raise

    def stream_generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        **kwargs
    ):
        """
        Stream text generation

        Args:
            prompt: User prompt
            system_prompt: Optional system prompt
            **kwargs: Additional parameters

        Yields:
            Text chunks as they're generated
        """
        try:
            messages = [{"role": "user", "content": prompt}]

            params = {
                "model": self.model,
                "messages": messages,
                "max_tokens": self.max_tokens,
                "stream": True,
            }

            if system_prompt:
                params["system"] = system_prompt

            params.update(kwargs)

            with self.client.messages.stream(**params) as stream:
                for text in stream.text_stream:
                    yield text

        except Exception as e:
            logger.error(f"Error streaming completion: {e}")
            raise

    async def astream_generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        **kwargs
    ):
        """Async streaming generation"""
        try:
            messages = [{"role": "user", "content": prompt}]

            params = {
                "model": self.model,
                "messages": messages,
                "max_tokens": self.max_tokens,
                "stream": True,
            }

            if system_prompt:
                params["system"] = system_prompt

            params.update(kwargs)

            async with self.async_client.messages.stream(**params) as stream:
                async for text in stream.text_stream:
                    yield text

        except Exception as e:
            logger.error(f"Error async streaming completion: {e}")
            raise

    def analyze_image(self, image_data: str, prompt: str, media_type: str = "image/jpeg") -> str:
        """
        Analyze a single image

        Args:
            image_data: Base64 encoded image
            prompt: Analysis prompt
            media_type: Image MIME type

        Returns:
            Analysis result
        """
        image = {
            "type": "base64",
            "media_type": media_type,
            "data": image_data
        }

        return self.generate_with_vision(prompt, [image])

    def batch_generate(self, prompts: List[str], **kwargs) -> List[str]:
        """
        Generate completions for multiple prompts

        Args:
            prompts: List of prompts
            **kwargs: Additional parameters

        Returns:
            List of generated responses
        """
        results = []
        for prompt in prompts:
            result = self.generate(prompt, **kwargs)
            results.append(result)
        return results

    async def abatch_generate(self, prompts: List[str], **kwargs) -> List[str]:
        """Async batch generation"""
        tasks = [self.agenerate(prompt, **kwargs) for prompt in prompts]
        return await asyncio.gather(*tasks)
