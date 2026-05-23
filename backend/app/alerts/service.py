from __future__ import annotations

from sqlalchemy.orm import Session

from app.db.models import Alert
from app.schemas import ArbiterDecisionOut


class AlertService:
    def create_if_allowed(self, db: Session, user_id: str | None, signal_id: str, alert_type: str, arbiter: ArbiterDecisionOut) -> Alert | None:
        if not arbiter.allowed_to_alert:
            return None
        alert = Alert(user_id=user_id, signal_id=signal_id, alert_type=alert_type, status="created")
        db.add(alert)
        db.commit()
        db.refresh(alert)
        return alert
