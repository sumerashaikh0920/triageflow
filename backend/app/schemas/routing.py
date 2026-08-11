from typing import Any, Optional

from pydantic import BaseModel, ConfigDict

from app.schemas.ticket import TicketListItem


class RoutingQueueResponse(BaseModel):
    unassigned: list[TicketListItem]
    total_unassigned: int


class RoutingRuleBase(BaseModel):
    name: str
    condition: dict[str, Any]
    target_team_id: str
    priority_order: int = 0
    is_active: bool = True


class RoutingRuleCreate(RoutingRuleBase):
    pass


class RoutingRuleUpdate(BaseModel):
    name: Optional[str] = None
    condition: Optional[dict[str, Any]] = None
    target_team_id: Optional[str] = None
    priority_order: Optional[int] = None
    is_active: Optional[bool] = None


class RoutingRuleRead(RoutingRuleBase):
    model_config = ConfigDict(from_attributes=True)

    id: str
