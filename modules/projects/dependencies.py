"""
NEXUS Task Dependencies Module
Manages task dependencies and relationships with cycle detection.
"""

from typing import Dict, List, Optional, Set, Tuple
from enum import Enum
from datetime import date, timedelta


class DependencyType(Enum):
    """Task dependency types (project management standard)."""
    FINISH_TO_START = "FS"  # Predecessor must finish before successor starts
    START_TO_START = "SS"   # Predecessor must start before successor starts
    FINISH_TO_FINISH = "FF"  # Predecessor must finish before successor finishes
    START_TO_FINISH = "SF"   # Predecessor must start before successor finishes


class Dependency:
    """
    Represents a dependency relationship between two tasks.

    Attributes:
        predecessor_id: Task that must be completed first
        successor_id: Task that depends on the predecessor
        dependency_type: Type of dependency relationship
        lag_days: Number of days lag (positive) or lead (negative)
    """

    def __init__(
        self,
        predecessor_id: str,
        successor_id: str,
        dependency_type: DependencyType = DependencyType.FINISH_TO_START,
        lag_days: int = 0
    ):
        """Initialize a dependency."""
        self.predecessor_id: str = predecessor_id
        self.successor_id: str = successor_id
        self.dependency_type: DependencyType = dependency_type
        self.lag_days: int = lag_days

    def to_dict(self) -> Dict[str, any]:
        """Convert dependency to dictionary."""
        return {
            "predecessor_id": self.predecessor_id,
            "successor_id": self.successor_id,
            "dependency_type": self.dependency_type.value,
            "lag_days": self.lag_days
        }

    @classmethod
    def from_dict(cls, data: Dict[str, any]) -> 'Dependency':
        """Create dependency from dictionary."""
        return cls(
            predecessor_id=data["predecessor_id"],
            successor_id=data["successor_id"],
            dependency_type=DependencyType(data.get("dependency_type", "FS")),
            lag_days=data.get("lag_days", 0)
        )


class DependencyManager:
    """
    Manages task dependencies and relationships.
    Handles dependency creation, validation, and cycle detection.
    """

    def __init__(self, task_manager):
        """
        Initialize the dependency manager.

        Args:
            task_manager: Task manager instance
        """
        self.task_manager = task_manager
        self.dependencies: Dict[Tuple[str, str], Dependency] = {}

    def add_dependency(
        self,
        predecessor_id: str,
        successor_id: str,
        dependency_type: DependencyType = DependencyType.FINISH_TO_START,
        lag_days: int = 0
    ) -> Optional[Dependency]:
        """
        Add a dependency between two tasks.

        Args:
            predecessor_id: Task that must complete first
            successor_id: Task that depends on predecessor
            dependency_type: Type of dependency
            lag_days: Lag or lead time in days

        Returns:
            Created dependency or None if invalid

        Raises:
            ValueError: If dependency would create a cycle
        """
        # Validate tasks exist
        predecessor = self.task_manager.get_task(predecessor_id)
        successor = self.task_manager.get_task(successor_id)

        if not predecessor or not successor:
            return None

        # Check for same task
        if predecessor_id == successor_id:
            raise ValueError("Cannot create dependency from task to itself")

        # Check for cycles
        if self._would_create_cycle(predecessor_id, successor_id):
            raise ValueError("Dependency would create a cycle")

        # Create dependency
        dependency = Dependency(
            predecessor_id=predecessor_id,
            successor_id=successor_id,
            dependency_type=dependency_type,
            lag_days=lag_days
        )

        key = (predecessor_id, successor_id)
        self.dependencies[key] = dependency

        # Update task dependency lists
        if successor_id not in predecessor.dependencies:
            successor.dependencies.append(predecessor_id)

        return dependency

    def remove_dependency(self, predecessor_id: str, successor_id: str) -> bool:
        """
        Remove a dependency.

        Args:
            predecessor_id: Predecessor task ID
            successor_id: Successor task ID

        Returns:
            True if removed, False if not found
        """
        key = (predecessor_id, successor_id)
        if key in self.dependencies:
            del self.dependencies[key]

            # Update task dependency list
            successor = self.task_manager.get_task(successor_id)
            if successor and predecessor_id in successor.dependencies:
                successor.dependencies.remove(predecessor_id)

            return True
        return False

    def get_dependencies(self, task_id: str) -> List[Dependency]:
        """
        Get all dependencies where task is the successor (tasks this task depends on).

        Args:
            task_id: Task identifier

        Returns:
            List of dependencies
        """
        return [
            dep for (pred, succ), dep in self.dependencies.items()
            if succ == task_id
        ]

    def get_dependents(self, task_id: str) -> List[Dependency]:
        """
        Get all dependencies where task is the predecessor (tasks that depend on this task).

        Args:
            task_id: Task identifier

        Returns:
            List of dependencies
        """
        return [
            dep for (pred, succ), dep in self.dependencies.items()
            if pred == task_id
        ]

    def _would_create_cycle(self, predecessor_id: str, successor_id: str) -> bool:
        """
        Check if adding a dependency would create a cycle.

        Args:
            predecessor_id: Proposed predecessor
            successor_id: Proposed successor

        Returns:
            True if cycle would be created
        """
        # Use DFS to check if there's a path from successor to predecessor
        visited: Set[str] = set()
        stack = [successor_id]

        while stack:
            current = stack.pop()

            if current == predecessor_id:
                return True

            if current in visited:
                continue

            visited.add(current)

            # Add all tasks that depend on current task
            dependents = self.get_dependents(current)
            stack.extend([dep.successor_id for dep in dependents])

        return False

    def get_all_dependencies_for_task(self, task_id: str) -> Set[str]:
        """
        Get all tasks that a task depends on (transitive closure).

        Args:
            task_id: Task identifier

        Returns:
            Set of all dependency task IDs
        """
        all_deps: Set[str] = set()
        to_process = [task_id]
        processed: Set[str] = set()

        while to_process:
            current = to_process.pop()

            if current in processed:
                continue

            processed.add(current)

            dependencies = self.get_dependencies(current)
            for dep in dependencies:
                all_deps.add(dep.predecessor_id)
                to_process.append(dep.predecessor_id)

        return all_deps

    def get_critical_path(self, project_id: str) -> List[str]:
        """
        Calculate the critical path for a project using the Critical Path Method (CPM).

        Args:
            project_id: Project identifier

        Returns:
            List of task IDs in the critical path
        """
        tasks = self.task_manager.get_tasks_by_project(project_id)
        if not tasks:
            return []

        # Build task duration map
        task_duration = {}
        for task in tasks:
            # Use estimated hours converted to days (assuming 8 hour workday)
            duration = task.estimated_hours / 8.0 if task.estimated_hours > 0 else 1.0
            task_duration[task.id] = duration

        # Calculate earliest start/finish times (forward pass)
        earliest_start = {}
        earliest_finish = {}

        # Topological sort to process tasks in dependency order
        sorted_tasks = self._topological_sort([t.id for t in tasks])

        for task_id in sorted_tasks:
            # Find maximum earliest finish of all predecessors
            dependencies = self.get_dependencies(task_id)
            if dependencies:
                max_predecessor_finish = 0.0
                for dep in dependencies:
                    pred_finish = earliest_finish.get(dep.predecessor_id, 0.0)
                    pred_finish += dep.lag_days
                    max_predecessor_finish = max(max_predecessor_finish, pred_finish)
                earliest_start[task_id] = max_predecessor_finish
            else:
                earliest_start[task_id] = 0.0

            earliest_finish[task_id] = earliest_start[task_id] + task_duration[task_id]

        # Calculate latest start/finish times (backward pass)
        latest_start = {}
        latest_finish = {}

        # Find project completion time
        if not earliest_finish:
            return []

        project_finish = max(earliest_finish.values())

        # Process in reverse order
        for task_id in reversed(sorted_tasks):
            dependents = self.get_dependents(task_id)
            if dependents:
                min_successor_start = project_finish
                for dep in dependents:
                    succ_start = latest_start.get(dep.successor_id, project_finish)
                    succ_start -= dep.lag_days
                    min_successor_start = min(min_successor_start, succ_start)
                latest_finish[task_id] = min_successor_start
            else:
                latest_finish[task_id] = project_finish

            latest_start[task_id] = latest_finish[task_id] - task_duration[task_id]

        # Find critical tasks (where earliest == latest)
        critical_tasks = []
        for task_id in sorted_tasks:
            slack = latest_start[task_id] - earliest_start[task_id]
            if abs(slack) < 0.001:  # Float comparison tolerance
                critical_tasks.append(task_id)

        return critical_tasks

    def _topological_sort(self, task_ids: List[str]) -> List[str]:
        """
        Topologically sort tasks based on dependencies.

        Args:
            task_ids: List of task identifiers

        Returns:
            Sorted list of task IDs
        """
        # Calculate in-degree for each task
        in_degree = {task_id: 0 for task_id in task_ids}

        for task_id in task_ids:
            dependencies = self.get_dependencies(task_id)
            in_degree[task_id] = len(dependencies)

        # Process tasks with no dependencies first
        queue = [task_id for task_id in task_ids if in_degree[task_id] == 0]
        result = []

        while queue:
            current = queue.pop(0)
            result.append(current)

            # Reduce in-degree for dependent tasks
            dependents = self.get_dependents(current)
            for dep in dependents:
                successor_id = dep.successor_id
                if successor_id in in_degree:
                    in_degree[successor_id] -= 1
                    if in_degree[successor_id] == 0:
                        queue.append(successor_id)

        return result

    def calculate_task_dates(self, task_id: str) -> Tuple[Optional[date], Optional[date]]:
        """
        Calculate earliest start and finish dates for a task based on dependencies.

        Args:
            task_id: Task identifier

        Returns:
            Tuple of (earliest_start_date, earliest_finish_date)
        """
        task = self.task_manager.get_task(task_id)
        if not task:
            return None, None

        dependencies = self.get_dependencies(task_id)
        if not dependencies:
            # No dependencies, use task's own dates or today
            start = task.start_date or date.today()
            duration_days = int(task.estimated_hours / 8.0) if task.estimated_hours > 0 else 1
            finish = start + timedelta(days=duration_days)
            return start, finish

        # Find latest finish date of all predecessors
        latest_predecessor_date = None

        for dep in dependencies:
            predecessor = self.task_manager.get_task(dep.predecessor_id)
            if not predecessor:
                continue

            # Recursively calculate predecessor dates if not set
            if not predecessor.due_date:
                _, pred_finish = self.calculate_task_dates(dep.predecessor_id)
            else:
                pred_finish = predecessor.due_date

            if not pred_finish:
                continue

            # Apply dependency type logic
            if dep.dependency_type == DependencyType.FINISH_TO_START:
                constraint_date = pred_finish
            elif dep.dependency_type == DependencyType.START_TO_START:
                constraint_date = predecessor.start_date or pred_finish
            elif dep.dependency_type == DependencyType.FINISH_TO_FINISH:
                constraint_date = pred_finish
            elif dep.dependency_type == DependencyType.START_TO_FINISH:
                constraint_date = predecessor.start_date or pred_finish

            # Apply lag
            constraint_date = constraint_date + timedelta(days=dep.lag_days)

            if latest_predecessor_date is None or constraint_date > latest_predecessor_date:
                latest_predecessor_date = constraint_date

        # Calculate task dates
        start = latest_predecessor_date or task.start_date or date.today()
        duration_days = int(task.estimated_hours / 8.0) if task.estimated_hours > 0 else 1
        finish = start + timedelta(days=duration_days)

        return start, finish

    def auto_schedule_tasks(self, project_id: str) -> Dict[str, Tuple[date, date]]:
        """
        Automatically schedule all tasks in a project based on dependencies.

        Args:
            project_id: Project identifier

        Returns:
            Dictionary mapping task IDs to (start_date, end_date) tuples
        """
        tasks = self.task_manager.get_tasks_by_project(project_id)
        sorted_tasks = self._topological_sort([t.id for t in tasks])

        schedule = {}
        for task_id in sorted_tasks:
            start, finish = self.calculate_task_dates(task_id)
            if start and finish:
                schedule[task_id] = (start, finish)

                # Update task dates
                self.task_manager.update_task(
                    task_id,
                    start_date=start,
                    due_date=finish
                )

        return schedule

    def get_blocking_tasks(self, task_id: str) -> List[str]:
        """
        Get all tasks that are blocking this task from starting.

        Args:
            task_id: Task identifier

        Returns:
            List of blocking task IDs
        """
        task = self.task_manager.get_task(task_id)
        if not task:
            return []

        blocking = []
        dependencies = self.get_dependencies(task_id)

        for dep in dependencies:
            predecessor = self.task_manager.get_task(dep.predecessor_id)
            if predecessor and predecessor.status.value not in ["done", "cancelled"]:
                blocking.append(dep.predecessor_id)

        return blocking

    def can_task_start(self, task_id: str) -> bool:
        """
        Check if a task can start based on its dependencies.

        Args:
            task_id: Task identifier

        Returns:
            True if all dependencies are satisfied
        """
        return len(self.get_blocking_tasks(task_id)) == 0

    def get_dependency_graph(self, project_id: str) -> Dict[str, List[str]]:
        """
        Get the dependency graph for a project.

        Args:
            project_id: Project identifier

        Returns:
            Dictionary mapping task IDs to lists of dependent task IDs
        """
        tasks = self.task_manager.get_tasks_by_project(project_id)
        graph = {task.id: [] for task in tasks}

        for task in tasks:
            dependencies = self.get_dependencies(task.id)
            graph[task.id] = [dep.predecessor_id for dep in dependencies]

        return graph
