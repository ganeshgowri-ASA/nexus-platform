"""
FastAPI routes for RPA module
"""
from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Optional

from src.config.database import get_db
from src.database.models import (
    Automation,
    AutomationExecution,
    Bot,
    Schedule,
    AutomationStatus,
    ExecutionStatus,
    TriggerType,
)
from src.modules.rpa import schemas
from src.modules.rpa.execution_manager import ExecutionManager
from src.modules.rpa.scheduler import AutomationScheduler
from src.modules.rpa.audit import AuditLogger
from src.utils.helpers import generate_id
from src.utils.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/api/v1/rpa", tags=["RPA"])


# ============= Bot Routes =============
@router.post("/bots", response_model=schemas.BotResponse)
def create_bot(bot: schemas.BotCreate, db: Session = Depends(get_db)):
    """Create a new bot"""
    # Check if bot with name already exists
    existing = db.query(Bot).filter(Bot.name == bot.name).first()
    if existing:
        raise HTTPException(status_code=400, detail="Bot with this name already exists")

    db_bot = Bot(
        id=generate_id(),
        **bot.model_dump(),
        status=AutomationStatus.ACTIVE,
    )

    db.add(db_bot)
    db.commit()
    db.refresh(db_bot)

    # Audit log
    audit = AuditLogger(db)
    audit.log(
        action="create",
        entity_type="bot",
        entity_id=db_bot.id,
        user_id=bot.created_by,
        details={"name": bot.name},
    )

    return db_bot


@router.get("/bots", response_model=List[schemas.BotResponse])
def list_bots(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    status: Optional[AutomationStatus] = None,
    db: Session = Depends(get_db),
):
    """List all bots"""
    query = db.query(Bot)

    if status:
        query = query.filter(Bot.status == status)

    bots = query.offset(skip).limit(limit).all()
    return bots


@router.get("/bots/{bot_id}", response_model=schemas.BotResponse)
def get_bot(bot_id: str, db: Session = Depends(get_db)):
    """Get bot by ID"""
    bot = db.query(Bot).filter(Bot.id == bot_id).first()
    if not bot:
        raise HTTPException(status_code=404, detail="Bot not found")
    return bot


@router.put("/bots/{bot_id}", response_model=schemas.BotResponse)
def update_bot(
    bot_id: str, bot_update: schemas.BotUpdate, db: Session = Depends(get_db)
):
    """Update bot"""
    bot = db.query(Bot).filter(Bot.id == bot_id).first()
    if not bot:
        raise HTTPException(status_code=404, detail="Bot not found")

    update_data = bot_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(bot, field, value)

    db.commit()
    db.refresh(bot)

    return bot


@router.delete("/bots/{bot_id}")
def delete_bot(bot_id: str, db: Session = Depends(get_db)):
    """Delete bot"""
    bot = db.query(Bot).filter(Bot.id == bot_id).first()
    if not bot:
        raise HTTPException(status_code=404, detail="Bot not found")

    db.delete(bot)
    db.commit()

    return {"message": "Bot deleted successfully"}


# ============= Automation Routes =============
@router.post("/automations", response_model=schemas.AutomationResponse)
def create_automation(
    automation: schemas.AutomationCreate, db: Session = Depends(get_db)
):
    """Create a new automation"""
    # Check if automation with name already exists
    existing = (
        db.query(Automation).filter(Automation.name == automation.name).first()
    )
    if existing:
        raise HTTPException(
            status_code=400, detail="Automation with this name already exists"
        )

    db_automation = Automation(
        id=generate_id(),
        **automation.model_dump(),
        status=AutomationStatus.DRAFT,
    )

    db.add(db_automation)
    db.commit()
    db.refresh(db_automation)

    # Audit log
    audit = AuditLogger(db)
    audit.log(
        action="create",
        entity_type="automation",
        entity_id=db_automation.id,
        automation_id=db_automation.id,
        user_id=automation.created_by,
        details={"name": automation.name},
    )

    return db_automation


@router.get("/automations", response_model=List[schemas.AutomationResponse])
def list_automations(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    status: Optional[AutomationStatus] = None,
    bot_id: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """List all automations"""
    query = db.query(Automation)

    if status:
        query = query.filter(Automation.status == status)

    if bot_id:
        query = query.filter(Automation.bot_id == bot_id)

    automations = query.offset(skip).limit(limit).all()
    return automations


@router.get("/automations/{automation_id}", response_model=schemas.AutomationResponse)
def get_automation(automation_id: str, db: Session = Depends(get_db)):
    """Get automation by ID"""
    automation = (
        db.query(Automation).filter(Automation.id == automation_id).first()
    )
    if not automation:
        raise HTTPException(status_code=404, detail="Automation not found")
    return automation


@router.put("/automations/{automation_id}", response_model=schemas.AutomationResponse)
def update_automation(
    automation_id: str,
    automation_update: schemas.AutomationUpdate,
    db: Session = Depends(get_db),
):
    """Update automation"""
    automation = (
        db.query(Automation).filter(Automation.id == automation_id).first()
    )
    if not automation:
        raise HTTPException(status_code=404, detail="Automation not found")

    update_data = automation_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(automation, field, value)

    db.commit()
    db.refresh(automation)

    return automation


@router.delete("/automations/{automation_id}")
def delete_automation(automation_id: str, db: Session = Depends(get_db)):
    """Delete automation"""
    automation = (
        db.query(Automation).filter(Automation.id == automation_id).first()
    )
    if not automation:
        raise HTTPException(status_code=404, detail="Automation not found")

    db.delete(automation)
    db.commit()

    return {"message": "Automation deleted successfully"}


# ============= Execution Routes =============
@router.post("/automations/{automation_id}/execute", response_model=schemas.ExecutionResponse)
def execute_automation(
    automation_id: str,
    execution_data: schemas.ExecutionCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    """Execute an automation"""
    automation = (
        db.query(Automation).filter(Automation.id == automation_id).first()
    )
    if not automation:
        raise HTTPException(status_code=404, detail="Automation not found")

    if automation.status != AutomationStatus.ACTIVE:
        raise HTTPException(
            status_code=400, detail="Automation is not active"
        )

    # Create execution record
    exec_manager = ExecutionManager(db)
    execution = exec_manager.create_execution(
        automation_id=automation_id,
        trigger_type=execution_data.trigger_type,
        input_data=execution_data.input_data,
        triggered_by=execution_data.triggered_by,
    )

    # Queue execution as background task
    from src.services.task_queue import execute_automation_task

    background_tasks.add_task(
        execute_automation_task,
        automation_id,
        execution.id,
        execution_data.input_data,
        execution_data.triggered_by,
    )

    return execution


@router.get("/executions", response_model=List[schemas.ExecutionResponse])
def list_executions(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    automation_id: Optional[str] = None,
    status: Optional[ExecutionStatus] = None,
    db: Session = Depends(get_db),
):
    """List executions"""
    exec_manager = ExecutionManager(db)
    executions = exec_manager.list_executions(
        automation_id=automation_id, status=status, skip=skip, limit=limit
    )
    return executions


@router.get("/executions/{execution_id}", response_model=schemas.ExecutionResponse)
def get_execution(execution_id: str, db: Session = Depends(get_db)):
    """Get execution by ID"""
    exec_manager = ExecutionManager(db)
    execution = exec_manager.get_execution(execution_id)
    if not execution:
        raise HTTPException(status_code=404, detail="Execution not found")
    return execution


@router.post("/executions/{execution_id}/cancel")
def cancel_execution(execution_id: str, db: Session = Depends(get_db)):
    """Cancel a running execution"""
    exec_manager = ExecutionManager(db)
    try:
        execution = exec_manager.cancel_execution(execution_id)
        return {"message": "Execution cancelled", "execution": execution}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/executions/{execution_id}/logs")
def get_execution_logs(execution_id: str, db: Session = Depends(get_db)):
    """Get execution logs"""
    exec_manager = ExecutionManager(db)
    try:
        logs = exec_manager.get_execution_logs(execution_id)
        return {"logs": logs}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


# ============= Schedule Routes =============
@router.post("/schedules", response_model=schemas.ScheduleResponse)
def create_schedule(
    schedule: schemas.ScheduleCreate, db: Session = Depends(get_db)
):
    """Create a new schedule"""
    scheduler = AutomationScheduler(db)
    try:
        db_schedule = scheduler.create_schedule(
            automation_id=schedule.automation_id,
            name=schedule.name,
            cron_expression=schedule.cron_expression,
            timezone=schedule.timezone,
            input_data=schedule.input_data,
            created_by=schedule.created_by,
        )
        return db_schedule
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/schedules", response_model=List[schemas.ScheduleResponse])
def list_schedules(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    automation_id: Optional[str] = None,
    is_active: Optional[bool] = None,
    db: Session = Depends(get_db),
):
    """List schedules"""
    scheduler = AutomationScheduler(db)
    schedules = scheduler.list_schedules(
        automation_id=automation_id, is_active=is_active, skip=skip, limit=limit
    )
    return schedules


@router.get("/schedules/{schedule_id}", response_model=schemas.ScheduleResponse)
def get_schedule(schedule_id: str, db: Session = Depends(get_db)):
    """Get schedule by ID"""
    scheduler = AutomationScheduler(db)
    schedule = scheduler.get_schedule(schedule_id)
    if not schedule:
        raise HTTPException(status_code=404, detail="Schedule not found")
    return schedule


@router.put("/schedules/{schedule_id}", response_model=schemas.ScheduleResponse)
def update_schedule(
    schedule_id: str,
    schedule_update: schemas.ScheduleUpdate,
    db: Session = Depends(get_db),
):
    """Update schedule"""
    scheduler = AutomationScheduler(db)
    try:
        schedule = scheduler.update_schedule(
            schedule_id, **schedule_update.model_dump(exclude_unset=True)
        )
        return schedule
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.delete("/schedules/{schedule_id}")
def delete_schedule(schedule_id: str, db: Session = Depends(get_db)):
    """Delete schedule"""
    scheduler = AutomationScheduler(db)
    success = scheduler.delete_schedule(schedule_id)
    if not success:
        raise HTTPException(status_code=404, detail="Schedule not found")
    return {"message": "Schedule deleted successfully"}


# ============= Statistics Routes =============
@router.get("/statistics/executions")
def get_execution_statistics(
    automation_id: Optional[str] = None, db: Session = Depends(get_db)
):
    """Get execution statistics"""
    exec_manager = ExecutionManager(db)
    stats = exec_manager.get_execution_statistics(automation_id)
    return stats


@router.get("/statistics/audit")
def get_audit_statistics(
    entity_type: Optional[str] = None, db: Session = Depends(get_db)
):
    """Get audit log statistics"""
    audit = AuditLogger(db)
    stats = audit.get_statistics(entity_type=entity_type)
    return stats
