"""
Pre-built integrations for popular third-party services.

This package contains ready-to-use integrations for 15+ services
including CRM, communication, storage, payment, and more.
"""

from typing import Dict, Any, List
import logging

logger = logging.getLogger(__name__)


# Integration metadata registry
INTEGRATIONS = {
    'salesforce': {
        'name': 'Salesforce',
        'category': 'CRM',
        'description': 'Salesforce CRM integration',
        'auth_type': 'oauth2',
        'icon': 'salesforce.svg'
    },
    'hubspot': {
        'name': 'HubSpot',
        'category': 'Marketing',
        'description': 'HubSpot marketing automation',
        'auth_type': 'oauth2',
        'icon': 'hubspot.svg'
    },
    'slack': {
        'name': 'Slack',
        'category': 'Communication',
        'description': 'Slack team communication',
        'auth_type': 'oauth2',
        'icon': 'slack.svg'
    },
    'gmail': {
        'name': 'Gmail',
        'category': 'Email',
        'description': 'Gmail email integration',
        'auth_type': 'oauth2',
        'icon': 'gmail.svg'
    },
    'google_drive': {
        'name': 'Google Drive',
        'category': 'Storage',
        'description': 'Google Drive file storage',
        'auth_type': 'oauth2',
        'icon': 'google-drive.svg'
    },
    'dropbox': {
        'name': 'Dropbox',
        'category': 'Storage',
        'description': 'Dropbox file storage',
        'auth_type': 'oauth2',
        'icon': 'dropbox.svg'
    },
    'stripe': {
        'name': 'Stripe',
        'category': 'Payment',
        'description': 'Stripe payment processing',
        'auth_type': 'api_key',
        'icon': 'stripe.svg'
    },
    'paypal': {
        'name': 'PayPal',
        'category': 'Payment',
        'description': 'PayPal payment processing',
        'auth_type': 'oauth2',
        'icon': 'paypal.svg'
    },
    'shopify': {
        'name': 'Shopify',
        'category': 'Ecommerce',
        'description': 'Shopify e-commerce platform',
        'auth_type': 'oauth2',
        'icon': 'shopify.svg'
    },
    'zapier': {
        'name': 'Zapier',
        'category': 'Automation',
        'description': 'Zapier workflow automation',
        'auth_type': 'api_key',
        'icon': 'zapier.svg'
    },
    'mailchimp': {
        'name': 'Mailchimp',
        'category': 'Marketing',
        'description': 'Mailchimp email marketing',
        'auth_type': 'oauth2',
        'icon': 'mailchimp.svg'
    },
    'twilio': {
        'name': 'Twilio',
        'category': 'Communication',
        'description': 'Twilio SMS and voice',
        'auth_type': 'api_key',
        'icon': 'twilio.svg'
    },
    'sendgrid': {
        'name': 'SendGrid',
        'category': 'Email',
        'description': 'SendGrid email delivery',
        'auth_type': 'api_key',
        'icon': 'sendgrid.svg'
    },
    'zoom': {
        'name': 'Zoom',
        'category': 'Video',
        'description': 'Zoom video conferencing',
        'auth_type': 'oauth2',
        'icon': 'zoom.svg'
    },
    'jira': {
        'name': 'Jira',
        'category': 'Project Management',
        'description': 'Atlassian Jira project management',
        'auth_type': 'oauth2',
        'icon': 'jira.svg'
    }
}


def get_integration_config(integration_slug: str) -> Dict[str, Any]:
    """
    Get configuration for a specific integration.

    Args:
        integration_slug: Integration identifier

    Returns:
        Integration configuration dictionary
    """
    if integration_slug not in INTEGRATIONS:
        raise ValueError(f"Unknown integration: {integration_slug}")

    return INTEGRATIONS[integration_slug]


def list_integrations(category: str = None) -> List[Dict[str, Any]]:
    """
    List available integrations.

    Args:
        category: Optional category filter

    Returns:
        List of integration configs
    """
    integrations = INTEGRATIONS.values()

    if category:
        integrations = [i for i in integrations if i.get('category') == category]

    return list(integrations)


__all__ = [
    'INTEGRATIONS',
    'get_integration_config',
    'list_integrations'
]
