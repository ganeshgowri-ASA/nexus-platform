"""
RPA Automation Engine - Core execution engine
"""
from typing import Dict, Any, List, Optional
from datetime import datetime
import asyncio
from sqlalchemy.orm import Session

from src.database.models import (
    Automation,
    AutomationExecution,
    ExecutionStatus,
    AuditLog,
)
from src.utils.logger import get_logger
from src.utils.helpers import generate_id, current_timestamp
from src.modules.rpa.actions import ActionExecutor

logger = get_logger(__name__)


class AutomationEngine:
    """Main automation execution engine"""

    def __init__(self, db: Session):
        self.db = db
        self.action_executor = ActionExecutor()

    async def execute(
        self,
        automation: Automation,
        execution_id: str,
        input_data: Dict[str, Any],
        triggered_by: str,
    ) -> AutomationExecution:
        """
        Execute an automation workflow

        Args:
            automation: Automation object to execute
            execution_id: Unique execution ID
            input_data: Input data for the execution
            triggered_by: User/system that triggered the execution

        Returns:
            AutomationExecution object with results
        """
        logger.info(
            f"Starting execution {execution_id} for automation {automation.name}"
        )

        # Get execution from database
        execution = (
            self.db.query(AutomationExecution)
            .filter(AutomationExecution.id == execution_id)
            .first()
        )

        try:
            # Update execution status to running
            execution.status = ExecutionStatus.RUNNING
            execution.started_at = current_timestamp()
            self.db.commit()

            # Initialize execution context
            context = {
                "variables": {**automation.variables, **input_data},
                "input": input_data,
                "output": {},
                "logs": [],
            }

            # Parse and validate workflow
            workflow = automation.workflow
            nodes = workflow.get("nodes", [])
            edges = workflow.get("edges", [])

            # Build execution graph
            execution_graph = self._build_execution_graph(nodes, edges)

            # Execute workflow
            await self._execute_workflow(
                execution_graph, nodes, context, execution.id
            )

            # Update execution with success
            execution.status = ExecutionStatus.SUCCESS
            execution.output_data = context["output"]
            execution.variables = context["variables"]
            execution.logs = context["logs"]
            execution.completed_at = current_timestamp()
            execution.duration = int(
                (execution.completed_at - execution.started_at).total_seconds()
            )

            logger.info(f"Execution {execution_id} completed successfully")

        except Exception as e:
            logger.error(f"Execution {execution_id} failed: {str(e)}", exc_info=True)

            # Update execution with failure
            execution.status = ExecutionStatus.FAILED
            execution.error_message = str(e)
            execution.error_details = {"type": type(e).__name__, "message": str(e)}
            execution.completed_at = current_timestamp()
            if execution.started_at:
                execution.duration = int(
                    (execution.completed_at - execution.started_at).total_seconds()
                )

        finally:
            self.db.commit()
            self._create_audit_log(
                execution_id=execution.id,
                automation_id=automation.id,
                action="execution_completed",
                details={
                    "status": execution.status.value,
                    "duration": execution.duration,
                },
                user_id=triggered_by,
            )

        return execution

    def _build_execution_graph(
        self, nodes: List[Dict], edges: List[Dict]
    ) -> Dict[str, List[str]]:
        """Build execution graph from nodes and edges"""
        graph = {node["id"]: [] for node in nodes}

        for edge in edges:
            source = edge["source"]
            target = edge["target"]
            if source in graph:
                graph[source].append(target)

        return graph

    async def _execute_workflow(
        self,
        graph: Dict[str, List[str]],
        nodes: List[Dict],
        context: Dict[str, Any],
        execution_id: str,
    ):
        """Execute workflow nodes in order"""
        # Create node map
        node_map = {node["id"]: node for node in nodes}

        # Find start node(s)
        all_targets = set()
        for targets in graph.values():
            all_targets.update(targets)

        start_nodes = [node_id for node_id in graph.keys() if node_id not in all_targets]

        # Execute nodes
        visited = set()
        for start_node in start_nodes:
            await self._execute_node_recursive(
                start_node, node_map, graph, context, visited, execution_id
            )

    async def _execute_node_recursive(
        self,
        node_id: str,
        node_map: Dict[str, Dict],
        graph: Dict[str, List[str]],
        context: Dict[str, Any],
        visited: set,
        execution_id: str,
    ):
        """Recursively execute nodes"""
        if node_id in visited:
            return

        visited.add(node_id)
        node = node_map.get(node_id)

        if not node:
            return

        # Execute the node
        logger.info(f"Executing node: {node['name']} ({node['type']})")
        context["logs"].append(
            {
                "timestamp": datetime.utcnow().isoformat(),
                "level": "INFO",
                "message": f"Executing node: {node['name']}",
                "node_id": node_id,
            }
        )

        try:
            # Execute action
            await self.action_executor.execute_action(
                node["type"], node.get("config", {}), context
            )

            context["logs"].append(
                {
                    "timestamp": datetime.utcnow().isoformat(),
                    "level": "INFO",
                    "message": f"Node {node['name']} completed successfully",
                    "node_id": node_id,
                }
            )

        except Exception as e:
            logger.error(f"Error executing node {node_id}: {str(e)}")
            context["logs"].append(
                {
                    "timestamp": datetime.utcnow().isoformat(),
                    "level": "ERROR",
                    "message": f"Node {node['name']} failed: {str(e)}",
                    "node_id": node_id,
                }
            )
            raise

        # Execute next nodes
        next_nodes = graph.get(node_id, [])
        for next_node_id in next_nodes:
            await self._execute_node_recursive(
                next_node_id, node_map, graph, context, visited, execution_id
            )

    def _create_audit_log(
        self,
        execution_id: str,
        automation_id: str,
        action: str,
        details: Dict[str, Any],
        user_id: str,
    ):
        """Create an audit log entry"""
        audit_log = AuditLog(
            id=generate_id(),
            execution_id=execution_id,
            automation_id=automation_id,
            action=action,
            entity_type="execution",
            entity_id=execution_id,
            details=details,
            user_id=user_id,
            timestamp=current_timestamp(),
        )
        self.db.add(audit_log)
        self.db.commit()
