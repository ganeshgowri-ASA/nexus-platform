"""
Example: Send notifications using NEXUS Platform API

This script demonstrates how to send notifications through all available channels.
"""
import requests
from datetime import datetime, timedelta

# API base URL
BASE_URL = "http://localhost:8000/api/notifications"


def send_email_notification():
    """Send an email notification"""
    print("\n📧 Sending email notification...")

    response = requests.post(f"{BASE_URL}/send", json={
        "user_id": "user123",
        "channel": "email",
        "recipient": "user@example.com",
        "title": "Welcome to NEXUS Platform",
        "message": "Thank you for joining! We're excited to have you onboard.",
        "category": "onboarding",
        "priority": "normal",
        "data": {
            "html_body": "<h1>Welcome!</h1><p>Thank you for joining! We're excited to have you onboard.</p>"
        }
    })

    if response.status_code == 200:
        result = response.json()
        print(f"✓ Email notification sent successfully")
        print(f"  Notification ID: {result['notification_id']}")
        print(f"  Status: {result['status']}")
    else:
        print(f"✗ Failed to send email: {response.text}")


def send_sms_notification():
    """Send an SMS notification"""
    print("\n💬 Sending SMS notification...")

    response = requests.post(f"{BASE_URL}/send", json={
        "user_id": "user123",
        "channel": "sms",
        "recipient": "+1234567890",
        "title": "Verification Code",
        "message": "Your NEXUS verification code is: 123456. Valid for 10 minutes.",
        "category": "security",
        "priority": "high"
    })

    if response.status_code == 200:
        result = response.json()
        print(f"✓ SMS notification sent successfully")
        print(f"  Notification ID: {result['notification_id']}")
    else:
        print(f"✗ Failed to send SMS: {response.text}")


def send_push_notification():
    """Send a push notification"""
    print("\n🔔 Sending push notification...")

    response = requests.post(f"{BASE_URL}/send", json={
        "user_id": "user123",
        "channel": "push",
        "recipient": "device-token-here",
        "title": "New Message Received",
        "message": "John Doe sent you a message",
        "category": "messaging",
        "priority": "normal",
        "data": {
            "action_url": "/messages/456",
            "badge": 3,
            "sound": "default"
        }
    })

    if response.status_code == 200:
        result = response.json()
        print(f"✓ Push notification sent successfully")
        print(f"  Notification ID: {result['notification_id']}")
    else:
        print(f"✗ Failed to send push notification: {response.text}")


def send_in_app_notification():
    """Send an in-app notification"""
    print("\n📱 Sending in-app notification...")

    response = requests.post(f"{BASE_URL}/send", json={
        "user_id": "user123",
        "channel": "in_app",
        "recipient": "user123",
        "title": "Report Ready",
        "message": "Your monthly analytics report is ready to download",
        "category": "system",
        "priority": "normal",
        "data": {
            "action_url": "/reports/monthly-analytics",
            "icon": "report"
        }
    })

    if response.status_code == 200:
        result = response.json()
        print(f"✓ In-app notification sent successfully")
        print(f"  Notification ID: {result['notification_id']}")
    else:
        print(f"✗ Failed to send in-app notification: {response.text}")


def send_with_template():
    """Send notification using a template"""
    print("\n📝 Creating and using a template...")

    # Create template
    template_response = requests.post(f"{BASE_URL}/templates", json={
        "name": "password_reset",
        "category": "security",
        "subject": "Password Reset Request",
        "body": "Hello {{ user_name }},\n\nWe received a request to reset your password. Use this code: {{ reset_code }}\n\nIf you didn't request this, please ignore this message.",
        "html_body": "<h2>Password Reset</h2><p>Hello {{ user_name }},</p><p>We received a request to reset your password. Use this code: <strong>{{ reset_code }}</strong></p><p>If you didn't request this, please ignore this message.</p>",
        "variables": ["user_name", "reset_code"]
    })

    if template_response.status_code == 200:
        print("✓ Template created successfully")

        # Send using template
        send_response = requests.post(f"{BASE_URL}/send-template", json={
            "user_id": "user123",
            "channel": "email",
            "recipient": "user@example.com",
            "template_name": "password_reset",
            "template_vars": {
                "user_name": "John Doe",
                "reset_code": "ABC123"
            },
            "category": "security"
        })

        if send_response.status_code == 200:
            print("✓ Template notification sent successfully")
        else:
            print(f"✗ Failed to send template notification: {send_response.text}")
    else:
        print(f"✗ Failed to create template: {template_response.text}")


def schedule_notification():
    """Schedule a notification for later"""
    print("\n⏰ Scheduling a notification...")

    # Schedule for 1 hour from now
    scheduled_time = (datetime.utcnow() + timedelta(hours=1)).isoformat()

    response = requests.post(f"{BASE_URL}/send", json={
        "user_id": "user123",
        "channel": "email",
        "recipient": "user@example.com",
        "title": "Meeting Reminder",
        "message": "Your meeting with the team starts in 15 minutes",
        "category": "reminder",
        "priority": "high",
        "scheduled_at": scheduled_time
    })

    if response.status_code == 200:
        result = response.json()
        print(f"✓ Notification scheduled successfully")
        print(f"  Notification ID: {result['notification_id']}")
        print(f"  Scheduled for: {result['scheduled_at']}")
    else:
        print(f"✗ Failed to schedule notification: {response.text}")


def send_bulk_notifications():
    """Send bulk notifications"""
    print("\n📢 Sending bulk notifications...")

    response = requests.post(f"{BASE_URL}/send-bulk", json={
        "user_ids": ["user1", "user2", "user3", "user4", "user5"],
        "channel": "email",
        "title": "Platform Update",
        "message": "We've released new features! Check out what's new in your dashboard.",
        "category": "announcement"
    })

    if response.status_code == 200:
        result = response.json()
        print(f"✓ Bulk notifications sent")
        print(f"  Total: {result['total']}")
        print(f"  Sent: {result['sent']}")
        print(f"  Failed: {result['failed']}")
        print(f"  Skipped: {result['skipped']}")
    else:
        print(f"✗ Failed to send bulk notifications: {response.text}")


def get_analytics():
    """Get delivery analytics"""
    print("\n📊 Fetching delivery analytics...")

    response = requests.get(f"{BASE_URL}/analytics/delivery", params={
        "channel": "email"
    })

    if response.status_code == 200:
        analytics = response.json()
        print(f"✓ Analytics retrieved")
        print(f"  Total: {analytics['total']}")
        print(f"  Sent: {analytics['sent']}")
        print(f"  Delivery Rate: {analytics['rates']['delivery_rate']}%")
        print(f"  Open Rate: {analytics['rates']['open_rate']}%")
        print(f"  Click Rate: {analytics['rates']['click_rate']}%")
    else:
        print(f"✗ Failed to get analytics: {response.text}")


def main():
    """Run all examples"""
    print("=" * 60)
    print("NEXUS Platform - Notification System Examples")
    print("=" * 60)

    try:
        # Check if API is running
        health = requests.get("http://localhost:8000/health")
        if health.status_code != 200:
            print("✗ API is not running. Please start the server first.")
            print("  Run: python backend/main.py")
            return
    except requests.exceptions.ConnectionError:
        print("✗ Cannot connect to API. Please start the server first.")
        print("  Run: python backend/main.py")
        return

    # Run examples
    send_email_notification()
    send_sms_notification()
    send_push_notification()
    send_in_app_notification()
    send_with_template()
    schedule_notification()
    send_bulk_notifications()
    get_analytics()

    print("\n" + "=" * 60)
    print("All examples completed!")
    print("=" * 60)


if __name__ == "__main__":
    main()
