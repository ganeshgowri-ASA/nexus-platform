"""
Celery task queue for asynchronous RPA execution
"""
from celery import Celery
from celery.schedules import crontab
import asyncio

from src.config.settings import settings
from src.config.database import SessionLocal
from src.database.models import Automation
from src.modules.rpa.engine import AutomationEngine
from src.modules.rpa.scheduler import AutomationScheduler
from src.modules.rpa.execution_manager import ExecutionManager
from src.utils.logger import get_logger

logger = get_logger(__name__)

# Create Celery app
celery_app = Celery(
    "nexus-rpa",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
)

# Configure Celery
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=settings.RPA_MAX_EXECUTION_TIME,
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=1000,
)


@celery_app.task(name="execute_automation")
def execute_automation_task(
    automation_id: str,
    execution_id: str,
    input_data: dict,
    triggered_by: str,
):
    """
    Execute an automation workflow

    Args:
        automation_id: ID of the automation to execute
        execution_id: ID of the execution record
        input_data: Input data for the automation
        triggered_by: User/system that triggered the execution
    """
    logger.info(f"Starting automation execution: {automation_id}")

    db = SessionLocal()
    try:
        # Get automation
        automation = (
            db.query(Automation).filter(Automation.id == automation_id).first()
        )

        if not automation:
            logger.error(f"Automation not found: {automation_id}")
            return {"success": False, "error": "Automation not found"}

        # Create engine and execute
        engine = AutomationEngine(db)

        # Run async execution in sync context
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        execution = loop.run_until_complete(
            engine.execute(automation, execution_id, input_data, triggered_by)
        )

        loop.close()

        logger.info(
            f"Automation execution completed: {execution_id} with status {execution.status}"
        )

        return {
            "success": True,
            "execution_id": execution.id,
            "status": execution.status.value,
        }

    except Exception as e:
        logger.error(f"Automation execution failed: {str(e)}", exc_info=True)

        # Update execution with error
        exec_manager = ExecutionManager(db)
        try:
            from src.database.models import ExecutionStatus

            exec_manager.update_execution_status(
                execution_id, ExecutionStatus.FAILED, str(e)
            )
        except Exception:
            pass

        return {"success": False, "error": str(e)}

    finally:
        db.close()


@celery_app.task(name="check_scheduled_automations")
def check_scheduled_automations():
    """
    Check for scheduled automations that are due to run
    This task runs periodically via Celery Beat
    """
    logger.info("Checking for scheduled automations...")

    db = SessionLocal()
    try:
        scheduler = AutomationScheduler(db)
        due_schedules = scheduler.get_due_schedules()

        logger.info(f"Found {len(due_schedules)} due schedules")

        for schedule in due_schedules:
            logger.info(
                f"Executing scheduled automation: {schedule.automation_id}"
            )

            # Create execution
            exec_manager = ExecutionManager(db)
            from src.database.models import TriggerType

            execution = exec_manager.create_execution(
                automation_id=schedule.automation_id,
                trigger_type=TriggerType.SCHEDULED,
                input_data=schedule.input_data,
                triggered_by=f"schedule:{schedule.id}",
            )

            # Queue execution
            execute_automation_task.delay(
                schedule.automation_id,
                execution.id,
                schedule.input_data,
                f"schedule:{schedule.id}",
            )

            # Mark schedule as executed
            scheduler.mark_schedule_executed(schedule.id)

        return {
            "success": True,
            "scheduled_count": len(due_schedules),
        }

    except Exception as e:
        logger.error(
            f"Failed to check scheduled automations: {str(e)}", exc_info=True
        )
        return {"success": False, "error": str(e)}

    finally:
        db.close()


@celery_app.task(name="cleanup_old_executions")
def cleanup_old_executions(days: int = 90):
    """
    Clean up old execution records

    Args:
        days: Number of days to keep
    """
    logger.info(f"Cleaning up executions older than {days} days...")

    db = SessionLocal()
    try:
        from datetime import datetime, timedelta
        from src.database.models import AutomationExecution

        cutoff_date = datetime.utcnow() - timedelta(days=days)

        deleted = (
            db.query(AutomationExecution)
            .filter(AutomationExecution.created_at < cutoff_date)
            .delete()
        )

        db.commit()

        logger.info(f"Cleaned up {deleted} old execution records")

        return {"success": True, "deleted_count": deleted}

    except Exception as e:
        logger.error(f"Failed to cleanup executions: {str(e)}", exc_info=True)
        db.rollback()
        return {"success": False, "error": str(e)}

    finally:
        db.close()


@celery_app.task(name="cleanup_old_audit_logs")
def cleanup_old_audit_logs(days: int = 90):
    """
    Clean up old audit logs

    Args:
        days: Number of days to keep
    """
    logger.info(f"Cleaning up audit logs older than {days} days...")

    db = SessionLocal()
    try:
        from src.modules.rpa.audit import AuditLogger

        audit = AuditLogger(db)
        deleted = audit.cleanup_old_logs(days)

        logger.info(f"Cleaned up {deleted} old audit log records")

        return {"success": True, "deleted_count": deleted}

    except Exception as e:
        logger.error(f"Failed to cleanup audit logs: {str(e)}", exc_info=True)
        return {"success": False, "error": str(e)}

    finally:
        db.close()


# Configure Celery Beat schedule
celery_app.conf.beat_schedule = {
    "check-scheduled-automations": {
        "task": "check_scheduled_automations",
        "schedule": 60.0,  # Check every minute
    },
    "cleanup-old-executions": {
        "task": "cleanup_old_executions",
        "schedule": crontab(hour=2, minute=0),  # Run at 2 AM daily
        "kwargs": {"days": 90},
    },
    "cleanup-old-audit-logs": {
        "task": "cleanup_old_audit_logs",
        "schedule": crontab(hour=3, minute=0),  # Run at 3 AM daily
        "kwargs": {"days": 90},
    },
}
