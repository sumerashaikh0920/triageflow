"""Import all models here so Alembic (and SQLAlchemy metadata) can discover them."""
from app.models.user import User
from app.models.team import Team
from app.models.ticket import Ticket
from app.models.ticket_message import TicketMessage
from app.models.ticket_prediction import TicketPrediction
from app.models.feedback_correction import FeedbackCorrection
from app.models.routing_rule import RoutingRule
from app.models.sla_event import SLAEvent
from app.models.model_version import ModelVersion
from app.models.integration import Integration
from app.models.audit_log import AuditLog

__all__ = [
    "User",
    "Team",
    "Ticket",
    "TicketMessage",
    "TicketPrediction",
    "FeedbackCorrection",
    "RoutingRule",
    "SLAEvent",
    "ModelVersion",
    "Integration",
    "AuditLog",
]
