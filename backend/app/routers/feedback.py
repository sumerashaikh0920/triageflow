from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.constants import AuditAction
from app.core.exceptions import NotFoundError
from app.database import get_db
from app.dependencies import get_current_user
from app.models.feedback_correction import FeedbackCorrection
from app.models.ticket import Ticket
from app.models.user import User
from app.schemas.feedback import (
    AcceptPredictionRequest,
    CorrectCategoryRequest,
    FeedbackRead,
    MarkUrgencyRequest,
)
from app.services.audit_service import write_audit_log

router = APIRouter(prefix="/feedback", tags=["feedback"])


def _get_ticket_or_404(db: Session, ticket_id: str) -> Ticket:
    ticket = db.get(Ticket, ticket_id)
    if not ticket:
        raise NotFoundError("Ticket not found")
    return ticket


@router.get("", response_model=list[FeedbackRead])
def list_feedback(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return db.query(FeedbackCorrection).order_by(FeedbackCorrection.created_at.desc()).all()


@router.post("/correct-category", response_model=FeedbackRead, status_code=201)
def correct_category(
    payload: CorrectCategoryRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    ticket = _get_ticket_or_404(db, payload.ticket_id)

    feedback = FeedbackCorrection(
        ticket_id=ticket.id,
        prediction_id=payload.prediction_id,
        user_id=payload.user_id or current_user.id,
        original_category=payload.original_category or ticket.category,
        corrected_category=payload.corrected_category,
        accepted=False,
        notes=payload.notes,
    )
    db.add(feedback)

    ticket.category = payload.corrected_category

    db.commit()
    db.refresh(feedback)
    write_audit_log(db, AuditAction.feedback, "ticket", ticket.id, user_id=current_user.id, details={"type": "correct_category"})
    return feedback


@router.post("/mark-urgency", response_model=FeedbackRead, status_code=201)
def mark_urgency(
    payload: MarkUrgencyRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    ticket = _get_ticket_or_404(db, payload.ticket_id)

    feedback = FeedbackCorrection(
        ticket_id=ticket.id,
        prediction_id=payload.prediction_id,
        user_id=payload.user_id or current_user.id,
        original_urgency=payload.original_urgency or ticket.urgency,
        corrected_urgency=payload.corrected_urgency,
        accepted=False,
        notes=payload.notes,
    )
    db.add(feedback)

    ticket.urgency = payload.corrected_urgency

    db.commit()
    db.refresh(feedback)
    write_audit_log(db, AuditAction.feedback, "ticket", ticket.id, user_id=current_user.id, details={"type": "mark_urgency"})
    return feedback


@router.post("/accept-prediction", response_model=FeedbackRead, status_code=201)
def accept_prediction(
    payload: AcceptPredictionRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    ticket = _get_ticket_or_404(db, payload.ticket_id)

    feedback = FeedbackCorrection(
        ticket_id=ticket.id,
        prediction_id=payload.prediction_id,
        user_id=payload.user_id or current_user.id,
        original_category=ticket.category,
        original_urgency=ticket.urgency,
        accepted=True,
        notes=payload.notes,
    )
    db.add(feedback)
    db.commit()
    db.refresh(feedback)
    write_audit_log(db, AuditAction.feedback, "ticket", ticket.id, user_id=current_user.id, details={"type": "accept_prediction"})
    return feedback
