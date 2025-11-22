"""
Sample Metrics Data

Sample metrics data for testing analytics aggregation.
"""

from datetime import datetime, timedelta
from typing import List, Dict, Any
import random

from shared.utils import get_utc_now


def get_sample_metric() -> Dict[str, Any]:
    """Get a single sample metric."""
    return {
        "name": "daily_active_users",
        "metric_type": "gauge",
        "value": 1250.0,
        "period": "day",
        "dimensions": {
            "module": "analytics",
            "region": "us-west"
        },
        "module": "analytics",
        "timestamp": get_utc_now()
    }


def get_sample_metrics(count: int = 10) -> List[Dict[str, Any]]:
    """Get multiple sample metrics."""
    base_time = get_utc_now()
    metrics = []

    for i in range(count):
        metric = get_sample_metric()
        metric["name"] = f"metric_{i}"
        metric["value"] = 100.0 + (i * 10)
        metric["timestamp"] = base_time + timedelta(hours=i)
        metrics.append(metric)

    return metrics


def get_time_series_metrics(
    name: str,
    days: int = 30,
    base_value: float = 1000.0,
    trend: float = 0.0,
    noise: float = 0.1
) -> List[Dict[str, Any]]:
    """
    Get time series metrics with trend and noise.

    Args:
        name: Metric name
        days: Number of days
        base_value: Starting value
        trend: Daily growth rate (0.1 = 10% growth per day)
        noise: Random noise factor (0.1 = ±10%)
    """
    metrics = []
    base_time = get_utc_now()

    for day in range(days):
        # Calculate value with trend
        value = base_value * (1 + trend) ** day

        # Add random noise
        if noise > 0:
            noise_factor = 1 + random.uniform(-noise, noise)
            value *= noise_factor

        metrics.append({
            "name": name,
            "metric_type": "gauge",
            "value": round(value, 2),
            "period": "day",
            "timestamp": base_time - timedelta(days=days - day),
            "dimensions": {}
        })

    return metrics


def get_user_metrics(days: int = 30) -> List[Dict[str, Any]]:
    """Get user-related metrics over time."""
    base_time = get_utc_now()
    metrics = []

    metric_types = [
        ("daily_active_users", 1000, 0.02),
        ("weekly_active_users", 5000, 0.03),
        ("monthly_active_users", 15000, 0.05),
        ("new_users", 100, 0.01)
    ]

    for name, base_value, growth in metric_types:
        for day in range(days):
            value = base_value * (1 + growth) ** day
            value += random.uniform(-value * 0.1, value * 0.1)

            metrics.append({
                "name": name,
                "metric_type": "gauge",
                "value": round(value, 2),
                "period": "day",
                "timestamp": base_time - timedelta(days=days - day)
            })

    return metrics


def get_engagement_metrics(days: int = 30) -> List[Dict[str, Any]]:
    """Get engagement metrics over time."""
    base_time = get_utc_now()
    metrics = []

    metric_configs = [
        ("avg_session_duration", 300, 0.005),  # seconds
        ("avg_page_views_per_session", 5.0, 0.01),
        ("bounce_rate", 45.0, -0.002),  # percentage
        ("conversion_rate", 2.5, 0.003)  # percentage
    ]

    for name, base_value, growth in metric_configs:
        for day in range(days):
            value = base_value * (1 + growth) ** day
            value += random.uniform(-value * 0.05, value * 0.05)

            metrics.append({
                "name": name,
                "metric_type": "gauge",
                "value": round(value, 2),
                "period": "day",
                "timestamp": base_time - timedelta(days=days - day)
            })

    return metrics


def get_revenue_metrics(days: int = 30) -> List[Dict[str, Any]]:
    """Get revenue metrics over time."""
    base_time = get_utc_now()
    metrics = []

    metric_configs = [
        ("daily_revenue", 10000.0, 0.03),
        ("average_order_value", 99.99, 0.01),
        ("total_orders", 100, 0.025),
        ("customer_lifetime_value", 500.0, 0.02)
    ]

    for name, base_value, growth in metric_configs:
        for day in range(days):
            value = base_value * (1 + growth) ** day

            # Add weekly seasonality
            day_of_week = (base_time - timedelta(days=days - day)).weekday()
            if day_of_week in [5, 6]:  # Weekend
                value *= 1.2

            value += random.uniform(-value * 0.1, value * 0.1)

            metrics.append({
                "name": name,
                "metric_type": "gauge",
                "value": round(value, 2),
                "period": "day",
                "timestamp": base_time - timedelta(days=days - day),
                "dimensions": {"currency": "USD"}
            })

    return metrics


def get_performance_metrics(hours: int = 24) -> List[Dict[str, Any]]:
    """Get system performance metrics."""
    base_time = get_utc_now()
    metrics = []

    metric_configs = [
        ("api_response_time", 150.0, 0.01),  # ms
        ("database_query_time", 50.0, 0.005),  # ms
        ("error_rate", 0.5, 0.0),  # percentage
        ("cpu_usage", 45.0, 0.0),  # percentage
        ("memory_usage", 60.0, 0.0)  # percentage
    ]

    for name, base_value, _ in metric_configs:
        for hour in range(hours):
            # Add hourly variation
            hour_of_day = (base_time - timedelta(hours=hours - hour)).hour

            # Higher load during business hours
            if 9 <= hour_of_day <= 17:
                multiplier = 1.3
            else:
                multiplier = 0.7

            value = base_value * multiplier
            value += random.uniform(-value * 0.2, value * 0.2)

            metrics.append({
                "name": name,
                "metric_type": "gauge",
                "value": round(value, 2),
                "period": "hour",
                "timestamp": base_time - timedelta(hours=hours - hour)
            })

    return metrics


def get_traffic_metrics(days: int = 30) -> List[Dict[str, Any]]:
    """Get traffic source metrics."""
    base_time = get_utc_now()
    metrics = []

    sources = ["organic", "direct", "social", "email", "paid"]

    for day in range(days):
        timestamp = base_time - timedelta(days=days - day)

        for source in sources:
            # Different base values for each source
            base_values = {
                "organic": 500,
                "direct": 300,
                "social": 200,
                "email": 150,
                "paid": 250
            }

            value = base_values[source]
            value *= (1 + random.uniform(-0.2, 0.3))

            metrics.append({
                "name": "traffic_by_source",
                "metric_type": "gauge",
                "value": round(value, 2),
                "period": "day",
                "timestamp": timestamp,
                "dimensions": {"source": source}
            })

    return metrics


def get_device_metrics(days: int = 30) -> List[Dict[str, Any]]:
    """Get device breakdown metrics."""
    base_time = get_utc_now()
    metrics = []

    devices = ["mobile", "desktop", "tablet"]

    for day in range(days):
        timestamp = base_time - timedelta(days=days - day)

        # Mobile-first trend
        base_values = {
            "mobile": 600,
            "desktop": 350,
            "tablet": 50
        }

        for device in devices:
            value = base_values[device]

            # Mobile growing, desktop declining
            if device == "mobile":
                value *= (1.01 ** day)
            elif device == "desktop":
                value *= (0.995 ** day)

            value += random.uniform(-value * 0.1, value * 0.1)

            metrics.append({
                "name": "users_by_device",
                "metric_type": "gauge",
                "value": round(value, 2),
                "period": "day",
                "timestamp": timestamp,
                "dimensions": {"device": device}
            })

    return metrics


def get_geo_metrics(days: int = 7) -> List[Dict[str, Any]]:
    """Get geographic metrics."""
    base_time = get_utc_now()
    metrics = []

    countries = ["US", "UK", "DE", "FR", "JP", "CA"]

    for day in range(days):
        timestamp = base_time - timedelta(days=days - day)

        for country in countries:
            # Different user bases per country
            base_values = {
                "US": 1000,
                "UK": 400,
                "DE": 300,
                "FR": 250,
                "JP": 200,
                "CA": 150
            }

            value = base_values.get(country, 100)
            value += random.uniform(-value * 0.15, value * 0.15)

            metrics.append({
                "name": "users_by_country",
                "metric_type": "gauge",
                "value": round(value, 2),
                "period": "day",
                "timestamp": timestamp,
                "dimensions": {"country": country}
            })

    return metrics


def get_seasonal_metrics(days: int = 90) -> List[Dict[str, Any]]:
    """Get metrics with seasonal patterns."""
    import math

    base_time = get_utc_now()
    metrics = []

    for day in range(days):
        timestamp = base_time - timedelta(days=days - day)

        # Weekly seasonality (7-day cycle)
        weekly_factor = 1 + 0.3 * math.sin(2 * math.pi * day / 7)

        # Monthly seasonality (30-day cycle)
        monthly_factor = 1 + 0.2 * math.sin(2 * math.pi * day / 30)

        # Base value with growth trend
        base_value = 1000 * (1.001 ** day)

        # Apply seasonality
        value = base_value * weekly_factor * monthly_factor

        # Add noise
        value += random.uniform(-value * 0.05, value * 0.05)

        metrics.append({
            "name": "seasonal_metric",
            "metric_type": "gauge",
            "value": round(value, 2),
            "period": "day",
            "timestamp": timestamp
        })

    return metrics


def get_cohort_metrics() -> List[Dict[str, Any]]:
    """Get cohort retention metrics."""
    base_time = get_utc_now()
    metrics = []

    cohorts = [
        base_time - timedelta(days=90),
        base_time - timedelta(days=60),
        base_time - timedelta(days=30)
    ]

    for cohort_date in cohorts:
        initial_users = 1000

        for week in range(12):
            # Retention decreases over time
            retention_rate = 100 * (0.85 ** week)
            active_users = initial_users * (retention_rate / 100)

            metrics.append({
                "name": "cohort_retention",
                "metric_type": "gauge",
                "value": round(active_users, 2),
                "period": "week",
                "timestamp": cohort_date + timedelta(weeks=week),
                "dimensions": {
                    "cohort_date": cohort_date.date().isoformat(),
                    "week": week,
                    "retention_rate": round(retention_rate, 2)
                }
            })

    return metrics


def get_funnel_metrics() -> List[Dict[str, Any]]:
    """Get funnel conversion metrics."""
    base_time = get_utc_now()

    steps = [
        ("landing", 10000),
        ("product_view", 7000),
        ("add_to_cart", 3000),
        ("checkout", 1500),
        ("purchase", 1000)
    ]

    metrics = []

    for step_name, users in steps:
        metrics.append({
            "name": "funnel_users",
            "metric_type": "gauge",
            "value": float(users),
            "period": "day",
            "timestamp": base_time,
            "dimensions": {
                "step": step_name,
                "funnel": "checkout_funnel"
            }
        })

    return metrics


# Metric templates for common scenarios
SAMPLE_METRIC_TEMPLATES = {
    "gauge": {
        "metric_type": "gauge",
        "period": "day"
    },
    "counter": {
        "metric_type": "counter",
        "period": "hour"
    },
    "timer": {
        "metric_type": "timer",
        "period": "minute"
    }
}


# Sample aggregated metrics
SAMPLE_AGGREGATED_METRICS = {
    "daily_summary": {
        "total_events": 50000,
        "unique_users": 5000,
        "unique_sessions": 10000,
        "avg_session_duration": 325.5,
        "bounce_rate": 42.3,
        "conversion_rate": 2.8
    },
    "weekly_summary": {
        "total_events": 350000,
        "unique_users": 25000,
        "new_users": 5000,
        "returning_users": 20000,
        "total_revenue": 75000.00
    },
    "monthly_summary": {
        "total_events": 1500000,
        "unique_users": 80000,
        "new_users": 20000,
        "churn_rate": 5.2,
        "total_revenue": 320000.00,
        "avg_ltv": 450.00
    }
}
