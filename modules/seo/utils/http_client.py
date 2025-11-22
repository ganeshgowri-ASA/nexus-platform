"""
HTTP client utilities.

Provides async HTTP client with retry logic, rate limiting,
and error handling for SEO operations.
"""

import asyncio
from typing import Any, Dict, Optional
from urllib.parse import urljoin, urlparse

import aiohttp
from aiohttp import ClientSession, ClientTimeout
from loguru import logger

from modules.seo.config.settings import get_settings
from .exceptions import APIException, CrawlException, RateLimitException


class HTTPClient:
    """
    Async HTTP client for SEO operations.

    Provides methods for making HTTP requests with built-in
    retry logic, rate limiting, and error handling.
    """

    def __init__(
        self,
        user_agent: Optional[str] = None,
        timeout: Optional[int] = None,
        max_retries: int = 3,
    ):
        """
        Initialize HTTP client.

        Args:
            user_agent: Custom user agent string
            timeout: Request timeout in seconds
            max_retries: Maximum number of retry attempts
        """
        self.settings = get_settings()
        self.user_agent = user_agent or self.settings.default_user_agent
        self.timeout = timeout or self.settings.request_timeout
        self.max_retries = max_retries
        self._session: Optional[ClientSession] = None

    async def get_session(self) -> ClientSession:
        """
        Get or create aiohttp session.

        Returns:
            ClientSession: Async HTTP session
        """
        if self._session is None or self._session.closed:
            timeout = ClientTimeout(total=self.timeout)
            headers = {"User-Agent": self.user_agent}
            self._session = ClientSession(
                timeout=timeout,
                headers=headers,
                raise_for_status=False,
            )
        return self._session

    async def close(self) -> None:
        """Close HTTP session."""
        if self._session and not self._session.closed:
            await self._session.close()
            self._session = None

    async def get(
        self,
        url: str,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        retry_count: int = 0,
    ) -> Dict[str, Any]:
        """
        Make GET request.

        Args:
            url: URL to request
            params: Query parameters
            headers: Additional headers
            retry_count: Current retry attempt

        Returns:
            Response data with status, headers, and content

        Raises:
            CrawlException: If request fails after retries
            RateLimitException: If rate limit is hit
        """
        session = await self.get_session()

        try:
            logger.debug(f"GET request to {url}")
            async with session.get(url, params=params, headers=headers) as response:
                content = await response.text()

                # Handle rate limiting
                if response.status == 429:
                    retry_after = int(response.headers.get("Retry-After", 60))
                    raise RateLimitException(
                        f"Rate limit exceeded for {url}",
                        retry_after=retry_after,
                    )

                # Handle other errors
                if response.status >= 400:
                    if retry_count < self.max_retries:
                        await asyncio.sleep(2 ** retry_count)
                        return await self.get(
                            url, params, headers, retry_count + 1
                        )
                    raise CrawlException(
                        f"HTTP {response.status} error for {url}",
                        url=url,
                        status_code=response.status,
                    )

                return {
                    "status": response.status,
                    "headers": dict(response.headers),
                    "content": content,
                    "url": str(response.url),
                }

        except aiohttp.ClientError as e:
            if retry_count < self.max_retries:
                await asyncio.sleep(2 ** retry_count)
                return await self.get(url, params, headers, retry_count + 1)
            raise CrawlException(f"Request failed for {url}: {str(e)}", url=url)
        except asyncio.TimeoutError:
            if retry_count < self.max_retries:
                await asyncio.sleep(2 ** retry_count)
                return await self.get(url, params, headers, retry_count + 1)
            raise CrawlException(f"Request timeout for {url}", url=url)

    async def post(
        self,
        url: str,
        data: Optional[Dict[str, Any]] = None,
        json: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        retry_count: int = 0,
    ) -> Dict[str, Any]:
        """
        Make POST request.

        Args:
            url: URL to request
            data: Form data
            json: JSON data
            headers: Additional headers
            retry_count: Current retry attempt

        Returns:
            Response data

        Raises:
            APIException: If request fails
        """
        session = await self.get_session()

        try:
            logger.debug(f"POST request to {url}")
            async with session.post(
                url, data=data, json=json, headers=headers
            ) as response:
                content = await response.text()

                if response.status == 429:
                    retry_after = int(response.headers.get("Retry-After", 60))
                    raise RateLimitException(
                        f"Rate limit exceeded for {url}",
                        retry_after=retry_after,
                    )

                if response.status >= 400:
                    if retry_count < self.max_retries:
                        await asyncio.sleep(2 ** retry_count)
                        return await self.post(
                            url, data, json, headers, retry_count + 1
                        )
                    raise APIException(
                        f"HTTP {response.status} error for {url}",
                        status_code=response.status,
                    )

                return {
                    "status": response.status,
                    "headers": dict(response.headers),
                    "content": content,
                    "url": str(response.url),
                }

        except aiohttp.ClientError as e:
            if retry_count < self.max_retries:
                await asyncio.sleep(2 ** retry_count)
                return await self.post(url, data, json, headers, retry_count + 1)
            raise APIException(f"Request failed for {url}: {str(e)}")

    async def fetch_url(self, url: str) -> Optional[str]:
        """
        Fetch URL content with error handling.

        Args:
            url: URL to fetch

        Returns:
            HTML content or None if failed
        """
        try:
            response = await self.get(url)
            return response.get("content")
        except Exception as e:
            logger.error(f"Failed to fetch {url}: {e}")
            return None

    def __del__(self):
        """Cleanup on deletion."""
        if self._session and not self._session.closed:
            try:
                asyncio.create_task(self.close())
            except RuntimeError:
                pass
