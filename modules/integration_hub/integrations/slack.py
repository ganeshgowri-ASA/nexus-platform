"""Slack team communication integration with OAuth 2.0."""

from typing import Dict, Any, List, Optional
from ..connectors import OAuthConnector


class SlackConnector(OAuthConnector):
    """Slack connector for team communication."""

    async def post_message(
        self,
        channel: str,
        text: str,
        attachments: Optional[List[Dict]] = None
    ) -> Dict[str, Any]:
        """Post a message to a Slack channel."""
        payload = {
            'channel': channel,
            'text': text
        }

        if attachments:
            payload['attachments'] = attachments

        return await self.request(
            'POST',
            '/chat.postMessage',
            json=payload
        )

    async def get_channels(self) -> List[Dict[str, Any]]:
        """Get list of channels."""
        response = await self.request('GET', '/conversations.list')
        return response.get('channels', [])

    async def get_users(self) -> List[Dict[str, Any]]:
        """Get list of workspace users."""
        response = await self.request('GET', '/users.list')
        return response.get('members', [])

    async def upload_file(
        self,
        channels: List[str],
        file_content: bytes,
        filename: str,
        title: Optional[str] = None
    ) -> Dict[str, Any]:
        """Upload a file to Slack."""
        return await self.request(
            'POST',
            '/files.upload',
            data={
                'channels': ','.join(channels),
                'filename': filename,
                'title': title or filename
            },
            files={'file': file_content}
        )


SLACK_CONFIG = {
    'name': 'Slack',
    'slug': 'slack',
    'provider': 'slack',
    'auth_type': 'oauth2',
    'category': 'Communication',
    'config': {
        'authorization_url': 'https://slack.com/oauth/v2/authorize',
        'token_url': 'https://slack.com/api/oauth.v2.access',
        'api_base_url': 'https://slack.com/api',
        'test_endpoint': '/auth.test'
    },
    'default_scopes': ['chat:write', 'channels:read', 'users:read'],
    'rate_limit_requests': 100,
    'rate_limit_period': 60,
    'supports_webhooks': True,
    'supports_bidirectional_sync': False
}
