from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, Enum, Float, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.constants import SentimentEnum, UrgencyEnum
from app.database import Base
from app.models.base import UUIDPrimaryKeyMixin, utcnow


class TicketPrediction(Base, UUIDPrimaryKeyMixin):
    """A single ML prediction run against a ticket. A ticket may have several over time
    (e.g. re-run after new messages), the most recent is treated as 'current'."""

    __tablename__ = "ticket_predictions"

    ticket_id: Mapped[str] = mapped_column(String(36), ForeignKey("tickets.id"), nullable=False, index=True)
    ticket: Mapped["Ticket"] = relationship("Ticket", back_populates="predictions")

    category: Mapped[str] = mapped_column(String(120), nullable=False)
    subcategory: Mapped[Optional[str]] = mapped_column(String(120), nullable=True)
    urgency: Mapped[UrgencyEnum] = mapped_column(Enum(UrgencyEnum), nullable=False)
    sentiment: Mapped[SentimentEnum] = mapped_column(Enum(SentimentEnum), nullable=False)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)

    predicted_team_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("teams.id"), nullable=True)
    predicted_team: Mapped[Optional["Team"]] = relationship("Team", foreign_keys=[predicted_team_id])

    model_version: Mapped[str] = mapped_column(String(50), nullable=False)
    explanation: Mapped[str] = mapped_column(Text, nullable=False)

    predicted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
