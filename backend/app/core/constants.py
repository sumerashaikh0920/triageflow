"""Shared enums used across models and schemas."""
import enum


class RoleEnum(str, enum.Enum):
    agent = "agent"
    team_lead = "team_lead"
    admin = "admin"


class TicketStatus(str, enum.Enum):
    new = "new"
    open = "open"
    in_progress = "in_progress"
    pending = "pending"
    resolved = "resolved"
    closed = "closed"


class UrgencyEnum(str, enum.Enum):
    low = "low"
    medium = "medium"
    high = "high"
    critical = "critical"


class SentimentEnum(str, enum.Enum):
    positive = "positive"
    neutral = "neutral"
    negative = "negative"


class ChannelEnum(str, enum.Enum):
    email = "email"
    chat = "chat"
    phone = "phone"
    web_form = "web_form"
    social = "social"


class MessageSenderType(str, enum.Enum):
    customer = "customer"
    agent = "agent"
    system = "system"


class SLAEventType(str, enum.Enum):
    created = "created"
    warning = "warning"
    breached = "breached"
    resolved = "resolved"


class IntegrationStatus(str, enum.Enum):
    connected = "connected"
    disconnected = "disconnected"
    error = "error"


class IntegrationType(str, enum.Enum):
    email = "email"
    slack = "slack"
    crm = "crm"
    chat_widget = "chat_widget"
    webhook = "webhook"


class AuditAction(str, enum.Enum):
    create = "create"
    update = "update"
    delete = "delete"
    login = "login"
    assign = "assign"
    status_change = "status_change"
    feedback = "feedback"
