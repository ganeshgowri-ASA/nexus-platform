"""DAG (Directed Acyclic Graph) engine for workflow orchestration."""

import networkx as nx
from typing import Dict, List, Set, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum
import json


class DAGValidationError(Exception):
    """Raised when DAG validation fails."""
    pass


class TaskNode:
    """Represents a task node in the DAG."""

    def __init__(
        self,
        task_key: str,
        name: str,
        task_type: str,
        config: Dict[str, Any],
        depends_on: Optional[List[str]] = None,
        retry_config: Optional[Dict[str, Any]] = None,
    ):
        self.task_key = task_key
        self.name = name
        self.task_type = task_type
        self.config = config
        self.depends_on = depends_on or []
        self.retry_config = retry_config or {
            "max_retries": 3,
            "retry_delay": 60,
            "timeout": 3600,
        }

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "task_key": self.task_key,
            "name": self.name,
            "task_type": self.task_type,
            "config": self.config,
            "depends_on": self.depends_on,
            "retry_config": self.retry_config,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TaskNode":
        """Create from dictionary."""
        return cls(
            task_key=data["task_key"],
            name=data["name"],
            task_type=data["task_type"],
            config=data["config"],
            depends_on=data.get("depends_on", []),
            retry_config=data.get("retry_config"),
        )


class DAGEngine:
    """
    DAG engine for building and managing workflow graphs.

    Features:
    - Build DAG from task definitions
    - Validate DAG structure (no cycles, valid dependencies)
    - Topological sort for execution order
    - Find parallel execution groups
    - Dependency resolution
    """

    def __init__(self):
        self.graph = nx.DiGraph()
        self.tasks: Dict[str, TaskNode] = {}

    def add_task(self, task: TaskNode) -> None:
        """Add a task to the DAG."""
        if task.task_key in self.tasks:
            raise DAGValidationError(f"Task {task.task_key} already exists in DAG")

        self.tasks[task.task_key] = task
        self.graph.add_node(task.task_key, task=task)

    def add_dependency(self, from_task: str, to_task: str) -> None:
        """
        Add a dependency between tasks.
        from_task must complete before to_task can start.
        """
        if from_task not in self.tasks:
            raise DAGValidationError(f"Task {from_task} not found in DAG")
        if to_task not in self.tasks:
            raise DAGValidationError(f"Task {to_task} not found in DAG")

        self.graph.add_edge(from_task, to_task)

    def build_from_tasks(self, tasks: List[TaskNode]) -> None:
        """Build DAG from list of tasks."""
        # Add all tasks first
        for task in tasks:
            self.add_task(task)

        # Then add dependencies
        for task in tasks:
            for dependency in task.depends_on:
                self.add_dependency(dependency, task.task_key)

    def validate(self) -> Tuple[bool, Optional[str]]:
        """
        Validate the DAG structure.

        Returns:
            Tuple of (is_valid, error_message)
        """
        # Check for cycles
        if not nx.is_directed_acyclic_graph(self.graph):
            try:
                cycle = nx.find_cycle(self.graph)
                return False, f"Cycle detected in DAG: {cycle}"
            except nx.NetworkXNoCycle:
                pass

        # Check for unreachable nodes (isolated nodes)
        if len(self.tasks) > 0:
            weakly_connected = list(nx.weakly_connected_components(self.graph))
            if len(weakly_connected) > 1:
                return False, f"DAG has disconnected components: {weakly_connected}"

        # Validate dependencies exist
        for task_key, task in self.tasks.items():
            for dep in task.depends_on:
                if dep not in self.tasks:
                    return False, f"Task {task_key} depends on non-existent task {dep}"

        return True, None

    def get_execution_order(self) -> List[str]:
        """
        Get topological sort order for task execution.

        Returns:
            List of task keys in execution order
        """
        try:
            return list(nx.topological_sort(self.graph))
        except nx.NetworkXError as e:
            raise DAGValidationError(f"Cannot determine execution order: {e}")

    def get_parallel_groups(self) -> List[Set[str]]:
        """
        Get groups of tasks that can be executed in parallel.

        Returns:
            List of sets, where each set contains tasks that can run in parallel
        """
        execution_order = self.get_execution_order()
        groups: List[Set[str]] = []
        executed: Set[str] = set()

        while len(executed) < len(execution_order):
            # Find all tasks whose dependencies are satisfied
            ready_tasks = set()
            for task_key in execution_order:
                if task_key in executed:
                    continue

                task = self.tasks[task_key]
                deps_satisfied = all(dep in executed for dep in task.depends_on)

                if deps_satisfied:
                    ready_tasks.add(task_key)

            if not ready_tasks:
                break

            groups.append(ready_tasks)
            executed.update(ready_tasks)

        return groups

    def get_dependencies(self, task_key: str) -> List[str]:
        """Get direct dependencies of a task."""
        if task_key not in self.tasks:
            raise DAGValidationError(f"Task {task_key} not found in DAG")
        return list(self.graph.predecessors(task_key))

    def get_dependents(self, task_key: str) -> List[str]:
        """Get tasks that depend on this task."""
        if task_key not in self.tasks:
            raise DAGValidationError(f"Task {task_key} not found in DAG")
        return list(self.graph.successors(task_key))

    def get_root_tasks(self) -> List[str]:
        """Get tasks with no dependencies (can start immediately)."""
        return [
            task_key
            for task_key in self.tasks.keys()
            if self.graph.in_degree(task_key) == 0
        ]

    def get_leaf_tasks(self) -> List[str]:
        """Get tasks with no dependents (final tasks)."""
        return [
            task_key
            for task_key in self.tasks.keys()
            if self.graph.out_degree(task_key) == 0
        ]

    def get_critical_path(self) -> List[str]:
        """
        Get the critical path (longest path) through the DAG.
        Assumes all tasks have equal weight.
        """
        try:
            return list(nx.dag_longest_path(self.graph))
        except nx.NetworkXError:
            return []

    def to_dict(self) -> Dict[str, Any]:
        """Convert DAG to dictionary representation."""
        return {
            "tasks": {k: v.to_dict() for k, v in self.tasks.items()},
            "dependencies": [
                {"from": u, "to": v} for u, v in self.graph.edges()
            ],
        }

    def to_json(self) -> str:
        """Convert DAG to JSON string."""
        return json.dumps(self.to_dict(), indent=2)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "DAGEngine":
        """Create DAG from dictionary representation."""
        dag = cls()

        # Add tasks
        for task_data in data["tasks"].values():
            task = TaskNode.from_dict(task_data)
            dag.add_task(task)

        # Dependencies are already in tasks' depends_on field
        for task in dag.tasks.values():
            for dep in task.depends_on:
                dag.add_dependency(dep, task.task_key)

        return dag

    @classmethod
    def from_json(cls, json_str: str) -> "DAGEngine":
        """Create DAG from JSON string."""
        data = json.loads(json_str)
        return cls.from_dict(data)

    def visualize(self) -> Dict[str, Any]:
        """
        Generate visualization data for the DAG.

        Returns:
            Dictionary with nodes and edges for visualization
        """
        nodes = []
        edges = []

        # Get parallel groups for coloring
        try:
            parallel_groups = self.get_parallel_groups()
            task_to_group = {}
            for i, group in enumerate(parallel_groups):
                for task_key in group:
                    task_to_group[task_key] = i
        except:
            task_to_group = {}

        # Create nodes
        for task_key, task in self.tasks.items():
            nodes.append({
                "id": task_key,
                "label": task.name,
                "type": task.task_type,
                "group": task_to_group.get(task_key, 0),
            })

        # Create edges
        for u, v in self.graph.edges():
            edges.append({
                "from": u,
                "to": v,
            })

        return {
            "nodes": nodes,
            "edges": edges,
        }

    def __repr__(self) -> str:
        return f"DAGEngine(tasks={len(self.tasks)}, edges={len(self.graph.edges())})"


class DAGBuilder:
    """Helper class for building DAGs fluently."""

    def __init__(self):
        self.dag = DAGEngine()

    def task(
        self,
        task_key: str,
        name: str,
        task_type: str,
        config: Dict[str, Any],
        depends_on: Optional[List[str]] = None,
        **kwargs,
    ) -> "DAGBuilder":
        """Add a task to the DAG."""
        task_node = TaskNode(
            task_key=task_key,
            name=name,
            task_type=task_type,
            config=config,
            depends_on=depends_on,
            retry_config=kwargs.get("retry_config"),
        )
        self.dag.add_task(task_node)
        return self

    def build(self) -> DAGEngine:
        """Build and validate the DAG."""
        # Add dependencies from tasks
        for task in self.dag.tasks.values():
            for dep in task.depends_on:
                if dep in self.dag.tasks:
                    self.dag.add_dependency(dep, task.task_key)

        # Validate
        is_valid, error = self.dag.validate()
        if not is_valid:
            raise DAGValidationError(error)

        return self.dag
