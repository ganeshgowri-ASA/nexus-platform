"""
Session 58: API Integrations Module
Features: Google/Microsoft/Slack/GitHub connectors, OAuth
"""
import asyncio
import json
from typing import Any, Dict, List, Optional
from datetime import datetime
from loguru import logger
import httpx

# Integration-specific imports
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from msal import ConfidentialClientApplication
from slack_sdk import WebClient
from slack_sdk.oauth import AuthorizeUrlGenerator
from github import Github

from ..base_module import BaseModule, ModuleConfig
from ...core.claude_client import ClaudeClient


class APIIntegrationsModule(BaseModule):
    """API Integration hub with OAuth support"""

    def __init__(self, claude_client: ClaudeClient, config_settings: Optional[Dict] = None, **kwargs):
        config = ModuleConfig(
            session=58,
            name="API Integrations",
            icon="🔌",
            description="Google/Microsoft/Slack/GitHub connectors, OAuth",
            version="1.0.0",
            features=["google", "microsoft", "slack", "github", "oauth", "webhooks"]
        )
        super().__init__(config, claude_client, **kwargs)
        self.settings = config_settings or {}
        self.tokens: Dict[str, Any] = {}  # Store OAuth tokens

    def validate_input(self, input_data: Dict[str, Any]) -> bool:
        """Validate input data"""
        return "provider" in input_data and "action" in input_data

    # Google Integration

    async def google_oauth_url(self, scopes: List[str], redirect_uri: str) -> str:
        """Generate Google OAuth URL"""
        from google_auth_oauthlib.flow import Flow

        flow = Flow.from_client_config(
            {
                "web": {
                    "client_id": self.settings.get("google_client_id"),
                    "client_secret": self.settings.get("google_client_secret"),
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token",
                }
            },
            scopes=scopes
        )
        flow.redirect_uri = redirect_uri

        auth_url, _ = flow.authorization_url(prompt='consent')
        return auth_url

    async def google_oauth_callback(self, code: str, redirect_uri: str) -> Dict[str, Any]:
        """Handle Google OAuth callback"""
        from google_auth_oauthlib.flow import Flow

        flow = Flow.from_client_config(
            {
                "web": {
                    "client_id": self.settings.get("google_client_id"),
                    "client_secret": self.settings.get("google_client_secret"),
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token",
                }
            },
            scopes=[]
        )
        flow.redirect_uri = redirect_uri
        flow.fetch_token(code=code)

        credentials = flow.credentials
        self.tokens["google"] = {
            "token": credentials.token,
            "refresh_token": credentials.refresh_token,
            "token_uri": credentials.token_uri,
            "client_id": credentials.client_id,
            "client_secret": credentials.client_secret,
            "scopes": credentials.scopes
        }

        return self.tokens["google"]

    async def google_drive_list(self, query: Optional[str] = None) -> List[Dict]:
        """List Google Drive files"""
        if "google" not in self.tokens:
            raise ValueError("Not authenticated with Google")

        creds = Credentials(**self.tokens["google"])
        service = build('drive', 'v3', credentials=creds)

        results = service.files().list(
            pageSize=100,
            q=query,
            fields="files(id, name, mimeType, createdTime, modifiedTime)"
        ).execute()

        return results.get('files', [])

    async def google_gmail_send(self, to: str, subject: str, body: str) -> Dict:
        """Send email via Gmail API"""
        if "google" not in self.tokens:
            raise ValueError("Not authenticated with Google")

        creds = Credentials(**self.tokens["google"])
        service = build('gmail', 'v1', credentials=creds)

        import base64
        from email.mime.text import MIMEText

        message = MIMEText(body)
        message['to'] = to
        message['subject'] = subject

        raw = base64.urlsafe_b64encode(message.as_bytes()).decode()
        result = service.users().messages().send(
            userId='me',
            body={'raw': raw}
        ).execute()

        return result

    async def google_calendar_events(self, max_results: int = 10) -> List[Dict]:
        """Get Google Calendar events"""
        if "google" not in self.tokens:
            raise ValueError("Not authenticated with Google")

        creds = Credentials(**self.tokens["google"])
        service = build('calendar', 'v3', credentials=creds)

        now = datetime.utcnow().isoformat() + 'Z'
        events_result = service.events().list(
            calendarId='primary',
            timeMin=now,
            maxResults=max_results,
            singleEvents=True,
            orderBy='startTime'
        ).execute()

        return events_result.get('items', [])

    # Microsoft Integration

    async def microsoft_oauth_url(self, scopes: List[str], redirect_uri: str) -> str:
        """Generate Microsoft OAuth URL"""
        app = ConfidentialClientApplication(
            self.settings.get("microsoft_client_id"),
            authority="https://login.microsoftonline.com/common",
            client_credential=self.settings.get("microsoft_client_secret"),
        )

        auth_url = app.get_authorization_request_url(
            scopes=scopes,
            redirect_uri=redirect_uri
        )

        return auth_url

    async def microsoft_oauth_callback(self, code: str, redirect_uri: str, scopes: List[str]) -> Dict:
        """Handle Microsoft OAuth callback"""
        app = ConfidentialClientApplication(
            self.settings.get("microsoft_client_id"),
            authority="https://login.microsoftonline.com/common",
            client_credential=self.settings.get("microsoft_client_secret"),
        )

        result = app.acquire_token_by_authorization_code(
            code=code,
            scopes=scopes,
            redirect_uri=redirect_uri
        )

        if "access_token" in result:
            self.tokens["microsoft"] = result
            return result
        else:
            raise ValueError(f"Failed to get token: {result.get('error_description')}")

    async def microsoft_graph_api(self, endpoint: str, method: str = "GET", data: Optional[Dict] = None) -> Dict:
        """Call Microsoft Graph API"""
        if "microsoft" not in self.tokens:
            raise ValueError("Not authenticated with Microsoft")

        url = f"https://graph.microsoft.com/v1.0/{endpoint}"
        headers = {
            "Authorization": f"Bearer {self.tokens['microsoft']['access_token']}",
            "Content-Type": "application/json"
        }

        async with httpx.AsyncClient() as client:
            if method == "GET":
                response = await client.get(url, headers=headers)
            elif method == "POST":
                response = await client.post(url, headers=headers, json=data)
            elif method == "PATCH":
                response = await client.patch(url, headers=headers, json=data)
            elif method == "DELETE":
                response = await client.delete(url, headers=headers)
            else:
                raise ValueError(f"Unsupported method: {method}")

            response.raise_for_status()
            return response.json() if response.content else {}

    # Slack Integration

    async def slack_oauth_url(self, scopes: List[str], redirect_uri: str) -> str:
        """Generate Slack OAuth URL"""
        generator = AuthorizeUrlGenerator(
            client_id=self.settings.get("slack_client_id"),
            scopes=scopes,
            redirect_uri=redirect_uri
        )
        return generator.generate()

    async def slack_oauth_callback(self, code: str) -> Dict:
        """Handle Slack OAuth callback"""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://slack.com/api/oauth.v2.access",
                data={
                    "client_id": self.settings.get("slack_client_id"),
                    "client_secret": self.settings.get("slack_client_secret"),
                    "code": code
                }
            )
            result = response.json()

            if result.get("ok"):
                self.tokens["slack"] = result
                return result
            else:
                raise ValueError(f"Slack OAuth failed: {result.get('error')}")

    async def slack_send_message(self, channel: str, text: str, blocks: Optional[List[Dict]] = None) -> Dict:
        """Send Slack message"""
        if "slack" not in self.tokens:
            raise ValueError("Not authenticated with Slack")

        client = WebClient(token=self.tokens["slack"]["access_token"])
        response = client.chat_postMessage(
            channel=channel,
            text=text,
            blocks=blocks
        )

        return response.data

    async def slack_list_channels(self) -> List[Dict]:
        """List Slack channels"""
        if "slack" not in self.tokens:
            raise ValueError("Not authenticated with Slack")

        client = WebClient(token=self.tokens["slack"]["access_token"])
        response = client.conversations_list()

        return response.data.get("channels", [])

    # GitHub Integration

    async def github_authenticate(self, token: str):
        """Authenticate with GitHub"""
        self.tokens["github"] = {"token": token}

    async def github_list_repos(self, username: Optional[str] = None) -> List[Dict]:
        """List GitHub repositories"""
        if "github" not in self.tokens:
            raise ValueError("Not authenticated with GitHub")

        g = Github(self.tokens["github"]["token"])

        if username:
            user = g.get_user(username)
        else:
            user = g.get_user()

        repos = []
        for repo in user.get_repos():
            repos.append({
                "name": repo.name,
                "full_name": repo.full_name,
                "description": repo.description,
                "url": repo.html_url,
                "stars": repo.stargazers_count,
                "forks": repo.forks_count,
                "language": repo.language
            })

        return repos

    async def github_create_issue(self, repo: str, title: str, body: str, labels: Optional[List[str]] = None) -> Dict:
        """Create GitHub issue"""
        if "github" not in self.tokens:
            raise ValueError("Not authenticated with GitHub")

        g = Github(self.tokens["github"]["token"])
        repository = g.get_repo(repo)

        issue = repository.create_issue(
            title=title,
            body=body,
            labels=labels or []
        )

        return {
            "number": issue.number,
            "title": issue.title,
            "url": issue.html_url,
            "state": issue.state
        }

    async def github_list_pull_requests(self, repo: str, state: str = "open") -> List[Dict]:
        """List GitHub pull requests"""
        if "github" not in self.tokens:
            raise ValueError("Not authenticated with GitHub")

        g = Github(self.tokens["github"]["token"])
        repository = g.get_repo(repo)

        prs = []
        for pr in repository.get_pulls(state=state):
            prs.append({
                "number": pr.number,
                "title": pr.title,
                "state": pr.state,
                "url": pr.html_url,
                "author": pr.user.login,
                "created_at": pr.created_at.isoformat()
            })

        return prs

    # Webhook Management

    async def create_webhook(self, provider: str, endpoint: str, events: List[str]) -> Dict[str, Any]:
        """Create webhook subscription"""
        webhook_id = f"{provider}_{datetime.now().timestamp()}"
        webhook = {
            "id": webhook_id,
            "provider": provider,
            "endpoint": endpoint,
            "events": events,
            "created_at": datetime.now().isoformat()
        }

        # Store webhook configuration
        if "webhooks" not in self.state:
            self.state["webhooks"] = {}
        self.state["webhooks"][webhook_id] = webhook

        logger.info(f"Created webhook: {webhook_id}")
        return webhook

    def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process API integration request (sync wrapper)"""
        return asyncio.run(self.aprocess(input_data))

    async def aprocess(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process API integration request"""
        if not self.validate_input(input_data):
            return {"success": False, "error": "Invalid input"}

        provider = input_data["provider"]
        action = input_data["action"]
        self.log_operation(f"{provider}_{action}", input_data)

        try:
            # Google
            if provider == "google":
                if action == "oauth_url":
                    url = await self.google_oauth_url(input_data["scopes"], input_data["redirect_uri"])
                    return {"success": True, "url": url}
                elif action == "oauth_callback":
                    token = await self.google_oauth_callback(input_data["code"], input_data["redirect_uri"])
                    return {"success": True, "token": token}
                elif action == "drive_list":
                    files = await self.google_drive_list(input_data.get("query"))
                    return {"success": True, "files": files}
                elif action == "gmail_send":
                    result = await self.google_gmail_send(input_data["to"], input_data["subject"], input_data["body"])
                    return {"success": True, "result": result}
                elif action == "calendar_events":
                    events = await self.google_calendar_events(input_data.get("max_results", 10))
                    return {"success": True, "events": events}

            # Microsoft
            elif provider == "microsoft":
                if action == "oauth_url":
                    url = await self.microsoft_oauth_url(input_data["scopes"], input_data["redirect_uri"])
                    return {"success": True, "url": url}
                elif action == "oauth_callback":
                    token = await self.microsoft_oauth_callback(input_data["code"], input_data["redirect_uri"], input_data["scopes"])
                    return {"success": True, "token": token}
                elif action == "graph_api":
                    result = await self.microsoft_graph_api(
                        input_data["endpoint"],
                        input_data.get("method", "GET"),
                        input_data.get("data")
                    )
                    return {"success": True, "result": result}

            # Slack
            elif provider == "slack":
                if action == "oauth_url":
                    url = await self.slack_oauth_url(input_data["scopes"], input_data["redirect_uri"])
                    return {"success": True, "url": url}
                elif action == "oauth_callback":
                    token = await self.slack_oauth_callback(input_data["code"])
                    return {"success": True, "token": token}
                elif action == "send_message":
                    result = await self.slack_send_message(input_data["channel"], input_data["text"], input_data.get("blocks"))
                    return {"success": True, "result": result}
                elif action == "list_channels":
                    channels = await self.slack_list_channels()
                    return {"success": True, "channels": channels}

            # GitHub
            elif provider == "github":
                if action == "authenticate":
                    await self.github_authenticate(input_data["token"])
                    return {"success": True}
                elif action == "list_repos":
                    repos = await self.github_list_repos(input_data.get("username"))
                    return {"success": True, "repos": repos}
                elif action == "create_issue":
                    issue = await self.github_create_issue(
                        input_data["repo"],
                        input_data["title"],
                        input_data["body"],
                        input_data.get("labels")
                    )
                    return {"success": True, "issue": issue}
                elif action == "list_pull_requests":
                    prs = await self.github_list_pull_requests(input_data["repo"], input_data.get("state", "open"))
                    return {"success": True, "pull_requests": prs}

            # Webhooks
            elif provider == "webhook":
                if action == "create":
                    webhook = await self.create_webhook(
                        input_data["target_provider"],
                        input_data["endpoint"],
                        input_data["events"]
                    )
                    return {"success": True, "webhook": webhook}

            return {"success": False, "error": f"Unknown action: {provider}.{action}"}

        except Exception as e:
            return self.handle_error(e, f"{provider}_{action}")
