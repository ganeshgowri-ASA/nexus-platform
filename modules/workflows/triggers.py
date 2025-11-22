"""
NEXUS Workflow Triggers
Comprehensive trigger system for workflow automation
"""

from typing import Dict, List, Any, Optional, Callable, Set
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import asyncio
import uuid
import json
import hashlib
import hmac
from abc import ABC, abstractmethod


class TriggerType(Enum):
    """Types of workflow triggers"""
    WEBHOOK = "webhook"
    SCHEDULE = "schedule"
    EMAIL = "email"
    FORM_SUBMISSION = "form_submission"
    DATABASE_CHANGE = "database_change"
    API_CALL = "api_call"
    FILE_WATCH = "file_watch"
    MANUAL = "manual"
    EVENT = "event"
    MESSAGE_QUEUE = "message_queue"
    RSS_FEED = "rss_feed"
    WEBHOOK_POLL = "webhook_poll"


@dataclass
class TriggerConfig:
    """Configuration for a trigger"""
    id: str
    workflow_id: str
    trigger_type: TriggerType
    config: Dict[str, Any]
    enabled: bool = True
    created_at: datetime = field(default_factory=datetime.utcnow)
    last_triggered: Optional[datetime] = None
    trigger_count: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class TriggerEvent:
    """Event data from a trigger"""
    id: str
    trigger_id: str
    workflow_id: str
    trigger_type: TriggerType
    data: Dict[str, Any]
    timestamp: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)


class BaseTrigger(ABC):
    """Base class for all triggers"""

    def __init__(self, config: TriggerConfig):
        self.config = config
        self.is_active = False
        self.listeners: List[Callable] = []

    @abstractmethod
    async def start(self) -> None:
        """Start the trigger"""
        pass

    @abstractmethod
    async def stop(self) -> None:
        """Stop the trigger"""
        pass

    def add_listener(self, listener: Callable) -> None:
        """Add a listener function to be called when trigger fires"""
        self.listeners.append(listener)

    async def fire(self, data: Dict[str, Any]) -> TriggerEvent:
        """Fire the trigger with given data"""
        event = TriggerEvent(
            id=str(uuid.uuid4()),
            trigger_id=self.config.id,
            workflow_id=self.config.workflow_id,
            trigger_type=self.config.trigger_type,
            data=data
        )

        self.config.last_triggered = datetime.utcnow()
        self.config.trigger_count += 1

        # Notify all listeners
        for listener in self.listeners:
            try:
                if asyncio.iscoroutinefunction(listener):
                    await listener(event)
                else:
                    listener(event)
            except Exception as e:
                print(f"Error in trigger listener: {e}")

        return event


class WebhookTrigger(BaseTrigger):
    """
    Webhook trigger - receives HTTP requests
    Config: {
        "path": "/webhook/my-workflow",
        "method": "POST",
        "secret": "optional-secret-for-validation",
        "validate_signature": true,
        "signature_header": "X-Signature",
        "allowed_ips": ["192.168.1.1"]
    }
    """

    def __init__(self, config: TriggerConfig):
        super().__init__(config)
        self.webhook_path = config.config.get('path', f'/webhook/{config.workflow_id}')
        self.method = config.config.get('method', 'POST')
        self.secret = config.config.get('secret')

    async def start(self) -> None:
        """Start webhook listener"""
        self.is_active = True

    async def stop(self) -> None:
        """Stop webhook listener"""
        self.is_active = False

    def validate_signature(self, payload: str, signature: str) -> bool:
        """Validate webhook signature"""
        if not self.secret:
            return True

        expected_signature = hmac.new(
            self.secret.encode(),
            payload.encode(),
            hashlib.sha256
        ).hexdigest()

        return hmac.compare_digest(signature, expected_signature)

    async def handle_request(
        self,
        headers: Dict[str, str],
        body: str,
        query_params: Dict[str, str]
    ) -> TriggerEvent:
        """Handle incoming webhook request"""
        # Validate signature if configured
        if self.config.config.get('validate_signature'):
            signature_header = self.config.config.get('signature_header', 'X-Signature')
            signature = headers.get(signature_header, '')
            if not self.validate_signature(body, signature):
                raise ValueError("Invalid webhook signature")

        # Parse payload
        try:
            payload = json.loads(body) if body else {}
        except json.JSONDecodeError:
            payload = {"raw": body}

        data = {
            "headers": headers,
            "body": payload,
            "query_params": query_params
        }

        return await self.fire(data)


class ScheduleTrigger(BaseTrigger):
    """
    Schedule trigger - executes on a schedule
    Config: {
        "cron": "0 9 * * *",  # Daily at 9 AM
        "interval": 3600,  # or interval in seconds
        "timezone": "UTC",
        "start_date": "2024-01-01",
        "end_date": "2024-12-31"
    }
    """

    def __init__(self, config: TriggerConfig):
        super().__init__(config)
        self.task: Optional[asyncio.Task] = None
        self.interval = config.config.get('interval')
        self.cron = config.config.get('cron')

    async def start(self) -> None:
        """Start schedule"""
        self.is_active = True
        if self.interval:
            self.task = asyncio.create_task(self._run_interval())
        elif self.cron:
            self.task = asyncio.create_task(self._run_cron())

    async def stop(self) -> None:
        """Stop schedule"""
        self.is_active = False
        if self.task:
            self.task.cancel()

    async def _run_interval(self) -> None:
        """Run on interval"""
        while self.is_active:
            try:
                await self.fire({"timestamp": datetime.utcnow().isoformat()})
                await asyncio.sleep(self.interval)
            except asyncio.CancelledError:
                break

    async def _run_cron(self) -> None:
        """Run on cron schedule"""
        # Simplified cron implementation
        # In production, use croniter or similar library
        while self.is_active:
            try:
                next_run = self._calculate_next_run()
                wait_seconds = (next_run - datetime.utcnow()).total_seconds()

                if wait_seconds > 0:
                    await asyncio.sleep(wait_seconds)

                await self.fire({"timestamp": datetime.utcnow().isoformat()})
            except asyncio.CancelledError:
                break

    def _calculate_next_run(self) -> datetime:
        """Calculate next cron run time"""
        # Simplified - should use croniter
        return datetime.utcnow() + timedelta(hours=1)


class EmailTrigger(BaseTrigger):
    """
    Email trigger - monitors email inbox
    Config: {
        "email": "trigger@example.com",
        "imap_server": "imap.gmail.com",
        "imap_port": 993,
        "username": "user@example.com",
        "password": "app-password",
        "folder": "INBOX",
        "filter": {
            "from": "specific@sender.com",
            "subject_contains": "trigger word",
            "has_attachments": true
        },
        "mark_as_read": true,
        "delete_after_trigger": false
    }
    """

    def __init__(self, config: TriggerConfig):
        super().__init__(config)
        self.task: Optional[asyncio.Task] = None
        self.poll_interval = config.config.get('poll_interval', 60)

    async def start(self) -> None:
        """Start email monitoring"""
        self.is_active = True
        self.task = asyncio.create_task(self._poll_emails())

    async def stop(self) -> None:
        """Stop email monitoring"""
        self.is_active = False
        if self.task:
            self.task.cancel()

    async def _poll_emails(self) -> None:
        """Poll for new emails"""
        while self.is_active:
            try:
                # In production, use imaplib or aiosmtplib
                emails = await self._fetch_emails()
                for email in emails:
                    if self._matches_filter(email):
                        await self.fire({
                            "from": email.get("from"),
                            "to": email.get("to"),
                            "subject": email.get("subject"),
                            "body": email.get("body"),
                            "attachments": email.get("attachments", []),
                            "received_at": email.get("received_at")
                        })

                await asyncio.sleep(self.poll_interval)
            except asyncio.CancelledError:
                break

    async def _fetch_emails(self) -> List[Dict[str, Any]]:
        """Fetch emails from inbox"""
        # Placeholder - implement with imaplib
        return []

    def _matches_filter(self, email: Dict[str, Any]) -> bool:
        """Check if email matches filter criteria"""
        email_filter = self.config.config.get('filter', {})

        if 'from' in email_filter:
            if email.get('from') != email_filter['from']:
                return False

        if 'subject_contains' in email_filter:
            if email_filter['subject_contains'] not in email.get('subject', ''):
                return False

        if 'has_attachments' in email_filter:
            if bool(email.get('attachments')) != email_filter['has_attachments']:
                return False

        return True


class FormSubmissionTrigger(BaseTrigger):
    """
    Form submission trigger
    Config: {
        "form_id": "contact-form",
        "fields": ["name", "email", "message"],
        "validate": true,
        "spam_protection": true,
        "recaptcha_secret": "secret-key"
    }
    """

    def __init__(self, config: TriggerConfig):
        super().__init__(config)
        self.form_id = config.config.get('form_id')

    async def start(self) -> None:
        """Start form listener"""
        self.is_active = True

    async def stop(self) -> None:
        """Stop form listener"""
        self.is_active = False

    async def handle_submission(self, form_data: Dict[str, Any]) -> TriggerEvent:
        """Handle form submission"""
        if self.config.config.get('validate'):
            self._validate_fields(form_data)

        if self.config.config.get('spam_protection'):
            await self._check_spam(form_data)

        return await self.fire({
            "form_id": self.form_id,
            "data": form_data,
            "timestamp": datetime.utcnow().isoformat()
        })

    def _validate_fields(self, form_data: Dict[str, Any]) -> None:
        """Validate required fields"""
        required_fields = self.config.config.get('fields', [])
        for field in required_fields:
            if field not in form_data or not form_data[field]:
                raise ValueError(f"Missing required field: {field}")

    async def _check_spam(self, form_data: Dict[str, Any]) -> None:
        """Check for spam"""
        # Implement reCAPTCHA verification or other spam checks
        pass


class DatabaseChangeTrigger(BaseTrigger):
    """
    Database change trigger - monitors database changes
    Config: {
        "connection_string": "postgresql://...",
        "table": "users",
        "operation": "INSERT",  # INSERT, UPDATE, DELETE
        "filter": {"status": "active"},
        "poll_interval": 10
    }
    """

    def __init__(self, config: TriggerConfig):
        super().__init__(config)
        self.task: Optional[asyncio.Task] = None
        self.poll_interval = config.config.get('poll_interval', 10)
        self.last_check: Optional[datetime] = None

    async def start(self) -> None:
        """Start database monitoring"""
        self.is_active = True
        self.last_check = datetime.utcnow()
        self.task = asyncio.create_task(self._poll_changes())

    async def stop(self) -> None:
        """Stop database monitoring"""
        self.is_active = False
        if self.task:
            self.task.cancel()

    async def _poll_changes(self) -> None:
        """Poll for database changes"""
        while self.is_active:
            try:
                changes = await self._fetch_changes()
                for change in changes:
                    await self.fire({
                        "table": self.config.config.get('table'),
                        "operation": change.get('operation'),
                        "old_data": change.get('old_data'),
                        "new_data": change.get('new_data'),
                        "timestamp": change.get('timestamp')
                    })

                self.last_check = datetime.utcnow()
                await asyncio.sleep(self.poll_interval)
            except asyncio.CancelledError:
                break

    async def _fetch_changes(self) -> List[Dict[str, Any]]:
        """Fetch database changes"""
        # Placeholder - implement with database-specific change tracking
        return []


class APICallTrigger(BaseTrigger):
    """
    API call trigger - polls an API endpoint
    Config: {
        "url": "https://api.example.com/data",
        "method": "GET",
        "headers": {"Authorization": "Bearer token"},
        "poll_interval": 300,
        "response_path": "data.items",
        "dedupe_key": "id"
    }
    """

    def __init__(self, config: TriggerConfig):
        super().__init__(config)
        self.task: Optional[asyncio.Task] = None
        self.poll_interval = config.config.get('poll_interval', 300)
        self.seen_items: Set[str] = set()

    async def start(self) -> None:
        """Start API polling"""
        self.is_active = True
        self.task = asyncio.create_task(self._poll_api())

    async def stop(self) -> None:
        """Stop API polling"""
        self.is_active = False
        if self.task:
            self.task.cancel()

    async def _poll_api(self) -> None:
        """Poll API endpoint"""
        while self.is_active:
            try:
                items = await self._fetch_api_data()
                dedupe_key = self.config.config.get('dedupe_key', 'id')

                for item in items:
                    item_id = str(item.get(dedupe_key))
                    if item_id not in self.seen_items:
                        self.seen_items.add(item_id)
                        await self.fire({"item": item})

                await asyncio.sleep(self.poll_interval)
            except asyncio.CancelledError:
                break

    async def _fetch_api_data(self) -> List[Dict[str, Any]]:
        """Fetch data from API"""
        # Placeholder - implement with aiohttp
        return []


class FileWatchTrigger(BaseTrigger):
    """
    File watch trigger - monitors file system changes
    Config: {
        "path": "/path/to/watch",
        "pattern": "*.csv",
        "recursive": true,
        "event_types": ["created", "modified", "deleted"]
    }
    """

    def __init__(self, config: TriggerConfig):
        super().__init__(config)
        self.task: Optional[asyncio.Task] = None

    async def start(self) -> None:
        """Start file watching"""
        self.is_active = True
        self.task = asyncio.create_task(self._watch_files())

    async def stop(self) -> None:
        """Stop file watching"""
        self.is_active = False
        if self.task:
            self.task.cancel()

    async def _watch_files(self) -> None:
        """Watch for file changes"""
        # Implement with watchdog or similar
        pass


class TriggerManager:
    """Manages all workflow triggers"""

    def __init__(self):
        self.triggers: Dict[str, BaseTrigger] = {}
        self.trigger_configs: Dict[str, TriggerConfig] = {}

    def register_trigger(
        self,
        workflow_id: str,
        trigger_type: TriggerType,
        config: Dict[str, Any]
    ) -> TriggerConfig:
        """Register a new trigger"""
        trigger_id = str(uuid.uuid4())

        trigger_config = TriggerConfig(
            id=trigger_id,
            workflow_id=workflow_id,
            trigger_type=trigger_type,
            config=config
        )

        self.trigger_configs[trigger_id] = trigger_config

        # Create trigger instance
        trigger_class = self._get_trigger_class(trigger_type)
        trigger = trigger_class(trigger_config)
        self.triggers[trigger_id] = trigger

        return trigger_config

    def _get_trigger_class(self, trigger_type: TriggerType) -> type:
        """Get trigger class for type"""
        mapping = {
            TriggerType.WEBHOOK: WebhookTrigger,
            TriggerType.SCHEDULE: ScheduleTrigger,
            TriggerType.EMAIL: EmailTrigger,
            TriggerType.FORM_SUBMISSION: FormSubmissionTrigger,
            TriggerType.DATABASE_CHANGE: DatabaseChangeTrigger,
            TriggerType.API_CALL: APICallTrigger,
            TriggerType.FILE_WATCH: FileWatchTrigger,
        }
        return mapping.get(trigger_type, BaseTrigger)

    async def start_trigger(self, trigger_id: str) -> None:
        """Start a trigger"""
        trigger = self.triggers.get(trigger_id)
        if trigger:
            await trigger.start()

    async def stop_trigger(self, trigger_id: str) -> None:
        """Stop a trigger"""
        trigger = self.triggers.get(trigger_id)
        if trigger:
            await trigger.stop()

    def delete_trigger(self, trigger_id: str) -> bool:
        """Delete a trigger"""
        if trigger_id in self.triggers:
            asyncio.create_task(self.triggers[trigger_id].stop())
            del self.triggers[trigger_id]
            del self.trigger_configs[trigger_id]
            return True
        return False

    def get_trigger(self, trigger_id: str) -> Optional[BaseTrigger]:
        """Get a trigger by ID"""
        return self.triggers.get(trigger_id)

    def list_triggers(self, workflow_id: Optional[str] = None) -> List[TriggerConfig]:
        """List all triggers"""
        configs = list(self.trigger_configs.values())
        if workflow_id:
            configs = [c for c in configs if c.workflow_id == workflow_id]
        return configs


# Global trigger manager instance
trigger_manager = TriggerManager()
