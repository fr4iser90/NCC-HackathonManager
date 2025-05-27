"""
Service layer for judging-related business logic.
"""

from sqlalchemy.orm import Session
from app.models.judging import Criterion, Score
from app.models.project import Project
from app.schemas.judging import CriterionCreate, ScoreCreate, ScoreUpdate
from app.models.user import User
from fastapi import HTTPException, status
import uuid
from sqlalchemy.exc import IntegrityError

IS_ADMIN = lambda user: any(
    r.role == "admin" for r in getattr(user, "roles_association", [])
)


def create_criterion(
    db: Session, criterion_in: CriterionCreate, current_user: User
) -> Criterion:
    """Create a new judging criterion (admin only)."""
    if not IS_ADMIN(current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can create criteria.",
        )
    try:
        db_criterion = Criterion(**criterion_in.model_dump())
        db.add(db_criterion)
        db.commit()
        db.refresh(db_criterion)
        return db_criterion
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Error creating criterion."
        )


def update_criterion(
    db: Session,
    criterion_id: uuid.UUID,
    criterion_in: CriterionCreate,
    current_user: User,
) -> Criterion:
    """Update a judging criterion (admin only)."""
    if not IS_ADMIN(current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can update criteria.",
        )
    db_criterion = db.query(Criterion).filter(Criterion.id == criterion_id).first()
    if not db_criterion:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Criterion not found"
        )
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
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Error updating criterion."
        )


def delete_criterion(db: Session, criterion_id: uuid.UUID, current_user: User):
    """Delete a judging criterion (admin only)."""
    if not IS_ADMIN(current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can delete criteria.",
        )
    db_criterion = db.query(Criterion).filter(Criterion.id == criterion_id).first()
    if not db_criterion:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Criterion not found"
        )
    db.delete(db_criterion)
    db.commit()
    return


def submit_score(db: Session, score_in: ScoreCreate, current_user: User) -> Score:
    """Submit a score for a project and criterion (judge or admin only)."""
    if not any(
        r.role in ["judge", "admin"]
        for r in getattr(current_user, "roles_association", [])
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only judges or admins can submit scores.",
        )
    project = db.query(Project).filter(Project.id == score_in.project_id).first()
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Project not found."
        )
    criterion = db.query(Criterion).filter(Criterion.id == score_in.criteria_id).first()
    if not criterion:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Criterion not found."
        )
    if score_in.score < 0 or score_in.score > criterion.max_score:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Score must be between 0 and {criterion.max_score} for this criterion.",
        )
    db_score = Score(**score_in.model_dump(), judge_id=current_user.id)
    try:
        db.add(db_score)
        db.commit()
        db.refresh(db_score)
        return db_score
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This judge has already scored this project for this criterion.",
        )


def update_score(
    db: Session, score_id: uuid.UUID, score_in: ScoreUpdate, current_user: User
) -> Score:
    """Update a score (judge or admin only)."""
    db_score = db.query(Score).filter(Score.id == score_id).first()
    if not db_score:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Score not found"
        )
    if db_score.judge_id != current_user.id and not IS_ADMIN(current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this score.",
        )
    if score_in.score is not None:
        criterion = (
            db.query(Criterion).filter(Criterion.id == db_score.criteria_id).first()
        )
        if not criterion:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Associated criterion not found. Cannot validate score.",
            )
        if score_in.score < 0 or score_in.score > criterion.max_score:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Score must be between 0 and {criterion.max_score} for this criterion.",
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
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Error updating score."
        )


def list_scores_for_project(db: Session, project_id: uuid.UUID):
    """List all scores for a project."""
    scores = db.query(Score).filter(Score.project_id == project_id).all()
    return scores


def list_scores_by_judge(db: Session, judge_id: uuid.UUID, current_user: User):
    """List all scores submitted by a judge (or admin)."""
    if judge_id != current_user.id and not IS_ADMIN(current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view these scores.",
        )
    scores = db.query(Score).filter(Score.judge_id == judge_id).all()
    return scores
