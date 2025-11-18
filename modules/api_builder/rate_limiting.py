"""
Rate Limiting Module

Handles request limits, throttling, quota management, and tiered plans.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from enum import Enum
from datetime import datetime, timedelta
import time
from collections import deque


class RateLimitPeriod(Enum):
    """Time periods for rate limiting."""
    SECOND = "second"
    MINUTE = "minute"
    HOUR = "hour"
    DAY = "day"
    MONTH = "month"


class ThrottleStrategy(Enum):
    """Throttling strategies."""
    FIXED_WINDOW = "fixed_window"
    SLIDING_WINDOW = "sliding_window"
    TOKEN_BUCKET = "token_bucket"
    LEAKY_BUCKET = "leaky_bucket"


@dataclass
class RateLimitRule:
    """Represents a rate limiting rule."""
    name: str
    max_requests: int
    period: RateLimitPeriod
    period_value: int = 1  # Number of periods (e.g., 2 hours = period_value=2, period=HOUR)
    description: str = ""
    enabled: bool = True

    def get_period_seconds(self) -> int:
        """Get the period in seconds."""
        base_seconds = {
            RateLimitPeriod.SECOND: 1,
            RateLimitPeriod.MINUTE: 60,
            RateLimitPeriod.HOUR: 3600,
            RateLimitPeriod.DAY: 86400,
            RateLimitPeriod.MONTH: 2592000,  # 30 days
        }
        return base_seconds[self.period] * self.period_value

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "max_requests": self.max_requests,
            "period": self.period.value,
            "period_value": self.period_value,
            "description": self.description,
            "enabled": self.enabled,
        }


@dataclass
class RateLimitInfo:
    """Information about current rate limit status."""
    limit: int
    remaining: int
    reset_time: datetime
    retry_after: Optional[int] = None  # Seconds until retry

    def to_headers(self) -> Dict[str, str]:
        """Convert to HTTP headers."""
        headers = {
            "X-RateLimit-Limit": str(self.limit),
            "X-RateLimit-Remaining": str(self.remaining),
            "X-RateLimit-Reset": str(int(self.reset_time.timestamp())),
        }

        if self.retry_after:
            headers["Retry-After"] = str(self.retry_after)

        return headers


class FixedWindowCounter:
    """Fixed window rate limiting."""

    def __init__(self, rule: RateLimitRule):
        self.rule = rule
        self.counters: Dict[str, Dict[str, Any]] = {}

    def check_limit(self, key: str) -> tuple[bool, RateLimitInfo]:
        """Check if request is within rate limit."""
        now = time.time()
        period_seconds = self.rule.get_period_seconds()

        if key not in self.counters:
            self.counters[key] = {
                "count": 0,
                "window_start": now,
            }

        counter = self.counters[key]
        window_start = counter["window_start"]

        # Reset if window has passed
        if now - window_start >= period_seconds:
            counter["count"] = 0
            counter["window_start"] = now

        # Check limit
        is_allowed = counter["count"] < self.rule.max_requests

        if is_allowed:
            counter["count"] += 1

        reset_time = datetime.fromtimestamp(window_start + period_seconds)
        remaining = max(0, self.rule.max_requests - counter["count"])
        retry_after = None if is_allowed else int(reset_time.timestamp() - now)

        info = RateLimitInfo(
            limit=self.rule.max_requests,
            remaining=remaining,
            reset_time=reset_time,
            retry_after=retry_after,
        )

        return is_allowed, info


class SlidingWindowCounter:
    """Sliding window rate limiting."""

    def __init__(self, rule: RateLimitRule):
        self.rule = rule
        self.windows: Dict[str, deque] = {}

    def check_limit(self, key: str) -> tuple[bool, RateLimitInfo]:
        """Check if request is within rate limit."""
        now = time.time()
        period_seconds = self.rule.get_period_seconds()

        if key not in self.windows:
            self.windows[key] = deque()

        window = self.windows[key]

        # Remove old requests outside the window
        while window and window[0] < now - period_seconds:
            window.popleft()

        # Check limit
        is_allowed = len(window) < self.rule.max_requests

        if is_allowed:
            window.append(now)

        # Calculate reset time (when oldest request expires)
        reset_time = datetime.fromtimestamp(
            window[0] + period_seconds if window else now + period_seconds
        )

        remaining = max(0, self.rule.max_requests - len(window))
        retry_after = None if is_allowed else int((window[0] + period_seconds) - now)

        info = RateLimitInfo(
            limit=self.rule.max_requests,
            remaining=remaining,
            reset_time=reset_time,
            retry_after=retry_after,
        )

        return is_allowed, info


class TokenBucket:
    """Token bucket rate limiting."""

    def __init__(self, rule: RateLimitRule):
        self.rule = rule
        self.buckets: Dict[str, Dict[str, Any]] = {}

    def check_limit(self, key: str, tokens: int = 1) -> tuple[bool, RateLimitInfo]:
        """Check if request is within rate limit."""
        now = time.time()
        period_seconds = self.rule.get_period_seconds()

        if key not in self.buckets:
            self.buckets[key] = {
                "tokens": self.rule.max_requests,
                "last_refill": now,
            }

        bucket = self.buckets[key]

        # Refill tokens
        time_passed = now - bucket["last_refill"]
        refill_rate = self.rule.max_requests / period_seconds
        new_tokens = time_passed * refill_rate

        bucket["tokens"] = min(
            self.rule.max_requests,
            bucket["tokens"] + new_tokens
        )
        bucket["last_refill"] = now

        # Check if enough tokens
        is_allowed = bucket["tokens"] >= tokens

        if is_allowed:
            bucket["tokens"] -= tokens

        # Calculate when next token will be available
        time_until_token = (tokens - bucket["tokens"]) / refill_rate if not is_allowed else 0
        reset_time = datetime.fromtimestamp(now + time_until_token)

        info = RateLimitInfo(
            limit=self.rule.max_requests,
            remaining=int(bucket["tokens"]),
            reset_time=reset_time,
            retry_after=int(time_until_token) if not is_allowed else None,
        )

        return is_allowed, info


class ThrottlePolicy:
    """Manages throttling for rate limiting."""

    def __init__(
        self,
        rule: RateLimitRule,
        strategy: ThrottleStrategy = ThrottleStrategy.SLIDING_WINDOW,
    ):
        self.rule = rule
        self.strategy = strategy

        # Initialize appropriate counter
        if strategy == ThrottleStrategy.FIXED_WINDOW:
            self.counter = FixedWindowCounter(rule)
        elif strategy == ThrottleStrategy.SLIDING_WINDOW:
            self.counter = SlidingWindowCounter(rule)
        elif strategy == ThrottleStrategy.TOKEN_BUCKET:
            self.counter = TokenBucket(rule)
        else:
            raise ValueError(f"Unsupported strategy: {strategy}")

    def check_limit(self, identifier: str) -> tuple[bool, RateLimitInfo]:
        """Check if request should be allowed."""
        if not self.rule.enabled:
            # If disabled, always allow
            info = RateLimitInfo(
                limit=self.rule.max_requests,
                remaining=self.rule.max_requests,
                reset_time=datetime.now(),
            )
            return True, info

        return self.counter.check_limit(identifier)


@dataclass
class QuotaPlan:
    """Represents a quota plan (e.g., free, pro, enterprise)."""
    name: str
    daily_quota: Optional[int] = None
    monthly_quota: Optional[int] = None
    rate_limit_rules: List[RateLimitRule] = field(default_factory=list)
    features: List[str] = field(default_factory=list)
    price: float = 0.0
    description: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "daily_quota": self.daily_quota,
            "monthly_quota": self.monthly_quota,
            "rate_limit_rules": [rule.to_dict() for rule in self.rate_limit_rules],
            "features": self.features,
            "price": self.price,
            "description": self.description,
        }


class QuotaManager:
    """Manages user quotas and usage."""

    def __init__(self):
        self.plans: Dict[str, QuotaPlan] = {}
        self.user_plans: Dict[str, str] = {}  # user_id -> plan_name
        self.usage: Dict[str, Dict[str, int]] = {}  # user_id -> {daily: count, monthly: count}
        self.last_reset: Dict[str, Dict[str, datetime]] = {}  # user_id -> {daily: time, monthly: time}

    def add_plan(self, plan: QuotaPlan) -> None:
        """Add a quota plan."""
        self.plans[plan.name] = plan

    def assign_plan(self, user_id: str, plan_name: str) -> bool:
        """Assign a plan to a user."""
        if plan_name not in self.plans:
            return False

        self.user_plans[user_id] = plan_name
        self._init_user_usage(user_id)
        return True

    def _init_user_usage(self, user_id: str) -> None:
        """Initialize usage tracking for a user."""
        if user_id not in self.usage:
            self.usage[user_id] = {"daily": 0, "monthly": 0}
            self.last_reset[user_id] = {
                "daily": datetime.now(),
                "monthly": datetime.now(),
            }

    def _reset_if_needed(self, user_id: str) -> None:
        """Reset quotas if period has passed."""
        now = datetime.now()

        # Check daily reset
        last_daily = self.last_reset[user_id]["daily"]
        if (now - last_daily).days >= 1:
            self.usage[user_id]["daily"] = 0
            self.last_reset[user_id]["daily"] = now

        # Check monthly reset
        last_monthly = self.last_reset[user_id]["monthly"]
        if (now - last_monthly).days >= 30:
            self.usage[user_id]["monthly"] = 0
            self.last_reset[user_id]["monthly"] = now

    def check_quota(self, user_id: str) -> tuple[bool, Optional[str]]:
        """Check if user is within quota."""
        if user_id not in self.user_plans:
            return False, "No plan assigned"

        self._init_user_usage(user_id)
        self._reset_if_needed(user_id)

        plan = self.plans[self.user_plans[user_id]]

        # Check daily quota
        if plan.daily_quota is not None:
            if self.usage[user_id]["daily"] >= plan.daily_quota:
                return False, "Daily quota exceeded"

        # Check monthly quota
        if plan.monthly_quota is not None:
            if self.usage[user_id]["monthly"] >= plan.monthly_quota:
                return False, "Monthly quota exceeded"

        return True, None

    def increment_usage(self, user_id: str) -> None:
        """Increment usage counters."""
        self._init_user_usage(user_id)
        self._reset_if_needed(user_id)

        self.usage[user_id]["daily"] += 1
        self.usage[user_id]["monthly"] += 1

    def get_usage(self, user_id: str) -> Dict[str, Any]:
        """Get current usage for a user."""
        if user_id not in self.user_plans:
            return {}

        self._init_user_usage(user_id)
        self._reset_if_needed(user_id)

        plan = self.plans[self.user_plans[user_id]]

        return {
            "plan": plan.name,
            "daily": {
                "used": self.usage[user_id]["daily"],
                "limit": plan.daily_quota,
                "remaining": (plan.daily_quota - self.usage[user_id]["daily"]) if plan.daily_quota else None,
            },
            "monthly": {
                "used": self.usage[user_id]["monthly"],
                "limit": plan.monthly_quota,
                "remaining": (plan.monthly_quota - self.usage[user_id]["monthly"]) if plan.monthly_quota else None,
            },
        }


class RateLimiter:
    """Main rate limiting manager."""

    def __init__(self):
        self.policies: Dict[str, ThrottlePolicy] = {}
        self.endpoint_policies: Dict[str, List[str]] = {}  # endpoint_id -> [policy_names]
        self.quota_manager = QuotaManager()

    def add_policy(
        self,
        name: str,
        rule: RateLimitRule,
        strategy: ThrottleStrategy = ThrottleStrategy.SLIDING_WINDOW,
    ) -> None:
        """Add a rate limit policy."""
        self.policies[name] = ThrottlePolicy(rule, strategy)

    def apply_to_endpoint(self, endpoint_id: str, policy_names: List[str]) -> None:
        """Apply rate limit policies to an endpoint."""
        self.endpoint_policies[endpoint_id] = policy_names

    def check_limits(
        self,
        endpoint_id: str,
        identifier: str,
        user_id: Optional[str] = None,
    ) -> tuple[bool, List[RateLimitInfo], Optional[str]]:
        """Check all rate limits for an endpoint."""
        infos = []

        # Check quota if user_id provided
        if user_id:
            quota_ok, quota_error = self.quota_manager.check_quota(user_id)
            if not quota_ok:
                return False, infos, quota_error

        # Check rate limit policies
        policy_names = self.endpoint_policies.get(endpoint_id, [])

        for policy_name in policy_names:
            if policy_name not in self.policies:
                continue

            policy = self.policies[policy_name]
            is_allowed, info = policy.check_limit(identifier)
            infos.append(info)

            if not is_allowed:
                return False, infos, f"Rate limit exceeded: {policy.rule.name}"

        # Increment quota if all checks passed
        if user_id:
            self.quota_manager.increment_usage(user_id)

        return True, infos, None

    def get_rate_limit_headers(self, infos: List[RateLimitInfo]) -> Dict[str, str]:
        """Get rate limit headers from all infos (use most restrictive)."""
        if not infos:
            return {}

        # Use the most restrictive limit
        most_restrictive = min(infos, key=lambda x: x.remaining)
        return most_restrictive.to_headers()


# Predefined quota plans

def create_free_plan() -> QuotaPlan:
    """Create a free tier plan."""
    return QuotaPlan(
        name="free",
        daily_quota=1000,
        monthly_quota=10000,
        rate_limit_rules=[
            RateLimitRule(
                name="free_rate_limit",
                max_requests=10,
                period=RateLimitPeriod.MINUTE,
                description="10 requests per minute",
            )
        ],
        features=["Basic API access", "Community support"],
        price=0.0,
        description="Free tier with basic limits",
    )


def create_pro_plan() -> QuotaPlan:
    """Create a pro tier plan."""
    return QuotaPlan(
        name="pro",
        daily_quota=100000,
        monthly_quota=1000000,
        rate_limit_rules=[
            RateLimitRule(
                name="pro_rate_limit",
                max_requests=100,
                period=RateLimitPeriod.MINUTE,
                description="100 requests per minute",
            )
        ],
        features=["Advanced API access", "Priority support", "Analytics"],
        price=29.99,
        description="Professional tier with higher limits",
    )


def create_enterprise_plan() -> QuotaPlan:
    """Create an enterprise tier plan."""
    return QuotaPlan(
        name="enterprise",
        daily_quota=None,  # Unlimited
        monthly_quota=None,  # Unlimited
        rate_limit_rules=[
            RateLimitRule(
                name="enterprise_rate_limit",
                max_requests=1000,
                period=RateLimitPeriod.MINUTE,
                description="1000 requests per minute",
            )
        ],
        features=[
            "Unlimited API access",
            "24/7 support",
            "Custom integrations",
            "SLA guarantees",
        ],
        price=299.99,
        description="Enterprise tier with unlimited access",
    )
