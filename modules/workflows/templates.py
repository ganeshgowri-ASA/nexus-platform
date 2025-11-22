"""
NEXUS Workflow Templates
Pre-built workflow templates and marketplace
"""

from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import json
import uuid


class TemplateCategory(Enum):
    """Categories of workflow templates"""
    AUTOMATION = "automation"
    INTEGRATION = "integration"
    DATA_PROCESSING = "data_processing"
    NOTIFICATIONS = "notifications"
    SCHEDULING = "scheduling"
    APPROVAL = "approval"
    MONITORING = "monitoring"
    REPORTING = "reporting"
    CUSTOMER_SERVICE = "customer_service"
    SALES = "sales"
    MARKETING = "marketing"
    HR = "hr"
    FINANCE = "finance"
    DEVELOPMENT = "development"


@dataclass
class WorkflowTemplate:
    """Workflow template definition"""
    id: str
    name: str
    description: str
    category: TemplateCategory
    icon: str
    workflow_definition: Dict[str, Any]
    variables: Dict[str, Any] = field(default_factory=dict)
    required_integrations: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    use_count: int = 0
    rating: float = 0.0
    author: str = "NEXUS"
    version: str = "1.0.0"
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    is_premium: bool = False
    is_featured: bool = False


class TemplateLibrary:
    """Library of workflow templates"""

    def __init__(self):
        self.templates: Dict[str, WorkflowTemplate] = {}
        self._load_default_templates()

    def _load_default_templates(self):
        """Load default workflow templates"""

        # 1. Email to Slack notification
        self.add_template(WorkflowTemplate(
            id="email-to-slack",
            name="Email to Slack Notification",
            description="Forward important emails to Slack channel",
            category=TemplateCategory.NOTIFICATIONS,
            icon="📧",
            workflow_definition={
                "nodes": [
                    {
                        "id": "trigger1",
                        "name": "Email Received",
                        "type": "trigger",
                        "config": {
                            "trigger_type": "email",
                            "filter": {
                                "subject_contains": "URGENT"
                            }
                        },
                        "position": {"x": 100, "y": 100}
                    },
                    {
                        "id": "action1",
                        "name": "Send to Slack",
                        "type": "action",
                        "config": {
                            "action_type": "send_slack_message",
                            "channel": "#alerts",
                            "message": "New urgent email: {{subject}}"
                        },
                        "position": {"x": 300, "y": 100}
                    }
                ],
                "connections": [
                    {
                        "source_node_id": "trigger1",
                        "target_node_id": "action1"
                    }
                ]
            },
            required_integrations=["email", "slack"],
            tags=["email", "slack", "notifications"],
            is_featured=True
        ))

        # 2. Daily report generation
        self.add_template(WorkflowTemplate(
            id="daily-report",
            name="Daily Report Generator",
            description="Generate and email daily reports automatically",
            category=TemplateCategory.REPORTING,
            icon="📊",
            workflow_definition={
                "nodes": [
                    {
                        "id": "trigger1",
                        "name": "Daily Schedule",
                        "type": "trigger",
                        "config": {
                            "trigger_type": "schedule",
                            "cron": "0 9 * * *"
                        },
                        "position": {"x": 100, "y": 100}
                    },
                    {
                        "id": "action1",
                        "name": "Fetch Data",
                        "type": "action",
                        "config": {
                            "action_type": "database_query",
                            "query": "SELECT * FROM analytics WHERE date = CURRENT_DATE"
                        },
                        "position": {"x": 300, "y": 100}
                    },
                    {
                        "id": "action2",
                        "name": "Send Report",
                        "type": "action",
                        "config": {
                            "action_type": "send_email",
                            "to": "team@example.com",
                            "subject": "Daily Report",
                            "body": "Here is your daily report: {{data}}"
                        },
                        "position": {"x": 500, "y": 100}
                    }
                ],
                "connections": [
                    {"source_node_id": "trigger1", "target_node_id": "action1"},
                    {"source_node_id": "action1", "target_node_id": "action2"}
                ]
            },
            required_integrations=["database", "email"],
            tags=["reporting", "automation", "email"],
            is_featured=True
        ))

        # 3. Lead capture from form
        self.add_template(WorkflowTemplate(
            id="lead-capture",
            name="Lead Capture & CRM Sync",
            description="Capture form submissions and add to CRM",
            category=TemplateCategory.SALES,
            icon="🎯",
            workflow_definition={
                "nodes": [
                    {
                        "id": "trigger1",
                        "name": "Form Submitted",
                        "type": "trigger",
                        "config": {
                            "trigger_type": "form_submission",
                            "form_id": "contact-form"
                        },
                        "position": {"x": 100, "y": 100}
                    },
                    {
                        "id": "action1",
                        "name": "Add to CRM",
                        "type": "action",
                        "config": {
                            "action_type": "api_request",
                            "integration": "salesforce",
                            "endpoint": "create_lead"
                        },
                        "position": {"x": 300, "y": 100}
                    },
                    {
                        "id": "action2",
                        "name": "Send Notification",
                        "type": "action",
                        "config": {
                            "action_type": "send_notification",
                            "message": "New lead: {{name}}"
                        },
                        "position": {"x": 500, "y": 100}
                    }
                ],
                "connections": [
                    {"source_node_id": "trigger1", "target_node_id": "action1"},
                    {"source_node_id": "action1", "target_node_id": "action2"}
                ]
            },
            required_integrations=["forms", "salesforce"],
            tags=["sales", "leads", "crm"],
            is_featured=True
        ))

        # 4. Customer onboarding
        self.add_template(WorkflowTemplate(
            id="customer-onboarding",
            name="Automated Customer Onboarding",
            description="Welcome new customers with automated email sequence",
            category=TemplateCategory.CUSTOMER_SERVICE,
            icon="👋",
            workflow_definition={
                "nodes": [
                    {
                        "id": "trigger1",
                        "name": "New Customer",
                        "type": "trigger",
                        "config": {
                            "trigger_type": "webhook",
                            "path": "/new-customer"
                        },
                        "position": {"x": 100, "y": 100}
                    },
                    {
                        "id": "action1",
                        "name": "Welcome Email",
                        "type": "action",
                        "config": {
                            "action_type": "send_email",
                            "subject": "Welcome to {{company}}!",
                            "template": "welcome"
                        },
                        "position": {"x": 300, "y": 100}
                    },
                    {
                        "id": "delay1",
                        "name": "Wait 1 Day",
                        "type": "delay",
                        "config": {
                            "duration": 1,
                            "unit": "days"
                        },
                        "position": {"x": 500, "y": 100}
                    },
                    {
                        "id": "action2",
                        "name": "Follow-up Email",
                        "type": "action",
                        "config": {
                            "action_type": "send_email",
                            "subject": "Getting started guide",
                            "template": "getting-started"
                        },
                        "position": {"x": 700, "y": 100}
                    }
                ],
                "connections": [
                    {"source_node_id": "trigger1", "target_node_id": "action1"},
                    {"source_node_id": "action1", "target_node_id": "delay1"},
                    {"source_node_id": "delay1", "target_node_id": "action2"}
                ]
            },
            required_integrations=["email"],
            tags=["customer-service", "onboarding", "email"],
            is_featured=True
        ))

        # 5. Invoice processing
        self.add_template(WorkflowTemplate(
            id="invoice-processing",
            name="Automated Invoice Processing",
            description="Process invoices and update accounting system",
            category=TemplateCategory.FINANCE,
            icon="💰",
            workflow_definition={
                "nodes": [
                    {
                        "id": "trigger1",
                        "name": "New Invoice",
                        "type": "trigger",
                        "config": {
                            "trigger_type": "email",
                            "filter": {"has_attachments": True}
                        },
                        "position": {"x": 100, "y": 100}
                    },
                    {
                        "id": "action1",
                        "name": "Extract Data",
                        "type": "action",
                        "config": {
                            "action_type": "parse_pdf",
                            "fields": ["amount", "date", "vendor"]
                        },
                        "position": {"x": 300, "y": 100}
                    },
                    {
                        "id": "condition1",
                        "name": "Check Amount",
                        "type": "condition",
                        "config": {
                            "field": "amount",
                            "operator": "greater_than",
                            "value": 1000
                        },
                        "position": {"x": 500, "y": 100}
                    },
                    {
                        "id": "action2",
                        "name": "Request Approval",
                        "type": "action",
                        "config": {
                            "action_type": "send_notification",
                            "message": "Approval needed for invoice"
                        },
                        "position": {"x": 700, "y": 50}
                    },
                    {
                        "id": "action3",
                        "name": "Auto-approve",
                        "type": "action",
                        "config": {
                            "action_type": "database_insert",
                            "table": "invoices"
                        },
                        "position": {"x": 700, "y": 150}
                    }
                ],
                "connections": [
                    {"source_node_id": "trigger1", "target_node_id": "action1"},
                    {"source_node_id": "action1", "target_node_id": "condition1"},
                    {
                        "source_node_id": "condition1",
                        "target_node_id": "action2",
                        "connection_type": "condition_true"
                    },
                    {
                        "source_node_id": "condition1",
                        "target_node_id": "action3",
                        "connection_type": "condition_false"
                    }
                ]
            },
            required_integrations=["email", "database"],
            tags=["finance", "invoices", "automation"]
        ))

        # 6. Social media scheduler
        self.add_template(WorkflowTemplate(
            id="social-media-scheduler",
            name="Social Media Post Scheduler",
            description="Schedule and post to multiple social media platforms",
            category=TemplateCategory.MARKETING,
            icon="📱",
            workflow_definition={
                "nodes": [
                    {
                        "id": "trigger1",
                        "name": "Schedule",
                        "type": "trigger",
                        "config": {
                            "trigger_type": "schedule",
                            "cron": "0 10,14,18 * * *"
                        },
                        "position": {"x": 100, "y": 100}
                    },
                    {
                        "id": "action1",
                        "name": "Get Content",
                        "type": "action",
                        "config": {
                            "action_type": "database_query",
                            "query": "SELECT * FROM posts WHERE scheduled_time = NOW()"
                        },
                        "position": {"x": 300, "y": 100}
                    },
                    {
                        "id": "parallel1",
                        "name": "Post to Platforms",
                        "type": "parallel",
                        "config": {},
                        "position": {"x": 500, "y": 100}
                    },
                    {
                        "id": "action2",
                        "name": "Post to Twitter",
                        "type": "action",
                        "config": {
                            "integration": "twitter",
                            "action": "post_tweet"
                        },
                        "position": {"x": 700, "y": 50}
                    },
                    {
                        "id": "action3",
                        "name": "Post to LinkedIn",
                        "type": "action",
                        "config": {
                            "integration": "linkedin",
                            "action": "create_post"
                        },
                        "position": {"x": 700, "y": 150}
                    }
                ],
                "connections": [
                    {"source_node_id": "trigger1", "target_node_id": "action1"},
                    {"source_node_id": "action1", "target_node_id": "parallel1"},
                    {"source_node_id": "parallel1", "target_node_id": "action2"},
                    {"source_node_id": "parallel1", "target_node_id": "action3"}
                ]
            },
            required_integrations=["database", "twitter", "linkedin"],
            tags=["marketing", "social-media", "scheduling"]
        ))

        # 7. Data backup
        self.add_template(WorkflowTemplate(
            id="data-backup",
            name="Automated Data Backup",
            description="Backup database to cloud storage daily",
            category=TemplateCategory.AUTOMATION,
            icon="💾",
            workflow_definition={
                "nodes": [
                    {
                        "id": "trigger1",
                        "name": "Daily at Midnight",
                        "type": "trigger",
                        "config": {
                            "trigger_type": "schedule",
                            "cron": "0 0 * * *"
                        },
                        "position": {"x": 100, "y": 100}
                    },
                    {
                        "id": "action1",
                        "name": "Create Backup",
                        "type": "action",
                        "config": {
                            "action_type": "execute_script",
                            "script": "pg_dump database > backup.sql"
                        },
                        "position": {"x": 300, "y": 100}
                    },
                    {
                        "id": "action2",
                        "name": "Upload to S3",
                        "type": "action",
                        "config": {
                            "integration": "aws_s3",
                            "action": "upload_file"
                        },
                        "position": {"x": 500, "y": 100}
                    },
                    {
                        "id": "action3",
                        "name": "Send Confirmation",
                        "type": "action",
                        "config": {
                            "action_type": "send_email",
                            "subject": "Backup completed"
                        },
                        "position": {"x": 700, "y": 100}
                    }
                ],
                "connections": [
                    {"source_node_id": "trigger1", "target_node_id": "action1"},
                    {"source_node_id": "action1", "target_node_id": "action2"},
                    {"source_node_id": "action2", "target_node_id": "action3"}
                ]
            },
            required_integrations=["database", "aws_s3", "email"],
            tags=["backup", "automation", "database"]
        ))

        # 8. Error monitoring
        self.add_template(WorkflowTemplate(
            id="error-monitoring",
            name="Error Monitoring & Alerting",
            description="Monitor application errors and send alerts",
            category=TemplateCategory.MONITORING,
            icon="🚨",
            workflow_definition={
                "nodes": [
                    {
                        "id": "trigger1",
                        "name": "Error Occurred",
                        "type": "trigger",
                        "config": {
                            "trigger_type": "webhook",
                            "path": "/error-webhook"
                        },
                        "position": {"x": 100, "y": 100}
                    },
                    {
                        "id": "condition1",
                        "name": "Check Severity",
                        "type": "condition",
                        "config": {
                            "field": "severity",
                            "operator": "equals",
                            "value": "critical"
                        },
                        "position": {"x": 300, "y": 100}
                    },
                    {
                        "id": "action1",
                        "name": "Send to Slack",
                        "type": "action",
                        "config": {
                            "integration": "slack",
                            "channel": "#alerts"
                        },
                        "position": {"x": 500, "y": 50}
                    },
                    {
                        "id": "action2",
                        "name": "Log Error",
                        "type": "action",
                        "config": {
                            "action_type": "database_insert",
                            "table": "error_logs"
                        },
                        "position": {"x": 500, "y": 150}
                    }
                ],
                "connections": [
                    {"source_node_id": "trigger1", "target_node_id": "condition1"},
                    {
                        "source_node_id": "condition1",
                        "target_node_id": "action1",
                        "connection_type": "condition_true"
                    },
                    {"source_node_id": "condition1", "target_node_id": "action2"}
                ]
            },
            required_integrations=["slack", "database"],
            tags=["monitoring", "errors", "alerts"]
        ))

    def add_template(self, template: WorkflowTemplate) -> None:
        """Add a template to the library"""
        self.templates[template.id] = template

    def get_template(self, template_id: str) -> Optional[WorkflowTemplate]:
        """Get a template by ID"""
        return self.templates.get(template_id)

    def list_templates(
        self,
        category: Optional[TemplateCategory] = None,
        tags: Optional[List[str]] = None,
        search: Optional[str] = None,
        featured_only: bool = False
    ) -> List[WorkflowTemplate]:
        """List templates with filters"""
        templates = list(self.templates.values())

        if category:
            templates = [t for t in templates if t.category == category]

        if tags:
            templates = [
                t for t in templates
                if any(tag in t.tags for tag in tags)
            ]

        if search:
            search_lower = search.lower()
            templates = [
                t for t in templates
                if search_lower in t.name.lower() or search_lower in t.description.lower()
            ]

        if featured_only:
            templates = [t for t in templates if t.is_featured]

        # Sort by use count and rating
        templates.sort(key=lambda x: (x.use_count, x.rating), reverse=True)

        return templates

    def create_workflow_from_template(
        self,
        template_id: str,
        name: str,
        variables: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Create a new workflow from a template"""
        template = self.get_template(template_id)
        if not template:
            raise ValueError(f"Template {template_id} not found")

        # Clone workflow definition
        workflow_def = json.loads(json.dumps(template.workflow_definition))

        # Replace variables
        if variables:
            workflow_def = self._replace_variables(workflow_def, variables)

        # Increment use count
        template.use_count += 1

        return {
            "name": name,
            "description": f"Created from template: {template.name}",
            "nodes": workflow_def["nodes"],
            "connections": workflow_def["connections"],
            "template_id": template_id
        }

    def _replace_variables(self, obj: Any, variables: Dict[str, Any]) -> Any:
        """Recursively replace variables in object"""
        if isinstance(obj, dict):
            return {k: self._replace_variables(v, variables) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._replace_variables(item, variables) for item in obj]
        elif isinstance(obj, str):
            for key, value in variables.items():
                obj = obj.replace(f"{{{{{key}}}}}", str(value))
            return obj
        else:
            return obj

    def export_template(self, template_id: str) -> str:
        """Export template as JSON"""
        template = self.get_template(template_id)
        if not template:
            raise ValueError(f"Template {template_id} not found")

        template_dict = {
            "id": template.id,
            "name": template.name,
            "description": template.description,
            "category": template.category.value,
            "workflow_definition": template.workflow_definition,
            "variables": template.variables,
            "required_integrations": template.required_integrations,
            "tags": template.tags,
            "version": template.version
        }

        return json.dumps(template_dict, indent=2, default=str)

    def import_template(self, template_json: str) -> WorkflowTemplate:
        """Import template from JSON"""
        data = json.loads(template_json)

        template = WorkflowTemplate(
            id=data.get('id', str(uuid.uuid4())),
            name=data['name'],
            description=data['description'],
            category=TemplateCategory(data['category']),
            icon=data.get('icon', '📋'),
            workflow_definition=data['workflow_definition'],
            variables=data.get('variables', {}),
            required_integrations=data.get('required_integrations', []),
            tags=data.get('tags', []),
            version=data.get('version', '1.0.0')
        )

        self.add_template(template)
        return template


# Global template library
template_library = TemplateLibrary()
