from datetime import datetime

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.constants import AuditAction, IntegrationStatus, RoleEnum
from app.core.exceptions import NotFoundError
from app.database import get_db
from app.dependencies import get_current_user, require_roles
from app.models.integration import Integration
from app.models.user import User
from app.schemas.integration import IntegrationRead, IntegrationUpdate
from app.services.audit_service import write_audit_log

router = APIRouter(prefix="/integrations", tags=["integrations"])


@router.get("", response_model=list[IntegrationRead])
def list_integrations(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return db.query(Integration).order_by(Integration.name).all()


@router.patch("/{integration_id}", response_model=IntegrationRead)
def update_integration(
    integration_id: str,
    payload: IntegrationUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(RoleEnum.admin)),
):
    integration = db.get(Integration, integration_id)
    if not integration:
        raise NotFoundError("Integration not found")

    changes = payload.model_dump(exclude_unset=True)
    for field, value in changes.items():
        setattr(integration, field, value)

    if changes.get("status") == IntegrationStatus.connected and not integration.connected_at:
        integration.connected_at = datetime.utcnow()

    db.commit()
    db.refresh(integration)
    write_audit_log(db, AuditAction.update, "integration", integration.id, user_id=current_user.id, details=changes)
    return integration
