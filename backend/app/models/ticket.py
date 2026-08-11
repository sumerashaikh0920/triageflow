from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, Enum, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.constants import ChannelEnum, TicketStatus, UrgencyEnum
from app.database import Base
from app.models.base import TimestampMixin, UUIDPrimaryKeyMixin


class Ticket(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "tickets"

    subject: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)

    requester_name: Mapped[str] = mapped_column(String(255), nullable=False)
    requester_email: Mapped[str] = mapped_column(String(255), nullable=False)
    channel: Mapped[ChannelEnum] = mapped_column(Enum(ChannelEnum), default=ChannelEnum.email, nullable=False)

    status: Mapped[TicketStatus] = mapped_column(Enum(TicketStatus), default=TicketStatus.new, nullable=False)

    # Agent-set / final urgency (may start as the ML-predicted value, editable via feedback).
    urgency: Mapped[UrgencyEnum] = mapped_column(Enum(UrgencyEnum), default=UrgencyEnum.medium, nullable=False)

    # Agent-facing / final category (may start as ML-predicted value, editable via feedback).
    category: Mapped[Optional[str]] = mapped_column(String(120), nullable=True)
    subcategory: Mapped[Optional[str]] = mapped_column(String(120), nullable=True)

    assigned_to_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("users.id"), nullable=True)
    assignee: Mapped[Optional["User"]] = relationship(
        "User", back_populates="assigned_tickets", foreign_keys=[assigned_to_id]
    )

    team_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("teams.id"), nullable=True)
    team: Mapped[Optional["Team"]] = relationship("Team", foreign_keys=[team_id])

    resolved_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    messages: Mapped[list["TicketMessage"]] = relationship(
        "TicketMessage", back_populates="ticket", cascade="all, delete-orphan", order_by="TicketMessage.created_at"
    )
    predictions: Mapped[list["TicketPrediction"]] = relationship(
        "TicketPrediction", back_populates="ticket", cascade="all, delete-orphan",
        order_by="TicketPrediction.predicted_at.desc()",
    )
    sla_events: Mapped[list["SLAEvent"]] = relationship(
        "SLAEvent", back_populates="ticket", cascade="all, delete-orphan"
    )
