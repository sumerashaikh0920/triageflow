from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user
from app.models.feedback_correction import FeedbackCorrection
from app.models.model_version import ModelVersion
from app.models.ticket_prediction import TicketPrediction
from app.models.user import User
from app.schemas.model_metrics import ModelMetricsResponse, ModelVersionRead

router = APIRouter(prefix="/models", tags=["model_metrics"])


@router.get("/versions", response_model=list[ModelVersionRead])
def list_model_versions(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return db.query(ModelVersion).order_by(ModelVersion.deployed_at.desc()).all()


@router.get("/metrics", response_model=ModelMetricsResponse)
def model_metrics(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    active = db.query(ModelVersion).filter(ModelVersion.is_active.is_(True)).first()

    total_predictions = db.query(TicketPrediction).count()
    avg_confidence = db.query(func.avg(TicketPrediction.confidence)).scalar() or 0.0

    total_feedback = db.query(FeedbackCorrection).count()
    accepted_feedback = db.query(FeedbackCorrection).filter(FeedbackCorrection.accepted.is_(True)).count()
    category_corrections = db.query(FeedbackCorrection).filter(
        FeedbackCorrection.corrected_category.isnot(None)
    ).count()
    urgency_corrections = db.query(FeedbackCorrection).filter(
        FeedbackCorrection.corrected_urgency.isnot(None)
    ).count()

    accepted_rate = (accepted_feedback / total_feedback) if total_feedback else 0.0
    correction_rate = ((category_corrections + urgency_corrections) / total_feedback) if total_feedback else 0.0

    return ModelMetricsResponse(
        active_version=active.version if active else None,
        total_predictions=total_predictions,
        avg_confidence=round(float(avg_confidence), 3),
        accepted_rate=round(accepted_rate, 3),
        correction_rate=round(correction_rate, 3),
        category_correction_count=category_corrections,
        urgency_correction_count=urgency_corrections,
    )
