"""
Nexus CRM Module - Enterprise-grade Customer Relationship Management

A production-ready CRM system rivaling Salesforce and HubSpot with:
- Full contact and company management
- Deal pipeline and forecasting
- Activity and task tracking
- Email integration and campaigns
- Advanced analytics and reporting
- Workflow automation
- AI-powered insights and predictions
"""

__version__ = "1.0.0"
__author__ = "Nexus Platform"

# Import all managers for easy access
from .contacts import (
    ContactManager,
    Contact,
    ContactStatus,
    LeadSource,
    ContactAddress,
    SocialProfile,
    CustomField,
)

from .companies import (
    CompanyManager,
    Company,
    CompanyType,
    Industry,
    CompanySize,
    CompanyAddress,
    CompanyFinancials,
)

from .deals import (
    DealManager,
    Deal,
    DealStage,
    DealPriority,
    LossReason,
    DealProduct,
)

from .pipeline import (
    PipelineManager,
    Pipeline,
    PipelineStage,
    StageType,
    DealMovement,
)

from .activities import (
    ActivityManager,
    Activity,
    ActivityType,
    ActivityStatus,
    CallOutcome,
)

from .tasks import (
    TaskManager,
    Task,
    TaskType,
    TaskPriority,
    TaskStatus,
    ReminderType,
)

from .email_integration import (
    EmailIntegrationManager,
    EmailTemplate,
    EmailTemplateType,
    EmailSequence,
    EmailSequenceStep,
    EmailTracking,
    EmailCampaign,
    EmailSequenceStatus,
    CampaignStatus,
)

from .analytics import (
    CRMAnalytics,
    MetricPeriod,
    ReportType,
    MetricValue,
    Dashboard,
)

from .automation import (
    AutomationEngine,
    Workflow,
    WorkflowAction,
    WorkflowExecution,
    LeadScoringRule,
    TriggerType,
    ActionType,
    ConditionOperator,
    WorkflowStatus,
    Condition,
)

from .ai_insights import (
    AIInsightsEngine,
    AIInsight,
    InsightType,
    PriorityLevel,
    ChurnRisk,
)

# UI
from .streamlit_ui import CRMUI, main as run_ui

__all__ = [
    # Contacts
    "ContactManager",
    "Contact",
    "ContactStatus",
    "LeadSource",
    "ContactAddress",
    "SocialProfile",
    "CustomField",
    # Companies
    "CompanyManager",
    "Company",
    "CompanyType",
    "Industry",
    "CompanySize",
    "CompanyAddress",
    "CompanyFinancials",
    # Deals
    "DealManager",
    "Deal",
    "DealStage",
    "DealPriority",
    "LossReason",
    "DealProduct",
    # Pipeline
    "PipelineManager",
    "Pipeline",
    "PipelineStage",
    "StageType",
    "DealMovement",
    # Activities
    "ActivityManager",
    "Activity",
    "ActivityType",
    "ActivityStatus",
    "CallOutcome",
    # Tasks
    "TaskManager",
    "Task",
    "TaskType",
    "TaskPriority",
    "TaskStatus",
    "ReminderType",
    # Email
    "EmailIntegrationManager",
    "EmailTemplate",
    "EmailTemplateType",
    "EmailSequence",
    "EmailSequenceStep",
    "EmailTracking",
    "EmailCampaign",
    "EmailSequenceStatus",
    "CampaignStatus",
    # Analytics
    "CRMAnalytics",
    "MetricPeriod",
    "ReportType",
    "MetricValue",
    "Dashboard",
    # Automation
    "AutomationEngine",
    "Workflow",
    "WorkflowAction",
    "WorkflowExecution",
    "LeadScoringRule",
    "TriggerType",
    "ActionType",
    "ConditionOperator",
    "WorkflowStatus",
    "Condition",
    # AI Insights
    "AIInsightsEngine",
    "AIInsight",
    "InsightType",
    "PriorityLevel",
    "ChurnRisk",
    # UI
    "CRMUI",
    "run_ui",
]


def create_crm_system():
    """
    Create a fully initialized CRM system with all managers.

    Returns:
        dict: Dictionary containing all initialized managers
    """
    # Initialize all managers
    contact_manager = ContactManager()
    company_manager = CompanyManager()
    deal_manager = DealManager()
    pipeline_manager = PipelineManager()
    activity_manager = ActivityManager()
    task_manager = TaskManager()
    email_manager = EmailIntegrationManager()
    automation_engine = AutomationEngine()

    # Initialize analytics with all managers
    analytics = CRMAnalytics(
        contact_manager=contact_manager,
        company_manager=company_manager,
        deal_manager=deal_manager,
        activity_manager=activity_manager,
        task_manager=task_manager,
        email_manager=email_manager,
    )

    # Initialize AI insights with all managers
    ai_insights = AIInsightsEngine(
        contact_manager=contact_manager,
        company_manager=company_manager,
        deal_manager=deal_manager,
        activity_manager=activity_manager,
        task_manager=task_manager,
    )

    # Create default pipeline
    pipeline_manager.create_default_pipeline()

    return {
        "contact_manager": contact_manager,
        "company_manager": company_manager,
        "deal_manager": deal_manager,
        "pipeline_manager": pipeline_manager,
        "activity_manager": activity_manager,
        "task_manager": task_manager,
        "email_manager": email_manager,
        "automation_engine": automation_engine,
        "analytics": analytics,
        "ai_insights": ai_insights,
    }


# Quick start example
def quick_start():
    """
    Quick start example demonstrating basic CRM usage.
    """
    # Create CRM system
    crm = create_crm_system()

    # Create a contact
    contact = Contact(
        id=crm["contact_manager"]._generate_id(),
        first_name="John",
        last_name="Doe",
        email="john.doe@example.com",
        phone="+1-555-0100",
        company_name="Acme Corp",
        status=ContactStatus.LEAD,
    )
    crm["contact_manager"].create_contact(contact)

    # Create a company
    company = Company(
        id=crm["company_manager"]._generate_id(),
        name="Acme Corp",
        company_type=CompanyType.PROSPECT,
        industry=Industry.TECHNOLOGY,
    )
    crm["company_manager"].create_company(company)

    # Create a deal
    deal = Deal(
        id=crm["deal_manager"]._generate_id(),
        name="Acme Corp - Enterprise License",
        company_id=company.id,
        contact_id=contact.id,
        amount=50000,
        stage=DealStage.QUALIFICATION,
    )
    crm["deal_manager"].create_deal(deal)

    # Log an activity
    crm["activity_manager"].log_call(
        subject="Initial discovery call",
        contact_id=contact.id,
        company_id=company.id,
        deal_id=deal.id,
        duration_minutes=30,
    )

    # Create a task
    task = Task(
        id=crm["task_manager"]._generate_id(),
        title="Follow up with John Doe",
        contact_id=contact.id,
        due_date=datetime.now() + timedelta(days=2),
        priority=TaskPriority.HIGH,
    )
    crm["task_manager"].create_task(task)

    print("✅ CRM Quick Start Complete!")
    print(f"   - Created contact: {contact.full_name}")
    print(f"   - Created company: {company.name}")
    print(f"   - Created deal: {deal.name} (${deal.amount:,.0f})")
    print(f"   - Logged activity and created follow-up task")

    return crm


if __name__ == "__main__":
    from datetime import timedelta

    # Run quick start example
    quick_start()
