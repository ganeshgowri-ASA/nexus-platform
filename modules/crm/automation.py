"""
CRM Automation Module - Workflows, triggers, actions, and lead scoring.
"""

from typing import Dict, List, Optional, Any, Callable, Set
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
import json


class TriggerType(Enum):
    """Workflow trigger types."""
    CONTACT_CREATED = "contact_created"
    CONTACT_UPDATED = "contact_updated"
    DEAL_CREATED = "deal_created"
    DEAL_STAGE_CHANGED = "deal_stage_changed"
    DEAL_WON = "deal_won"
    DEAL_LOST = "deal_lost"
    EMAIL_OPENED = "email_opened"
    EMAIL_CLICKED = "email_clicked"
    EMAIL_REPLIED = "email_replied"
    TASK_COMPLETED = "task_completed"
    ACTIVITY_LOGGED = "activity_logged"
    FORM_SUBMITTED = "form_submitted"
    FIELD_VALUE_CHANGED = "field_value_changed"
    TIME_BASED = "time_based"


class ActionType(Enum):
    """Workflow action types."""
    SEND_EMAIL = "send_email"
    CREATE_TASK = "create_task"
    UPDATE_FIELD = "update_field"
    ADD_TAG = "add_tag"
    REMOVE_TAG = "remove_tag"
    CHANGE_OWNER = "change_owner"
    ADD_TO_SEQUENCE = "add_to_sequence"
    REMOVE_FROM_SEQUENCE = "remove_from_sequence"
    CREATE_DEAL = "create_deal"
    UPDATE_DEAL_STAGE = "update_deal_stage"
    SEND_NOTIFICATION = "send_notification"
    WEBHOOK = "webhook"
    UPDATE_SCORE = "update_score"


class ConditionOperator(Enum):
    """Condition operators."""
    EQUALS = "equals"
    NOT_EQUALS = "not_equals"
    CONTAINS = "contains"
    NOT_CONTAINS = "not_contains"
    GREATER_THAN = "greater_than"
    LESS_THAN = "less_than"
    IS_EMPTY = "is_empty"
    IS_NOT_EMPTY = "is_not_empty"
    IN_LIST = "in_list"
    NOT_IN_LIST = "not_in_list"


class WorkflowStatus(Enum):
    """Workflow status."""
    DRAFT = "draft"
    ACTIVE = "active"
    PAUSED = "paused"
    ARCHIVED = "archived"


@dataclass
class Condition:
    """Workflow condition."""
    field: str
    operator: ConditionOperator
    value: Any

    def evaluate(self, data: Dict[str, Any]) -> bool:
        """Evaluate condition against data."""
        field_value = data.get(self.field)

        if self.operator == ConditionOperator.EQUALS:
            return field_value == self.value
        elif self.operator == ConditionOperator.NOT_EQUALS:
            return field_value != self.value
        elif self.operator == ConditionOperator.CONTAINS:
            return self.value in str(field_value) if field_value else False
        elif self.operator == ConditionOperator.NOT_CONTAINS:
            return self.value not in str(field_value) if field_value else True
        elif self.operator == ConditionOperator.GREATER_THAN:
            try:
                return float(field_value) > float(self.value)
            except (ValueError, TypeError):
                return False
        elif self.operator == ConditionOperator.LESS_THAN:
            try:
                return float(field_value) < float(self.value)
            except (ValueError, TypeError):
                return False
        elif self.operator == ConditionOperator.IS_EMPTY:
            return not field_value
        elif self.operator == ConditionOperator.IS_NOT_EMPTY:
            return bool(field_value)
        elif self.operator == ConditionOperator.IN_LIST:
            return field_value in self.value
        elif self.operator == ConditionOperator.NOT_IN_LIST:
            return field_value not in self.value

        return False

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'field': self.field,
            'operator': self.operator.value,
            'value': self.value,
        }


@dataclass
class WorkflowAction:
    """Workflow action definition."""
    action_type: ActionType
    parameters: Dict[str, Any] = field(default_factory=dict)
    delay_minutes: int = 0  # Delay before executing

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'action_type': self.action_type.value,
            'parameters': self.parameters,
            'delay_minutes': self.delay_minutes,
        }


@dataclass
class Workflow:
    """Workflow automation definition."""
    id: str
    name: str
    description: Optional[str] = None
    status: WorkflowStatus = WorkflowStatus.DRAFT

    # Trigger configuration
    trigger_type: TriggerType = TriggerType.CONTACT_CREATED
    trigger_conditions: List[Condition] = field(default_factory=list)

    # Actions to execute
    actions: List[WorkflowAction] = field(default_factory=list)

    # Execution settings
    run_once_per_contact: bool = True
    re_enrollment_delay_days: Optional[int] = None

    # Metadata
    created_by: Optional[str] = None
    tags: Set[str] = field(default_factory=set)

    # Statistics
    times_triggered: int = 0
    times_executed: int = 0
    last_triggered: Optional[datetime] = None

    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'status': self.status.value,
            'trigger_type': self.trigger_type.value,
            'trigger_conditions': [c.to_dict() for c in self.trigger_conditions],
            'actions': [a.to_dict() for a in self.actions],
            'run_once_per_contact': self.run_once_per_contact,
            're_enrollment_delay_days': self.re_enrollment_delay_days,
            'created_by': self.created_by,
            'tags': list(self.tags),
            'times_triggered': self.times_triggered,
            'times_executed': self.times_executed,
            'last_triggered': self.last_triggered.isoformat() if self.last_triggered else None,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
        }


@dataclass
class WorkflowExecution:
    """Record of a workflow execution."""
    id: str
    workflow_id: str
    trigger_data: Dict[str, Any]
    executed_at: datetime = field(default_factory=datetime.now)
    success: bool = True
    error_message: Optional[str] = None
    actions_executed: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'id': self.id,
            'workflow_id': self.workflow_id,
            'trigger_data': self.trigger_data,
            'executed_at': self.executed_at.isoformat(),
            'success': self.success,
            'error_message': self.error_message,
            'actions_executed': self.actions_executed,
        }


@dataclass
class LeadScoringRule:
    """Lead scoring rule."""
    id: str
    name: str
    description: Optional[str] = None

    # Criteria
    field: str
    operator: ConditionOperator
    value: Any

    # Score adjustment
    score_change: int  # Positive or negative

    is_active: bool = True
    created_at: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'field': self.field,
            'operator': self.operator.value,
            'value': self.value,
            'score_change': self.score_change,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat(),
        }


class AutomationEngine:
    """CRM automation engine for workflows and lead scoring."""

    def __init__(self):
        """Initialize automation engine."""
        self.workflows: Dict[str, Workflow] = {}
        self.executions: List[WorkflowExecution] = []
        self.scoring_rules: Dict[str, LeadScoringRule] = {}

        # Track enrollment to prevent duplicates
        self._enrollments: Dict[str, Set[str]] = {}  # workflow_id -> {entity_ids}
        self._last_enrollment: Dict[str, Dict[str, datetime]] = {}  # workflow_id -> entity_id -> timestamp

        # Action handlers (can be registered externally)
        self._action_handlers: Dict[ActionType, Callable] = {}

    # Workflow Management

    def create_workflow(self, workflow: Workflow) -> Workflow:
        """Create a new workflow."""
        self.workflows[workflow.id] = workflow
        self._enrollments[workflow.id] = set()
        self._last_enrollment[workflow.id] = {}
        return workflow

    def get_workflow(self, workflow_id: str) -> Optional[Workflow]:
        """Get a workflow by ID."""
        return self.workflows.get(workflow_id)

    def update_workflow(self, workflow_id: str, updates: Dict[str, Any]) -> Optional[Workflow]:
        """Update a workflow."""
        workflow = self.workflows.get(workflow_id)
        if not workflow:
            return None

        for key, value in updates.items():
            if hasattr(workflow, key):
                if key == 'status' and isinstance(value, str):
                    value = WorkflowStatus(value)
                elif key == 'trigger_type' and isinstance(value, str):
                    value = TriggerType(value)
                setattr(workflow, key, value)

        workflow.updated_at = datetime.now()
        return workflow

    def delete_workflow(self, workflow_id: str) -> bool:
        """Delete a workflow."""
        if workflow_id in self.workflows:
            del self.workflows[workflow_id]
            if workflow_id in self._enrollments:
                del self._enrollments[workflow_id]
            if workflow_id in self._last_enrollment:
                del self._last_enrollment[workflow_id]
            return True
        return False

    def list_workflows(self, status: Optional[WorkflowStatus] = None) -> List[Workflow]:
        """List workflows."""
        workflows = list(self.workflows.values())

        if status:
            workflows = [w for w in workflows if w.status == status]

        return sorted(workflows, key=lambda w: w.created_at, reverse=True)

    def add_action(
        self,
        workflow_id: str,
        action_type: ActionType,
        parameters: Dict[str, Any],
        delay_minutes: int = 0
    ) -> Optional[Workflow]:
        """Add an action to a workflow."""
        workflow = self.workflows.get(workflow_id)
        if not workflow:
            return None

        action = WorkflowAction(
            action_type=action_type,
            parameters=parameters,
            delay_minutes=delay_minutes,
        )
        workflow.actions.append(action)
        workflow.updated_at = datetime.now()
        return workflow

    def add_condition(
        self,
        workflow_id: str,
        field: str,
        operator: ConditionOperator,
        value: Any
    ) -> Optional[Workflow]:
        """Add a condition to a workflow."""
        workflow = self.workflows.get(workflow_id)
        if not workflow:
            return None

        condition = Condition(field=field, operator=operator, value=value)
        workflow.trigger_conditions.append(condition)
        workflow.updated_at = datetime.now()
        return workflow

    # Workflow Execution

    def trigger_workflow(
        self,
        trigger_type: TriggerType,
        data: Dict[str, Any],
        entity_id: Optional[str] = None
    ) -> List[WorkflowExecution]:
        """Trigger workflows matching the trigger type."""
        executions = []

        # Find matching workflows
        matching_workflows = [
            w for w in self.workflows.values()
            if w.status == WorkflowStatus.ACTIVE and w.trigger_type == trigger_type
        ]

        for workflow in matching_workflows:
            # Check if entity can be enrolled
            if entity_id and not self._can_enroll(workflow, entity_id):
                continue

            # Check conditions
            if workflow.trigger_conditions:
                all_conditions_met = all(
                    condition.evaluate(data) for condition in workflow.trigger_conditions
                )
                if not all_conditions_met:
                    continue

            # Execute workflow
            execution = self._execute_workflow(workflow, data, entity_id)
            if execution:
                executions.append(execution)

        return executions

    def _can_enroll(self, workflow: Workflow, entity_id: str) -> bool:
        """Check if an entity can be enrolled in a workflow."""
        if not workflow.run_once_per_contact:
            return True

        # Check if already enrolled
        if entity_id in self._enrollments.get(workflow.id, set()):
            # Check re-enrollment delay
            if workflow.re_enrollment_delay_days:
                last_enrollment = self._last_enrollment.get(workflow.id, {}).get(entity_id)
                if last_enrollment:
                    days_since = (datetime.now() - last_enrollment).days
                    if days_since < workflow.re_enrollment_delay_days:
                        return False
                    # Can re-enroll
                    return True
            else:
                # Cannot re-enroll
                return False

        return True

    def _execute_workflow(
        self,
        workflow: Workflow,
        data: Dict[str, Any],
        entity_id: Optional[str] = None
    ) -> Optional[WorkflowExecution]:
        """Execute a workflow."""
        execution_id = self._generate_id("execution")
        actions_executed = []
        success = True
        error_message = None

        try:
            # Execute each action
            for action in workflow.actions:
                # Apply delay if specified
                if action.delay_minutes > 0:
                    # In a real system, this would schedule the action for later
                    # For now, we'll note it in the execution log
                    pass

                # Execute action
                result = self._execute_action(action, data)
                if result:
                    actions_executed.append(action.action_type.value)

            # Mark as enrolled
            if entity_id:
                if workflow.id not in self._enrollments:
                    self._enrollments[workflow.id] = set()
                self._enrollments[workflow.id].add(entity_id)

                if workflow.id not in self._last_enrollment:
                    self._last_enrollment[workflow.id] = {}
                self._last_enrollment[workflow.id][entity_id] = datetime.now()

            # Update workflow stats
            workflow.times_triggered += 1
            workflow.times_executed += 1
            workflow.last_triggered = datetime.now()

        except Exception as e:
            success = False
            error_message = str(e)

        # Create execution record
        execution = WorkflowExecution(
            id=execution_id,
            workflow_id=workflow.id,
            trigger_data=data,
            success=success,
            error_message=error_message,
            actions_executed=actions_executed,
        )
        self.executions.append(execution)

        return execution

    def _execute_action(self, action: WorkflowAction, data: Dict[str, Any]) -> bool:
        """Execute a single workflow action."""
        # Check if there's a registered handler
        handler = self._action_handlers.get(action.action_type)
        if handler:
            return handler(action, data)

        # Default behavior for common actions
        # In a real system, these would integrate with other managers
        return True

    def register_action_handler(self, action_type: ActionType, handler: Callable) -> None:
        """Register a custom action handler."""
        self._action_handlers[action_type] = handler

    def get_execution_history(
        self,
        workflow_id: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Get workflow execution history."""
        executions = self.executions

        if workflow_id:
            executions = [e for e in executions if e.workflow_id == workflow_id]

        # Sort by executed_at descending
        executions = sorted(executions, key=lambda e: e.executed_at, reverse=True)

        # Apply limit
        executions = executions[:limit]

        return [e.to_dict() for e in executions]

    # Lead Scoring

    def create_scoring_rule(self, rule: LeadScoringRule) -> LeadScoringRule:
        """Create a lead scoring rule."""
        self.scoring_rules[rule.id] = rule
        return rule

    def get_scoring_rule(self, rule_id: str) -> Optional[LeadScoringRule]:
        """Get a scoring rule by ID."""
        return self.scoring_rules.get(rule_id)

    def update_scoring_rule(self, rule_id: str, updates: Dict[str, Any]) -> Optional[LeadScoringRule]:
        """Update a scoring rule."""
        rule = self.scoring_rules.get(rule_id)
        if not rule:
            return None

        for key, value in updates.items():
            if hasattr(rule, key):
                if key == 'operator' and isinstance(value, str):
                    value = ConditionOperator(value)
                setattr(rule, key, value)

        return rule

    def delete_scoring_rule(self, rule_id: str) -> bool:
        """Delete a scoring rule."""
        if rule_id in self.scoring_rules:
            del self.scoring_rules[rule_id]
            return True
        return False

    def list_scoring_rules(self, active_only: bool = True) -> List[LeadScoringRule]:
        """List scoring rules."""
        rules = list(self.scoring_rules.values())

        if active_only:
            rules = [r for r in rules if r.is_active]

        return rules

    def calculate_lead_score(self, contact_data: Dict[str, Any]) -> int:
        """Calculate lead score based on active rules."""
        score = 0

        active_rules = [r for r in self.scoring_rules.values() if r.is_active]

        for rule in active_rules:
            condition = Condition(
                field=rule.field,
                operator=rule.operator,
                value=rule.value
            )

            if condition.evaluate(contact_data):
                score += rule.score_change

        # Ensure score is between 0 and 100
        return max(0, min(100, score))

    def score_contact(self, contact_data: Dict[str, Any]) -> Dict[str, Any]:
        """Score a contact and return details."""
        score = self.calculate_lead_score(contact_data)

        # Determine qualification
        if score >= 80:
            qualification = "Hot"
        elif score >= 60:
            qualification = "Warm"
        elif score >= 40:
            qualification = "Cold"
        else:
            qualification = "Unqualified"

        # Find matching rules
        matched_rules = []
        for rule in self.scoring_rules.values():
            if not rule.is_active:
                continue

            condition = Condition(
                field=rule.field,
                operator=rule.operator,
                value=rule.value
            )

            if condition.evaluate(contact_data):
                matched_rules.append({
                    'rule_name': rule.name,
                    'score_change': rule.score_change,
                })

        return {
            'score': score,
            'qualification': qualification,
            'matched_rules': matched_rules,
        }

    # Statistics

    def get_workflow_statistics(self) -> Dict[str, Any]:
        """Get workflow automation statistics."""
        total_workflows = len(self.workflows)
        active_workflows = len([w for w in self.workflows.values() if w.status == WorkflowStatus.ACTIVE])

        total_executions = len(self.executions)
        successful_executions = len([e for e in self.executions if e.success])
        failed_executions = total_executions - successful_executions

        return {
            'total_workflows': total_workflows,
            'active_workflows': active_workflows,
            'total_executions': total_executions,
            'successful_executions': successful_executions,
            'failed_executions': failed_executions,
            'success_rate': round((successful_executions / total_executions * 100) if total_executions > 0 else 0, 2),
            'total_scoring_rules': len(self.scoring_rules),
        }

    def _generate_id(self, prefix: str) -> str:
        """Generate a unique ID."""
        import uuid
        return f"{prefix}_{uuid.uuid4().hex[:12]}"
