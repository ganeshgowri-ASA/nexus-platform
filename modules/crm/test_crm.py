"""
Comprehensive test suite for the CRM module.
"""

import pytest
from datetime import datetime, date, timedelta

from .contacts import ContactManager, Contact, ContactStatus, LeadSource
from .companies import CompanyManager, Company, CompanyType, Industry, CompanySize
from .deals import DealManager, Deal, DealStage, DealPriority, DealProduct
from .pipeline import PipelineManager, Pipeline, PipelineStage, StageType
from .activities import ActivityManager, Activity, ActivityType, ActivityStatus
from .tasks import TaskManager, Task, TaskType, TaskPriority, TaskStatus
from .email_integration import EmailIntegrationManager, EmailTemplate, EmailTemplateType
from .automation import AutomationEngine, Workflow, TriggerType, WorkflowStatus, LeadScoringRule, ConditionOperator
from .ai_insights import AIInsightsEngine


class TestContacts:
    """Test contact management."""

    def test_create_contact(self):
        manager = ContactManager()
        contact = Contact(
            id="contact_1",
            first_name="John",
            last_name="Doe",
            email="john.doe@example.com",
            status=ContactStatus.LEAD,
        )
        created = manager.create_contact(contact)
        assert created.id == "contact_1"
        assert created.full_name == "John Doe"

    def test_duplicate_email(self):
        manager = ContactManager()
        contact1 = Contact(
            id="contact_1",
            first_name="John",
            last_name="Doe",
            email="john@example.com"
        )
        manager.create_contact(contact1)

        contact2 = Contact(
            id="contact_2",
            first_name="Jane",
            last_name="Doe",
            email="john@example.com"
        )

        with pytest.raises(ValueError):
            manager.create_contact(contact2)

    def test_search_contacts(self):
        manager = ContactManager()
        contact1 = Contact(
            id="contact_1",
            first_name="John",
            last_name="Doe",
            email="john@example.com"
        )
        contact2 = Contact(
            id="contact_2",
            first_name="Jane",
            last_name="Smith",
            email="jane@example.com"
        )
        manager.create_contact(contact1)
        manager.create_contact(contact2)

        results = manager.search_contacts("John")
        assert len(results) == 1
        assert results[0].first_name == "John"

    def test_add_tags(self):
        manager = ContactManager()
        contact = Contact(
            id="contact_1",
            first_name="John",
            last_name="Doe",
            email="john@example.com"
        )
        manager.create_contact(contact)
        manager.add_tags("contact_1", ["vip", "enterprise"])

        updated = manager.get_contact("contact_1")
        assert "vip" in updated.tags
        assert "enterprise" in updated.tags


class TestCompanies:
    """Test company management."""

    def test_create_company(self):
        manager = CompanyManager()
        company = Company(
            id="company_1",
            name="Acme Corp",
            company_type=CompanyType.CUSTOMER,
            industry=Industry.TECHNOLOGY,
        )
        created = manager.create_company(company)
        assert created.name == "Acme Corp"

    def test_company_hierarchy(self):
        manager = CompanyManager()
        parent = Company(
            id="parent_1",
            name="Parent Corp",
        )
        manager.create_company(parent)

        subsidiary = Company(
            id="sub_1",
            name="Subsidiary Inc",
        )
        manager.create_company(subsidiary)
        manager.set_parent_company("sub_1", "parent_1")

        hierarchy = manager.get_company_hierarchy("parent_1")
        assert len(hierarchy['subsidiaries']) == 1

    def test_calculate_health_score(self):
        manager = CompanyManager()
        company = Company(
            id="company_1",
            name="Acme Corp",
            total_revenue=100000,
            won_deals_count=5,
            lost_deals_count=1,
            last_interaction=datetime.now(),
        )
        manager.create_company(company)

        score = manager.calculate_health_score("company_1")
        assert 0 <= score <= 100


class TestDeals:
    """Test deal management."""

    def test_create_deal(self):
        manager = DealManager()
        deal = Deal(
            id="deal_1",
            name="Big Deal",
            amount=50000,
            stage=DealStage.PROPOSAL,
        )
        created = manager.create_deal(deal)
        assert created.probability == 50  # Default for proposal stage

    def test_move_to_stage(self):
        manager = DealManager()
        deal = Deal(
            id="deal_1",
            name="Test Deal",
            amount=10000,
            stage=DealStage.QUALIFICATION,
        )
        manager.create_deal(deal)
        manager.move_to_stage("deal_1", DealStage.PROPOSAL)

        updated = manager.get_deal("deal_1")
        assert updated.stage == DealStage.PROPOSAL
        assert updated.probability == 50

    def test_win_deal(self):
        manager = DealManager()
        deal = Deal(
            id="deal_1",
            name="Test Deal",
            amount=10000,
        )
        manager.create_deal(deal)
        manager.win_deal("deal_1", actual_amount=12000)

        won = manager.get_deal("deal_1")
        assert won.is_won is True
        assert won.is_closed is True
        assert won.amount == 12000

    def test_forecast(self):
        manager = DealManager()
        deal1 = Deal(
            id="deal_1",
            name="Deal 1",
            amount=10000,
            probability=50,
            expected_close_date=date.today() + timedelta(days=30),
        )
        deal2 = Deal(
            id="deal_2",
            name="Deal 2",
            amount=20000,
            probability=75,
            expected_close_date=date.today() + timedelta(days=30),
        )
        manager.create_deal(deal1)
        manager.create_deal(deal2)

        forecast = manager.get_forecast()
        assert forecast['total_pipeline_value'] == 30000
        assert forecast['weighted_pipeline_value'] == 20000  # (10000*0.5 + 20000*0.75)


class TestPipeline:
    """Test pipeline management."""

    def test_create_default_pipeline(self):
        manager = PipelineManager()
        pipeline = manager.create_default_pipeline()

        assert pipeline is not None
        assert len(pipeline.stages) == 7  # Default stages
        assert pipeline.is_default is True

    def test_add_stage(self):
        manager = PipelineManager()
        pipeline = manager.create_default_pipeline()

        stage = manager.add_stage(
            pipeline.id,
            "Custom Stage",
            order=3,
            probability=60,
        )

        assert stage is not None
        updated = manager.get_pipeline(pipeline.id)
        assert len(updated.stages) == 8

    def test_move_deal(self):
        manager = PipelineManager()
        pipeline = manager.create_default_pipeline()

        success = manager.move_deal(
            pipeline.id,
            "deal_1",
            "Test Deal",
            None,
            pipeline.stages[0].id,
        )

        assert success is True


class TestActivities:
    """Test activity management."""

    def test_log_call(self):
        from .activities import CallOutcome
        manager = ActivityManager()

        activity = manager.log_call(
            subject="Follow-up call",
            contact_id="contact_1",
            outcome=CallOutcome.CONNECTED,
            duration_minutes=15,
        )

        assert activity.activity_type == ActivityType.CALL
        assert activity.status == ActivityStatus.COMPLETED

    def test_schedule_meeting(self):
        manager = ActivityManager()
        scheduled_time = datetime.now() + timedelta(days=1)

        meeting = manager.schedule_meeting(
            subject="Product Demo",
            scheduled_at=scheduled_time,
            duration_minutes=60,
            contact_id="contact_1",
        )

        assert meeting.activity_type == ActivityType.MEETING
        assert meeting.status == ActivityStatus.SCHEDULED

    def test_get_timeline(self):
        manager = ActivityManager()

        manager.log_call("Call 1", contact_id="contact_1")
        manager.log_call("Call 2", contact_id="contact_1")
        manager.add_note("Note 1", "Test note", contact_id="contact_1")

        timeline = manager.get_timeline(contact_id="contact_1")
        assert len(timeline) == 3


class TestTasks:
    """Test task management."""

    def test_create_task(self):
        manager = TaskManager()
        task = Task(
            id="task_1",
            title="Follow up with customer",
            priority=TaskPriority.HIGH,
            due_date=datetime.now() + timedelta(days=3),
        )
        created = manager.create_task(task)
        assert created.title == "Follow up with customer"

    def test_complete_task(self):
        manager = TaskManager()
        task = Task(
            id="task_1",
            title="Test task",
        )
        manager.create_task(task)
        manager.complete_task("task_1")

        completed = manager.get_task("task_1")
        assert completed.status == TaskStatus.COMPLETED
        assert completed.progress == 100

    def test_get_overdue_tasks(self):
        manager = TaskManager()
        overdue_task = Task(
            id="task_1",
            title="Overdue",
            due_date=datetime.now() - timedelta(days=1),
        )
        manager.create_task(overdue_task)

        overdue = manager.get_overdue_tasks()
        assert len(overdue) == 1


class TestEmailIntegration:
    """Test email integration."""

    def test_create_template(self):
        manager = EmailIntegrationManager()
        template = EmailTemplate(
            id="template_1",
            name="Welcome Email",
            template_type=EmailTemplateType.COLD_OUTREACH,
            subject="Welcome {{first_name}}!",
            body="Hi {{first_name}}, welcome to {{company_name}}!",
        )
        created = manager.create_template(template)

        assert "first_name" in created.variables
        assert "company_name" in created.variables

    def test_render_template(self):
        manager = EmailIntegrationManager()
        template = EmailTemplate(
            id="template_1",
            name="Test",
            template_type=EmailTemplateType.CUSTOM,
            subject="Hi {{name}}",
            body="Hello {{name}}, from {{company}}",
        )

        rendered = template.render({
            "name": "John",
            "company": "Acme Corp",
        })

        assert rendered['subject'] == "Hi John"
        assert rendered['body'] == "Hello John, from Acme Corp"

    def test_track_email(self):
        manager = EmailIntegrationManager()
        template = EmailTemplate(
            id="template_1",
            name="Test",
            template_type=EmailTemplateType.CUSTOM,
            subject="Test",
            body="Test",
        )
        manager.create_template(template)

        tracking = manager.track_email_sent(
            email_id="email_1",
            contact_id="contact_1",
            subject="Test email",
            template_id="template_1",
        )

        assert tracking.email_id == "email_1"

        # Track open
        manager.track_email_opened("email_1")
        updated = manager.tracking["email_1"]
        assert updated.opened is True


class TestAutomation:
    """Test automation engine."""

    def test_create_workflow(self):
        engine = AutomationEngine()
        workflow = Workflow(
            id="workflow_1",
            name="Welcome Workflow",
            trigger_type=TriggerType.CONTACT_CREATED,
            status=WorkflowStatus.ACTIVE,
        )
        created = engine.create_workflow(workflow)
        assert created.name == "Welcome Workflow"

    def test_lead_scoring(self):
        engine = AutomationEngine()

        rule = LeadScoringRule(
            id="rule_1",
            name="Email Engagement",
            field="email_opens",
            operator=ConditionOperator.GREATER_THAN,
            value=5,
            score_change=20,
        )
        engine.create_scoring_rule(rule)

        score = engine.calculate_lead_score({
            "email_opens": 10,
        })

        assert score == 20


class TestAIInsights:
    """Test AI insights engine."""

    def test_prioritize_leads(self):
        from .contacts import ContactManager, Contact

        contact_mgr = ContactManager()
        contact = Contact(
            id="contact_1",
            first_name="John",
            last_name="Doe",
            email="john@example.com",
            lead_score=80,
            email_opens=10,
        )
        contact_mgr.create_contact(contact)

        ai = AIInsightsEngine(contact_manager=contact_mgr)
        leads = ai.prioritize_leads()

        assert len(leads) > 0
        assert leads[0]['contact_id'] == "contact_1"

    def test_predict_win_probability(self):
        from .deals import DealManager, Deal

        deal_mgr = DealManager()
        deal = Deal(
            id="deal_1",
            name="Test Deal",
            amount=10000,
            stage=DealStage.PROPOSAL,
        )
        deal_mgr.create_deal(deal)

        ai = AIInsightsEngine(deal_manager=deal_mgr)
        prediction = ai.predict_win_probability("deal_1")

        assert 'predicted_probability' in prediction
        assert 0 <= prediction['predicted_probability'] <= 100


def run_all_tests():
    """Run all tests."""
    pytest.main([__file__, "-v"])


if __name__ == "__main__":
    run_all_tests()
