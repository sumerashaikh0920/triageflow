from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.constants import AuditAction, RoleEnum
from app.core.exceptions import NotFoundError
from app.database import get_db
from app.dependencies import get_current_user, require_roles
from app.models.routing_rule import RoutingRule
from app.models.ticket import Ticket
from app.models.user import User
from app.routers.tickets import _to_list_item
from app.schemas.routing import RoutingQueueResponse, RoutingRuleCreate, RoutingRuleRead, RoutingRuleUpdate
from app.services.audit_service import write_audit_log

router = APIRouter(prefix="/routing", tags=["routing"])


@router.get("/queue", response_model=RoutingQueueResponse)
def routing_queue(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    unassigned = db.query(Ticket).filter(Ticket.assigned_to_id.is_(None)).order_by(Ticket.created_at.asc()).all()
    return RoutingQueueResponse(
        unassigned=[_to_list_item(t) for t in unassigned],
        total_unassigned=len(unassigned),
    )


@router.get("/rules", response_model=list[RoutingRuleRead])
def list_rules(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return db.query(RoutingRule).order_by(RoutingRule.priority_order).all()


@router.post("/rules", response_model=RoutingRuleRead, status_code=201)
def create_rule(
    payload: RoutingRuleCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(RoleEnum.admin, RoleEnum.team_lead)),
):
    rule = RoutingRule(**payload.model_dump())
    db.add(rule)
    db.commit()
    db.refresh(rule)
    write_audit_log(db, AuditAction.create, "routing_rule", rule.id, user_id=current_user.id)
    return rule


@router.patch("/rules/{rule_id}", response_model=RoutingRuleRead)
def update_rule(
    rule_id: str,
    payload: RoutingRuleUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(RoleEnum.admin, RoleEnum.team_lead)),
):
    rule = db.get(RoutingRule, rule_id)
    if not rule:
        raise NotFoundError("Routing rule not found")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(rule, field, value)
    db.commit()
    db.refresh(rule)
    write_audit_log(db, AuditAction.update, "routing_rule", rule.id, user_id=current_user.id)
    return rule
