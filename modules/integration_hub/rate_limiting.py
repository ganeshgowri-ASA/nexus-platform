"""
Rate limiting and throttle management system.

Handles API rate limiting, request throttling, and backoff strategies
to prevent exceeding API quotas.
"""

from typing import Dict, Any, Optional
from datetime import datetime, timedelta
import logging
import asyncio
from sqlalchemy.orm import Session
from sqlalchemy import and_

from .models import RateLimitTracker, Connection

logger = logging.getLogger(__name__)


class RateLimitExceeded(Exception):
    """Raised when rate limit is exceeded."""
    def __init__(self, message: str, retry_after: int):
        super().__init__(message)
        self.retry_after = retry_after


class RateLimiter:
    """
    Manages API rate limiting for connections.

    Tracks request counts and enforces rate limits based on
    provider-specific quotas.
    """

    def __init__(self, db: Session):
        """
        Initialize rate limiter.

        Args:
            db: Database session
        """
        self.db = db
        self._in_memory_cache: Dict[int, Dict[str, Any]] = {}

    async def check_rate_limit(
        self,
        connection_id: int,
        requests_needed: int = 1
    ) -> bool:
        """
        Check if request is within rate limit.

        Args:
            connection_id: Connection ID
            requests_needed: Number of requests needed

        Returns:
            True if within limit

        Raises:
            RateLimitExceeded: If rate limit exceeded
        """
        connection = self.db.query(Connection).filter(
            Connection.id == connection_id
        ).first()

        if not connection or not connection.integration:
            return True

        integration = connection.integration
        rate_limit = integration.rate_limit_requests
        period = integration.rate_limit_period

        if not rate_limit or not period:
            return True  # No rate limiting configured

        # Get current window
        now = datetime.now()
        window_start = now.replace(second=0, microsecond=0)
        window_end = window_start + timedelta(seconds=period)

        # Get or create tracker
        tracker = self.db.query(RateLimitTracker).filter(
            and_(
                RateLimitTracker.connection_id == connection_id,
                RateLimitTracker.window_start == window_start
            )
        ).first()

        if not tracker:
            tracker = RateLimitTracker(
                connection_id=connection_id,
                window_start=window_start,
                window_end=window_end,
                request_count=0,
                limit=rate_limit
            )
            self.db.add(tracker)
            self.db.commit()

        # Check if adding requests would exceed limit
        if tracker.request_count + requests_needed > rate_limit:
            retry_after = int((window_end - now).total_seconds())

            tracker.is_throttled = True
            tracker.throttle_until = window_end
            self.db.commit()

            raise RateLimitExceeded(
                f"Rate limit exceeded: {tracker.request_count}/{rate_limit}",
                retry_after=retry_after
            )

        return True

    async def record_request(
        self,
        connection_id: int,
        requests: int = 1
    ) -> None:
        """
        Record API request(s).

        Args:
            connection_id: Connection ID
            requests: Number of requests made
        """
        connection = self.db.query(Connection).filter(
            Connection.id == connection_id
        ).first()

        if not connection or not connection.integration:
            return

        rate_limit = connection.integration.rate_limit_requests
        period = connection.integration.rate_limit_period

        if not rate_limit or not period:
            return

        now = datetime.now()
        window_start = now.replace(second=0, microsecond=0)
        window_end = window_start + timedelta(seconds=period)

        # Get or create tracker
        tracker = self.db.query(RateLimitTracker).filter(
            and_(
                RateLimitTracker.connection_id == connection_id,
                RateLimitTracker.window_start == window_start
            )
        ).first()

        if not tracker:
            tracker = RateLimitTracker(
                connection_id=connection_id,
                window_start=window_start,
                window_end=window_end,
                request_count=0,
                limit=rate_limit
            )
            self.db.add(tracker)

        tracker.request_count += requests
        tracker.updated_at = now
        self.db.commit()

        logger.debug(f"Recorded {requests} request(s) for connection {connection_id}: {tracker.request_count}/{rate_limit}")

    def get_remaining_requests(self, connection_id: int) -> Optional[int]:
        """
        Get number of remaining requests in current window.

        Args:
            connection_id: Connection ID

        Returns:
            Number of remaining requests, or None if no limit
        """
        connection = self.db.query(Connection).filter(
            Connection.id == connection_id
        ).first()

        if not connection or not connection.integration:
            return None

        rate_limit = connection.integration.rate_limit_requests
        period = connection.integration.rate_limit_period

        if not rate_limit or not period:
            return None

        now = datetime.now()
        window_start = now.replace(second=0, microsecond=0)

        tracker = self.db.query(RateLimitTracker).filter(
            and_(
                RateLimitTracker.connection_id == connection_id,
                RateLimitTracker.window_start == window_start
            )
        ).first()

        if not tracker:
            return rate_limit

        return max(0, rate_limit - tracker.request_count)

    async def wait_if_needed(
        self,
        connection_id: int,
        requests_needed: int = 1
    ) -> None:
        """
        Wait if rate limit would be exceeded.

        Args:
            connection_id: Connection ID
            requests_needed: Number of requests needed
        """
        try:
            await self.check_rate_limit(connection_id, requests_needed)
        except RateLimitExceeded as e:
            logger.info(f"Rate limit exceeded, waiting {e.retry_after}s")
            await asyncio.sleep(e.retry_after)


class ThrottleManager:
    """
    Manages request throttling with various strategies.

    Implements adaptive throttling based on API responses and
    usage patterns.
    """

    def __init__(self, db: Session):
        """
        Initialize throttle manager.

        Args:
            db: Database session
        """
        self.db = db
        self._throttle_state: Dict[int, Dict[str, Any]] = {}

    async def throttle(
        self,
        connection_id: int,
        strategy: str = 'fixed'
    ) -> None:
        """
        Apply throttling delay.

        Args:
            connection_id: Connection ID
            strategy: Throttling strategy ('fixed', 'adaptive', 'exponential')
        """
        if strategy == 'fixed':
            await self._fixed_throttle(connection_id)
        elif strategy == 'adaptive':
            await self._adaptive_throttle(connection_id)
        elif strategy == 'exponential':
            await self._exponential_throttle(connection_id)

    async def _fixed_throttle(self, connection_id: int) -> None:
        """Apply fixed delay between requests."""
        delay = 0.1  # 100ms default
        await asyncio.sleep(delay)

    async def _adaptive_throttle(self, connection_id: int) -> None:
        """Adapt delay based on recent error rates."""
        state = self._throttle_state.get(connection_id, {
            'errors': 0,
            'successes': 0,
            'delay': 0.1
        })

        # Adjust delay based on error rate
        if state['errors'] > 0:
            error_rate = state['errors'] / (state['errors'] + state['successes'])
            if error_rate > 0.1:  # More than 10% errors
                state['delay'] = min(state['delay'] * 1.5, 5.0)  # Increase delay
        else:
            state['delay'] = max(state['delay'] * 0.9, 0.05)  # Decrease delay

        self._throttle_state[connection_id] = state
        await asyncio.sleep(state['delay'])

    async def _exponential_throttle(self, connection_id: int) -> None:
        """Apply exponential backoff."""
        state = self._throttle_state.get(connection_id, {'retry_count': 0})
        delay = min(2 ** state['retry_count'], 60)  # Cap at 60 seconds
        await asyncio.sleep(delay)

    def record_success(self, connection_id: int) -> None:
        """Record successful request."""
        if connection_id in self._throttle_state:
            self._throttle_state[connection_id]['successes'] += 1
            self._throttle_state[connection_id]['retry_count'] = 0

    def record_error(self, connection_id: int) -> None:
        """Record failed request."""
        if connection_id not in self._throttle_state:
            self._throttle_state[connection_id] = {
                'errors': 0,
                'successes': 0,
                'retry_count': 0,
                'delay': 0.1
            }

        self._throttle_state[connection_id]['errors'] += 1
        self._throttle_state[connection_id]['retry_count'] += 1


class BackoffStrategy:
    """
    Implements various backoff strategies for retries.

    Provides exponential, linear, and custom backoff algorithms.
    """

    @staticmethod
    def exponential_backoff(
        attempt: int,
        base_delay: float = 1.0,
        max_delay: float = 60.0,
        exponential_base: float = 2.0
    ) -> float:
        """
        Calculate exponential backoff delay.

        Args:
            attempt: Retry attempt number (0-indexed)
            base_delay: Base delay in seconds
            max_delay: Maximum delay in seconds
            exponential_base: Exponential base

        Returns:
            Delay in seconds
        """
        delay = base_delay * (exponential_base ** attempt)
        return min(delay, max_delay)

    @staticmethod
    def linear_backoff(
        attempt: int,
        base_delay: float = 1.0,
        increment: float = 1.0,
        max_delay: float = 60.0
    ) -> float:
        """
        Calculate linear backoff delay.

        Args:
            attempt: Retry attempt number (0-indexed)
            base_delay: Base delay in seconds
            increment: Delay increment per attempt
            max_delay: Maximum delay in seconds

        Returns:
            Delay in seconds
        """
        delay = base_delay + (increment * attempt)
        return min(delay, max_delay)

    @staticmethod
    def fibonacci_backoff(
        attempt: int,
        base_delay: float = 1.0,
        max_delay: float = 60.0
    ) -> float:
        """
        Calculate Fibonacci backoff delay.

        Args:
            attempt: Retry attempt number (0-indexed)
            base_delay: Base delay in seconds
            max_delay: Maximum delay in seconds

        Returns:
            Delay in seconds
        """
        def fibonacci(n):
            if n <= 1:
                return n
            a, b = 0, 1
            for _ in range(n - 1):
                a, b = b, a + b
            return b

        delay = base_delay * fibonacci(attempt + 1)
        return min(delay, max_delay)

    @staticmethod
    def jittered_backoff(
        attempt: int,
        base_delay: float = 1.0,
        max_delay: float = 60.0
    ) -> float:
        """
        Calculate exponential backoff with jitter.

        Args:
            attempt: Retry attempt number (0-indexed)
            base_delay: Base delay in seconds
            max_delay: Maximum delay in seconds

        Returns:
            Delay in seconds with random jitter
        """
        import random

        delay = base_delay * (2 ** attempt)
        # Add random jitter (±20%)
        jitter = delay * random.uniform(-0.2, 0.2)
        return min(delay + jitter, max_delay)
