from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class TeamBase(BaseModel):
    name: str
    description: Optional[str] = None


class TeamCreate(TeamBase):
    pass


class TeamUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None


class TeamRead(TeamBase):
    model_config = ConfigDict(from_attributes=True)

    id: str
    created_at: datetime
    member_count: int = 0
