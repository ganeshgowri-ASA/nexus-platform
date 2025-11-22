"""
NEXUS AI Project Assistant
AI-powered project insights, recommendations, and automation.
"""

from typing import Dict, List, Optional, Any, Tuple
from datetime import date, datetime, timedelta
from dataclasses import dataclass
import random


@dataclass
class AIInsight:
    """
    AI-generated insight.

    Attributes:
        type: Insight type
        title: Insight title
        description: Insight description
        severity: Severity level (info, warning, critical)
        entity_type: Related entity type
        entity_id: Related entity ID
        recommendations: List of recommendations
        confidence: Confidence score (0-1)
    """
    type: str
    title: str
    description: str
    severity: str = "info"
    entity_type: Optional[str] = None
    entity_id: Optional[str] = None
    recommendations: List[str] = None
    confidence: float = 0.8

    def __post_init__(self):
        if self.recommendations is None:
            self.recommendations = []

    def to_dict(self) -> Dict[str, Any]:
        """Convert insight to dictionary."""
        return {
            "type": self.type,
            "title": self.title,
            "description": self.description,
            "severity": self.severity,
            "entity_type": self.entity_type,
            "entity_id": self.entity_id,
            "recommendations": self.recommendations,
            "confidence": self.confidence
        }


class AIProjectAssistant:
    """
    AI-powered project management assistant.
    Provides insights, predictions, and intelligent recommendations.
    """

    def __init__(
        self,
        project_manager,
        task_manager,
        dependency_manager=None,
        resource_manager=None,
        time_tracking_manager=None,
        budget_manager=None
    ):
        """
        Initialize the AI assistant.

        Args:
            project_manager: Project manager instance
            task_manager: Task manager instance
            dependency_manager: Dependency manager instance (optional)
            resource_manager: Resource manager instance (optional)
            time_tracking_manager: Time tracking manager instance (optional)
            budget_manager: Budget manager instance (optional)
        """
        self.project_manager = project_manager
        self.task_manager = task_manager
        self.dependency_manager = dependency_manager
        self.resource_manager = resource_manager
        self.time_tracking_manager = time_tracking_manager
        self.budget_manager = budget_manager

    def analyze_project_health(self, project_id: str) -> Dict[str, Any]:
        """
        Analyze overall project health.

        Args:
            project_id: Project identifier

        Returns:
            Project health analysis
        """
        project = self.project_manager.get_project(project_id)
        if not project:
            return {"error": "Project not found"}

        tasks = self.task_manager.get_tasks_by_project(project_id)
        task_stats = self.task_manager.get_task_statistics(project_id)

        # Calculate health metrics
        health_score = 100.0
        issues = []

        # Check overdue tasks
        overdue_tasks = self.task_manager.get_overdue_tasks(project_id)
        if overdue_tasks:
            health_score -= min(30, len(overdue_tasks) * 5)
            issues.append(f"{len(overdue_tasks)} overdue tasks")

        # Check blocked tasks
        blocked_count = task_stats["by_status"].get("blocked", 0)
        if blocked_count > 0:
            health_score -= min(20, blocked_count * 5)
            issues.append(f"{blocked_count} blocked tasks")

        # Check resource overallocation
        if self.resource_manager and project.start_date and project.end_date:
            overallocated = self.resource_manager.get_overallocated_resources(
                project.start_date, project.end_date
            )
            if overallocated:
                health_score -= min(20, len(overallocated) * 10)
                issues.append(f"{len(overallocated)} overallocated resources")

        # Check budget
        if self.budget_manager:
            budget_util = self.budget_manager.get_budget_utilization(project_id)
            if not isinstance(budget_util, dict) or "error" not in budget_util:
                if budget_util.get("is_over_budget"):
                    health_score -= 30
                    issues.append("Over budget")
                elif budget_util.get("utilization_percentage", 0) > 90:
                    health_score -= 15
                    issues.append("Near budget limit")

        # Determine health status
        if health_score >= 80:
            status = "healthy"
            color = "green"
        elif health_score >= 60:
            status = "at_risk"
            color = "yellow"
        else:
            status = "critical"
            color = "red"

        return {
            "project_id": project_id,
            "health_score": max(0, health_score),
            "status": status,
            "color": color,
            "issues": issues,
            "task_completion_rate": (
                task_stats["by_status"].get("done", 0) / task_stats["total_tasks"] * 100
                if task_stats["total_tasks"] > 0 else 0
            ),
            "analyzed_at": datetime.now().isoformat()
        }

    def detect_risks(self, project_id: str) -> List[AIInsight]:
        """
        Detect potential project risks.

        Args:
            project_id: Project identifier

        Returns:
            List of detected risks
        """
        risks = []
        tasks = self.task_manager.get_tasks_by_project(project_id)

        # Risk: Overdue tasks
        overdue_tasks = [t for t in tasks if t.is_overdue()]
        if overdue_tasks:
            risks.append(AIInsight(
                type="deadline_risk",
                title="Overdue Tasks Detected",
                description=f"{len(overdue_tasks)} tasks are overdue, which may impact project timeline.",
                severity="warning" if len(overdue_tasks) < 5 else "critical",
                recommendations=[
                    "Review and reprioritize overdue tasks",
                    "Consider reallocating resources",
                    "Update task deadlines if needed"
                ],
                confidence=0.95
            ))

        # Risk: Tasks without assignees
        unassigned = [t for t in tasks if not t.assignee and t.status.value != "done"]
        if unassigned:
            risks.append(AIInsight(
                type="resource_risk",
                title="Unassigned Tasks",
                description=f"{len(unassigned)} tasks have no assignee.",
                severity="warning",
                recommendations=[
                    "Assign tasks to team members",
                    "Use auto-assignment feature",
                    "Review team capacity"
                ],
                confidence=0.9
            ))

        # Risk: Dependency bottlenecks
        if self.dependency_manager:
            for task in tasks:
                dependents = self.dependency_manager.get_dependents(task.id)
                if len(dependents) > 5 and task.status.value not in ["done", "cancelled"]:
                    risks.append(AIInsight(
                        type="dependency_risk",
                        title="Dependency Bottleneck",
                        description=f"Task '{task.name}' is blocking {len(dependents)} other tasks.",
                        severity="warning",
                        entity_type="task",
                        entity_id=task.id,
                        recommendations=[
                            "Prioritize this task",
                            "Add more resources",
                            "Break down into smaller tasks"
                        ],
                        confidence=0.85
                    ))

        # Risk: Budget overrun
        if self.budget_manager:
            budget_util = self.budget_manager.get_budget_utilization(project_id)
            if not isinstance(budget_util, dict) or "error" not in budget_util:
                if budget_util.get("utilization_percentage", 0) > 100:
                    risks.append(AIInsight(
                        type="budget_risk",
                        title="Budget Overrun",
                        description=f"Project is {budget_util.get('utilization_percentage', 0) - 100:.1f}% over budget.",
                        severity="critical",
                        recommendations=[
                            "Review and reduce expenses",
                            "Request additional budget",
                            "Reduce project scope"
                        ],
                        confidence=0.95
                    ))
                elif budget_util.get("utilization_percentage", 0) > 85:
                    risks.append(AIInsight(
                        type="budget_risk",
                        title="Budget Warning",
                        description="Project is approaching budget limit.",
                        severity="warning",
                        recommendations=[
                            "Monitor expenses closely",
                            "Plan for contingency",
                            "Optimize resource allocation"
                        ],
                        confidence=0.8
                    ))

        return risks

    def predict_completion_date(self, project_id: str) -> Dict[str, Any]:
        """
        Predict project completion date based on current velocity.

        Args:
            project_id: Project identifier

        Returns:
            Completion date prediction
        """
        project = self.project_manager.get_project(project_id)
        tasks = self.task_manager.get_tasks_by_project(project_id)

        if not tasks:
            return {"error": "No tasks to analyze"}

        # Calculate velocity (work completed per day)
        completed_tasks = [t for t in tasks if t.status.value == "done" and t.completed_at]

        if not completed_tasks:
            return {
                "error": "No completed tasks for velocity calculation",
                "recommendation": "Complete some tasks to enable prediction"
            }

        # Calculate average completion time
        total_days = 0
        for task in completed_tasks:
            if task.start_date and task.completed_at:
                days = (task.completed_at.date() - task.start_date).days + 1
                total_days += days

        avg_days_per_task = total_days / len(completed_tasks) if completed_tasks else 1

        # Calculate remaining work
        remaining_tasks = [t for t in tasks if t.status.value not in ["done", "cancelled"]]
        remaining_count = len(remaining_tasks)
        remaining_hours = sum(t.estimated_hours for t in remaining_tasks)

        # Predict completion
        estimated_days = remaining_count * avg_days_per_task
        predicted_date = date.today() + timedelta(days=int(estimated_days))

        # Compare with planned end date
        on_track = True
        variance_days = 0

        if project.end_date:
            variance_days = (predicted_date - project.end_date).days
            on_track = variance_days <= 0

        return {
            "project_id": project_id,
            "predicted_completion_date": predicted_date.isoformat(),
            "planned_completion_date": project.end_date.isoformat() if project.end_date else None,
            "variance_days": variance_days,
            "on_track": on_track,
            "remaining_tasks": remaining_count,
            "remaining_hours": remaining_hours,
            "velocity": {
                "completed_tasks": len(completed_tasks),
                "avg_days_per_task": avg_days_per_task
            },
            "confidence": 0.7 if len(completed_tasks) > 5 else 0.5
        }

    def suggest_task_priorities(self, project_id: str) -> List[Dict[str, Any]]:
        """
        Suggest task prioritization based on multiple factors.

        Args:
            project_id: Project identifier

        Returns:
            List of task suggestions with priority scores
        """
        tasks = self.task_manager.get_tasks_by_project(project_id)
        suggestions = []

        for task in tasks:
            if task.status.value in ["done", "cancelled"]:
                continue

            score = 50.0  # Base score

            # Factor: Due date proximity
            if task.due_date:
                days_until_due = (task.due_date - date.today()).days
                if days_until_due < 0:
                    score += 40  # Overdue
                elif days_until_due < 3:
                    score += 30  # Due very soon
                elif days_until_due < 7:
                    score += 20  # Due this week
                elif days_until_due < 30:
                    score += 10  # Due this month

            # Factor: Current priority
            priority_scores = {
                "urgent": 30,
                "high": 20,
                "medium": 10,
                "low": 0
            }
            score += priority_scores.get(task.priority.value, 0)

            # Factor: Dependencies (blocking other tasks)
            if self.dependency_manager:
                dependents = self.dependency_manager.get_dependents(task.id)
                score += min(20, len(dependents) * 5)

            # Factor: Task progress (prioritize started tasks)
            if task.progress > 0:
                score += 15

            # Determine recommendation
            if score >= 80:
                recommendation = "Critical - Complete immediately"
                priority = "urgent"
            elif score >= 60:
                recommendation = "High - Complete soon"
                priority = "high"
            elif score >= 40:
                recommendation = "Medium - Complete this week"
                priority = "medium"
            else:
                recommendation = "Low - Can be deferred"
                priority = "low"

            suggestions.append({
                "task_id": task.id,
                "task_name": task.name,
                "current_priority": task.priority.value,
                "suggested_priority": priority,
                "priority_score": score,
                "recommendation": recommendation,
                "factors": {
                    "overdue": task.is_overdue(),
                    "blocking_tasks": len(self.dependency_manager.get_dependents(task.id)) if self.dependency_manager else 0,
                    "in_progress": task.progress > 0
                }
            })

        # Sort by score
        suggestions.sort(key=lambda x: x["priority_score"], reverse=True)

        return suggestions

    def optimize_resource_allocation(self, project_id: str) -> List[Dict[str, Any]]:
        """
        Suggest optimal resource allocation.

        Args:
            project_id: Project identifier

        Returns:
            List of allocation suggestions
        """
        if not self.resource_manager:
            return [{"error": "Resource manager not available"}]

        tasks = self.task_manager.get_tasks_by_project(project_id)
        unassigned_tasks = [t for t in tasks if not t.assignee and t.status.value != "done"]

        suggestions = []

        for task in unassigned_tasks:
            if not task.start_date or not task.due_date:
                continue

            # Find best resource
            available = self.resource_manager.find_available_resources(
                required_hours=task.estimated_hours,
                start_date=task.start_date,
                end_date=task.due_date,
                required_skills=task.tags  # Using tags as skills proxy
            )

            if available:
                best_resource = available[0]
                utilization = self.resource_manager.get_resource_utilization(
                    best_resource.id,
                    task.start_date,
                    task.due_date
                )

                suggestions.append({
                    "task_id": task.id,
                    "task_name": task.name,
                    "suggested_resource": best_resource.name,
                    "resource_id": best_resource.id,
                    "current_utilization": utilization,
                    "confidence": 0.8
                })

        return suggestions

    def generate_insights(self, project_id: str) -> List[AIInsight]:
        """
        Generate comprehensive AI insights for a project.

        Args:
            project_id: Project identifier

        Returns:
            List of AI insights
        """
        insights = []

        # Add risk insights
        risks = self.detect_risks(project_id)
        insights.extend(risks)

        # Add completion prediction insight
        prediction = self.predict_completion_date(project_id)
        if "error" not in prediction:
            if not prediction["on_track"]:
                insights.append(AIInsight(
                    type="timeline_insight",
                    title="Project Timeline Risk",
                    description=f"Project is predicted to finish {abs(prediction['variance_days'])} days late.",
                    severity="warning",
                    recommendations=[
                        "Review critical path",
                        "Add resources to critical tasks",
                        "Adjust project timeline"
                    ],
                    confidence=prediction["confidence"]
                ))

        # Add resource insights
        if self.resource_manager:
            allocation_suggestions = self.optimize_resource_allocation(project_id)
            if allocation_suggestions and "error" not in allocation_suggestions[0]:
                insights.append(AIInsight(
                    type="resource_insight",
                    title="Resource Optimization Available",
                    description=f"Found {len(allocation_suggestions)} tasks that can be auto-assigned.",
                    severity="info",
                    recommendations=[
                        "Review suggested assignments",
                        "Use auto-assign feature",
                        "Balance workload across team"
                    ],
                    confidence=0.75
                ))

        return insights

    def smart_schedule(self, project_id: str) -> Dict[str, Any]:
        """
        Create an AI-optimized schedule for the project.

        Args:
            project_id: Project identifier

        Returns:
            Scheduling recommendations
        """
        if not self.dependency_manager:
            return {"error": "Dependency manager required for smart scheduling"}

        tasks = self.task_manager.get_tasks_by_project(project_id)

        # Auto-schedule based on dependencies
        schedule = self.dependency_manager.auto_schedule_tasks(project_id)

        return {
            "project_id": project_id,
            "scheduled_tasks": len(schedule),
            "schedule": {
                task_id: {
                    "start_date": start.isoformat(),
                    "end_date": end.isoformat()
                }
                for task_id, (start, end) in schedule.items()
            },
            "recommendation": "Review and approve the suggested schedule"
        }

    def get_recommendations(self, project_id: str) -> Dict[str, Any]:
        """
        Get comprehensive AI recommendations for the project.

        Args:
            project_id: Project identifier

        Returns:
            Recommendations dictionary
        """
        return {
            "project_id": project_id,
            "health": self.analyze_project_health(project_id),
            "insights": [i.to_dict() for i in self.generate_insights(project_id)],
            "priority_suggestions": self.suggest_task_priorities(project_id)[:10],
            "completion_prediction": self.predict_completion_date(project_id),
            "generated_at": datetime.now().isoformat()
        }
