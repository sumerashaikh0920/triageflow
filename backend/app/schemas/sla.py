from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class SLAEventRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    ticket_id: str
    event_type: str
    due_at: Optional[datetime] = None
    occurred_at: datetime
    breached: bool


class SLAMonitorItem(BaseModel):
    ticket_id: str
    subject: str
    urgency: str
    status: str
    due_at: Optional[datetime] = None
    breached: bool
    minutes_remaining: Optional[float] = None


class SLAMonitorResponse(BaseModel):
    items: list[SLAMonitorItem]
    breached_count: int
    at_risk_count: int
