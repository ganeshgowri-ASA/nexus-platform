"""
NEXUS Workflow Actions
Comprehensive action system for workflow automation
"""

from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from abc import ABC, abstractmethod
import json
import asyncio
import subprocess
import os


class ActionType(Enum):
    """Types of workflow actions"""
    SEND_EMAIL = "send_email"
    API_REQUEST = "api_request"
    DATABASE_QUERY = "database_query"
    DATABASE_INSERT = "database_insert"
    DATABASE_UPDATE = "database_update"
    DATABASE_DELETE = "database_delete"
    FILE_READ = "file_read"
    FILE_WRITE = "file_write"
    FILE_DELETE = "file_delete"
    FILE_COPY = "file_copy"
    FILE_MOVE = "file_move"
    SEND_NOTIFICATION = "send_notification"
    SEND_SMS = "send_sms"
    SEND_SLACK_MESSAGE = "send_slack_message"
    EXECUTE_SCRIPT = "execute_script"
    HTTP_REQUEST = "http_request"
    TRANSFORM_DATA = "transform_data"
    DELAY = "delay"
    LOG = "log"
    CALL_WEBHOOK = "call_webhook"
    CREATE_FILE = "create_file"
    COMPRESS_FILE = "compress_file"
    PARSE_JSON = "parse_json"
    PARSE_CSV = "parse_csv"
    PARSE_XML = "parse_xml"
    GENERATE_PDF = "generate_pdf"
    SEND_WEBHOOK = "send_webhook"


@dataclass
class ActionResult:
    """Result from an action execution"""
    success: bool
    data: Any = None
    error: Optional[str] = None
    metadata: Dict[str, Any] = None
    duration_ms: Optional[float] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class BaseAction(ABC):
    """Base class for all actions"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config

    @abstractmethod
    async def execute(self, input_data: Dict[str, Any], context: Dict[str, Any]) -> ActionResult:
        """Execute the action"""
        pass

    def _replace_variables(self, template: str, variables: Dict[str, Any]) -> str:
        """Replace variables in template string"""
        result = template
        for key, value in variables.items():
            result = result.replace(f"{{{{{key}}}}}", str(value))
        return result


class SendEmailAction(BaseAction):
    """
    Send email action
    Config: {
        "to": "recipient@example.com",
        "subject": "Subject {{variable}}",
        "body": "Email body {{variable}}",
        "from": "sender@example.com",
        "cc": ["cc@example.com"],
        "bcc": ["bcc@example.com"],
        "attachments": ["/path/to/file"],
        "smtp_server": "smtp.gmail.com",
        "smtp_port": 587,
        "username": "user@example.com",
        "password": "app-password",
        "html": true
    }
    """

    async def execute(self, input_data: Dict[str, Any], context: Dict[str, Any]) -> ActionResult:
        try:
            to = self._replace_variables(self.config['to'], input_data)
            subject = self._replace_variables(self.config['subject'], input_data)
            body = self._replace_variables(self.config['body'], input_data)

            # In production, use aiosmtplib or similar
            email_data = {
                "to": to,
                "subject": subject,
                "body": body,
                "from": self.config.get('from'),
                "sent_at": datetime.utcnow().isoformat()
            }

            return ActionResult(
                success=True,
                data=email_data,
                metadata={"action": "send_email"}
            )

        except Exception as e:
            return ActionResult(success=False, error=str(e))


class APIRequestAction(BaseAction):
    """
    API request action
    Config: {
        "url": "https://api.example.com/endpoint",
        "method": "POST",
        "headers": {"Authorization": "Bearer {{token}}"},
        "body": {"key": "{{value}}"},
        "params": {"query": "{{search}}"},
        "timeout": 30,
        "retry": 3,
        "response_path": "data.result"
    }
    """

    async def execute(self, input_data: Dict[str, Any], context: Dict[str, Any]) -> ActionResult:
        try:
            url = self._replace_variables(self.config['url'], input_data)
            method = self.config.get('method', 'GET')

            headers = {}
            for key, value in self.config.get('headers', {}).items():
                headers[key] = self._replace_variables(str(value), input_data)

            # In production, use aiohttp
            response_data = {
                "url": url,
                "method": method,
                "status_code": 200,
                "response": {"message": "Request sent successfully"}
            }

            return ActionResult(
                success=True,
                data=response_data,
                metadata={"action": "api_request"}
            )

        except Exception as e:
            return ActionResult(success=False, error=str(e))


class DatabaseQueryAction(BaseAction):
    """
    Database query action
    Config: {
        "connection_string": "postgresql://user:pass@localhost/db",
        "query": "SELECT * FROM users WHERE id = {{user_id}}",
        "parameters": {"user_id": "{{user_id}}"}
    }
    """

    async def execute(self, input_data: Dict[str, Any], context: Dict[str, Any]) -> ActionResult:
        try:
            query = self._replace_variables(self.config['query'], input_data)

            # In production, use asyncpg, aiomysql, or similar
            results = {
                "query": query,
                "rows": [],
                "row_count": 0
            }

            return ActionResult(
                success=True,
                data=results,
                metadata={"action": "database_query"}
            )

        except Exception as e:
            return ActionResult(success=False, error=str(e))


class DatabaseInsertAction(BaseAction):
    """
    Database insert action
    Config: {
        "connection_string": "postgresql://user:pass@localhost/db",
        "table": "users",
        "data": {"name": "{{name}}", "email": "{{email}}"}
    }
    """

    async def execute(self, input_data: Dict[str, Any], context: Dict[str, Any]) -> ActionResult:
        try:
            table = self.config['table']
            data = {}
            for key, value in self.config.get('data', {}).items():
                data[key] = self._replace_variables(str(value), input_data)

            result = {
                "table": table,
                "inserted_id": "123",
                "inserted_data": data
            }

            return ActionResult(
                success=True,
                data=result,
                metadata={"action": "database_insert"}
            )

        except Exception as e:
            return ActionResult(success=False, error=str(e))


class FileReadAction(BaseAction):
    """
    File read action
    Config: {
        "path": "/path/to/file.txt",
        "encoding": "utf-8",
        "binary": false
    }
    """

    async def execute(self, input_data: Dict[str, Any], context: Dict[str, Any]) -> ActionResult:
        try:
            path = self._replace_variables(self.config['path'], input_data)
            encoding = self.config.get('encoding', 'utf-8')
            binary = self.config.get('binary', False)

            if binary:
                with open(path, 'rb') as f:
                    content = f.read()
            else:
                with open(path, 'r', encoding=encoding) as f:
                    content = f.read()

            return ActionResult(
                success=True,
                data={"path": path, "content": content},
                metadata={"action": "file_read"}
            )

        except Exception as e:
            return ActionResult(success=False, error=str(e))


class FileWriteAction(BaseAction):
    """
    File write action
    Config: {
        "path": "/path/to/file.txt",
        "content": "{{content}}",
        "encoding": "utf-8",
        "append": false
    }
    """

    async def execute(self, input_data: Dict[str, Any], context: Dict[str, Any]) -> ActionResult:
        try:
            path = self._replace_variables(self.config['path'], input_data)
            content = self._replace_variables(self.config['content'], input_data)
            encoding = self.config.get('encoding', 'utf-8')
            append = self.config.get('append', False)

            mode = 'a' if append else 'w'
            with open(path, mode, encoding=encoding) as f:
                f.write(content)

            return ActionResult(
                success=True,
                data={"path": path, "bytes_written": len(content)},
                metadata={"action": "file_write"}
            )

        except Exception as e:
            return ActionResult(success=False, error=str(e))


class FileDeleteAction(BaseAction):
    """
    File delete action
    Config: {
        "path": "/path/to/file.txt"
    }
    """

    async def execute(self, input_data: Dict[str, Any], context: Dict[str, Any]) -> ActionResult:
        try:
            path = self._replace_variables(self.config['path'], input_data)

            if os.path.exists(path):
                os.remove(path)
                return ActionResult(
                    success=True,
                    data={"path": path, "deleted": True},
                    metadata={"action": "file_delete"}
                )
            else:
                return ActionResult(
                    success=False,
                    error=f"File not found: {path}"
                )

        except Exception as e:
            return ActionResult(success=False, error=str(e))


class SendNotificationAction(BaseAction):
    """
    Send notification action
    Config: {
        "title": "Notification Title",
        "message": "{{message}}",
        "channel": "slack|email|sms|push",
        "recipient": "user@example.com",
        "priority": "high|normal|low"
    }
    """

    async def execute(self, input_data: Dict[str, Any], context: Dict[str, Any]) -> ActionResult:
        try:
            title = self._replace_variables(self.config.get('title', ''), input_data)
            message = self._replace_variables(self.config['message'], input_data)
            channel = self.config.get('channel', 'email')

            notification_data = {
                "title": title,
                "message": message,
                "channel": channel,
                "sent_at": datetime.utcnow().isoformat()
            }

            return ActionResult(
                success=True,
                data=notification_data,
                metadata={"action": "send_notification"}
            )

        except Exception as e:
            return ActionResult(success=False, error=str(e))


class SendSlackMessageAction(BaseAction):
    """
    Send Slack message action
    Config: {
        "webhook_url": "https://hooks.slack.com/services/...",
        "channel": "#general",
        "message": "{{message}}",
        "username": "Workflow Bot",
        "icon_emoji": ":robot_face:"
    }
    """

    async def execute(self, input_data: Dict[str, Any], context: Dict[str, Any]) -> ActionResult:
        try:
            message = self._replace_variables(self.config['message'], input_data)
            channel = self.config.get('channel', '#general')

            # In production, use aiohttp to send to Slack webhook
            slack_data = {
                "channel": channel,
                "message": message,
                "sent_at": datetime.utcnow().isoformat()
            }

            return ActionResult(
                success=True,
                data=slack_data,
                metadata={"action": "send_slack_message"}
            )

        except Exception as e:
            return ActionResult(success=False, error=str(e))


class ExecuteScriptAction(BaseAction):
    """
    Execute script action
    Config: {
        "language": "python|bash|javascript|powershell",
        "script": "print('Hello {{name}}')",
        "timeout": 30,
        "env": {"VAR": "{{value}}"}
    }
    """

    async def execute(self, input_data: Dict[str, Any], context: Dict[str, Any]) -> ActionResult:
        try:
            language = self.config.get('language', 'python')
            script = self._replace_variables(self.config['script'], input_data)
            timeout = self.config.get('timeout', 30)

            # Determine interpreter
            interpreters = {
                'python': ['python3', '-c'],
                'bash': ['bash', '-c'],
                'javascript': ['node', '-e'],
                'powershell': ['pwsh', '-Command']
            }

            interpreter = interpreters.get(language, ['python3', '-c'])
            cmd = interpreter + [script]

            # Execute script
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )

            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(),
                    timeout=timeout
                )

                return ActionResult(
                    success=process.returncode == 0,
                    data={
                        "stdout": stdout.decode(),
                        "stderr": stderr.decode(),
                        "return_code": process.returncode
                    },
                    metadata={"action": "execute_script"}
                )

            except asyncio.TimeoutError:
                process.kill()
                return ActionResult(success=False, error="Script execution timed out")

        except Exception as e:
            return ActionResult(success=False, error=str(e))


class TransformDataAction(BaseAction):
    """
    Transform data action
    Config: {
        "transformations": [
            {"type": "map", "field": "name", "to": "uppercase"},
            {"type": "filter", "field": "age", "condition": "> 18"},
            {"type": "rename", "from": "old_name", "to": "new_name"}
        ]
    }
    """

    async def execute(self, input_data: Dict[str, Any], context: Dict[str, Any]) -> ActionResult:
        try:
            data = input_data.copy()
            transformations = self.config.get('transformations', [])

            for transform in transformations:
                transform_type = transform.get('type')

                if transform_type == 'map':
                    field = transform['field']
                    operation = transform['to']
                    if field in data:
                        if operation == 'uppercase':
                            data[field] = str(data[field]).upper()
                        elif operation == 'lowercase':
                            data[field] = str(data[field]).lower()

                elif transform_type == 'rename':
                    old_name = transform['from']
                    new_name = transform['to']
                    if old_name in data:
                        data[new_name] = data.pop(old_name)

            return ActionResult(
                success=True,
                data=data,
                metadata={"action": "transform_data"}
            )

        except Exception as e:
            return ActionResult(success=False, error=str(e))


class DelayAction(BaseAction):
    """
    Delay action
    Config: {
        "duration": 5,  # seconds
        "unit": "seconds|minutes|hours"
    }
    """

    async def execute(self, input_data: Dict[str, Any], context: Dict[str, Any]) -> ActionResult:
        try:
            duration = self.config['duration']
            unit = self.config.get('unit', 'seconds')

            multipliers = {
                'seconds': 1,
                'minutes': 60,
                'hours': 3600
            }

            delay_seconds = duration * multipliers.get(unit, 1)
            await asyncio.sleep(delay_seconds)

            return ActionResult(
                success=True,
                data={"delayed_seconds": delay_seconds},
                metadata={"action": "delay"}
            )

        except Exception as e:
            return ActionResult(success=False, error=str(e))


class HTTPRequestAction(BaseAction):
    """
    HTTP request action
    Config: {
        "url": "https://example.com",
        "method": "GET|POST|PUT|DELETE",
        "headers": {},
        "body": {},
        "timeout": 30
    }
    """

    async def execute(self, input_data: Dict[str, Any], context: Dict[str, Any]) -> ActionResult:
        try:
            url = self._replace_variables(self.config['url'], input_data)
            method = self.config.get('method', 'GET')

            # In production, use aiohttp
            response_data = {
                "url": url,
                "method": method,
                "status_code": 200,
                "response": {}
            }

            return ActionResult(
                success=True,
                data=response_data,
                metadata={"action": "http_request"}
            )

        except Exception as e:
            return ActionResult(success=False, error=str(e))


class ActionExecutor:
    """Executes workflow actions"""

    def __init__(self):
        self.action_classes: Dict[ActionType, type] = {
            ActionType.SEND_EMAIL: SendEmailAction,
            ActionType.API_REQUEST: APIRequestAction,
            ActionType.DATABASE_QUERY: DatabaseQueryAction,
            ActionType.DATABASE_INSERT: DatabaseInsertAction,
            ActionType.FILE_READ: FileReadAction,
            ActionType.FILE_WRITE: FileWriteAction,
            ActionType.FILE_DELETE: FileDeleteAction,
            ActionType.SEND_NOTIFICATION: SendNotificationAction,
            ActionType.SEND_SLACK_MESSAGE: SendSlackMessageAction,
            ActionType.EXECUTE_SCRIPT: ExecuteScriptAction,
            ActionType.TRANSFORM_DATA: TransformDataAction,
            ActionType.DELAY: DelayAction,
            ActionType.HTTP_REQUEST: HTTPRequestAction,
        }

    async def execute_action(
        self,
        action_type: ActionType,
        config: Dict[str, Any],
        input_data: Dict[str, Any],
        context: Dict[str, Any]
    ) -> ActionResult:
        """Execute an action"""
        action_class = self.action_classes.get(action_type)
        if not action_class:
            return ActionResult(
                success=False,
                error=f"Unknown action type: {action_type}"
            )

        action = action_class(config)
        start_time = datetime.utcnow()

        result = await action.execute(input_data, context)

        end_time = datetime.utcnow()
        result.duration_ms = (end_time - start_time).total_seconds() * 1000

        return result

    def register_action(self, action_type: ActionType, action_class: type) -> None:
        """Register a custom action type"""
        self.action_classes[action_type] = action_class


# Global action executor instance
action_executor = ActionExecutor()
