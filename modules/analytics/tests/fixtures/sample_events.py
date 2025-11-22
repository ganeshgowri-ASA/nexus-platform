"""
Sample Event Data

Sample event data for testing analytics functionality.
"""

from datetime import datetime, timedelta
from typing import List, Dict, Any

from shared.utils import get_utc_now, generate_uuid


def get_sample_event() -> Dict[str, Any]:
    """Get a single sample event."""
    return {
        "name": "page_view",
        "event_type": "page_view",
        "properties": {
            "page": "/home",
            "referrer": "https://google.com",
            "utm_source": "google",
            "utm_medium": "organic"
        },
        "user_id": "user_sample_123",
        "session_id": "session_sample_456",
        "module": "analytics",
        "page_url": "https://example.com/home",
        "page_title": "Home Page",
        "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
        "ip_address": "192.168.1.1",
        "country": "US",
        "city": "San Francisco",
        "device_type": "desktop",
        "browser": "Chrome",
        "os": "Windows"
    }


def get_sample_events(count: int = 10) -> List[Dict[str, Any]]:
    """Get multiple sample events."""
    base_time = get_utc_now()
    events = []

    for i in range(count):
        event = get_sample_event()
        event["name"] = f"event_{i}"
        event["user_id"] = f"user_{i % 5}"  # 5 different users
        event["session_id"] = f"session_{i % 3}"  # 3 different sessions
        event["timestamp"] = base_time + timedelta(seconds=i * 10)
        events.append(event)

    return events


def get_page_view_events(count: int = 10) -> List[Dict[str, Any]]:
    """Get page view events."""
    pages = ["/home", "/products", "/about", "/contact", "/pricing"]
    events = []
    base_time = get_utc_now()

    for i in range(count):
        events.append({
            "name": "page_view",
            "event_type": "page_view",
            "page_url": f"https://example.com{pages[i % len(pages)]}",
            "page_title": f"Page {i}",
            "user_id": f"user_{i % 3}",
            "session_id": f"session_{i}",
            "timestamp": base_time + timedelta(seconds=i * 5),
            "properties": {
                "page": pages[i % len(pages)],
                "load_time": 1.2 + (i * 0.1)
            }
        })

    return events


def get_click_events(count: int = 10) -> List[Dict[str, Any]]:
    """Get click events."""
    elements = ["button", "link", "image", "form", "menu"]
    events = []
    base_time = get_utc_now()

    for i in range(count):
        events.append({
            "name": "click",
            "event_type": "click",
            "user_id": f"user_{i % 5}",
            "session_id": f"session_{i % 2}",
            "timestamp": base_time + timedelta(seconds=i * 3),
            "properties": {
                "element_type": elements[i % len(elements)],
                "element_id": f"elem_{i}",
                "x": 100 + i * 10,
                "y": 200 + i * 5
            }
        })

    return events


def get_purchase_events(count: int = 5) -> List[Dict[str, Any]]:
    """Get purchase events."""
    events = []
    base_time = get_utc_now()

    for i in range(count):
        events.append({
            "name": "purchase",
            "event_type": "purchase",
            "user_id": f"user_{i}",
            "session_id": f"session_{i}",
            "timestamp": base_time + timedelta(hours=i),
            "properties": {
                "order_id": f"order_{i}",
                "product_id": f"product_{i % 3}",
                "quantity": i + 1,
                "price": 99.99 + (i * 10),
                "currency": "USD",
                "payment_method": "credit_card"
            }
        })

    return events


def get_form_submit_events(count: int = 10) -> List[Dict[str, Any]]:
    """Get form submission events."""
    forms = ["contact", "signup", "login", "newsletter", "feedback"]
    events = []
    base_time = get_utc_now()

    for i in range(count):
        events.append({
            "name": "form_submit",
            "event_type": "form_submit",
            "user_id": f"user_{i % 4}",
            "session_id": f"session_{i}",
            "timestamp": base_time + timedelta(minutes=i * 2),
            "properties": {
                "form_name": forms[i % len(forms)],
                "form_id": f"form_{i}",
                "success": i % 5 != 0,  # 80% success rate
                "fields_count": 3 + (i % 3)
            }
        })

    return events


def get_video_events(count: int = 10) -> List[Dict[str, Any]]:
    """Get video interaction events."""
    events = []
    base_time = get_utc_now()

    actions = ["play", "pause", "complete", "seek"]

    for i in range(count):
        events.append({
            "name": "video_interaction",
            "event_type": "video",
            "user_id": f"user_{i % 3}",
            "session_id": f"session_{i}",
            "timestamp": base_time + timedelta(seconds=i * 15),
            "properties": {
                "video_id": f"video_{i % 2}",
                "action": actions[i % len(actions)],
                "position": i * 10,
                "duration": 300,
                "quality": "1080p"
            }
        })

    return events


def get_search_events(count: int = 10) -> List[Dict[str, Any]]:
    """Get search events."""
    queries = ["analytics", "dashboard", "reports", "metrics", "data"]
    events = []
    base_time = get_utc_now()

    for i in range(count):
        events.append({
            "name": "search",
            "event_type": "search",
            "user_id": f"user_{i % 5}",
            "session_id": f"session_{i}",
            "timestamp": base_time + timedelta(minutes=i),
            "properties": {
                "query": queries[i % len(queries)],
                "results_count": 10 + i,
                "click_position": i % 10 if i % 2 == 0 else None,
                "filters": {"category": "all"}
            }
        })

    return events


def get_error_events(count: int = 5) -> List[Dict[str, Any]]:
    """Get error events."""
    events = []
    base_time = get_utc_now()

    error_types = ["404", "500", "timeout", "validation", "auth"]

    for i in range(count):
        events.append({
            "name": "error",
            "event_type": "error",
            "user_id": f"user_{i}",
            "session_id": f"session_{i}",
            "timestamp": base_time + timedelta(minutes=i * 5),
            "properties": {
                "error_type": error_types[i % len(error_types)],
                "error_message": f"Error message {i}",
                "stack_trace": f"Stack trace {i}",
                "url": f"/api/endpoint_{i}",
                "severity": "error"
            }
        })

    return events


def get_user_journey_events(user_id: str = "user_journey") -> List[Dict[str, Any]]:
    """Get events representing a complete user journey."""
    base_time = get_utc_now()
    session_id = f"session_{user_id}"

    journey = [
        {
            "name": "landing",
            "event_type": "page_view",
            "page_url": "https://example.com/",
            "referrer": "https://google.com",
            "properties": {"utm_source": "google", "utm_medium": "cpc"},
            "timestamp": base_time
        },
        {
            "name": "product_browse",
            "event_type": "page_view",
            "page_url": "https://example.com/products",
            "properties": {"category": "electronics"},
            "timestamp": base_time + timedelta(seconds=30)
        },
        {
            "name": "product_view",
            "event_type": "page_view",
            "page_url": "https://example.com/product/123",
            "properties": {"product_id": "123", "price": 99.99},
            "timestamp": base_time + timedelta(seconds=60)
        },
        {
            "name": "add_to_cart",
            "event_type": "click",
            "properties": {"product_id": "123", "quantity": 1},
            "timestamp": base_time + timedelta(seconds=90)
        },
        {
            "name": "checkout_start",
            "event_type": "page_view",
            "page_url": "https://example.com/checkout",
            "properties": {"cart_value": 99.99},
            "timestamp": base_time + timedelta(seconds=120)
        },
        {
            "name": "payment_info",
            "event_type": "form_submit",
            "properties": {"step": "payment"},
            "timestamp": base_time + timedelta(seconds=180)
        },
        {
            "name": "purchase",
            "event_type": "purchase",
            "properties": {
                "order_id": "order_123",
                "value": 99.99,
                "currency": "USD"
            },
            "timestamp": base_time + timedelta(seconds=240)
        }
    ]

    for event in journey:
        event["user_id"] = user_id
        event["session_id"] = session_id

    return journey


def get_multi_user_events(user_count: int = 5, events_per_user: int = 10) -> List[Dict[str, Any]]:
    """Get events for multiple users."""
    all_events = []
    base_time = get_utc_now()

    for user_num in range(user_count):
        user_id = f"user_{user_num}"

        for event_num in range(events_per_user):
            all_events.append({
                "name": f"event_{event_num}",
                "event_type": "page_view" if event_num % 2 == 0 else "click",
                "user_id": user_id,
                "session_id": f"session_{user_num}_{event_num // 5}",
                "timestamp": base_time + timedelta(
                    hours=user_num,
                    seconds=event_num * 10
                ),
                "properties": {
                    "user_index": user_num,
                    "event_index": event_num
                }
            })

    return all_events


def get_events_by_date_range(
    start_date: datetime,
    end_date: datetime,
    events_per_day: int = 10
) -> List[Dict[str, Any]]:
    """Get events distributed across a date range."""
    events = []
    current_date = start_date
    event_index = 0

    while current_date <= end_date:
        for i in range(events_per_day):
            events.append({
                "name": f"event_{event_index}",
                "event_type": "page_view",
                "user_id": f"user_{event_index % 5}",
                "session_id": f"session_{event_index}",
                "timestamp": current_date + timedelta(
                    hours=i,
                    minutes=i * 5
                ),
                "properties": {
                    "date": current_date.date().isoformat(),
                    "index": event_index
                }
            })
            event_index += 1

        current_date += timedelta(days=1)

    return events


# Sample event templates for specific scenarios
SAMPLE_EVENT_TEMPLATES = {
    "page_view": {
        "name": "page_view",
        "event_type": "page_view",
        "properties": {"page": "/home"}
    },
    "button_click": {
        "name": "button_click",
        "event_type": "click",
        "properties": {"button_id": "submit", "button_text": "Submit"}
    },
    "form_submission": {
        "name": "form_submit",
        "event_type": "form_submit",
        "properties": {"form_id": "contact", "success": True}
    },
    "purchase": {
        "name": "purchase",
        "event_type": "purchase",
        "properties": {"value": 99.99, "currency": "USD"}
    },
    "signup": {
        "name": "signup",
        "event_type": "signup",
        "properties": {"method": "email", "plan": "free"}
    },
    "login": {
        "name": "login",
        "event_type": "login",
        "properties": {"method": "password", "success": True}
    },
    "logout": {
        "name": "logout",
        "event_type": "logout",
        "properties": {"duration": 3600}
    },
    "share": {
        "name": "share",
        "event_type": "share",
        "properties": {"platform": "twitter", "content_id": "123"}
    },
    "download": {
        "name": "download",
        "event_type": "download",
        "properties": {"file_name": "report.pdf", "file_size": 1024000}
    },
    "rating": {
        "name": "rating",
        "event_type": "rating",
        "properties": {"stars": 5, "item_id": "product_123"}
    }
}
