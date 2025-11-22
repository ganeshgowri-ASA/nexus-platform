"""Tests for DAG engine."""

import pytest
from modules.orchestration.core.dag import DAGEngine, DAGBuilder, TaskNode, DAGValidationError


def test_dag_creation():
    """Test DAG creation."""
    dag = DAGEngine()

    task1 = TaskNode(
        task_key="task1",
        name="Task 1",
        task_type="python",
        config={"code": "print('hello')"},
    )

    task2 = TaskNode(
        task_key="task2",
        name="Task 2",
        task_type="python",
        config={"code": "print('world')"},
        depends_on=["task1"],
    )

    dag.add_task(task1)
    dag.add_task(task2)
    dag.add_dependency("task1", "task2")

    assert len(dag.tasks) == 2
    assert "task1" in dag.tasks
    assert "task2" in dag.tasks


def test_dag_validation():
    """Test DAG validation."""
    dag = DAGEngine()

    task1 = TaskNode(
        task_key="task1",
        name="Task 1",
        task_type="python",
        config={},
    )

    task2 = TaskNode(
        task_key="task2",
        name="Task 2",
        task_type="python",
        config={},
        depends_on=["task1"],
    )

    dag.add_task(task1)
    dag.add_task(task2)
    dag.add_dependency("task1", "task2")

    is_valid, error = dag.validate()
    assert is_valid is True
    assert error is None


def test_dag_cycle_detection():
    """Test cycle detection in DAG."""
    dag = DAGEngine()

    task1 = TaskNode(task_key="task1", name="Task 1", task_type="python", config={})
    task2 = TaskNode(task_key="task2", name="Task 2", task_type="python", config={})

    dag.add_task(task1)
    dag.add_task(task2)
    dag.add_dependency("task1", "task2")
    dag.add_dependency("task2", "task1")  # Create cycle

    is_valid, error = dag.validate()
    assert is_valid is False
    assert "cycle" in error.lower()


def test_execution_order():
    """Test topological sort for execution order."""
    dag = DAGEngine()

    tasks = [
        TaskNode("task1", "Task 1", "python", {}),
        TaskNode("task2", "Task 2", "python", {}, depends_on=["task1"]),
        TaskNode("task3", "Task 3", "python", {}, depends_on=["task1"]),
        TaskNode("task4", "Task 4", "python", {}, depends_on=["task2", "task3"]),
    ]

    dag.build_from_tasks(tasks)

    execution_order = dag.get_execution_order()

    # task1 should be first, task4 should be last
    assert execution_order[0] == "task1"
    assert execution_order[-1] == "task4"


def test_parallel_groups():
    """Test parallel execution groups."""
    dag = DAGEngine()

    tasks = [
        TaskNode("task1", "Task 1", "python", {}),
        TaskNode("task2", "Task 2", "python", {}, depends_on=["task1"]),
        TaskNode("task3", "Task 3", "python", {}, depends_on=["task1"]),
        TaskNode("task4", "Task 4", "python", {}, depends_on=["task2", "task3"]),
    ]

    dag.build_from_tasks(tasks)

    parallel_groups = dag.get_parallel_groups()

    # First group should have task1
    assert "task1" in parallel_groups[0]

    # Second group should have task2 and task3 (can run in parallel)
    assert "task2" in parallel_groups[1]
    assert "task3" in parallel_groups[1]

    # Third group should have task4
    assert "task4" in parallel_groups[2]


def test_dag_builder():
    """Test DAG builder."""
    builder = DAGBuilder()

    dag = (
        builder.task("task1", "Task 1", "python", {"code": "print('1')"})
        .task("task2", "Task 2", "python", {"code": "print('2')"}, depends_on=["task1"])
        .task("task3", "Task 3", "python", {"code": "print('3')"}, depends_on=["task1"])
        .build()
    )

    assert len(dag.tasks) == 3
    is_valid, error = dag.validate()
    assert is_valid is True


def test_dag_serialization():
    """Test DAG to/from dict."""
    builder = DAGBuilder()

    dag = (
        builder.task("task1", "Task 1", "python", {"code": "print('1')"})
        .task("task2", "Task 2", "python", {"code": "print('2')"}, depends_on=["task1"])
        .build()
    )

    # Convert to dict
    dag_dict = dag.to_dict()

    # Create from dict
    dag2 = DAGEngine.from_dict(dag_dict)

    assert len(dag2.tasks) == len(dag.tasks)
    assert set(dag2.tasks.keys()) == set(dag.tasks.keys())


def test_root_and_leaf_tasks():
    """Test getting root and leaf tasks."""
    dag = DAGEngine()

    tasks = [
        TaskNode("task1", "Task 1", "python", {}),
        TaskNode("task2", "Task 2", "python", {}, depends_on=["task1"]),
        TaskNode("task3", "Task 3", "python", {}, depends_on=["task2"]),
    ]

    dag.build_from_tasks(tasks)

    root_tasks = dag.get_root_tasks()
    leaf_tasks = dag.get_leaf_tasks()

    assert root_tasks == ["task1"]
    assert leaf_tasks == ["task3"]
