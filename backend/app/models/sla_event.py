from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.constants import SLAEventType
from app.database import Base
from app.models.base import UUIDPrimaryKeyMixin, utcnow


class SLAEvent(Base, UUIDPrimaryKeyMixin):
    __tablename__ = "sla_events"

    ticket_id: Mapped[str] = mapped_column(String(36), ForeignKey("tickets.id"), nullable=False, index=True)
    ticket: Mapped["Ticket"] = relationship("Ticket", back_populates="sla_events")

    event_type: Mapped[SLAEventType] = mapped_column(Enum(SLAEventType), nullable=False)
    due_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    breached: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
