# routers/judging.py
import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.database import get_db
from app.models.user import User, UserRole
from app.models.project import Project # To check if project exists
from app.models.judging import Criterion, Score # SQLAlchemy models
from app.schemas.judging import (
    CriterionCreate, CriterionRead,
    ScoreCreate, ScoreRead, ScoreUpdate
) # Pydantic schemas
from app.auth import get_current_user
from app.middleware import require_roles, require_admin, require_judge
from app.services.judging_service import create_criterion, update_criterion, delete_criterion, submit_score, update_score, list_scores_for_project, list_scores_by_judge

router = APIRouter(tags=["judging"])

# --- Criterion Endpoints (Admin-focused) ---
@router.post("/criteria/", response_model=CriterionRead, status_code=status.HTTP_201_CREATED, dependencies=[Depends(require_admin())])
def create_criterion_endpoint(
    criterion_in: CriterionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new judging criterion. Only accessible by admin users."""
    return create_criterion(db, criterion_in, current_user)

@router.get("/criteria/", response_model=List[CriterionRead])
def list_criteria(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """List all judging criteria. Public endpoint."""
    criteria = db.query(Criterion).offset(skip).limit(limit).all()
    return criteria

@router.get("/criteria/{criterion_id}", response_model=CriterionRead)
def get_criterion(criterion_id: uuid.UUID, db: Session = Depends(get_db)):
    """Get details of a specific criterion. Public endpoint."""
    criterion = db.query(Criterion).filter(Criterion.id == criterion_id).first()
    if not criterion:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Criterion not found")
    return criterion

@router.put("/criteria/{criterion_id}", response_model=CriterionRead, dependencies=[Depends(require_admin())])
def update_criterion_endpoint(
    criterion_id: uuid.UUID,
    criterion_in: CriterionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update a judging criterion. Only accessible by admin users."""
    return update_criterion(db, criterion_id, criterion_in, current_user)

@router.delete("/criteria/{criterion_id}", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(require_admin())])
def delete_criterion_endpoint(
    criterion_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete a judging criterion. Only accessible by admin users."""
    delete_criterion(db, criterion_id, current_user)
    return

# --- Score Endpoints (Judge-focused) ---
@router.post("/scores/", response_model=ScoreRead, status_code=status.HTTP_201_CREATED, dependencies=[Depends(require_roles([UserRole.JUDGE, UserRole.ADMIN]))])
def submit_score_endpoint(
    score_in: ScoreCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Submit a score for a project. Only accessible by judges or admins."""
    return submit_score(db, score_in, current_user)

@router.put("/scores/{score_id}", response_model=ScoreRead, dependencies=[Depends(require_roles([UserRole.JUDGE, UserRole.ADMIN]))])
def update_score_endpoint(
    score_id: uuid.UUID,
    score_in: ScoreUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update a score. Only accessible by judges or admins."""
    return update_score(db, score_id, score_in, current_user)

@router.get("/scores/project/{project_id}", response_model=List[ScoreRead])
def list_scores_for_project_endpoint(
    project_id: uuid.UUID,
    db: Session = Depends(get_db)
):
    """List all scores for a project. Public endpoint."""
    return list_scores_for_project(db, project_id)

@router.get("/scores/judge/{judge_id}", response_model=List[ScoreRead], dependencies=[Depends(require_roles([UserRole.JUDGE, UserRole.ADMIN]))])
def list_scores_by_judge_endpoint(
    judge_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List all scores submitted by a judge. Only accessible by the judge themselves or admins."""
    return list_scores_by_judge(db, judge_id, current_user)

# Consider adding an endpoint to get aggregated results for a project
# e.g., /results/project/{project_id} 

@router.get("/check-judge", dependencies=[Depends(require_judge())])
def check_judge_rights(current_user: User = Depends(get_current_user)):
    """Check if the current user has judge rights. Only accessible by judges."""
    return {"detail": "User is a judge."}
