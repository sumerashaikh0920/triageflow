from typing import Optional

from sqlalchemy import Boolean, Enum, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.constants import UrgencyEnum
from app.database import Base
from app.models.base import TimestampMixin, UUIDPrimaryKeyMixin


class FeedbackCorrection(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Human feedback on an ML prediction: category correction, urgency correction,
    or a simple 'accept as-is'. Used to build future training data."""

    __tablename__ = "feedback_corrections"

    ticket_id: Mapped[str] = mapped_column(String(36), ForeignKey("tickets.id"), nullable=False, index=True)
    prediction_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("ticket_predictions.id"), nullable=True
    )
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=False)

    original_category: Mapped[Optional[str]] = mapped_column(String(120), nullable=True)
    corrected_category: Mapped[Optional[str]] = mapped_column(String(120), nullable=True)

    original_urgency: Mapped[Optional[UrgencyEnum]] = mapped_column(Enum(UrgencyEnum), nullable=True)
    corrected_urgency: Mapped[Optional[UrgencyEnum]] = mapped_column(Enum(UrgencyEnum), nullable=True)

    accepted: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    ticket: Mapped["Ticket"] = relationship("Ticket")
    user: Mapped["User"] = relationship("User")
