"""Salesforce CRM integration with OAuth 2.0."""

from typing import Dict, Any, List, Optional
from ..connectors import OAuthConnector


class SalesforceConnector(OAuthConnector):
    """Salesforce CRM connector."""

    async def get_contacts(
        self,
        filters: Optional[Dict[str, Any]] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Get contacts from Salesforce."""
        query = "SELECT Id, FirstName, LastName, Email, Phone, AccountId FROM Contact"

        if filters:
            where = " AND ".join([f"{k}='{v}'" for k, v in filters.items()])
            query += f" WHERE {where}"

        query += f" LIMIT {limit}"

        response = await self.request(
            'GET',
            '/query',
            params={'q': query}
        )

        return response.get('records', [])

    async def create_contact(self, contact: Dict[str, Any]) -> Dict[str, Any]:
        """Create a contact in Salesforce."""
        return await self.request(
            'POST',
            '/sobjects/Contact',
            json=contact
        )

    async def update_contact(self, contact_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
        """Update a contact in Salesforce."""
        return await self.request(
            'PATCH',
            f'/sobjects/Contact/{contact_id}',
            json=updates
        )

    async def get_accounts(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get accounts from Salesforce."""
        query = f"SELECT Id, Name, Type, Industry, Website FROM Account LIMIT {limit}"

        response = await self.request(
            'GET',
            '/query',
            params={'q': query}
        )

        return response.get('records', [])

    async def get_opportunities(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get opportunities from Salesforce."""
        query = f"SELECT Id, Name, StageName, Amount, CloseDate, AccountId FROM Opportunity LIMIT {limit}"

        response = await self.request(
            'GET',
            '/query',
            params={'q': query}
        )

        return response.get('records', [])


# Integration configuration
SALESFORCE_CONFIG = {
    'name': 'Salesforce',
    'slug': 'salesforce',
    'provider': 'salesforce',
    'auth_type': 'oauth2',
    'category': 'CRM',
    'description': 'Salesforce CRM integration with full CRUD operations',
    'config': {
        'authorization_url': 'https://login.salesforce.com/services/oauth2/authorize',
        'token_url': 'https://login.salesforce.com/services/oauth2/token',
        'revoke_url': 'https://login.salesforce.com/services/oauth2/revoke',
        'user_info_url': 'https://login.salesforce.com/services/oauth2/userinfo',
        'api_base_url': 'https://instance.salesforce.com/services/data/v57.0',
        'test_endpoint': '/query?q=SELECT+Id+FROM+User+LIMIT+1'
    },
    'default_scopes': ['api', 'refresh_token', 'offline_access'],
    'rate_limit_requests': 15000,
    'rate_limit_period': 86400,  # 24 hours
    'supports_webhooks': True,
    'supports_bidirectional_sync': True,
    'supports_batch_operations': True
}
