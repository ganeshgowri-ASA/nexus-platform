"""Stripe payment processing integration with API Key auth."""

from typing import Dict, Any, List, Optional
from ..connectors import APIKeyConnector


class StripeConnector(APIKeyConnector):
    """Stripe payment processing connector."""

    def __init__(self, *args, **kwargs):
        """Initialize Stripe connector."""
        super().__init__(*args, **kwargs)
        # Stripe uses Bearer token format
        self.api_key_location = 'header'
        self.api_key_name = 'Authorization'

    def _get_default_headers(self) -> Dict[str, str]:
        """Override to use Bearer format."""
        headers = super()._get_default_headers()
        if self.api_key:
            headers['Authorization'] = f"Bearer {self.api_key}"
        return headers

    async def create_customer(
        self,
        email: str,
        name: Optional[str] = None,
        metadata: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """Create a Stripe customer."""
        data = {'email': email}
        if name:
            data['name'] = name
        if metadata:
            data['metadata'] = metadata

        return await self.request('POST', '/customers', data=data)

    async def create_payment_intent(
        self,
        amount: int,
        currency: str = 'usd',
        customer: Optional[str] = None,
        metadata: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """Create a payment intent."""
        data = {
            'amount': amount,
            'currency': currency
        }
        if customer:
            data['customer'] = customer
        if metadata:
            data['metadata'] = metadata

        return await self.request('POST', '/payment_intents', data=data)

    async def get_customers(
        self,
        limit: int = 100,
        starting_after: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get list of customers."""
        params = {'limit': limit}
        if starting_after:
            params['starting_after'] = starting_after

        response = await self.request('GET', '/customers', params=params)
        return response.get('data', [])

    async def get_charges(
        self,
        customer: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Get list of charges."""
        params = {'limit': limit}
        if customer:
            params['customer'] = customer

        response = await self.request('GET', '/charges', params=params)
        return response.get('data', [])


STRIPE_CONFIG = {
    'name': 'Stripe',
    'slug': 'stripe',
    'provider': 'stripe',
    'auth_type': 'api_key',
    'category': 'Payment',
    'config': {
        'api_base_url': 'https://api.stripe.com/v1',
        'api_key_location': 'header',
        'api_key_name': 'Authorization',
        'test_endpoint': '/customers?limit=1'
    },
    'rate_limit_requests': 100,
    'rate_limit_period': 1,
    'supports_webhooks': True,
    'supports_bidirectional_sync': False
}
