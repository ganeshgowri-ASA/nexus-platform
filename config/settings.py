"""
Application settings and configuration
"""
import os
from typing import Dict, Any


class Settings:
    """Application settings"""

    # Database
    DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./nexus.db")

    # Email configuration
    EMAIL_CONFIG: Dict[str, Any] = {
        "backend": os.getenv("EMAIL_BACKEND", "smtp"),  # smtp, sendgrid, ses
        "smtp_host": os.getenv("SMTP_HOST", "localhost"),
        "smtp_port": int(os.getenv("SMTP_PORT", "587")),
        "smtp_user": os.getenv("SMTP_USER", ""),
        "smtp_password": os.getenv("SMTP_PASSWORD", ""),
        "smtp_use_tls": os.getenv("SMTP_USE_TLS", "true").lower() == "true",
        "from_email": os.getenv("EMAIL_FROM", "noreply@nexus.com"),
        "from_name": os.getenv("EMAIL_FROM_NAME", "NEXUS Platform"),
        "sendgrid_api_key": os.getenv("SENDGRID_API_KEY", ""),
        "aws_region": os.getenv("AWS_REGION", "us-east-1"),
    }

    # SMS configuration
    SMS_CONFIG: Dict[str, Any] = {
        "backend": os.getenv("SMS_BACKEND", "twilio"),  # twilio, sns
        "twilio_account_sid": os.getenv("TWILIO_ACCOUNT_SID", ""),
        "twilio_auth_token": os.getenv("TWILIO_AUTH_TOKEN", ""),
        "twilio_from_number": os.getenv("TWILIO_FROM_NUMBER", ""),
        "aws_region": os.getenv("AWS_REGION", "us-east-1"),
        "sns_sender_id": os.getenv("SNS_SENDER_ID", "NEXUS"),
    }

    # Push notification configuration
    PUSH_CONFIG: Dict[str, Any] = {
        "backend": os.getenv("PUSH_BACKEND", "fcm"),  # fcm, apns
        "fcm_server_key": os.getenv("FCM_SERVER_KEY", ""),
        "fcm_credentials_path": os.getenv("FCM_CREDENTIALS_PATH", ""),
        "fcm_project_id": os.getenv("FCM_PROJECT_ID", ""),
        "apns_certificate_path": os.getenv("APNS_CERTIFICATE_PATH", ""),
        "apns_key_id": os.getenv("APNS_KEY_ID", ""),
        "apns_team_id": os.getenv("APNS_TEAM_ID", ""),
    }

    # In-app notification configuration
    IN_APP_CONFIG: Dict[str, Any] = {
        "ttl_days": int(os.getenv("IN_APP_TTL_DAYS", "30")),
        "max_notifications_per_user": int(os.getenv("IN_APP_MAX_PER_USER", "100")),
    }

    # Notification service configuration
    NOTIFICATION_CONFIG: Dict[str, Any] = {
        "email": EMAIL_CONFIG,
        "sms": SMS_CONFIG,
        "push": PUSH_CONFIG,
        "in_app": IN_APP_CONFIG,
    }

    # Scheduler configuration
    SCHEDULER_CHECK_INTERVAL = int(os.getenv("SCHEDULER_CHECK_INTERVAL", "60"))

    # Unsubscribe token configuration
    UNSUBSCRIBE_TOKEN_EXPIRY_DAYS = int(os.getenv("UNSUBSCRIBE_TOKEN_EXPIRY_DAYS", "90"))

    # Application settings
    APP_NAME = "NEXUS Platform"
    APP_VERSION = "1.0.0"
    DEBUG = os.getenv("DEBUG", "false").lower() == "true"


# Create settings instance
settings = Settings()
