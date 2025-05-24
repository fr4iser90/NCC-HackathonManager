# routers/judging.py
import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.database import get_db
from app.models.user import User
from app.models.project import Project # To check if project exists
from app.models.judging import Criterion, Score # SQLAlchemy models
from app.schemas.judging import (
    CriterionCreate, CriterionRead,
    ScoreCreate, ScoreRead, ScoreUpdate
) # Pydantic schemas
from app.auth import get_current_user
from app.services.judging_service import create_criterion, update_criterion, delete_criterion, submit_score, update_score, list_scores_for_project, list_scores_by_judge

router = APIRouter()

# --- Criterion Endpoints (Admin-focused) ---
@router.post("/criteria/", response_model=CriterionRead, status_code=status.HTTP_201_CREATED, tags=["judging-criteria"])
def create_criterion_endpoint(
    criterion_in: CriterionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return create_criterion(db, criterion_in, current_user)

@router.get("/criteria/", response_model=List[CriterionRead], tags=["judging-criteria"])
def list_criteria(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    criteria = db.query(Criterion).offset(skip).limit(limit).all()
    return criteria

@router.get("/criteria/{criterion_id}", response_model=CriterionRead, tags=["judging-criteria"])
def get_criterion(criterion_id: uuid.UUID, db: Session = Depends(get_db)):
    criterion = db.query(Criterion).filter(Criterion.id == criterion_id).first()
    if not criterion:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Criterion not found")
    return criterion

@router.put("/criteria/{criterion_id}", response_model=CriterionRead, tags=["judging-criteria"])
def update_criterion_endpoint(
    criterion_id: uuid.UUID,
    criterion_in: CriterionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return update_criterion(db, criterion_id, criterion_in, current_user)

@router.delete("/criteria/{criterion_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["judging-criteria"])
def delete_criterion_endpoint(criterion_id: uuid.UUID, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    delete_criterion(db, criterion_id, current_user)
    return

# --- Score Endpoints (Judge-focused) ---
@router.post("/scores/", response_model=ScoreRead, status_code=status.HTTP_201_CREATED, tags=["judging-scores"])
def submit_score_endpoint(
    score_in: ScoreCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return submit_score(db, score_in, current_user)

@router.put("/scores/{score_id}", response_model=ScoreRead, tags=["judging-scores"])
def update_score_endpoint(
    score_id: uuid.UUID,
    score_in: ScoreUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return update_score(db, score_id, score_in, current_user)

@router.get("/scores/project/{project_id}", response_model=List[ScoreRead], tags=["judging-scores"])
def list_scores_for_project_endpoint(project_id: uuid.UUID, db: Session = Depends(get_db)):
    return list_scores_for_project(db, project_id)

@router.get("/scores/judge/{judge_id}", response_model=List[ScoreRead], tags=["judging-scores"])
def list_scores_by_judge_endpoint(judge_id: uuid.UUID, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return list_scores_by_judge(db, judge_id, current_user)

# Consider adding an endpoint to get aggregated results for a project
# e.g., /results/project/{project_id} 