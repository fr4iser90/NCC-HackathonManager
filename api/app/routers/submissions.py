from typing import List, Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.submission import Submission
from app.models.user import User
from app.schemas.submission import SubmissionCreate, SubmissionRead, SubmissionUpdate
from app.auth import (
    get_submission_owner_project_team_member_or_admin,
    get_submission_owner_project_team_owner_or_admin,
    get_project_team_member_or_admin,
)
from app.models.project import Project # Required for project existence check

router = APIRouter()


@router.post(
    "/projects/{project_id}/submissions/",
    response_model=SubmissionRead,
    status_code=status.HTTP_201_CREATED,
    tags=["Submissions"],
    summary="Create a new submission for a project",
)
def create_submission(
    project_id: UUID,
    submission_in: SubmissionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_project_team_member_or_admin), # User must be a team member of the project
) -> Submission:
    """
    Create a new submission for a project.

    Users can only submit to projects they are a member of.
    """
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project with id {project_id} not found",
        )

    submission = Submission(
        **submission_in.model_dump(),
        user_id=current_user.id,
    )
    db.add(submission)
    db.commit()
    db.refresh(submission)
    return submission


@router.get(
    "/projects/{project_id}/submissions/",
    response_model=List[SubmissionRead],
    tags=["Submissions"],
    summary="List all submissions for a project",
)
def list_submissions_for_project(
    project_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_project_team_member_or_admin), # User must be a team member or admin
) -> List[Submission]:
    """
    List all submissions for a specific project.
    Only team members of the project or administrators can view submissions.
    """
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project with id {project_id} not found",
        )
    return project.submissions


@router.get(
    "/submissions/{submission_id}",
    response_model=SubmissionRead,
    tags=["Submissions"],
    summary="Get a specific submission by ID",
)
def get_submission(
    submission_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_submission_owner_project_team_member_or_admin),
) -> Submission:
    """
    Get a specific submission by its ID.
    Accessible by the submission owner, any member of the project team, or an administrator.
    """
    submission = (
        db.query(Submission).filter(Submission.id == submission_id).first()
    )
    if not submission:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Submission with id {submission_id} not found",
        )
    return submission


@router.put(
    "/submissions/{submission_id}",
    response_model=SubmissionRead,
    tags=["Submissions"],
    summary="Update a submission",
)
def update_submission(
    submission_id: UUID,
    submission_in: SubmissionUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_submission_owner_project_team_owner_or_admin),
) -> Submission:
    """
    Update an existing submission.
    Only the submission owner, the project's team owner, or an administrator can update a submission.
    """
    submission = (
        db.query(Submission).filter(Submission.id == submission_id).first()
    )
    if not submission:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Submission with id {submission_id} not found",
        )

    update_data = submission_in.model_dump(exclude_none=True)
    for key, value in update_data.items():
        setattr(submission, key, value)

    db.add(submission)
    db.commit()
    db.refresh(submission)
    return submission


@router.delete(
    "/submissions/{submission_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    tags=["Submissions"],
    summary="Delete a submission",
)
def delete_submission(
    submission_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_submission_owner_project_team_owner_or_admin),
) -> None:
    """
    Delete a submission.
    Only the submission owner, the project's team owner, or an administrator can delete a submission.
    """
    submission = (
        db.query(Submission).filter(Submission.id == submission_id).first()
    )
    if not submission:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Submission with id {submission_id} not found",
        )

    db.delete(submission)
    db.commit()
    return None 