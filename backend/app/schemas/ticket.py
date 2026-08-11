from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, EmailStr

from app.core.constants import ChannelEnum, SentimentEnum, TicketStatus, UrgencyEnum


class TicketMessageCreate(BaseModel):
    sender_type: str
    sender_name: str
    body: str


class TicketMessageRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    sender_type: str
    sender_name: str
    body: str
    created_at: datetime


class TicketPredictionRead(BaseModel):
    """ML prediction fields attached to a ticket, per the API contract."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    category: str
    subcategory: Optional[str] = None
    urgency: UrgencyEnum
    sentiment: SentimentEnum
    confidence: float
    predicted_team_id: Optional[str] = None
    predicted_team_name: Optional[str] = None
    model_version: str
    explanation: str
    predicted_at: datetime


class TicketCreate(BaseModel):
    subject: str
    description: str
    requester_name: str
    requester_email: EmailStr
    channel: ChannelEnum = ChannelEnum.email


class TicketUpdate(BaseModel):
    status: Optional[TicketStatus] = None
    urgency: Optional[UrgencyEnum] = None
    category: Optional[str] = None
    subcategory: Optional[str] = None
    assigned_to_id: Optional[str] = None
    team_id: Optional[str] = None


class TicketAssignRequest(BaseModel):
    assigned_to_id: Optional[str] = None
    team_id: Optional[str] = None


class TicketStatusUpdateRequest(BaseModel):
    status: TicketStatus


class TicketListItem(BaseModel):
    """Lightweight representation used in list/search endpoints."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    subject: str
    status: TicketStatus
    urgency: UrgencyEnum
    category: Optional[str] = None
    channel: ChannelEnum
    requester_name: str
    assigned_to_id: Optional[str] = None
    assignee_name: Optional[str] = None
    team_id: Optional[str] = None
    team_name: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class TicketDetail(TicketListItem):
    description: str
    requester_email: str
    resolved_at: Optional[datetime] = None
    latest_prediction: Optional[TicketPredictionRead] = None
    messages: list[TicketMessageRead] = []


class PaginatedTickets(BaseModel):
    items: list[TicketListItem]
    total: int
    page: int
    page_size: int
    total_pages: int


class ActivityEvent(BaseModel):
    """A single item in a ticket's activity/history timeline."""

    type: str  # created | status_change | assignment | message | feedback | sla
    description: str
    actor: Optional[str] = None
    timestamp: datetime
    metadata: dict = {}


class TicketHistoryResponse(BaseModel):
    ticket_id: str
    events: list[ActivityEvent]
