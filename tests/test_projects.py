"""
Unit tests for NEXUS Project Management Module
Comprehensive test coverage for all project management features.
"""

import unittest
from datetime import date, datetime, timedelta
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from modules.projects import (
    ProjectManager, Project, ProjectStatus, ProjectPriority,
    TaskManager, Task, TaskStatus, TaskPriority,
    DependencyManager, DependencyType,
    KanbanManager,
    ResourceManager,
    MilestoneManager,
    TimeTrackingManager,
    BudgetManager, ExpenseCategory, ExpenseStatus,
    CollaborationManager, ActivityType,
    AIProjectAssistant,
    create_project_management_system
)


class TestProjectManager(unittest.TestCase):
    """Test cases for ProjectManager."""

    def setUp(self):
        """Set up test fixtures."""
        self.pm = ProjectManager()

    def test_create_project(self):
        """Test project creation."""
        project = self.pm.create_project(
            name="Test Project",
            description="A test project",
            status=ProjectStatus.PLANNING
        )

        self.assertIsNotNone(project)
        self.assertEqual(project.name, "Test Project")
        self.assertEqual(project.status, ProjectStatus.PLANNING)
        self.assertIn(project.id, self.pm.projects)

    def test_get_project(self):
        """Test retrieving a project."""
        project = self.pm.create_project(name="Test Project")
        retrieved = self.pm.get_project(project.id)

        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved.id, project.id)

    def test_update_project(self):
        """Test updating a project."""
        project = self.pm.create_project(name="Test Project")
        updated = self.pm.update_project(project.id, name="Updated Project")

        self.assertIsNotNone(updated)
        self.assertEqual(updated.name, "Updated Project")

    def test_delete_project(self):
        """Test deleting a project."""
        project = self.pm.create_project(name="Test Project")
        result = self.pm.delete_project(project.id)

        self.assertTrue(result)
        self.assertNotIn(project.id, self.pm.projects)

    def test_list_projects(self):
        """Test listing projects."""
        self.pm.create_project(name="Project 1", status=ProjectStatus.ACTIVE)
        self.pm.create_project(name="Project 2", status=ProjectStatus.COMPLETED)

        all_projects = self.pm.list_projects()
        self.assertEqual(len(all_projects), 2)

        active_projects = self.pm.list_projects(status=ProjectStatus.ACTIVE)
        self.assertEqual(len(active_projects), 1)

    def test_create_portfolio(self):
        """Test creating a portfolio."""
        p1 = self.pm.create_project(name="Project 1")
        p2 = self.pm.create_project(name="Project 2")

        self.pm.create_portfolio("Test Portfolio", [p1.id, p2.id])

        self.assertIn("Test Portfolio", self.pm.portfolios)
        self.assertEqual(len(self.pm.portfolios["Test Portfolio"]), 2)


class TestTaskManager(unittest.TestCase):
    """Test cases for TaskManager."""

    def setUp(self):
        """Set up test fixtures."""
        self.pm = ProjectManager()
        self.tm = TaskManager()
        self.project = self.pm.create_project(name="Test Project")

    def test_create_task(self):
        """Test task creation."""
        task = self.tm.create_task(
            project_id=self.project.id,
            name="Test Task",
            description="A test task",
            priority=TaskPriority.HIGH
        )

        self.assertIsNotNone(task)
        self.assertEqual(task.name, "Test Task")
        self.assertEqual(task.priority, TaskPriority.HIGH)
        self.assertIn(task.id, self.tm.tasks)

    def test_get_task(self):
        """Test retrieving a task."""
        task = self.tm.create_task(
            project_id=self.project.id,
            name="Test Task"
        )
        retrieved = self.tm.get_task(task.id)

        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved.id, task.id)

    def test_update_task(self):
        """Test updating a task."""
        task = self.tm.create_task(
            project_id=self.project.id,
            name="Test Task"
        )
        updated = self.tm.update_task(task.id, status=TaskStatus.DONE)

        self.assertIsNotNone(updated)
        self.assertEqual(updated.status, TaskStatus.DONE)
        self.assertIsNotNone(updated.completed_at)

    def test_delete_task(self):
        """Test deleting a task."""
        task = self.tm.create_task(
            project_id=self.project.id,
            name="Test Task"
        )
        result = self.tm.delete_task(task.id)

        self.assertTrue(result)
        self.assertNotIn(task.id, self.tm.tasks)

    def test_get_tasks_by_project(self):
        """Test getting tasks by project."""
        self.tm.create_task(project_id=self.project.id, name="Task 1")
        self.tm.create_task(project_id=self.project.id, name="Task 2")

        tasks = self.tm.get_tasks_by_project(self.project.id)
        self.assertEqual(len(tasks), 2)

    def test_filter_tasks(self):
        """Test filtering tasks."""
        self.tm.create_task(
            project_id=self.project.id,
            name="Task 1",
            status=TaskStatus.TODO,
            priority=TaskPriority.HIGH
        )
        self.tm.create_task(
            project_id=self.project.id,
            name="Task 2",
            status=TaskStatus.DONE,
            priority=TaskPriority.LOW
        )

        high_priority = self.tm.filter_tasks(
            project_id=self.project.id,
            priority=TaskPriority.HIGH
        )
        self.assertEqual(len(high_priority), 1)

        done_tasks = self.tm.filter_tasks(
            project_id=self.project.id,
            status=TaskStatus.DONE
        )
        self.assertEqual(len(done_tasks), 1)

    def test_overdue_tasks(self):
        """Test getting overdue tasks."""
        past_date = date.today() - timedelta(days=5)

        self.tm.create_task(
            project_id=self.project.id,
            name="Overdue Task",
            due_date=past_date,
            status=TaskStatus.TODO
        )

        overdue = self.tm.get_overdue_tasks(self.project.id)
        self.assertEqual(len(overdue), 1)


class TestDependencyManager(unittest.TestCase):
    """Test cases for DependencyManager."""

    def setUp(self):
        """Set up test fixtures."""
        self.pm = ProjectManager()
        self.tm = TaskManager()
        self.dm = DependencyManager(self.tm)
        self.project = self.pm.create_project(name="Test Project")

        self.task1 = self.tm.create_task(
            project_id=self.project.id,
            name="Task 1"
        )
        self.task2 = self.tm.create_task(
            project_id=self.project.id,
            name="Task 2"
        )

    def test_add_dependency(self):
        """Test adding a dependency."""
        dep = self.dm.add_dependency(
            predecessor_id=self.task1.id,
            successor_id=self.task2.id,
            dependency_type=DependencyType.FINISH_TO_START
        )

        self.assertIsNotNone(dep)
        self.assertEqual(dep.predecessor_id, self.task1.id)
        self.assertEqual(dep.successor_id, self.task2.id)

    def test_cycle_detection(self):
        """Test cycle detection in dependencies."""
        self.dm.add_dependency(self.task1.id, self.task2.id)

        # This should raise an error due to cycle
        with self.assertRaises(ValueError):
            self.dm.add_dependency(self.task2.id, self.task1.id)

    def test_get_dependencies(self):
        """Test getting task dependencies."""
        self.dm.add_dependency(self.task1.id, self.task2.id)

        deps = self.dm.get_dependencies(self.task2.id)
        self.assertEqual(len(deps), 1)
        self.assertEqual(deps[0].predecessor_id, self.task1.id)

    def test_get_dependents(self):
        """Test getting dependent tasks."""
        self.dm.add_dependency(self.task1.id, self.task2.id)

        dependents = self.dm.get_dependents(self.task1.id)
        self.assertEqual(len(dependents), 1)
        self.assertEqual(dependents[0].successor_id, self.task2.id)

    def test_remove_dependency(self):
        """Test removing a dependency."""
        self.dm.add_dependency(self.task1.id, self.task2.id)
        result = self.dm.remove_dependency(self.task1.id, self.task2.id)

        self.assertTrue(result)
        deps = self.dm.get_dependencies(self.task2.id)
        self.assertEqual(len(deps), 0)


class TestResourceManager(unittest.TestCase):
    """Test cases for ResourceManager."""

    def setUp(self):
        """Set up test fixtures."""
        self.tm = TaskManager()
        self.rm = ResourceManager(self.tm)

    def test_add_resource(self):
        """Test adding a resource."""
        resource = self.rm.add_resource(
            name="John Doe",
            email="john@example.com",
            role="Developer",
            skills=["Python", "JavaScript"]
        )

        self.assertIsNotNone(resource)
        self.assertEqual(resource.name, "John Doe")
        self.assertIn("Python", resource.skills)

    def test_list_resources(self):
        """Test listing resources."""
        self.rm.add_resource(name="Developer 1", role="Developer")
        self.rm.add_resource(name="Designer 1", role="Designer")

        all_resources = self.rm.list_resources()
        self.assertEqual(len(all_resources), 2)

        developers = self.rm.list_resources(role="Developer")
        self.assertEqual(len(developers), 1)

    def test_allocate_resource(self):
        """Test resource allocation."""
        pm = ProjectManager()
        project = pm.create_project(name="Test Project")
        task = self.tm.create_task(
            project_id=project.id,
            name="Test Task",
            start_date=date.today(),
            due_date=date.today() + timedelta(days=7)
        )
        resource = self.rm.add_resource(name="John Doe")

        allocation = self.rm.allocate_resource(
            resource_id=resource.id,
            task_id=task.id,
            allocated_hours=40.0,
            start_date=date.today(),
            end_date=date.today() + timedelta(days=7)
        )

        self.assertIsNotNone(allocation)
        self.assertEqual(allocation.resource_id, resource.id)
        self.assertEqual(allocation.task_id, task.id)


class TestMilestoneManager(unittest.TestCase):
    """Test cases for MilestoneManager."""

    def setUp(self):
        """Set up test fixtures."""
        self.pm = ProjectManager()
        self.tm = TaskManager()
        self.mm = MilestoneManager(self.tm)
        self.project = self.pm.create_project(name="Test Project")

    def test_create_milestone(self):
        """Test milestone creation."""
        milestone = self.mm.create_milestone(
            project_id=self.project.id,
            name="Release 1.0",
            description="First major release",
            due_date=date.today() + timedelta(days=30)
        )

        self.assertIsNotNone(milestone)
        self.assertEqual(milestone.name, "Release 1.0")

    def test_mark_milestone_completed(self):
        """Test marking milestone as completed."""
        milestone = self.mm.create_milestone(
            project_id=self.project.id,
            name="Release 1.0"
        )

        milestone.mark_completed()

        self.assertTrue(milestone.is_completed)
        self.assertEqual(milestone.progress, 100.0)
        self.assertIsNotNone(milestone.completed_at)

    def test_link_task_to_milestone(self):
        """Test linking a task to a milestone."""
        milestone = self.mm.create_milestone(
            project_id=self.project.id,
            name="Release 1.0"
        )
        task = self.tm.create_task(
            project_id=self.project.id,
            name="Test Task"
        )

        result = self.mm.link_task_to_milestone(milestone.id, task.id)

        self.assertTrue(result)
        self.assertIn(task.id, milestone.linked_tasks)


class TestTimeTrackingManager(unittest.TestCase):
    """Test cases for TimeTrackingManager."""

    def setUp(self):
        """Set up test fixtures."""
        self.pm = ProjectManager()
        self.tm = TaskManager()
        self.ttm = TimeTrackingManager(self.tm)
        self.project = self.pm.create_project(name="Test Project")
        self.task = self.tm.create_task(
            project_id=self.project.id,
            name="Test Task"
        )

    def test_log_time(self):
        """Test logging time."""
        entry = self.ttm.log_time(
            task_id=self.task.id,
            user_id="user1",
            duration_hours=4.0,
            description="Worked on feature"
        )

        self.assertIsNotNone(entry)
        self.assertEqual(entry.duration_hours, 4.0)
        self.assertEqual(self.task.actual_hours, 4.0)

    def test_start_stop_timer(self):
        """Test starting and stopping a timer."""
        timer = self.ttm.start_timer(
            task_id=self.task.id,
            user_id="user1"
        )

        self.assertIsNotNone(timer)
        self.assertEqual(timer.task_id, self.task.id)

        entry = self.ttm.stop_timer("user1")

        self.assertIsNotNone(entry)
        self.assertGreater(entry.duration_hours, 0)


class TestBudgetManager(unittest.TestCase):
    """Test cases for BudgetManager."""

    def setUp(self):
        """Set up test fixtures."""
        self.pm = ProjectManager()
        self.bm = BudgetManager()
        self.project = self.pm.create_project(name="Test Project")

    def test_create_budget(self):
        """Test budget creation."""
        budget = self.bm.create_budget(
            project_id=self.project.id,
            total_budget=100000.0,
            labor_budget=60000.0,
            materials_budget=30000.0
        )

        self.assertIsNotNone(budget)
        self.assertEqual(budget.total_budget, 100000.0)

    def test_add_expense(self):
        """Test adding an expense."""
        expense = self.bm.add_expense(
            project_id=self.project.id,
            category=ExpenseCategory.SOFTWARE,
            amount=500.0,
            description="Software license"
        )

        self.assertIsNotNone(expense)
        self.assertEqual(expense.amount, 500.0)

    def test_budget_utilization(self):
        """Test budget utilization calculation."""
        self.bm.create_budget(
            project_id=self.project.id,
            total_budget=10000.0
        )
        self.bm.add_expense(
            project_id=self.project.id,
            category=ExpenseCategory.MATERIALS,
            amount=5000.0,
            status=ExpenseStatus.APPROVED
        )

        utilization = self.bm.get_budget_utilization(self.project.id)

        self.assertIsNotNone(utilization)
        self.assertEqual(utilization["actual"]["total"], 5000.0)
        self.assertEqual(utilization["utilization_percentage"], 50.0)


class TestCollaborationManager(unittest.TestCase):
    """Test cases for CollaborationManager."""

    def setUp(self):
        """Set up test fixtures."""
        self.cm = CollaborationManager()

    def test_add_comment(self):
        """Test adding a comment."""
        comment = self.cm.add_comment(
            entity_type="task",
            entity_id="task123",
            user_id="user1",
            content="This is a test comment"
        )

        self.assertIsNotNone(comment)
        self.assertEqual(comment.content, "This is a test comment")

    def test_extract_mentions(self):
        """Test extracting mentions from comments."""
        comment = self.cm.add_comment(
            entity_type="task",
            entity_id="task123",
            user_id="user1",
            content="@john @jane please review this"
        )

        self.assertIn("john", comment.mentions)
        self.assertIn("jane", comment.mentions)

    def test_log_activity(self):
        """Test logging an activity."""
        activity = self.cm.log_activity(
            project_id="project123",
            activity_type=ActivityType.TASK_CREATED,
            user_id="user1",
            entity_type="task",
            entity_id="task123",
            title="Task Created"
        )

        self.assertIsNotNone(activity)
        self.assertEqual(activity.activity_type, ActivityType.TASK_CREATED)


class TestAIProjectAssistant(unittest.TestCase):
    """Test cases for AIProjectAssistant."""

    def setUp(self):
        """Set up test fixtures."""
        self.pm = ProjectManager()
        self.tm = TaskManager()
        self.dm = DependencyManager(self.tm)
        self.ai = AIProjectAssistant(
            self.pm,
            self.tm,
            self.dm
        )
        self.project = self.pm.create_project(name="Test Project")

    def test_analyze_project_health(self):
        """Test project health analysis."""
        health = self.ai.analyze_project_health(self.project.id)

        self.assertIsNotNone(health)
        self.assertIn("health_score", health)
        self.assertIn("status", health)

    def test_detect_risks(self):
        """Test risk detection."""
        # Create an overdue task
        past_date = date.today() - timedelta(days=5)
        self.tm.create_task(
            project_id=self.project.id,
            name="Overdue Task",
            due_date=past_date,
            status=TaskStatus.TODO
        )

        risks = self.ai.detect_risks(self.project.id)

        self.assertGreater(len(risks), 0)
        self.assertEqual(risks[0].type, "deadline_risk")

    def test_suggest_task_priorities(self):
        """Test task priority suggestions."""
        self.tm.create_task(
            project_id=self.project.id,
            name="Task 1",
            priority=TaskPriority.MEDIUM,
            due_date=date.today() + timedelta(days=2)
        )

        suggestions = self.ai.suggest_task_priorities(self.project.id)

        self.assertGreater(len(suggestions), 0)
        self.assertIn("priority_score", suggestions[0])


class TestIntegration(unittest.TestCase):
    """Integration tests for the complete system."""

    def test_create_project_management_system(self):
        """Test creating the complete project management system."""
        system = create_project_management_system()

        self.assertIn("project_manager", system)
        self.assertIn("task_manager", system)
        self.assertIn("dependency_manager", system)
        self.assertIn("ai_assistant", system)

    def test_full_workflow(self):
        """Test a complete project management workflow."""
        # Create system
        system = create_project_management_system()
        pm = system["project_manager"]
        tm = system["task_manager"]
        mm = system["milestone_manager"]

        # Create project
        project = pm.create_project(
            name="Website Redesign",
            description="Complete website overhaul",
            start_date=date.today(),
            end_date=date.today() + timedelta(days=90)
        )

        # Create tasks
        task1 = tm.create_task(
            project_id=project.id,
            name="Design mockups",
            priority=TaskPriority.HIGH,
            estimated_hours=40.0
        )

        task2 = tm.create_task(
            project_id=project.id,
            name="Implement frontend",
            priority=TaskPriority.MEDIUM,
            estimated_hours=80.0
        )

        # Create milestone
        milestone = mm.create_milestone(
            project_id=project.id,
            name="Launch",
            due_date=date.today() + timedelta(days=90)
        )

        mm.link_task_to_milestone(milestone.id, task1.id)
        mm.link_task_to_milestone(milestone.id, task2.id)

        # Verify
        self.assertEqual(len(tm.get_tasks_by_project(project.id)), 2)
        self.assertEqual(len(mm.get_milestones_by_project(project.id)), 1)


if __name__ == "__main__":
    unittest.main()
