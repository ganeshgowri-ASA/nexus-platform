"""
NEXUS HR - Onboarding Module
New hire onboarding workflows, tasks, and document collection.
"""

from dataclasses import dataclass, field
from datetime import datetime, date
from typing import List, Dict, Optional
from enum import Enum


class OnboardingStatus(Enum):
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    OVERDUE = "overdue"


class TaskStatus(Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    SKIPPED = "skipped"


@dataclass
class OnboardingTask:
    """Onboarding task"""
    id: str
    title: str
    description: str
    task_type: str  # "form", "document", "meeting", "training", "system_access"

    # Assignment
    assigned_to: str  # "employee", "hr", "manager", "it"
    due_days: int = 0  # days from start date

    # Status
    status: TaskStatus = TaskStatus.PENDING
    completed_at: Optional[datetime] = None

    # Content
    form_url: str = ""
    document_template: str = ""
    instructions: str = ""


@dataclass
class OnboardingWorkflow:
    """Onboarding workflow template"""
    id: str
    name: str
    description: str

    # Tasks
    tasks: List[OnboardingTask] = field(default_factory=list)

    # Settings
    duration_days: int = 30
    is_active: bool = True
    department: Optional[str] = None


@dataclass
class EmployeeOnboarding:
    """Employee onboarding instance"""
    id: str
    employee_id: str
    workflow_id: str

    # Dates
    start_date: date
    target_completion_date: date
    actual_completion_date: Optional[date] = None

    # Progress
    status: OnboardingStatus = OnboardingStatus.NOT_STARTED
    tasks_completed: int = 0
    tasks_total: int = 0
    completion_percentage: float = 0.0

    # Task instances
    task_statuses: Dict[str, TaskStatus] = field(default_factory=dict)

    # Metadata
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)


class OnboardingManager:
    """Onboarding management"""

    def __init__(self):
        self.workflows: Dict[str, OnboardingWorkflow] = {}
        self.onboardings: Dict[str, EmployeeOnboarding] = {}

    def create_workflow(
        self,
        name: str,
        description: str,
        **kwargs
    ) -> OnboardingWorkflow:
        """Create onboarding workflow"""
        import uuid
        workflow = OnboardingWorkflow(
            id=str(uuid.uuid4()),
            name=name,
            description=description,
            **kwargs
        )
        self.workflows[workflow.id] = workflow
        return workflow

    def add_task_to_workflow(
        self,
        workflow_id: str,
        title: str,
        description: str,
        task_type: str,
        assigned_to: str,
        **kwargs
    ) -> Optional[OnboardingTask]:
        """Add task to workflow"""
        workflow = self.workflows.get(workflow_id)
        if not workflow:
            return None

        import uuid
        task = OnboardingTask(
            id=str(uuid.uuid4()),
            title=title,
            description=description,
            task_type=task_type,
            assigned_to=assigned_to,
            **kwargs
        )

        workflow.tasks.append(task)
        return task

    def start_onboarding(
        self,
        employee_id: str,
        workflow_id: str,
        start_date: date
    ) -> Optional[EmployeeOnboarding]:
        """Start onboarding for employee"""
        workflow = self.workflows.get(workflow_id)
        if not workflow:
            return None

        from datetime import timedelta
        target_completion = start_date + timedelta(days=workflow.duration_days)

        import uuid
        onboarding = EmployeeOnboarding(
            id=str(uuid.uuid4()),
            employee_id=employee_id,
            workflow_id=workflow_id,
            start_date=start_date,
            target_completion_date=target_completion,
            status=OnboardingStatus.IN_PROGRESS,
            tasks_total=len(workflow.tasks)
        )

        # Initialize task statuses
        for task in workflow.tasks:
            onboarding.task_statuses[task.id] = TaskStatus.PENDING

        self.onboardings[onboarding.id] = onboarding
        return onboarding

    def complete_task(
        self,
        onboarding_id: str,
        task_id: str
    ) -> bool:
        """Mark task as completed"""
        onboarding = self.onboardings.get(onboarding_id)
        if not onboarding or task_id not in onboarding.task_statuses:
            return False

        if onboarding.task_statuses[task_id] != TaskStatus.COMPLETED:
            onboarding.task_statuses[task_id] = TaskStatus.COMPLETED
            onboarding.tasks_completed += 1

            # Update completion percentage
            onboarding.completion_percentage = (
                (onboarding.tasks_completed / onboarding.tasks_total * 100)
                if onboarding.tasks_total > 0 else 0
            )

            # Check if fully completed
            if onboarding.tasks_completed >= onboarding.tasks_total:
                onboarding.status = OnboardingStatus.COMPLETED
                onboarding.actual_completion_date = date.today()

            onboarding.updated_at = datetime.now()

        return True

    def get_employee_onboarding(self, employee_id: str) -> Optional[EmployeeOnboarding]:
        """Get onboarding for employee"""
        for onboarding in self.onboardings.values():
            if onboarding.employee_id == employee_id:
                return onboarding
        return None

    def get_pending_tasks(self, employee_id: str) -> List[Dict]:
        """Get pending tasks for employee"""
        onboarding = self.get_employee_onboarding(employee_id)
        if not onboarding:
            return []

        workflow = self.workflows.get(onboarding.workflow_id)
        if not workflow:
            return []

        pending = []
        for task in workflow.tasks:
            if onboarding.task_statuses.get(task.id) == TaskStatus.PENDING:
                pending.append({
                    "task": task,
                    "onboarding_id": onboarding.id
                })

        return pending


if __name__ == "__main__":
    manager = OnboardingManager()

    workflow = manager.create_workflow(
        "Engineering Onboarding",
        "Standard onboarding for engineering team",
        duration_days=30,
        department="Engineering"
    )

    manager.add_task_to_workflow(
        workflow.id,
        "Complete I-9 Form",
        "Fill out employment eligibility verification",
        "form",
        "employee",
        due_days=1
    )

    manager.add_task_to_workflow(
        workflow.id,
        "Setup Development Environment",
        "Install required software and tools",
        "system_access",
        "employee",
        due_days=3
    )

    onboarding = manager.start_onboarding(
        "employee_001",
        workflow.id,
        date.today()
    )

    # Complete first task
    task_id = workflow.tasks[0].id
    manager.complete_task(onboarding.id, task_id)

    print(f"Onboarding: {onboarding.completion_percentage:.1f}% complete")
    print(f"Pending tasks: {len(manager.get_pending_tasks('employee_001'))}")
