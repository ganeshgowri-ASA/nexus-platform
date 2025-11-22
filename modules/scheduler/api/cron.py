"""Cron validation and utilities API"""
from fastapi import APIRouter
from modules.scheduler.models.pydantic_models import CronValidationRequest, CronValidationResponse
from modules.scheduler.utils.cron_utils import validate_cron_expression, get_next_run_times

router = APIRouter(prefix="/cron", tags=["cron"])


@router.post("/validate", response_model=CronValidationResponse)
async def validate_cron(request: CronValidationRequest):
    """Validate a cron expression and get next run times"""
    is_valid, description, error = validate_cron_expression(request.expression)

    next_runs = []
    if is_valid:
        next_runs = get_next_run_times(
            request.expression,
            count=5,
            timezone=request.timezone
        )

    return CronValidationResponse(
        is_valid=is_valid,
        description=description,
        next_runs=next_runs,
        error=error
    )


@router.get("/presets")
async def get_cron_presets():
    """Get common cron expression presets"""
    presets = {
        "every_minute": {
            "expression": "* * * * *",
            "description": "Every minute"
        },
        "every_5_minutes": {
            "expression": "*/5 * * * *",
            "description": "Every 5 minutes"
        },
        "every_15_minutes": {
            "expression": "*/15 * * * *",
            "description": "Every 15 minutes"
        },
        "every_30_minutes": {
            "expression": "*/30 * * * *",
            "description": "Every 30 minutes"
        },
        "hourly": {
            "expression": "0 * * * *",
            "description": "Every hour"
        },
        "daily_midnight": {
            "expression": "0 0 * * *",
            "description": "Daily at midnight"
        },
        "daily_noon": {
            "expression": "0 12 * * *",
            "description": "Daily at noon"
        },
        "weekly_sunday": {
            "expression": "0 0 * * 0",
            "description": "Weekly on Sunday at midnight"
        },
        "weekly_monday": {
            "expression": "0 0 * * 1",
            "description": "Weekly on Monday at midnight"
        },
        "monthly": {
            "expression": "0 0 1 * *",
            "description": "Monthly on the 1st at midnight"
        },
        "yearly": {
            "expression": "0 0 1 1 *",
            "description": "Yearly on January 1st at midnight"
        },
        "weekdays_9am": {
            "expression": "0 9 * * 1-5",
            "description": "Weekdays at 9 AM"
        },
        "weekends_10am": {
            "expression": "0 10 * * 0,6",
            "description": "Weekends at 10 AM"
        }
    }
    return presets
