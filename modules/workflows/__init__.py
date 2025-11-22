"""
NEXUS Workflow Automation Engine
A comprehensive workflow automation system that rivals Zapier, Make, and n8n
"""

from .engine import (
    workflow_engine,
    WorkflowEngine,
    WorkflowDefinition,
    WorkflowNode,
    NodeConnection,
    WorkflowExecution,
    NodeType,
    ExecutionStatus
)

from .triggers import (
    trigger_manager,
    TriggerManager,
    BaseTrigger,
    TriggerType,
    TriggerConfig,
    WebhookTrigger,
    ScheduleTrigger,
    EmailTrigger
)

from .actions import (
    action_executor,
    ActionExecutor,
    ActionType,
    ActionResult,
    BaseAction
)

from .conditions import (
    condition_evaluator,
    data_filter,
    loop_controller,
    branch_controller,
    ConditionEvaluator,
    DataFilter,
    ConditionType
)

from .scheduler import (
    workflow_scheduler,
    WorkflowScheduler,
    Schedule,
    ScheduleType,
    CronParser
)

from .integrations import (
    integration_registry,
    IntegrationRegistry,
    IntegrationCategory,
    BaseIntegration
)

from .templates import (
    template_library,
    TemplateLibrary,
    WorkflowTemplate,
    TemplateCategory
)

from .monitoring import (
    workflow_monitor,
    WorkflowMonitor,
    WorkflowLogger,
    MetricsCollector,
    ErrorHandler,
    AlertManager
)

__version__ = "1.0.0"
__author__ = "NEXUS Platform"

__all__ = [
    # Engine
    "workflow_engine",
    "WorkflowEngine",
    "WorkflowDefinition",
    "WorkflowNode",
    "NodeConnection",
    "WorkflowExecution",
    "NodeType",
    "ExecutionStatus",

    # Triggers
    "trigger_manager",
    "TriggerManager",
    "BaseTrigger",
    "TriggerType",
    "TriggerConfig",

    # Actions
    "action_executor",
    "ActionExecutor",
    "ActionType",
    "ActionResult",

    # Conditions
    "condition_evaluator",
    "data_filter",
    "ConditionEvaluator",
    "DataFilter",
    "ConditionType",

    # Scheduler
    "workflow_scheduler",
    "WorkflowScheduler",
    "Schedule",
    "ScheduleType",

    # Integrations
    "integration_registry",
    "IntegrationRegistry",
    "IntegrationCategory",

    # Templates
    "template_library",
    "TemplateLibrary",
    "WorkflowTemplate",
    "TemplateCategory",

    # Monitoring
    "workflow_monitor",
    "WorkflowMonitor",
]
