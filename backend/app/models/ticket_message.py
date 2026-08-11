from sqlalchemy import Enum, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.constants import MessageSenderType
from app.database import Base
from app.models.base import TimestampMixin, UUIDPrimaryKeyMixin


class TicketMessage(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "ticket_messages"

    ticket_id: Mapped[str] = mapped_column(String(36), ForeignKey("tickets.id"), nullable=False, index=True)
    ticket: Mapped["Ticket"] = relationship("Ticket", back_populates="messages")

    sender_type: Mapped[MessageSenderType] = mapped_column(Enum(MessageSenderType), nullable=False)
    sender_name: Mapped[str] = mapped_column(String(255), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
