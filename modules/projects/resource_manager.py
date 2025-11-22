"""
NEXUS Resource Management Module
Resource allocation, workload tracking, and capacity planning.
"""

from typing import Dict, List, Optional, Any, Set
from datetime import date, datetime, timedelta
from dataclasses import dataclass
import uuid


@dataclass
class Resource:
    """
    Represents a resource (team member).

    Attributes:
        id: Resource identifier
        name: Resource name
        email: Resource email
        role: Resource role/title
        skills: List of skills
        capacity_hours_per_day: Available hours per day
        cost_per_hour: Hourly cost/rate
        availability: Availability calendar
        metadata: Additional metadata
    """
    id: str
    name: str
    email: str = ""
    role: str = ""
    skills: List[str] = None
    capacity_hours_per_day: float = 8.0
    cost_per_hour: float = 0.0
    availability: Dict[date, float] = None
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.skills is None:
            self.skills = []
        if self.availability is None:
            self.availability = {}
        if self.metadata is None:
            self.metadata = {}

    def to_dict(self) -> Dict[str, Any]:
        """Convert resource to dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "email": self.email,
            "role": self.role,
            "skills": self.skills,
            "capacity_hours_per_day": self.capacity_hours_per_day,
            "cost_per_hour": self.cost_per_hour,
            "availability": {
                d.isoformat(): h for d, h in self.availability.items()
            },
            "metadata": self.metadata
        }


@dataclass
class ResourceAllocation:
    """
    Represents a resource allocation to a task.

    Attributes:
        id: Allocation identifier
        resource_id: Resource identifier
        task_id: Task identifier
        allocated_hours: Hours allocated
        start_date: Allocation start date
        end_date: Allocation end date
        allocation_percentage: Percentage of resource capacity (0-100)
    """
    id: str
    resource_id: str
    task_id: str
    allocated_hours: float
    start_date: date
    end_date: date
    allocation_percentage: float = 100.0

    def to_dict(self) -> Dict[str, Any]:
        """Convert allocation to dictionary."""
        return {
            "id": self.id,
            "resource_id": self.resource_id,
            "task_id": self.task_id,
            "allocated_hours": self.allocated_hours,
            "start_date": self.start_date.isoformat(),
            "end_date": self.end_date.isoformat(),
            "allocation_percentage": self.allocation_percentage
        }


class ResourceManager:
    """
    Resource management and allocation engine.
    Handles resource allocation, workload tracking, and capacity planning.
    """

    def __init__(self, task_manager):
        """
        Initialize the resource manager.

        Args:
            task_manager: Task manager instance
        """
        self.task_manager = task_manager
        self.resources: Dict[str, Resource] = {}
        self.allocations: Dict[str, ResourceAllocation] = {}

    def add_resource(
        self,
        name: str,
        email: str = "",
        role: str = "",
        skills: Optional[List[str]] = None,
        capacity_hours_per_day: float = 8.0,
        cost_per_hour: float = 0.0,
        resource_id: Optional[str] = None
    ) -> Resource:
        """
        Add a resource.

        Args:
            name: Resource name
            email: Resource email
            role: Resource role
            skills: List of skills
            capacity_hours_per_day: Available hours per day
            cost_per_hour: Hourly cost
            resource_id: Optional resource ID

        Returns:
            Created resource
        """
        resource = Resource(
            id=resource_id or str(uuid.uuid4()),
            name=name,
            email=email,
            role=role,
            skills=skills or [],
            capacity_hours_per_day=capacity_hours_per_day,
            cost_per_hour=cost_per_hour
        )

        self.resources[resource.id] = resource
        return resource

    def remove_resource(self, resource_id: str) -> bool:
        """Remove a resource."""
        if resource_id in self.resources:
            # Remove all allocations
            to_remove = [
                alloc_id for alloc_id, alloc in self.allocations.items()
                if alloc.resource_id == resource_id
            ]
            for alloc_id in to_remove:
                del self.allocations[alloc_id]

            del self.resources[resource_id]
            return True
        return False

    def get_resource(self, resource_id: str) -> Optional[Resource]:
        """Get a resource by ID."""
        return self.resources.get(resource_id)

    def list_resources(
        self,
        role: Optional[str] = None,
        skills: Optional[List[str]] = None
    ) -> List[Resource]:
        """
        List resources with optional filters.

        Args:
            role: Filter by role
            skills: Filter by required skills

        Returns:
            List of matching resources
        """
        resources = list(self.resources.values())

        if role:
            resources = [r for r in resources if r.role == role]

        if skills:
            resources = [
                r for r in resources
                if all(skill in r.skills for skill in skills)
            ]

        return resources

    def allocate_resource(
        self,
        resource_id: str,
        task_id: str,
        allocated_hours: float,
        start_date: date,
        end_date: date,
        allocation_percentage: float = 100.0
    ) -> Optional[ResourceAllocation]:
        """
        Allocate a resource to a task.

        Args:
            resource_id: Resource identifier
            task_id: Task identifier
            allocated_hours: Hours to allocate
            start_date: Allocation start date
            end_date: Allocation end date
            allocation_percentage: Percentage of capacity

        Returns:
            Created allocation or None if invalid
        """
        resource = self.get_resource(resource_id)
        task = self.task_manager.get_task(task_id)

        if not resource or not task:
            return None

        allocation = ResourceAllocation(
            id=str(uuid.uuid4()),
            resource_id=resource_id,
            task_id=task_id,
            allocated_hours=allocated_hours,
            start_date=start_date,
            end_date=end_date,
            allocation_percentage=allocation_percentage
        )

        self.allocations[allocation.id] = allocation

        # Update task assignee if not set
        if not task.assignee:
            self.task_manager.update_task(task_id, assignee=resource_id)

        return allocation

    def deallocate_resource(self, allocation_id: str) -> bool:
        """Remove a resource allocation."""
        if allocation_id in self.allocations:
            del self.allocations[allocation_id]
            return True
        return False

    def get_resource_allocations(self, resource_id: str) -> List[ResourceAllocation]:
        """Get all allocations for a resource."""
        return [
            alloc for alloc in self.allocations.values()
            if alloc.resource_id == resource_id
        ]

    def get_task_allocations(self, task_id: str) -> List[ResourceAllocation]:
        """Get all allocations for a task."""
        return [
            alloc for alloc in self.allocations.values()
            if alloc.task_id == task_id
        ]

    def get_resource_workload(
        self,
        resource_id: str,
        start_date: date,
        end_date: date
    ) -> Dict[date, float]:
        """
        Calculate resource workload over a date range.

        Args:
            resource_id: Resource identifier
            start_date: Start date
            end_date: End date

        Returns:
            Dictionary mapping dates to allocated hours
        """
        allocations = self.get_resource_allocations(resource_id)
        workload: Dict[date, float] = {}

        current_date = start_date
        while current_date <= end_date:
            daily_hours = 0.0

            for alloc in allocations:
                if alloc.start_date <= current_date <= alloc.end_date:
                    # Calculate daily hours for this allocation
                    task_days = (alloc.end_date - alloc.start_date).days + 1
                    daily_hours += alloc.allocated_hours / max(1, task_days)

            workload[current_date] = daily_hours
            current_date += timedelta(days=1)

        return workload

    def get_resource_utilization(
        self,
        resource_id: str,
        start_date: date,
        end_date: date
    ) -> float:
        """
        Calculate resource utilization percentage.

        Args:
            resource_id: Resource identifier
            start_date: Start date
            end_date: End date

        Returns:
            Utilization percentage (0-100+)
        """
        resource = self.get_resource(resource_id)
        if not resource:
            return 0.0

        workload = self.get_resource_workload(resource_id, start_date, end_date)
        total_days = (end_date - start_date).days + 1

        if total_days == 0:
            return 0.0

        total_allocated = sum(workload.values())
        total_capacity = resource.capacity_hours_per_day * total_days

        if total_capacity == 0:
            return 0.0

        return (total_allocated / total_capacity) * 100

    def find_available_resources(
        self,
        required_hours: float,
        start_date: date,
        end_date: date,
        required_skills: Optional[List[str]] = None,
        max_utilization: float = 80.0
    ) -> List[Resource]:
        """
        Find available resources for allocation.

        Args:
            required_hours: Required hours
            start_date: Start date
            end_date: End date
            required_skills: Required skills
            max_utilization: Maximum acceptable utilization (%)

        Returns:
            List of available resources
        """
        available = []

        for resource in self.resources.values():
            # Check skills
            if required_skills:
                if not all(skill in resource.skills for skill in required_skills):
                    continue

            # Check utilization
            utilization = self.get_resource_utilization(resource.id, start_date, end_date)
            if utilization >= max_utilization:
                continue

            available.append(resource)

        return available

    def auto_assign_resource(
        self,
        task_id: str,
        required_skills: Optional[List[str]] = None
    ) -> Optional[Resource]:
        """
        Automatically assign the best available resource to a task.

        Args:
            task_id: Task identifier
            required_skills: Required skills

        Returns:
            Assigned resource or None
        """
        task = self.task_manager.get_task(task_id)
        if not task or not task.start_date or not task.due_date:
            return None

        # Find available resources
        available = self.find_available_resources(
            required_hours=task.estimated_hours,
            start_date=task.start_date,
            end_date=task.due_date,
            required_skills=required_skills
        )

        if not available:
            return None

        # Select resource with lowest utilization
        best_resource = min(
            available,
            key=lambda r: self.get_resource_utilization(
                r.id, task.start_date, task.due_date
            )
        )

        # Create allocation
        self.allocate_resource(
            resource_id=best_resource.id,
            task_id=task_id,
            allocated_hours=task.estimated_hours,
            start_date=task.start_date,
            end_date=task.due_date
        )

        return best_resource

    def get_overallocated_resources(
        self,
        start_date: date,
        end_date: date,
        threshold: float = 100.0
    ) -> List[Tuple[Resource, float]]:
        """
        Find overallocated resources.

        Args:
            start_date: Start date
            end_date: End date
            threshold: Overallocation threshold (%)

        Returns:
            List of tuples (resource, utilization_percentage)
        """
        overallocated = []

        for resource in self.resources.values():
            utilization = self.get_resource_utilization(
                resource.id, start_date, end_date
            )

            if utilization > threshold:
                overallocated.append((resource, utilization))

        return sorted(overallocated, key=lambda x: x[1], reverse=True)

    def calculate_project_cost(
        self,
        project_id: str,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> Dict[str, Any]:
        """
        Calculate project cost based on resource allocations.

        Args:
            project_id: Project identifier
            start_date: Start date (None = all time)
            end_date: End date (None = all time)

        Returns:
            Dictionary with cost breakdown
        """
        tasks = self.task_manager.get_tasks_by_project(project_id)
        task_ids = {t.id for t in tasks}

        total_cost = 0.0
        resource_costs: Dict[str, float] = {}

        for allocation in self.allocations.values():
            if allocation.task_id not in task_ids:
                continue

            # Apply date filter
            if start_date and allocation.end_date < start_date:
                continue
            if end_date and allocation.start_date > end_date:
                continue

            resource = self.get_resource(allocation.resource_id)
            if not resource:
                continue

            cost = allocation.allocated_hours * resource.cost_per_hour
            total_cost += cost

            if resource.name not in resource_costs:
                resource_costs[resource.name] = 0.0
            resource_costs[resource.name] += cost

        return {
            "total_cost": total_cost,
            "by_resource": resource_costs,
            "currency": "USD"  # TODO: Make configurable
        }

    def generate_capacity_report(
        self,
        start_date: date,
        end_date: date
    ) -> Dict[str, Any]:
        """
        Generate a capacity planning report.

        Args:
            start_date: Start date
            end_date: End date

        Returns:
            Capacity report dictionary
        """
        report = {
            "period": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat()
            },
            "resources": []
        }

        for resource in self.resources.values():
            workload = self.get_resource_workload(resource.id, start_date, end_date)
            utilization = self.get_resource_utilization(resource.id, start_date, end_date)

            total_allocated = sum(workload.values())
            total_days = (end_date - start_date).days + 1
            total_capacity = resource.capacity_hours_per_day * total_days

            report["resources"].append({
                "id": resource.id,
                "name": resource.name,
                "role": resource.role,
                "utilization_percentage": utilization,
                "total_allocated_hours": total_allocated,
                "total_capacity_hours": total_capacity,
                "available_hours": total_capacity - total_allocated,
                "is_overallocated": utilization > 100.0
            })

        return report
