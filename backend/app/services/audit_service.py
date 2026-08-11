"""Helper to write audit log entries consistently."""
from typing import Any, Optional

from sqlalchemy.orm import Session

from app.core.constants import AuditAction
from app.models.audit_log import AuditLog


def write_audit_log(
    db: Session,
    action: AuditAction,
    entity_type: str,
    entity_id: Optional[str] = None,
    user_id: Optional[str] = None,
    details: Optional[dict[str, Any]] = None,
) -> AuditLog:
    log = AuditLog(
        user_id=user_id,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        details=details or {},
    )
    db.add(log)
    db.commit()
    db.refresh(log)
    return log
