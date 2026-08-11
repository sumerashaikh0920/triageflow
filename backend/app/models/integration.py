from datetime import datetime
from typing import Any, Optional

from sqlalchemy import DateTime, Enum, JSON, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.constants import IntegrationStatus, IntegrationType
from app.database import Base
from app.models.base import TimestampMixin, UUIDPrimaryKeyMixin


class Integration(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "integrations"

    name: Mapped[str] = mapped_column(String(150), nullable=False)
    type: Mapped[IntegrationType] = mapped_column(Enum(IntegrationType), nullable=False)
    status: Mapped[IntegrationStatus] = mapped_column(
        Enum(IntegrationStatus), default=IntegrationStatus.disconnected, nullable=False
    )
    config: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    connected_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
