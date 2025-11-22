"""Monitoring and metrics for A/B testing module."""

from prometheus_client import Counter, Histogram, generate_latest
from fastapi import Response


# Metrics
experiment_created = Counter(
    "ab_test_experiments_created_total",
    "Total number of experiments created",
)

experiment_started = Counter(
    "ab_test_experiments_started_total",
    "Total number of experiments started",
)

experiment_completed = Counter(
    "ab_test_experiments_completed_total",
    "Total number of experiments completed",
)

variant_assignment = Counter(
    "ab_test_variant_assignments_total",
    "Total number of variant assignments",
    ["experiment_id", "variant_id"],
)

metric_event_tracked = Counter(
    "ab_test_metric_events_total",
    "Total number of metric events tracked",
    ["metric_type"],
)

api_request_duration = Histogram(
    "ab_test_api_request_duration_seconds",
    "API request duration in seconds",
    ["endpoint", "method"],
)

statistical_test_duration = Histogram(
    "ab_test_statistical_test_duration_seconds",
    "Statistical test computation duration in seconds",
    ["test_type"],
)


async def metrics_endpoint() -> Response:
    """
    Prometheus metrics endpoint.

    Returns:
        Response: Prometheus metrics in text format
    """
    return Response(
        content=generate_latest(),
        media_type="text/plain",
    )
