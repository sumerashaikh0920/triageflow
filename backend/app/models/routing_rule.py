from typing import Any, Optional

from sqlalchemy import Boolean, ForeignKey, Integer, JSON, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.base import TimestampMixin, UUIDPrimaryKeyMixin


class RoutingRule(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """A rule that routes tickets to a team based on JSON conditions,
    e.g. {"category": "billing", "urgency": ["high", "critical"]}."""

    __tablename__ = "routing_rules"

    name: Mapped[str] = mapped_column(String(150), nullable=False)
    condition: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    target_team_id: Mapped[str] = mapped_column(String(36), ForeignKey("teams.id"), nullable=False)
    target_team: Mapped["Team"] = relationship("Team", foreign_keys=[target_team_id])

    priority_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
