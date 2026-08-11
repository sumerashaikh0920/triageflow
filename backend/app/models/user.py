from typing import Optional

from sqlalchemy import Boolean, Enum, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.constants import RoleEnum
from app.database import Base
from app.models.base import TimestampMixin, UUIDPrimaryKeyMixin


class User(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "users"

    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[RoleEnum] = mapped_column(Enum(RoleEnum), nullable=False, default=RoleEnum.agent)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    team_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("teams.id"), nullable=True)
    team: Mapped[Optional["Team"]] = relationship("Team", back_populates="members", foreign_keys=[team_id])

    assigned_tickets: Mapped[list["Ticket"]] = relationship(
        "Ticket", back_populates="assignee", foreign_keys="Ticket.assigned_to_id"
    )
