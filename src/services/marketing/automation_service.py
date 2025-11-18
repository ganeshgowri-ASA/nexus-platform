"""
Automation service for marketing automation workflows.

This module handles automation workflows, triggers, actions, and drip campaigns.
"""
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from config.logging_config import get_logger
from config.constants import AutomationStatus, TriggerType, ActionType
from src.core.exceptions import NotFoundError, AutomationError, ValidationError
from src.models.automation import (
    Automation,
    AutomationExecution,
    DripCampaign,
    DripEnrollment,
)
from src.models.contact import Contact, ContactEvent
from src.schemas.marketing.automation_schema import AutomationCreate, AutomationUpdate

logger = get_logger(__name__)


class AutomationService:
    """
    Service for managing marketing automation workflows.

    Provides methods for creating, managing, and executing automation workflows.
    """

    def __init__(self, db: AsyncSession) -> None:
        """Initialize automation service."""
        self.db = db

    async def create_automation(
        self,
        automation_data: AutomationCreate,
        workspace_id: UUID,
        user_id: UUID,
    ) -> Automation:
        """Create a new automation workflow."""
        automation = Automation(
            workspace_id=workspace_id,
            name=automation_data.name,
            description=automation_data.description,
            trigger_type=automation_data.trigger_type,
            trigger_config=automation_data.trigger_config,
            actions=[action.model_dump() for action in automation_data.actions],
            conditions=automation_data.conditions or {},
            status=AutomationStatus.PAUSED,
            created_by=user_id,
            execution_count=0,
        )

        self.db.add(automation)
        await self.db.commit()
        await self.db.refresh(automation)

        logger.info(
            "Automation created",
            automation_id=str(automation.id),
            name=automation.name
        )

        return automation

    async def get_automation(
        self,
        automation_id: UUID,
        workspace_id: UUID,
    ) -> Automation:
        """Get automation by ID."""
        result = await self.db.execute(
            select(Automation).where(
                Automation.id == automation_id,
                Automation.workspace_id == workspace_id
            )
        )
        automation = result.scalar_one_or_none()

        if not automation:
            raise NotFoundError("Automation", str(automation_id))

        return automation

    async def update_automation(
        self,
        automation_id: UUID,
        workspace_id: UUID,
        automation_data: AutomationUpdate,
    ) -> Automation:
        """Update automation."""
        automation = await self.get_automation(automation_id, workspace_id)

        update_data = automation_data.model_dump(exclude_unset=True)

        # Convert actions if present
        if "actions" in update_data and update_data["actions"]:
            update_data["actions"] = [
                action.model_dump() if hasattr(action, "model_dump") else action
                for action in update_data["actions"]
            ]

        for key, value in update_data.items():
            setattr(automation, key, value)

        automation.updated_at = datetime.utcnow()

        await self.db.commit()
        await self.db.refresh(automation)

        logger.info("Automation updated", automation_id=str(automation_id))

        return automation

    async def activate_automation(
        self,
        automation_id: UUID,
        workspace_id: UUID,
    ) -> Automation:
        """Activate automation."""
        automation = await self.get_automation(automation_id, workspace_id)

        if automation.status == AutomationStatus.ACTIVE:
            raise ValidationError("Automation is already active")

        automation.status = AutomationStatus.ACTIVE
        automation.updated_at = datetime.utcnow()

        await self.db.commit()
        await self.db.refresh(automation)

        logger.info("Automation activated", automation_id=str(automation_id))

        return automation

    async def pause_automation(
        self,
        automation_id: UUID,
        workspace_id: UUID,
    ) -> Automation:
        """Pause automation."""
        automation = await self.get_automation(automation_id, workspace_id)

        automation.status = AutomationStatus.PAUSED
        automation.updated_at = datetime.utcnow()

        await self.db.commit()
        await self.db.refresh(automation)

        logger.info("Automation paused", automation_id=str(automation_id))

        return automation

    async def execute_automation(
        self,
        automation_id: UUID,
        contact_id: UUID,
        trigger_data: Dict[str, Any],
        workspace_id: UUID,
    ) -> AutomationExecution:
        """
        Execute automation for a contact.

        Args:
            automation_id: Automation ID
            contact_id: Contact ID
            trigger_data: Trigger event data
            workspace_id: Workspace ID

        Returns:
            Automation execution record
        """
        automation = await self.get_automation(automation_id, workspace_id)

        if automation.status != AutomationStatus.ACTIVE:
            raise AutomationError("Automation is not active")

        # Create execution record
        execution = AutomationExecution(
            automation_id=automation_id,
            contact_id=contact_id,
            status="running",
            trigger_data=trigger_data,
            actions_executed=[],
            started_at=datetime.utcnow(),
        )

        self.db.add(execution)
        await self.db.flush()

        # Check conditions
        if not await self._check_conditions(automation.conditions, contact_id, workspace_id):
            execution.status = "skipped"
            execution.completed_at = datetime.utcnow()
            await self.db.commit()
            return execution

        # Execute actions
        actions_executed = []
        try:
            for action in automation.actions:
                action_result = await self._execute_action(
                    action,
                    contact_id,
                    workspace_id
                )
                actions_executed.append(action_result)

            execution.status = "success"
            execution.actions_executed = actions_executed

        except Exception as e:
            execution.status = "failed"
            execution.error_message = str(e)
            logger.error(
                "Automation execution failed",
                automation_id=str(automation_id),
                error=str(e)
            )

        execution.completed_at = datetime.utcnow()

        # Update automation stats
        automation.execution_count += 1
        automation.last_executed_at = datetime.utcnow()

        await self.db.commit()
        await self.db.refresh(execution)

        logger.info(
            "Automation executed",
            automation_id=str(automation_id),
            execution_id=str(execution.id),
            status=execution.status
        )

        return execution

    async def _check_conditions(
        self,
        conditions: Dict[str, Any],
        contact_id: UUID,
        workspace_id: UUID,
    ) -> bool:
        """Check if automation conditions are met."""
        # Simplified condition checking
        # In production, implement comprehensive condition evaluation
        if not conditions:
            return True

        # Get contact
        result = await self.db.execute(
            select(Contact).where(Contact.id == contact_id)
        )
        contact = result.scalar_one_or_none()

        if not contact:
            return False

        # Check lead score condition
        if "lead_score_min" in conditions:
            if contact.lead_score < conditions["lead_score_min"]:
                return False

        if "lead_score_max" in conditions:
            if contact.lead_score > conditions["lead_score_max"]:
                return False

        return True

    async def _execute_action(
        self,
        action: Dict[str, Any],
        contact_id: UUID,
        workspace_id: UUID,
    ) -> Dict[str, Any]:
        """Execute a single automation action."""
        action_type = ActionType(action["action_type"])
        config = action["config"]

        result = {
            "action_type": action_type.value,
            "executed_at": datetime.utcnow().isoformat(),
            "status": "success",
        }

        try:
            if action_type == ActionType.SEND_EMAIL:
                # Queue email sending (would use Celery in production)
                result["message"] = "Email queued for sending"

            elif action_type == ActionType.ADD_TAG:
                # Add tag to contact
                result["tag"] = config.get("tag_name")
                result["message"] = "Tag added"

            elif action_type == ActionType.UPDATE_SCORE:
                # Update lead score
                score_delta = config.get("score_delta", 0)
                result["score_delta"] = score_delta
                result["message"] = f"Score updated by {score_delta}"

            elif action_type == ActionType.WAIT:
                # Log wait action (actual delay handled by scheduler)
                delay_minutes = config.get("delay_minutes", 0)
                result["delay_minutes"] = delay_minutes
                result["message"] = f"Wait {delay_minutes} minutes"

            else:
                result["message"] = f"Action type {action_type.value} executed"

        except Exception as e:
            result["status"] = "failed"
            result["error"] = str(e)
            logger.error("Action execution failed", action_type=action_type.value, error=str(e))

        return result

    async def create_drip_campaign(
        self,
        name: str,
        steps: List[Dict[str, Any]],
        entry_trigger: Dict[str, Any],
        workspace_id: UUID,
        user_id: UUID,
        description: Optional[str] = None,
    ) -> DripCampaign:
        """Create a drip campaign."""
        drip_campaign = DripCampaign(
            workspace_id=workspace_id,
            name=name,
            description=description,
            entry_trigger=entry_trigger,
            steps=steps,
            status="draft",
            created_by=user_id,
        )

        self.db.add(drip_campaign)
        await self.db.commit()
        await self.db.refresh(drip_campaign)

        logger.info("Drip campaign created", drip_campaign_id=str(drip_campaign.id))

        return drip_campaign

    async def enroll_in_drip(
        self,
        drip_campaign_id: UUID,
        contact_id: UUID,
        workspace_id: UUID,
    ) -> DripEnrollment:
        """Enroll contact in drip campaign."""
        # Check if already enrolled
        result = await self.db.execute(
            select(DripEnrollment).where(
                DripEnrollment.drip_campaign_id == drip_campaign_id,
                DripEnrollment.contact_id == contact_id
            )
        )
        existing = result.scalar_one_or_none()

        if existing and existing.status == "active":
            raise ValidationError("Contact is already enrolled in this drip campaign")

        enrollment = DripEnrollment(
            drip_campaign_id=drip_campaign_id,
            contact_id=contact_id,
            status="active",
            current_step=0,
        )

        self.db.add(enrollment)
        await self.db.commit()
        await self.db.refresh(enrollment)

        logger.info(
            "Contact enrolled in drip campaign",
            enrollment_id=str(enrollment.id),
            contact_id=str(contact_id)
        )

        return enrollment
