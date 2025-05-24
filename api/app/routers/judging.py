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

router = APIRouter()

# --- Criterion Endpoints (Admin-focused) ---
@router.post("/criteria/", response_model=CriterionRead, status_code=status.HTTP_201_CREATED, tags=["judging-criteria"])
def create_criterion(
    criterion_in: CriterionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only admins can create criteria.")
    try:
        db_criterion = Criterion(**criterion_in.model_dump())
        db.add(db_criterion)
        db.commit()
        db.refresh(db_criterion)
        return db_criterion
    except IntegrityError: # Should not happen if name is not unique, but good for other constraints
        db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Error creating criterion.")

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
def update_criterion(
    criterion_id: uuid.UUID,
    criterion_in: CriterionCreate, # Using Create schema for full update, can use a dedicated Update schema
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only admins can update criteria.")
    db_criterion = db.query(Criterion).filter(Criterion.id == criterion_id).first()
    if not db_criterion:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Criterion not found")

    update_data = criterion_in.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_criterion, key, value)
    try:
        db.add(db_criterion)
        db.commit()
        db.refresh(db_criterion)
        return db_criterion
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Error updating criterion.")

@router.delete("/criteria/{criterion_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["judging-criteria"])
def delete_criterion(criterion_id: uuid.UUID, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if current_user.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only admins can delete criteria.")
    db_criterion = db.query(Criterion).filter(Criterion.id == criterion_id).first()
    if not db_criterion:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Criterion not found")
    db.delete(db_criterion)
    db.commit()
    return

# --- Score Endpoints (Judge-focused) ---
@router.post("/scores/", response_model=ScoreRead, status_code=status.HTTP_201_CREATED, tags=["judging-scores"])
def submit_score(
    score_in: ScoreCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user) # This user is the judge
):
    if current_user.role not in ["judge", "admin"]: # Allow admins to submit scores too, if needed
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only judges or admins can submit scores.")

    # Check if project exists
    project = db.query(Project).filter(Project.id == score_in.project_id).first()
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found.")

    # Check if criterion exists
    criterion = db.query(Criterion).filter(Criterion.id == score_in.criteria_id).first()
    if not criterion:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Criterion not found.")

    # Validate score against criterion max_score
    if score_in.score < 0 or score_in.score > criterion.max_score:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Score must be between 0 and {criterion.max_score} for this criterion."
        )

    db_score = Score(
        **score_in.model_dump(),
        judge_id=current_user.id
    )
    try:
        db.add(db_score)
        db.commit()
        db.refresh(db_score)
        return db_score
    except IntegrityError: # Handles the UniqueConstraint for (project_id, criteria_id, judge_id)
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This judge has already scored this project for this criterion."
        )

@router.put("/scores/{score_id}", response_model=ScoreRead, tags=["judging-scores"])
def update_score(
    score_id: uuid.UUID,
    score_in: ScoreUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    db_score = db.query(Score).filter(Score.id == score_id).first()
    if not db_score:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Score not found")

    # Only the judge who submitted or an admin can update
    if db_score.judge_id != current_user.id and current_user.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to update this score.")

    # Fetch criterion to validate score if score is being updated
    if score_in.score is not None:
        criterion = db.query(Criterion).filter(Criterion.id == db_score.criteria_id).first()
        if not criterion:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Associated criterion not found. Cannot validate score.")
        if score_in.score < 0 or score_in.score > criterion.max_score:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Score must be between 0 and {criterion.max_score} for this criterion."
            )

    update_data = score_in.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_score, key, value)
    try:
        db.add(db_score)
        db.commit()
        db.refresh(db_score)
        return db_score
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Error updating score.")

@router.get("/scores/project/{project_id}", response_model=List[ScoreRead], tags=["judging-scores"])
def list_scores_for_project(project_id: uuid.UUID, db: Session = Depends(get_db)):
    scores = db.query(Score).filter(Score.project_id == project_id).all()
    if not scores:
        # Return empty list if no scores, or 404 if project itself doesn't exist (handled by project check elsewhere)
        pass # Allow returning empty list
    return scores

@router.get("/scores/judge/{judge_id}", response_model=List[ScoreRead], tags=["judging-scores"])
def list_scores_by_judge(judge_id: uuid.UUID, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    # A judge can see their own scores, an admin can see any judge's scores
    if judge_id != current_user.id and current_user.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to view these scores.")
    scores = db.query(Score).filter(Score.judge_id == judge_id).all()
    return scores

# Consider adding an endpoint to get aggregated results for a project
# e.g., /results/project/{project_id} 