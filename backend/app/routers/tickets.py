import math
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.core.constants import AuditAction, TicketStatus, UrgencyEnum
from app.core.exceptions import NotFoundError
from app.database import get_db
from app.dependencies import get_current_user
from app.models.feedback_correction import FeedbackCorrection
from app.models.team import Team
from app.models.ticket import Ticket
from app.models.ticket_message import TicketMessage
from app.models.ticket_prediction import TicketPrediction
from app.models.user import User
from app.schemas.ticket import (
    ActivityEvent,
    PaginatedTickets,
    TicketAssignRequest,
    TicketCreate,
    TicketDetail,
    TicketHistoryResponse,
    TicketListItem,
    TicketMessageCreate,
    TicketMessageRead,
    TicketPredictionRead,
    TicketStatusUpdateRequest,
    TicketUpdate,
)
from app.services.audit_service import write_audit_log
from app.services.ticket_service import create_ticket_with_prediction

router = APIRouter(prefix="/tickets", tags=["tickets"])


def _to_list_item(ticket: Ticket) -> TicketListItem:
    return TicketListItem(
        id=ticket.id,
        subject=ticket.subject,
        status=ticket.status,
        urgency=ticket.urgency,
        category=ticket.category,
        channel=ticket.channel,
        requester_name=ticket.requester_name,
        assigned_to_id=ticket.assigned_to_id,
        assignee_name=ticket.assignee.full_name if ticket.assignee else None,
        team_id=ticket.team_id,
        team_name=ticket.team.name if ticket.team else None,
        created_at=ticket.created_at,
        updated_at=ticket.updated_at,
    )


def _latest_prediction_read(ticket: Ticket) -> Optional[TicketPredictionRead]:
    if not ticket.predictions:
        return None
    latest = ticket.predictions[0]  # relationship is ordered predicted_at desc
    read = TicketPredictionRead.model_validate(latest)
    read.predicted_team_name = latest.predicted_team.name if latest.predicted_team else None
    return read


def _to_detail(ticket: Ticket) -> TicketDetail:
    base = _to_list_item(ticket)
    return TicketDetail(
        **base.model_dump(),
        description=ticket.description,
        requester_email=ticket.requester_email,
        resolved_at=ticket.resolved_at,
        latest_prediction=_latest_prediction_read(ticket),
        messages=[TicketMessageRead.model_validate(m) for m in ticket.messages],
    )


@router.get("", response_model=PaginatedTickets)
def list_tickets(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    search: Optional[str] = Query(None, description="Search subject, description, requester name/email"),
    status_filter: Optional[TicketStatus] = Query(None, alias="status"),
    urgency: Optional[UrgencyEnum] = None,
    category: Optional[str] = None,
    team_id: Optional[str] = None,
    assigned_to_id: Optional[str] = None,
    unassigned_only: bool = False,
    sort_by: str = Query("created_at", pattern="^(created_at|updated_at|urgency|status)$"),
    sort_dir: str = Query("desc", pattern="^(asc|desc)$"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    query = db.query(Ticket)

    if search:
        like = f"%{search}%"
        query = query.filter(
            or_(
                Ticket.subject.ilike(like),
                Ticket.description.ilike(like),
                Ticket.requester_name.ilike(like),
                Ticket.requester_email.ilike(like),
            )
        )
    if status_filter:
        query = query.filter(Ticket.status == status_filter)
    if urgency:
        query = query.filter(Ticket.urgency == urgency)
    if category:
        query = query.filter(Ticket.category == category)
    if team_id:
        query = query.filter(Ticket.team_id == team_id)
    if assigned_to_id:
        query = query.filter(Ticket.assigned_to_id == assigned_to_id)
    if unassigned_only:
        query = query.filter(Ticket.assigned_to_id.is_(None))

    total = query.count()

    sort_column = getattr(Ticket, sort_by)
    query = query.order_by(sort_column.desc() if sort_dir == "desc" else sort_column.asc())

    items = query.offset((page - 1) * page_size).limit(page_size).all()
    total_pages = max(1, math.ceil(total / page_size))

    return PaginatedTickets(
        items=[_to_list_item(t) for t in items],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


@router.post("", response_model=TicketDetail, status_code=201)
def create_ticket(
    payload: TicketCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    ticket = create_ticket_with_prediction(db, payload.model_dump())
    write_audit_log(db, AuditAction.create, "ticket", ticket.id, user_id=current_user.id)
    return _to_detail(ticket)


@router.get("/{ticket_id}", response_model=TicketDetail)
def get_ticket(ticket_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    ticket = db.get(Ticket, ticket_id)
    if not ticket:
        raise NotFoundError("Ticket not found")
    return _to_detail(ticket)


@router.patch("/{ticket_id}", response_model=TicketDetail)
def update_ticket(
    ticket_id: str,
    payload: TicketUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    ticket = db.get(Ticket, ticket_id)
    if not ticket:
        raise NotFoundError("Ticket not found")

    changes = payload.model_dump(exclude_unset=True)
    for field, value in changes.items():
        setattr(ticket, field, value)

    if changes.get("status") == TicketStatus.resolved and not ticket.resolved_at:
        ticket.resolved_at = datetime.utcnow()

    db.commit()
    db.refresh(ticket)
    write_audit_log(db, AuditAction.update, "ticket", ticket.id, user_id=current_user.id, details=changes)
    return _to_detail(ticket)


@router.post("/{ticket_id}/assign", response_model=TicketDetail)
def assign_ticket(
    ticket_id: str,
    payload: TicketAssignRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    ticket = db.get(Ticket, ticket_id)
    if not ticket:
        raise NotFoundError("Ticket not found")

    if payload.assigned_to_id is not None:
        ticket.assigned_to_id = payload.assigned_to_id
        if ticket.status == TicketStatus.new:
            ticket.status = TicketStatus.open
    if payload.team_id is not None:
        ticket.team_id = payload.team_id

    db.commit()
    db.refresh(ticket)
    write_audit_log(
        db, AuditAction.assign, "ticket", ticket.id, user_id=current_user.id,
        details=payload.model_dump(exclude_unset=True),
    )
    return _to_detail(ticket)


@router.post("/{ticket_id}/status", response_model=TicketDetail)
def update_ticket_status(
    ticket_id: str,
    payload: TicketStatusUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    ticket = db.get(Ticket, ticket_id)
    if not ticket:
        raise NotFoundError("Ticket not found")

    ticket.status = payload.status
    if payload.status == TicketStatus.resolved and not ticket.resolved_at:
        ticket.resolved_at = datetime.utcnow()

    db.commit()
    db.refresh(ticket)
    write_audit_log(
        db, AuditAction.status_change, "ticket", ticket.id, user_id=current_user.id,
        details={"status": payload.status.value},
    )
    return _to_detail(ticket)


@router.post("/{ticket_id}/messages", response_model=TicketMessageRead, status_code=201)
def add_message(
    ticket_id: str,
    payload: TicketMessageCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    ticket = db.get(Ticket, ticket_id)
    if not ticket:
        raise NotFoundError("Ticket not found")

    message = TicketMessage(ticket_id=ticket.id, **payload.model_dump())
    db.add(message)
    db.commit()
    db.refresh(message)
    return message


@router.get("/{ticket_id}/history", response_model=TicketHistoryResponse)
def ticket_history(ticket_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    ticket = db.get(Ticket, ticket_id)
    if not ticket:
        raise NotFoundError("Ticket not found")

    events: list[ActivityEvent] = [
        ActivityEvent(type="created", description="Ticket created", timestamp=ticket.created_at)
    ]

    for msg in ticket.messages:
        events.append(
            ActivityEvent(
                type="message",
                description=f"Message from {msg.sender_name} ({msg.sender_type.value})",
                actor=msg.sender_name,
                timestamp=msg.created_at,
            )
        )

    for pred in sorted(ticket.predictions, key=lambda p: p.predicted_at):
        events.append(
            ActivityEvent(
                type="prediction",
                description=f"ML prediction: {pred.category} / {pred.urgency.value} "
                             f"(confidence {pred.confidence:.2f}, model {pred.model_version})",
                timestamp=pred.predicted_at,
            )
        )

    corrections = db.query(FeedbackCorrection).filter(FeedbackCorrection.ticket_id == ticket.id).all()
    for fb in corrections:
        desc = "Feedback: accepted prediction" if fb.accepted else "Feedback: correction submitted"
        events.append(
            ActivityEvent(
                type="feedback",
                description=desc,
                actor=fb.user_id,
                timestamp=fb.created_at,
                metadata={
                    "corrected_category": fb.corrected_category,
                    "corrected_urgency": fb.corrected_urgency.value if fb.corrected_urgency else None,
                },
            )
        )

    events.sort(key=lambda e: e.timestamp)
    return TicketHistoryResponse(ticket_id=ticket.id, events=events)
