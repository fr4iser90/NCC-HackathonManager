# schemas/judging.py
import uuid
from datetime import datetime
from typing import Optional
from decimal import Decimal
from pydantic import BaseModel, Field


# Pydantic Schemas for Criterion
class CriterionBase(BaseModel):
    name: str
    description: Optional[str] = None
    max_score: int = Field(..., gt=0)
    weight: Decimal = Field(..., gt=0)


class CriterionCreate(CriterionBase):
    pass


class CriterionRead(CriterionBase):
    id: uuid.UUID
    created_at: datetime  # This was in the original model, let's keep it for now and see if it causes issues.

    model_config = {"from_attributes": True}


# Pydantic Schemas for Score
class ScoreBase(BaseModel):
    project_id: uuid.UUID
    criteria_id: uuid.UUID
    score: int
    comment: Optional[str] = None


class ScoreCreate(ScoreBase):
    # judge_id will be taken from current_user
    pass


class ScoreUpdate(BaseModel):
    score: Optional[int] = None
    comment: Optional[str] = None


class ScoreRead(ScoreBase):
    id: uuid.UUID
    judge_id: uuid.UUID
    submitted_at: datetime  # Consistent with the model fix
    updated_at: datetime
    # criterion: Optional[CriterionRead] = None # To include criterion details if needed

    model_config = {"from_attributes": True}
