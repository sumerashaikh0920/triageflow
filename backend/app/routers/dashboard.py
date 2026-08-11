from datetime import datetime, time, timedelta

from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.constants import TicketStatus
from app.database import get_db
from app.dependencies import get_current_user
from app.models.sla_event import SLAEvent
from app.models.ticket import Ticket
from app.models.ticket_prediction import TicketPrediction
from app.models.user import User
from app.schemas.dashboard import DashboardSummary, StatusBreakdown, UrgencyBreakdown

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/summary", response_model=DashboardSummary)
def dashboard_summary(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    total_tickets = db.query(Ticket).count()
    open_tickets = db.query(Ticket).filter(
        Ticket.status.in_([TicketStatus.new, TicketStatus.open, TicketStatus.in_progress, TicketStatus.pending])
    ).count()

    today_start = datetime.combine(datetime.utcnow().date(), time.min)
    resolved_today = db.query(Ticket).filter(
        Ticket.status == TicketStatus.resolved, Ticket.resolved_at >= today_start
    ).count()

    unassigned_tickets = db.query(Ticket).filter(Ticket.assigned_to_id.is_(None)).count()

    sla_breaches_today = db.query(SLAEvent).filter(
        SLAEvent.breached.is_(True), SLAEvent.occurred_at >= today_start
    ).count()

    avg_confidence = db.query(func.avg(TicketPrediction.confidence)).scalar() or 0.0

    status_rows = db.query(Ticket.status, func.count(Ticket.id)).group_by(Ticket.status).all()
    urgency_rows = db.query(Ticket.urgency, func.count(Ticket.id)).group_by(Ticket.urgency).all()

    return DashboardSummary(
        total_tickets=total_tickets,
        open_tickets=open_tickets,
        resolved_today=resolved_today,
        unassigned_tickets=unassigned_tickets,
        sla_breaches_today=sla_breaches_today,
        avg_confidence=round(float(avg_confidence), 3),
        status_breakdown=[StatusBreakdown(status=s.value, count=c) for s, c in status_rows],
        urgency_breakdown=[UrgencyBreakdown(urgency=u.value, count=c) for u, c in urgency_rows],
    )
