from pydantic import BaseModel


class StatusBreakdown(BaseModel):
    status: str
    count: int


class UrgencyBreakdown(BaseModel):
    urgency: str
    count: int


class DashboardSummary(BaseModel):
    total_tickets: int
    open_tickets: int
    resolved_today: int
    unassigned_tickets: int
    sla_breaches_today: int
    avg_confidence: float
    status_breakdown: list[StatusBreakdown]
    urgency_breakdown: list[UrgencyBreakdown]
