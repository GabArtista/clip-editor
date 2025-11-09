from __future__ import annotations

from datetime import datetime
from typing import Dict, Optional

from pydantic import BaseModel, Field


class ClipLearningSummary(BaseModel):
    samples: int = Field(ge=0)
    positives: int = Field(ge=0)
    negatives: int = Field(ge=0)
    metrics: Dict[str, float]
    trained_at: datetime


class ClipLearningTrainResponse(BaseModel):
    result: ClipLearningSummary
    message: Optional[str] = None

