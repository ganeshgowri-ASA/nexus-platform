"""
NEXUS Workflow Automation Engine
Core workflow execution engine with visual workflow support
"""

from typing import Dict, List, Any, Optional, Union, Callable, TypedDict
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import uuid
import asyncio
import json
import copy
from collections import defaultdict


class NodeType(Enum):
    """Types of workflow nodes"""
    TRIGGER = "trigger"
    ACTION = "action"
    CONDITION = "condition"
    LOOP = "loop"
    PARALLEL = "parallel"
    DELAY = "delay"
    TRANSFORM = "transform"
    SPLIT = "split"
    MERGE = "merge"


class ExecutionStatus(Enum):
    """Workflow execution status"""
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    PAUSED = "paused"
    CANCELLED = "cancelled"
    RETRY = "retry"


class ConnectionType(Enum):
    """Connection types between nodes"""
    DEFAULT = "default"
    SUCCESS = "success"
    FAILURE = "failure"
    CONDITION_TRUE = "condition_true"
    CONDITION_FALSE = "condition_false"


@dataclass
class WorkflowVariable:
    """Variable that can be passed between workflow steps"""
    name: str
    value: Any
    type: str
    source_node: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class NodeConnection:
    """Connection between workflow nodes"""
    id: str
    source_node_id: str
    target_node_id: str
    connection_type: ConnectionType = ConnectionType.DEFAULT
    condition: Optional[str] = None  # JavaScript-like condition expression
    label: Optional[str] = None


@dataclass
class WorkflowNode:
    """Individual node in a workflow"""
    id: str
    name: str
    type: NodeType
    config: Dict[str, Any]
    position: Dict[str, float] = field(default_factory=lambda: {"x": 0, "y": 0})
    input_variables: List[str] = field(default_factory=list)
    output_variables: List[str] = field(default_factory=list)
    retry_config: Optional[Dict[str, Any]] = None
    timeout: Optional[int] = None  # seconds
    enabled: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class WorkflowDefinition:
    """Complete workflow definition"""
    id: str
    name: str
    description: str
    nodes: List[WorkflowNode]
    connections: List[NodeConnection]
    variables: Dict[str, Any] = field(default_factory=dict)
    environment_variables: Dict[str, str] = field(default_factory=dict)
    settings: Dict[str, Any] = field(default_factory=dict)
    tags: List[str] = field(default_factory=list)
    version: int = 1
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    created_by: Optional[str] = None
    is_template: bool = False
    is_active: bool = True


@dataclass
class NodeExecution:
    """Execution record for a single node"""
    node_id: str
    execution_id: str
    status: ExecutionStatus
    input_data: Dict[str, Any] = field(default_factory=dict)
    output_data: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    duration_ms: Optional[float] = None
    retry_count: int = 0
    logs: List[str] = field(default_factory=list)


@dataclass
class WorkflowExecution:
    """Complete workflow execution record"""
    id: str
    workflow_id: str
    status: ExecutionStatus
    trigger_data: Dict[str, Any] = field(default_factory=dict)
    context: Dict[str, Any] = field(default_factory=dict)
    variables: Dict[str, WorkflowVariable] = field(default_factory=dict)
    node_executions: Dict[str, NodeExecution] = field(default_factory=dict)
    started_at: datetime = field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    duration_ms: Optional[float] = None
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class WorkflowEngine:
    """
    Core workflow execution engine
    Handles workflow execution, node processing, and data flow
    """

    def __init__(self):
        self.workflows: Dict[str, WorkflowDefinition] = {}
        self.executions: Dict[str, WorkflowExecution] = {}
        self.node_handlers: Dict[NodeType, Callable] = {}
        self.active_executions: Dict[str, asyncio.Task] = {}

    def register_node_handler(self, node_type: NodeType, handler: Callable) -> None:
        """Register a handler function for a specific node type"""
        self.node_handlers[node_type] = handler

    def create_workflow(
        self,
        name: str,
        description: str,
        nodes: List[Dict[str, Any]],
        connections: List[Dict[str, Any]],
        **kwargs
    ) -> WorkflowDefinition:
        """Create a new workflow definition"""
        workflow_id = kwargs.get('id', str(uuid.uuid4()))

        # Parse nodes
        workflow_nodes = [
            WorkflowNode(
                id=node.get('id', str(uuid.uuid4())),
                name=node['name'],
                type=NodeType(node['type']),
                config=node.get('config', {}),
                position=node.get('position', {"x": 0, "y": 0}),
                input_variables=node.get('input_variables', []),
                output_variables=node.get('output_variables', []),
                retry_config=node.get('retry_config'),
                timeout=node.get('timeout'),
                enabled=node.get('enabled', True),
                metadata=node.get('metadata', {})
            )
            for node in nodes
        ]

        # Parse connections
        workflow_connections = [
            NodeConnection(
                id=conn.get('id', str(uuid.uuid4())),
                source_node_id=conn['source_node_id'],
                target_node_id=conn['target_node_id'],
                connection_type=ConnectionType(conn.get('connection_type', 'default')),
                condition=conn.get('condition'),
                label=conn.get('label')
            )
            for conn in connections
        ]

        workflow = WorkflowDefinition(
            id=workflow_id,
            name=name,
            description=description,
            nodes=workflow_nodes,
            connections=workflow_connections,
            variables=kwargs.get('variables', {}),
            environment_variables=kwargs.get('environment_variables', {}),
            settings=kwargs.get('settings', {}),
            tags=kwargs.get('tags', []),
            version=kwargs.get('version', 1),
            created_by=kwargs.get('created_by'),
            is_template=kwargs.get('is_template', False),
            is_active=kwargs.get('is_active', True)
        )

        self.workflows[workflow_id] = workflow
        return workflow

    def get_workflow(self, workflow_id: str) -> Optional[WorkflowDefinition]:
        """Get a workflow definition by ID"""
        return self.workflows.get(workflow_id)

    def update_workflow(self, workflow_id: str, **updates) -> WorkflowDefinition:
        """Update a workflow definition"""
        workflow = self.workflows.get(workflow_id)
        if not workflow:
            raise ValueError(f"Workflow {workflow_id} not found")

        for key, value in updates.items():
            if hasattr(workflow, key):
                setattr(workflow, key, value)

        workflow.updated_at = datetime.utcnow()
        workflow.version += 1
        return workflow

    def delete_workflow(self, workflow_id: str) -> bool:
        """Delete a workflow definition"""
        if workflow_id in self.workflows:
            del self.workflows[workflow_id]
            return True
        return False

    async def execute_workflow(
        self,
        workflow_id: str,
        trigger_data: Optional[Dict[str, Any]] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> WorkflowExecution:
        """Execute a workflow"""
        workflow = self.get_workflow(workflow_id)
        if not workflow:
            raise ValueError(f"Workflow {workflow_id} not found")

        if not workflow.is_active:
            raise ValueError(f"Workflow {workflow_id} is not active")

        execution_id = str(uuid.uuid4())
        execution = WorkflowExecution(
            id=execution_id,
            workflow_id=workflow_id,
            status=ExecutionStatus.RUNNING,
            trigger_data=trigger_data or {},
            context=context or {},
            variables={},
            node_executions={}
        )

        self.executions[execution_id] = execution

        try:
            # Initialize variables
            for var_name, var_value in workflow.variables.items():
                execution.variables[var_name] = WorkflowVariable(
                    name=var_name,
                    value=var_value,
                    type=type(var_value).__name__
                )

            # Add trigger data as variables
            if trigger_data:
                execution.variables['trigger'] = WorkflowVariable(
                    name='trigger',
                    value=trigger_data,
                    type='dict'
                )

            # Find trigger nodes (starting points)
            trigger_nodes = [n for n in workflow.nodes if n.type == NodeType.TRIGGER]

            if not trigger_nodes:
                raise ValueError("Workflow has no trigger nodes")

            # Execute workflow starting from trigger nodes
            for trigger_node in trigger_nodes:
                await self._execute_node(workflow, execution, trigger_node)

            # Mark as successful if no errors
            if execution.status == ExecutionStatus.RUNNING:
                execution.status = ExecutionStatus.SUCCESS

        except Exception as e:
            execution.status = ExecutionStatus.FAILED
            execution.error = str(e)
            raise

        finally:
            execution.completed_at = datetime.utcnow()
            if execution.started_at:
                delta = execution.completed_at - execution.started_at
                execution.duration_ms = delta.total_seconds() * 1000

        return execution

    async def _execute_node(
        self,
        workflow: WorkflowDefinition,
        execution: WorkflowExecution,
        node: WorkflowNode
    ) -> NodeExecution:
        """Execute a single workflow node"""
        if not node.enabled:
            return None

        node_exec = NodeExecution(
            node_id=node.id,
            execution_id=execution.id,
            status=ExecutionStatus.RUNNING,
            started_at=datetime.utcnow()
        )

        execution.node_executions[node.id] = node_exec

        try:
            # Prepare input data from variables
            input_data = {}
            for var_name in node.input_variables:
                if var_name in execution.variables:
                    input_data[var_name] = execution.variables[var_name].value

            node_exec.input_data = input_data

            # Execute node based on type
            handler = self.node_handlers.get(node.type)
            if handler:
                output_data = await handler(node, input_data, execution.context)
            else:
                output_data = await self._default_node_handler(node, input_data, execution.context)

            node_exec.output_data = output_data or {}
            node_exec.status = ExecutionStatus.SUCCESS

            # Store output variables
            if output_data:
                for var_name, var_value in output_data.items():
                    execution.variables[var_name] = WorkflowVariable(
                        name=var_name,
                        value=var_value,
                        type=type(var_value).__name__,
                        source_node=node.id
                    )

            # Execute next nodes
            next_nodes = self._get_next_nodes(workflow, node, node_exec)
            for next_node in next_nodes:
                await self._execute_node(workflow, execution, next_node)

        except Exception as e:
            node_exec.status = ExecutionStatus.FAILED
            node_exec.error = str(e)

            # Handle retry logic
            if node.retry_config and node_exec.retry_count < node.retry_config.get('max_retries', 0):
                node_exec.retry_count += 1
                node_exec.status = ExecutionStatus.RETRY
                await asyncio.sleep(node.retry_config.get('retry_delay', 1))
                return await self._execute_node(workflow, execution, node)

            execution.status = ExecutionStatus.FAILED
            raise

        finally:
            node_exec.completed_at = datetime.utcnow()
            if node_exec.started_at:
                delta = node_exec.completed_at - node_exec.started_at
                node_exec.duration_ms = delta.total_seconds() * 1000

        return node_exec

    def _get_next_nodes(
        self,
        workflow: WorkflowDefinition,
        current_node: WorkflowNode,
        node_execution: NodeExecution
    ) -> List[WorkflowNode]:
        """Get the next nodes to execute based on connections and conditions"""
        next_nodes = []

        for connection in workflow.connections:
            if connection.source_node_id != current_node.id:
                continue

            # Check connection type
            if connection.connection_type == ConnectionType.SUCCESS and node_execution.status != ExecutionStatus.SUCCESS:
                continue
            if connection.connection_type == ConnectionType.FAILURE and node_execution.status != ExecutionStatus.FAILED:
                continue

            # Check condition if present
            if connection.condition:
                if not self._evaluate_condition(connection.condition, node_execution.output_data):
                    continue

            # Find target node
            target_node = next(
                (n for n in workflow.nodes if n.id == connection.target_node_id),
                None
            )
            if target_node:
                next_nodes.append(target_node)

        return next_nodes

    def _evaluate_condition(self, condition: str, context: Dict[str, Any]) -> bool:
        """Evaluate a condition expression"""
        try:
            # Simple evaluation - in production, use a safe expression evaluator
            # This is a placeholder - should use something like simpleeval or custom parser
            return eval(condition, {"__builtins__": {}}, context)
        except Exception:
            return False

    async def _default_node_handler(
        self,
        node: WorkflowNode,
        input_data: Dict[str, Any],
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Default handler for nodes without specific handlers"""
        return {"result": "Node executed", "node_id": node.id}

    def get_execution(self, execution_id: str) -> Optional[WorkflowExecution]:
        """Get execution by ID"""
        return self.executions.get(execution_id)

    def list_executions(
        self,
        workflow_id: Optional[str] = None,
        status: Optional[ExecutionStatus] = None,
        limit: int = 100
    ) -> List[WorkflowExecution]:
        """List workflow executions with optional filters"""
        executions = list(self.executions.values())

        if workflow_id:
            executions = [e for e in executions if e.workflow_id == workflow_id]

        if status:
            executions = [e for e in executions if e.status == status]

        # Sort by started_at descending
        executions.sort(key=lambda e: e.started_at, reverse=True)

        return executions[:limit]

    async def cancel_execution(self, execution_id: str) -> bool:
        """Cancel a running execution"""
        execution = self.executions.get(execution_id)
        if not execution:
            return False

        if execution.status == ExecutionStatus.RUNNING:
            execution.status = ExecutionStatus.CANCELLED
            execution.completed_at = datetime.utcnow()

            # Cancel async task if exists
            if execution_id in self.active_executions:
                self.active_executions[execution_id].cancel()
                del self.active_executions[execution_id]

            return True

        return False

    def export_workflow(self, workflow_id: str) -> str:
        """Export workflow as JSON"""
        workflow = self.get_workflow(workflow_id)
        if not workflow:
            raise ValueError(f"Workflow {workflow_id} not found")

        workflow_dict = {
            "id": workflow.id,
            "name": workflow.name,
            "description": workflow.description,
            "nodes": [
                {
                    "id": n.id,
                    "name": n.name,
                    "type": n.type.value,
                    "config": n.config,
                    "position": n.position,
                    "input_variables": n.input_variables,
                    "output_variables": n.output_variables,
                    "retry_config": n.retry_config,
                    "timeout": n.timeout,
                    "enabled": n.enabled,
                    "metadata": n.metadata
                }
                for n in workflow.nodes
            ],
            "connections": [
                {
                    "id": c.id,
                    "source_node_id": c.source_node_id,
                    "target_node_id": c.target_node_id,
                    "connection_type": c.connection_type.value,
                    "condition": c.condition,
                    "label": c.label
                }
                for c in workflow.connections
            ],
            "variables": workflow.variables,
            "environment_variables": workflow.environment_variables,
            "settings": workflow.settings,
            "tags": workflow.tags,
            "version": workflow.version
        }

        return json.dumps(workflow_dict, indent=2, default=str)

    def import_workflow(self, workflow_json: str) -> WorkflowDefinition:
        """Import workflow from JSON"""
        data = json.loads(workflow_json)

        return self.create_workflow(
            name=data['name'],
            description=data['description'],
            nodes=data['nodes'],
            connections=data['connections'],
            id=data.get('id'),
            variables=data.get('variables', {}),
            environment_variables=data.get('environment_variables', {}),
            settings=data.get('settings', {}),
            tags=data.get('tags', []),
            version=data.get('version', 1)
        )


# Global workflow engine instance
workflow_engine = WorkflowEngine()
