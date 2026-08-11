from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict

from app.core.constants import IntegrationStatus, IntegrationType


class IntegrationRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    type: IntegrationType
    status: IntegrationStatus
    config: dict[str, Any]
    connected_at: Optional[datetime] = None


class IntegrationUpdate(BaseModel):
    status: Optional[IntegrationStatus] = None
    config: Optional[dict[str, Any]] = None
