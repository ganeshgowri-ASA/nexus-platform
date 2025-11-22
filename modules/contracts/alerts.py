"""Alert and notification system."""

from datetime import datetime, timedelta
from typing import Dict, List, Optional
from uuid import UUID, uuid4
from pydantic import BaseModel, Field
import structlog

logger = structlog.get_logger(__name__)


class Alert(BaseModel):
    """Contract alert/notification."""

    id: UUID = Field(default_factory=uuid4)
    contract_id: UUID
    alert_type: str  # expiration, renewal, obligation_due, milestone_due
    title: str
    message: str
    severity: str = "info"  # info, warning, critical
    recipient_ids: List[UUID] = Field(default_factory=list)
    sent: bool = False
    sent_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)


class AlertManager:
    """Manages contract alerts and notifications."""

    def __init__(self):
        """Initialize alert manager."""
        self.alerts: Dict[UUID, Alert] = {}

    def create_alert(
        self,
        contract_id: UUID,
        alert_type: str,
        title: str,
        message: str,
        recipient_ids: List[UUID],
        severity: str = "info",
    ) -> Alert:
        """Create a new alert."""
        logger.info("Creating alert", contract_id=contract_id, alert_type=alert_type)

        alert = Alert(
            contract_id=contract_id,
            alert_type=alert_type,
            title=title,
            message=message,
            recipient_ids=recipient_ids,
            severity=severity,
        )

        self.alerts[alert.id] = alert
        return alert

    def check_expirations(self, contracts: List, days: int = 30) -> List[Alert]:
        """Check for expiring contracts and create alerts."""
        logger.info("Checking contract expirations", days=days)

        alerts = []
        threshold = datetime.utcnow() + timedelta(days=days)

        for contract in contracts:
            if contract.end_date and contract.end_date <= threshold:
                alert = self.create_alert(
                    contract_id=contract.id,
                    alert_type="expiration",
                    title=f"Contract Expiring: {contract.title}",
                    message=f"Contract expires on {contract.end_date.date()}",
                    recipient_ids=[contract.created_by] if contract.created_by else [],
                    severity="warning",
                )
                alerts.append(alert)

        return alerts

    def send_alert(self, alert_id: UUID) -> bool:
        """Send an alert to recipients."""
        logger.info("Sending alert", alert_id=alert_id)

        alert = self.alerts.get(alert_id)
        if not alert:
            return False

        # Implementation would send email/notification
        alert.sent = True
        alert.sent_at = datetime.utcnow()
        return True

    def get_pending_alerts(self, contract_id: Optional[UUID] = None) -> List[Alert]:
        """Get pending alerts."""
        alerts = list(self.alerts.values())

        if contract_id:
            alerts = [a for a in alerts if a.contract_id == contract_id]

        return [a for a in alerts if not a.sent]
