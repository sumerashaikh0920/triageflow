from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class ModelVersionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    version: str
    description: Optional[str] = None
    accuracy: Optional[float] = None
    is_active: bool
    deployed_at: datetime


class ModelMetricsResponse(BaseModel):
    active_version: Optional[str] = None
    total_predictions: int
    avg_confidence: float
    accepted_rate: float
    correction_rate: float
    category_correction_count: int
    urgency_correction_count: int
