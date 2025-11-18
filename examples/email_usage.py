"""Email service usage examples."""

import sys
import os
from datetime import datetime, timedelta

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.modules.email.service import EmailService
from src.core.database import init_db


def example_setup():
    """Example: Initialize database and create account."""
    print("=== Setting up Email Service ===\n")

    # Initialize database
    init_db()

    # Create email service
    service = EmailService()

    # Create email account
    account = service.create_account(
        email="your-email@gmail.com",
        name="Your Name",
        smtp_host="smtp.gmail.com",
        smtp_port=587,
        smtp_username="your-email@gmail.com",
        smtp_password="your-app-password",  # Use app-specific password
        imap_host="imap.gmail.com",
        imap_port=993,
        imap_username="your-email@gmail.com",
        imap_password="your-app-password",
        is_default=True
    )

    print(f"Created account: {account.email} (ID: {account.id})")
    return service, account


def example_send_simple_email(service, account):
    """Example: Send a simple email."""
    print("\n=== Sending Simple Email ===\n")

    email = service.send_email(
        to=["recipient@example.com"],
        subject="Hello from NEXUS Email Service",
        body_text="This is a simple text email sent from NEXUS.",
        body_html="<h1>Hello!</h1><p>This is an <strong>HTML</strong> email.</p>",
        account_id=account.id
    )

    print(f"Email sent! ID: {email.id}, Status: {email.status}")


def example_send_with_attachments(service, account):
    """Example: Send email with attachments."""
    print("\n=== Sending Email with Attachments ===\n")

    email = service.send_email(
        to=["recipient@example.com"],
        subject="Email with Attachments",
        body_text="Please find the attached files.",
        attachments=[
            "/path/to/document.pdf",
            "/path/to/image.png"
        ],
        account_id=account.id
    )

    print(f"Email with attachments sent! ID: {email.id}")


def example_send_template_email(service, account):
    """Example: Create and use email template."""
    print("\n=== Using Email Templates ===\n")

    # Create template
    template = service.create_template(
        name="welcome_email",
        subject="Welcome to {{ app_name }}!",
        body_html="""
            <h1>Welcome, {{ user_name }}!</h1>
            <p>Thank you for joining {{ app_name }}.</p>
            <p>Your account has been created successfully.</p>
            <p>Best regards,<br>The {{ app_name }} Team</p>
        """,
        body_text="""
            Welcome, {{ user_name }}!

            Thank you for joining {{ app_name }}.
            Your account has been created successfully.

            Best regards,
            The {{ app_name }} Team
        """
    )

    print(f"Created template: {template.name}")

    # Send email using template
    email = service.send_template_email(
        to=["newuser@example.com"],
        template_name="welcome_email",
        context={
            "user_name": "John Doe",
            "app_name": "NEXUS Platform"
        }
    )

    print(f"Template email sent! ID: {email.id}")


def example_schedule_email(service, account):
    """Example: Schedule email for later."""
    print("\n=== Scheduling Email ===\n")

    # Schedule email for 1 hour from now
    send_time = datetime.utcnow() + timedelta(hours=1)

    email = service.schedule_email(
        to=["recipient@example.com"],
        subject="Scheduled Email",
        body_text="This email was scheduled to be sent later.",
        send_at=send_time,
        account_id=account.id
    )

    print(f"Email scheduled for {send_time}. ID: {email.id}")

    # Start scheduler (in production, this would run continuously)
    service.start_scheduler()
    print("Scheduler started. Email will be sent at scheduled time.")


def example_sync_inbox(service, account):
    """Example: Sync inbox from IMAP."""
    print("\n=== Syncing Inbox ===\n")

    # Sync emails from last 7 days
    since = datetime.utcnow() - timedelta(days=7)

    stats = service.sync_inbox(
        folders=["INBOX"],
        since=since
    )

    print(f"Sync completed:")
    print(f"  Total synced: {stats['total_synced']}")
    print(f"  New emails: {stats['total_new']}")
    print(f"  Spam detected: {stats['total_spam']}")


def example_fetch_and_read_emails(service, account):
    """Example: Fetch and read emails."""
    print("\n=== Fetching Emails ===\n")

    # Fetch unread emails
    emails = service.fetch_emails(unread_only=True, limit=10)

    print(f"Found {len(emails)} unread emails:")

    for email in emails:
        print(f"\n  From: {email.from_address}")
        print(f"  Subject: {email.subject}")
        print(f"  Date: {email.received_at}")
        print(f"  Spam: {email.is_spam} (score: {email.spam_score:.2f})")

        # Mark as read
        service.mark_as_read(email.id)


def example_tracking_stats(service, account):
    """Example: Get email tracking statistics."""
    print("\n=== Email Tracking Statistics ===\n")

    # Get inbox stats
    stats = service.get_inbox_stats()

    print("Inbox Statistics:")
    print(f"  Total emails: {stats['total']}")
    print(f"  Unread: {stats['unread']}")
    print(f"  Spam: {stats['spam']}")
    print(f"  Sent: {stats['sent']}")

    # Get specific email stats (if tracking was enabled)
    # email_stats = service.get_email_stats(email_id=1)
    # if email_stats:
    #     print(f"\nEmail ID 1 Statistics:")
    #     print(f"  Opens: {email_stats['opened_count']}")
    #     print(f"  Clicks: {email_stats['clicked_count']}")
    #     print(f"  Last opened: {email_stats['last_opened_at']}")


def example_search_emails(service, account):
    """Example: Search emails."""
    print("\n=== Searching Emails ===\n")

    from src.modules.email.models import Email

    # Search by subject
    emails = service.db.query(Email).filter(
        Email.account_id == account.id,
        Email.subject.like("%invoice%")
    ).all()

    print(f"Found {len(emails)} emails containing 'invoice'")

    # Search spam emails
    spam_emails = service.db.query(Email).filter(
        Email.account_id == account.id,
        Email.is_spam == True
    ).all()

    print(f"Found {len(spam_emails)} spam emails")


def main():
    """Run all examples."""
    print("NEXUS Email Service - Usage Examples")
    print("=" * 50)

    # Note: These are examples. Uncomment and configure as needed.

    # 1. Setup
    # service, account = example_setup()

    # 2. Send simple email
    # example_send_simple_email(service, account)

    # 3. Send email with attachments
    # example_send_with_attachments(service, account)

    # 4. Use templates
    # example_send_template_email(service, account)

    # 5. Schedule email
    # example_schedule_email(service, account)

    # 6. Sync inbox
    # example_sync_inbox(service, account)

    # 7. Fetch and read emails
    # example_fetch_and_read_emails(service, account)

    # 8. View tracking statistics
    # example_tracking_stats(service, account)

    # 9. Search emails
    # example_search_emails(service, account)

    print("\n" + "=" * 50)
    print("Examples completed!")
    print("\nNote: Uncomment the examples in main() to run them.")
    print("Make sure to configure your email credentials in .env file.")


if __name__ == "__main__":
    main()
