"""
Mock API Responses

Mock API response data for testing API endpoints.
"""

from datetime import datetime, timedelta
from typing import Dict, Any, List

from shared.utils import get_utc_now, generate_uuid


def get_mock_event_response() -> Dict[str, Any]:
    """Get mock event API response."""
    return {
        "id": generate_uuid(),
        "name": "page_view",
        "event_type": "page_view",
        "user_id": "user_123",
        "session_id": "session_456",
        "timestamp": get_utc_now().isoformat(),
        "properties": {
            "page": "/home",
            "referrer": "https://google.com"
        },
        "processed": False,
        "created_at": get_utc_now().isoformat()
    }


def get_mock_events_list_response(count: int = 10) -> Dict[str, Any]:
    """Get mock events list API response."""
    events = []
    for i in range(count):
        event = get_mock_event_response()
        event["name"] = f"event_{i}"
        event["id"] = generate_uuid()
        events.append(event)

    return {
        "items": events,
        "total": count,
        "page": 1,
        "page_size": 10,
        "pages": 1
    }


def get_mock_metric_response() -> Dict[str, Any]:
    """Get mock metric API response."""
    return {
        "id": generate_uuid(),
        "name": "daily_active_users",
        "metric_type": "gauge",
        "value": 1250.0,
        "period": "day",
        "timestamp": get_utc_now().isoformat(),
        "dimensions": {
            "module": "analytics"
        }
    }


def get_mock_metrics_list_response(count: int = 10) -> List[Dict[str, Any]]:
    """Get mock metrics list API response."""
    metrics = []
    base_time = get_utc_now()

    for i in range(count):
        metric = get_mock_metric_response()
        metric["id"] = generate_uuid()
        metric["value"] = 1000.0 + (i * 50)
        metric["timestamp"] = (base_time - timedelta(days=count - i)).isoformat()
        metrics.append(metric)

    return metrics


def get_mock_session_response() -> Dict[str, Any]:
    """Get mock session API response."""
    now = get_utc_now()
    return {
        "session_id": "session_123",
        "user_id": "user_456",
        "started_at": now.isoformat(),
        "ended_at": (now + timedelta(minutes=15)).isoformat(),
        "duration_seconds": 900,
        "page_views": 5,
        "events_count": 12,
        "is_bounce": False,
        "converted": True,
        "conversion_value": 99.99,
        "landing_page": "/home",
        "exit_page": "/checkout/complete"
    }


def get_mock_user_response() -> Dict[str, Any]:
    """Get mock user API response."""
    return {
        "id": "user_123",
        "first_seen_at": (get_utc_now() - timedelta(days=30)).isoformat(),
        "last_seen_at": get_utc_now().isoformat(),
        "total_events": 500,
        "total_sessions": 50,
        "total_conversions": 5,
        "total_value": 499.95,
        "properties": {
            "plan": "premium",
            "country": "US"
        }
    }


def get_mock_dashboard_overview_response() -> Dict[str, Any]:
    """Get mock dashboard overview API response."""
    return {
        "total_events": 50000,
        "unique_users": 5000,
        "unique_sessions": 10000,
        "total_page_views": 30000,
        "avg_session_duration": 325.5,
        "bounce_rate": 42.3,
        "conversion_rate": 2.8,
        "total_conversions": 280,
        "total_revenue": 25000.00,
        "time_period": {
            "start": (get_utc_now() - timedelta(days=7)).isoformat(),
            "end": get_utc_now().isoformat()
        }
    }


def get_mock_funnel_analysis_response() -> Dict[str, Any]:
    """Get mock funnel analysis API response."""
    return {
        "funnel_id": "checkout_funnel",
        "funnel_name": "Checkout Funnel",
        "start_date": (get_utc_now() - timedelta(days=7)).isoformat(),
        "end_date": get_utc_now().isoformat(),
        "total_entered": 10000,
        "total_completed": 1000,
        "overall_conversion_rate": 10.0,
        "steps": [
            {
                "step_id": "step_1",
                "step_name": "Product View",
                "order": 0,
                "entered": 10000,
                "completed": 7000,
                "dropped": 3000,
                "completion_rate": 70.0,
                "drop_off_rate": 30.0
            },
            {
                "step_id": "step_2",
                "step_name": "Add to Cart",
                "order": 1,
                "entered": 7000,
                "completed": 3000,
                "dropped": 4000,
                "completion_rate": 42.86,
                "drop_off_rate": 57.14
            },
            {
                "step_id": "step_3",
                "step_name": "Checkout",
                "order": 2,
                "entered": 3000,
                "completed": 1500,
                "dropped": 1500,
                "completion_rate": 50.0,
                "drop_off_rate": 50.0
            },
            {
                "step_id": "step_4",
                "step_name": "Purchase",
                "order": 3,
                "entered": 1500,
                "completed": 1000,
                "dropped": 500,
                "completion_rate": 66.67,
                "drop_off_rate": 33.33
            }
        ]
    }


def get_mock_cohort_analysis_response() -> Dict[str, Any]:
    """Get mock cohort analysis API response."""
    retention_data = []

    for week in range(12):
        retention_rate = 100 * (0.85 ** week)
        retention_data.append({
            "period": week,
            "users_active": int(1000 * (retention_rate / 100)),
            "retention_rate": round(retention_rate, 2),
            "cumulative_retention": round(retention_rate, 2)
        })

    return {
        "cohort_id": "cohort_2024_01",
        "cohort_name": "January 2024 Cohort",
        "cohort_date": (get_utc_now() - timedelta(days=90)).isoformat(),
        "initial_users": 1000,
        "retention_data": retention_data,
        "avg_retention_rate": 65.3,
        "churn_rate": 34.7
    }


def get_mock_time_series_response() -> List[Dict[str, Any]]:
    """Get mock time series API response."""
    data = []
    base_time = get_utc_now()

    for i in range(30):
        data.append({
            "timestamp": (base_time - timedelta(days=30 - i)).isoformat(),
            "value": 1000.0 + (i * 20) + (i % 7 * 50)  # Trend with weekly pattern
        })

    return data


def get_mock_aggregation_response() -> Dict[str, Any]:
    """Get mock aggregation API response."""
    return {
        "period": "day",
        "start_date": (get_utc_now() - timedelta(days=7)).isoformat(),
        "end_date": get_utc_now().isoformat(),
        "data": [
            {
                "period": (get_utc_now() - timedelta(days=i)).date().isoformat(),
                "event_type": "page_view",
                "count": 5000 + (i * 100),
                "unique_users": 500 + (i * 10),
                "unique_sessions": 1000 + (i * 20)
            }
            for i in range(7)
        ]
    }


def get_mock_export_response() -> Dict[str, Any]:
    """Get mock export API response."""
    return {
        "export_id": generate_uuid(),
        "format": "csv",
        "status": "completed",
        "url": "https://example.com/exports/data.csv",
        "created_at": get_utc_now().isoformat(),
        "expires_at": (get_utc_now() + timedelta(hours=24)).isoformat(),
        "rows": 10000,
        "size_bytes": 1024000
    }


def get_mock_error_response(
    status_code: int = 400,
    message: str = "Bad Request"
) -> Dict[str, Any]:
    """Get mock error API response."""
    return {
        "error": {
            "code": status_code,
            "message": message,
            "timestamp": get_utc_now().isoformat()
        }
    }


def get_mock_validation_error_response() -> Dict[str, Any]:
    """Get mock validation error response."""
    return {
        "error": {
            "code": 422,
            "message": "Validation Error",
            "details": [
                {
                    "field": "name",
                    "message": "Field required",
                    "type": "value_error.missing"
                },
                {
                    "field": "event_type",
                    "message": "Invalid event type",
                    "type": "value_error.enum"
                }
            ]
        }
    }


def get_mock_rate_limit_response() -> Dict[str, Any]:
    """Get mock rate limit response."""
    return {
        "error": {
            "code": 429,
            "message": "Rate limit exceeded",
            "retry_after": 60,
            "limit": 1000,
            "remaining": 0,
            "reset": (get_utc_now() + timedelta(minutes=1)).isoformat()
        }
    }


def get_mock_batch_response(success_count: int = 10, error_count: int = 0) -> Dict[str, Any]:
    """Get mock batch operation response."""
    return {
        "success": success_count,
        "errors": error_count,
        "total": success_count + error_count,
        "ids": [generate_uuid() for _ in range(success_count)],
        "error_details": [
            {
                "index": i,
                "error": "Validation error"
            }
            for i in range(error_count)
        ] if error_count > 0 else []
    }


def get_mock_health_check_response() -> Dict[str, Any]:
    """Get mock health check response."""
    return {
        "status": "healthy",
        "version": "1.0.0",
        "timestamp": get_utc_now().isoformat(),
        "services": {
            "database": "healthy",
            "cache": "healthy",
            "queue": "healthy"
        },
        "metrics": {
            "uptime_seconds": 86400,
            "requests_total": 100000,
            "requests_per_second": 50.5
        }
    }


def get_mock_analytics_report_response() -> Dict[str, Any]:
    """Get mock analytics report response."""
    return {
        "report_id": generate_uuid(),
        "report_type": "weekly_summary",
        "period": {
            "start": (get_utc_now() - timedelta(days=7)).isoformat(),
            "end": get_utc_now().isoformat()
        },
        "summary": {
            "total_events": 50000,
            "unique_users": 5000,
            "new_users": 1000,
            "total_sessions": 10000,
            "avg_session_duration": 325.5,
            "bounce_rate": 42.3,
            "conversion_rate": 2.8,
            "total_revenue": 25000.00
        },
        "top_pages": [
            {"url": "/home", "views": 10000},
            {"url": "/products", "views": 7500},
            {"url": "/about", "views": 5000}
        ],
        "traffic_sources": {
            "organic": 20000,
            "direct": 15000,
            "social": 10000,
            "email": 5000
        },
        "devices": {
            "mobile": 30000,
            "desktop": 17000,
            "tablet": 3000
        },
        "geography": {
            "US": 25000,
            "UK": 10000,
            "DE": 7500,
            "FR": 5000,
            "other": 2500
        }
    }


# Response templates for different scenarios
MOCK_RESPONSE_TEMPLATES = {
    "success": {
        "status": "success",
        "message": "Operation completed successfully"
    },
    "created": {
        "status": "created",
        "message": "Resource created successfully"
    },
    "accepted": {
        "status": "accepted",
        "message": "Request accepted for processing"
    },
    "no_content": {
        "status": "success",
        "message": "No content"
    },
    "bad_request": {
        "error": "Bad Request",
        "message": "Invalid request parameters"
    },
    "unauthorized": {
        "error": "Unauthorized",
        "message": "Authentication required"
    },
    "forbidden": {
        "error": "Forbidden",
        "message": "Insufficient permissions"
    },
    "not_found": {
        "error": "Not Found",
        "message": "Resource not found"
    },
    "server_error": {
        "error": "Internal Server Error",
        "message": "An unexpected error occurred"
    }
}
