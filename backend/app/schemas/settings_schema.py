from typing import Optional

from pydantic import BaseModel


class SettingsRead(BaseModel):
    project_name: str
    cors_origins: list[str]
    sla_default_minutes: dict[str, int]
    seed_on_startup: bool


class SettingsUpdate(BaseModel):
    sla_default_minutes: Optional[dict[str, int]] = None
