from datetime import datetime, timedelta

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.constants import TicketStatus, UrgencyEnum
from app.database import get_db
from app.dependencies import get_current_user
from app.models.sla_event import SLAEvent
from app.models.ticket import Ticket
from app.models.user import User
from app.schemas.sla import SLAEventRead, SLAMonitorItem, SLAMonitorResponse

router = APIRouter(prefix="/sla", tags=["sla"])

# Response-time SLA targets by urgency, in minutes.
SLA_TARGET_MINUTES = {
    UrgencyEnum.critical: 60,
    UrgencyEnum.high: 240,
    UrgencyEnum.medium: 1440,
    UrgencyEnum.low: 4320,
}


@router.get("/monitor", response_model=SLAMonitorResponse)
def sla_monitor(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    active_tickets = db.query(Ticket).filter(
        Ticket.status.notin_([TicketStatus.resolved, TicketStatus.closed])
    ).all()

    items: list[SLAMonitorItem] = []
    breached_count = 0
    at_risk_count = 0
    now = datetime.utcnow()

    for ticket in active_tickets:
        target_minutes = SLA_TARGET_MINUTES.get(ticket.urgency, 1440)
        due_at = ticket.created_at.replace(tzinfo=None) + timedelta(minutes=target_minutes)
        minutes_remaining = (due_at - now).total_seconds() / 60
        breached = minutes_remaining < 0

        if breached:
            breached_count += 1
        elif minutes_remaining < target_minutes * 0.2:
            at_risk_count += 1

        items.append(
            SLAMonitorItem(
                ticket_id=ticket.id,
                subject=ticket.subject,
                urgency=ticket.urgency.value,
                status=ticket.status.value,
                due_at=due_at,
                breached=breached,
                minutes_remaining=round(minutes_remaining, 1),
            )
        )

    items.sort(key=lambda i: i.minutes_remaining if i.minutes_remaining is not None else 0)

    return SLAMonitorResponse(items=items, breached_count=breached_count, at_risk_count=at_risk_count)


@router.get("/events", response_model=list[SLAEventRead])
def list_sla_events(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return db.query(SLAEvent).order_by(SLAEvent.occurred_at.desc()).all()
