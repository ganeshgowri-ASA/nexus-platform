"""
AI Cost Tracking and Usage Analytics

Tracks token usage, calculates costs per model, and provides usage statistics
for budget management and optimization.
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from decimal import Decimal
from collections import defaultdict
import json


class CostTracker:
    """
    Tracks AI API usage costs and provides analytics.

    Features:
    - Token counting per request
    - Cost calculation per model
    - Usage statistics (daily/weekly/monthly)
    - Per-user tracking
    - Budget alerts
    - Cost optimization suggestions
    """

    # Pricing per 1M tokens (input, output) - as of 2025
    PRICING = {
        # Claude models
        "claude-3-opus-20240229": (Decimal("15.00"), Decimal("75.00")),
        "claude-3-5-sonnet-20241022": (Decimal("3.00"), Decimal("15.00")),
        "claude-3-haiku-20240307": (Decimal("0.25"), Decimal("1.25")),

        # OpenAI models
        "gpt-4-turbo-preview": (Decimal("10.00"), Decimal("30.00")),
        "gpt-4": (Decimal("30.00"), Decimal("60.00")),
        "gpt-3.5-turbo": (Decimal("0.50"), Decimal("1.50")),
        "gpt-4o": (Decimal("5.00"), Decimal("15.00")),

        # Google Gemini models
        "gemini-pro": (Decimal("0.50"), Decimal("1.50")),
        "gemini-pro-vision": (Decimal("0.50"), Decimal("1.50")),
        "gemini-1.5-pro": (Decimal("3.50"), Decimal("10.50")),
    }

    def __init__(self):
        """Initialize cost tracker with empty usage data."""
        self.usage_log: List[Dict] = []
        self.user_usage: Dict[int, List[Dict]] = defaultdict(list)
        self.daily_costs: Dict[str, Decimal] = defaultdict(Decimal)
        self.monthly_budget: Optional[Decimal] = None
        self.budget_alert_threshold: Decimal = Decimal("0.8")  # 80%

    def track_request(
        self,
        user_id: int,
        model: str,
        input_tokens: int,
        output_tokens: int,
        task_type: str,
        module: str,
        cached: bool = False,
        cache_savings: Decimal = Decimal("0")
    ) -> Dict:
        """
        Track a single AI request and calculate its cost.

        Args:
            user_id: User making the request
            model: AI model used
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens
            task_type: Type of task (writing, coding, analysis, etc.)
            module: Module requesting AI (word, excel, email, etc.)
            cached: Whether response was served from cache
            cache_savings: Cost saved by using cache

        Returns:
            Dictionary with request details and cost
        """
        timestamp = datetime.utcnow()

        # Calculate cost
        if cached:
            cost = Decimal("0")
        else:
            cost = self.calculate_cost(model, input_tokens, output_tokens)

        # Create usage entry
        entry = {
            "timestamp": timestamp.isoformat(),
            "user_id": user_id,
            "model": model,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "total_tokens": input_tokens + output_tokens,
            "cost": float(cost),
            "task_type": task_type,
            "module": module,
            "cached": cached,
            "cache_savings": float(cache_savings),
        }

        # Store in logs
        self.usage_log.append(entry)
        self.user_usage[user_id].append(entry)

        # Update daily costs
        date_key = timestamp.strftime("%Y-%m-%d")
        self.daily_costs[date_key] += cost

        # Check budget alerts
        if self.monthly_budget:
            self._check_budget_alert(timestamp)

        return entry

    def calculate_cost(
        self,
        model: str,
        input_tokens: int,
        output_tokens: int
    ) -> Decimal:
        """
        Calculate cost for a request.

        Args:
            model: AI model name
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens

        Returns:
            Cost in USD
        """
        if model not in self.PRICING:
            # Unknown model, use average pricing
            input_price = Decimal("5.00")
            output_price = Decimal("15.00")
        else:
            input_price, output_price = self.PRICING[model]

        # Calculate cost (price is per 1M tokens)
        input_cost = (Decimal(input_tokens) / Decimal("1000000")) * input_price
        output_cost = (Decimal(output_tokens) / Decimal("1000000")) * output_price

        return input_cost + output_cost

    def get_user_usage(
        self,
        user_id: int,
        period: str = "day"
    ) -> Dict:
        """
        Get usage statistics for a specific user.

        Args:
            user_id: User ID
            period: Time period (day, week, month, all)

        Returns:
            Dictionary with usage statistics
        """
        now = datetime.utcnow()

        # Determine time filter
        if period == "day":
            start_time = now - timedelta(days=1)
        elif period == "week":
            start_time = now - timedelta(days=7)
        elif period == "month":
            start_time = now - timedelta(days=30)
        else:
            start_time = datetime.min

        # Filter user entries
        entries = [
            e for e in self.user_usage[user_id]
            if datetime.fromisoformat(e["timestamp"]) >= start_time
        ]

        if not entries:
            return {
                "total_requests": 0,
                "total_tokens": 0,
                "total_cost": 0.0,
                "by_model": {},
                "by_module": {},
                "cache_hit_rate": 0.0,
                "total_cache_savings": 0.0,
            }

        # Calculate statistics
        total_requests = len(entries)
        total_tokens = sum(e["total_tokens"] for e in entries)
        total_cost = sum(Decimal(str(e["cost"])) for e in entries)
        cached_requests = sum(1 for e in entries if e["cached"])
        cache_savings = sum(Decimal(str(e["cache_savings"])) for e in entries)

        # Group by model
        by_model = defaultdict(lambda: {"requests": 0, "tokens": 0, "cost": Decimal("0")})
        for entry in entries:
            model = entry["model"]
            by_model[model]["requests"] += 1
            by_model[model]["tokens"] += entry["total_tokens"]
            by_model[model]["cost"] += Decimal(str(entry["cost"]))

        # Group by module
        by_module = defaultdict(lambda: {"requests": 0, "tokens": 0, "cost": Decimal("0")})
        for entry in entries:
            module = entry["module"]
            by_module[module]["requests"] += 1
            by_module[module]["tokens"] += entry["total_tokens"]
            by_module[module]["cost"] += Decimal(str(entry["cost"]))

        return {
            "total_requests": total_requests,
            "total_tokens": total_tokens,
            "total_cost": float(total_cost),
            "by_model": {
                k: {
                    "requests": v["requests"],
                    "tokens": v["tokens"],
                    "cost": float(v["cost"])
                }
                for k, v in by_model.items()
            },
            "by_module": {
                k: {
                    "requests": v["requests"],
                    "tokens": v["tokens"],
                    "cost": float(v["cost"])
                }
                for k, v in by_module.items()
            },
            "cache_hit_rate": (cached_requests / total_requests) * 100 if total_requests > 0 else 0.0,
            "total_cache_savings": float(cache_savings),
        }

    def get_daily_costs(self, days: int = 30) -> Dict[str, float]:
        """
        Get daily costs for the last N days.

        Args:
            days: Number of days to retrieve

        Returns:
            Dictionary mapping date to cost
        """
        result = {}
        for i in range(days):
            date = datetime.utcnow() - timedelta(days=i)
            date_key = date.strftime("%Y-%m-%d")
            result[date_key] = float(self.daily_costs.get(date_key, Decimal("0")))

        return dict(sorted(result.items()))

    def get_monthly_total(self) -> float:
        """
        Get total cost for the current month.

        Returns:
            Total monthly cost in USD
        """
        now = datetime.utcnow()
        month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

        total = Decimal("0")
        for date_str, cost in self.daily_costs.items():
            date = datetime.strptime(date_str, "%Y-%m-%d")
            if date >= month_start:
                total += cost

        return float(total)

    def set_monthly_budget(self, budget: float):
        """Set monthly budget for alert tracking."""
        self.monthly_budget = Decimal(str(budget))

    def _check_budget_alert(self, timestamp: datetime) -> Optional[Dict]:
        """
        Check if budget alert threshold has been exceeded.

        Returns:
            Alert dictionary if threshold exceeded, None otherwise
        """
        if not self.monthly_budget:
            return None

        monthly_total = Decimal(str(self.get_monthly_total()))
        threshold = self.monthly_budget * self.budget_alert_threshold

        if monthly_total >= threshold:
            return {
                "type": "budget_alert",
                "timestamp": timestamp.isoformat(),
                "monthly_total": float(monthly_total),
                "budget": float(self.monthly_budget),
                "percentage": float((monthly_total / self.monthly_budget) * 100),
            }

        return None

    def get_optimization_suggestions(self, user_id: int) -> List[Dict]:
        """
        Analyze usage patterns and provide cost optimization suggestions.

        Args:
            user_id: User ID to analyze

        Returns:
            List of optimization suggestions
        """
        suggestions = []

        # Get last 30 days of usage
        stats = self.get_user_usage(user_id, period="month")

        if stats["total_requests"] == 0:
            return suggestions

        # Check cache hit rate
        if stats["cache_hit_rate"] < 50:
            suggestions.append({
                "type": "cache",
                "priority": "high",
                "message": f"Cache hit rate is {stats['cache_hit_rate']:.1f}%. Enable caching for repeated queries to reduce costs.",
                "potential_savings": stats["total_cost"] * 0.5,  # Estimate 50% savings
            })

        # Check model usage
        by_model = stats["by_model"]
        expensive_usage = 0
        total_requests = stats["total_requests"]

        for model, data in by_model.items():
            if model in ["gpt-4", "claude-3-opus-20240229"]:
                expensive_usage += data["requests"]

        if expensive_usage / total_requests > 0.5:
            suggestions.append({
                "type": "model_selection",
                "priority": "medium",
                "message": f"{(expensive_usage/total_requests)*100:.1f}% of requests use expensive models. Consider using GPT-3.5 or Claude Haiku for simpler tasks.",
                "potential_savings": stats["total_cost"] * 0.3,  # Estimate 30% savings
            })

        # Check for low cache usage
        if stats["total_cache_savings"] > 0:
            roi = (stats["total_cache_savings"] / stats["total_cost"]) * 100
            if roi > 50:
                suggestions.append({
                    "type": "cache_success",
                    "priority": "info",
                    "message": f"Caching is saving {roi:.1f}% of costs. Great job!",
                    "potential_savings": 0,
                })

        return suggestions

    def export_usage_report(self, user_id: int, period: str = "month") -> str:
        """
        Export usage report as JSON.

        Args:
            user_id: User ID
            period: Time period

        Returns:
            JSON string with usage report
        """
        stats = self.get_user_usage(user_id, period)
        suggestions = self.get_optimization_suggestions(user_id)

        report = {
            "period": period,
            "generated_at": datetime.utcnow().isoformat(),
            "user_id": user_id,
            "statistics": stats,
            "optimization_suggestions": suggestions,
        }

        return json.dumps(report, indent=2)


# Global cost tracker instance
cost_tracker = CostTracker()
