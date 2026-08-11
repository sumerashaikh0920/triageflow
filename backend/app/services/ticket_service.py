"""Business logic for ticket creation, including running the (stubbed) ML prediction."""
from sqlalchemy.orm import Session

from app.models.team import Team
from app.models.ticket import Ticket
from app.models.ticket_prediction import TicketPrediction
from app.services.ml_stub import get_predictor


def create_ticket_with_prediction(db: Session, ticket_data: dict) -> Ticket:
    ticket = Ticket(**ticket_data)
    db.add(ticket)
    db.flush()  # get ticket.id without committing yet

    predictor = get_predictor()
    result = predictor.predict(ticket.subject, ticket.description)

    predicted_team = None
    if result.predicted_team_name:
        predicted_team = db.query(Team).filter(Team.name == result.predicted_team_name).first()

    prediction = TicketPrediction(
        ticket_id=ticket.id,
        category=result.category,
        subcategory=result.subcategory,
        urgency=result.urgency,
        sentiment=result.sentiment,
        confidence=result.confidence,
        predicted_team_id=predicted_team.id if predicted_team else None,
        model_version=result.model_version,
        explanation=result.explanation,
    )
    db.add(prediction)

    # Seed the ticket's working fields from the prediction (agents can override later).
    ticket.category = result.category
    ticket.subcategory = result.subcategory
    ticket.urgency = result.urgency
    if predicted_team:
        ticket.team_id = predicted_team.id

    db.commit()
    db.refresh(ticket)
    return ticket
