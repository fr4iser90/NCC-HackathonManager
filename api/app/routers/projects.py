# routers/projects.py
import uuid
from typing import List, Optional
from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
    Body,
    UploadFile,
    File,
    Query,
    Form,
)
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
import os
import tempfile
import zipfile
import subprocess
import shutil
import sys
import logging
from app.database import get_db
from datetime import datetime, timezone  # Added datetime, timezone
from app.models.user import User, UserRole
from app.models.team import Team, TeamMember, TeamMemberRole
from app.models.project import (
    Project,
    ProjectTemplate,
    ProjectVersion,
)  # SQLAlchemy models
from app.models.hackathon import Hackathon  # Need Hackathon model
from app.models.submission import Submission  # Need Submission model
from app.schemas.project import (  # Pydantic schemas
    ProjectCreate,
    ProjectRead,
    ProjectUpdate,
    ProjectStatus,  # Added ProjectStatus
    ProjectTemplateCreate,
    ProjectTemplateRead,  # Added ProjectTemplateCreate, ProjectTemplateRead
    ProjectStorageType,
    ProjectVersionCreate,
    ProjectVersionRead,
)
from app.schemas.hackathon import HackathonStatus  # HackathonStatus enum
from app.schemas.submission import (
    SubmissionContentType,
    SubmissionRead,
)  # Submission schemas
from app.auth import (
    get_current_user,
    get_team_member_or_admin,  # For create_project
    get_project_team_member_or_admin,  # For update_project
    get_project_team_owner_or_admin,  # For delete_project
)
from app.middleware import (
    require_roles,
    require_admin,
    require_organizer,
    require_judge,
)
from app.static import (
    STATIC_DIR,
    project_image_path as project_file_path,
    project_image_url as project_file_url,
    SCRIPTS_DIR,
)  # Import project file functions and SCRIPTS_DIR
from app.logger import get_logger
from app.services.project_service import create_project, submit_project_version

router = APIRouter(tags=["projects"])

# Initialize logger
logger = get_logger("projects_router")

IS_ADMIN = lambda user: any(
    r.role == "admin" for r in getattr(user, "roles_association", [])
)


@router.get("/projects/{project_id}/versions/{version_id}/build_logs")
def get_build_logs(
    project_id: str,
    version_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # Ensure sys is imported if not already at the top of the file
    import sys
    import uuid

    logger.debug(
        f"ENTERING: get_build_logs for project_id='{project_id}', version_id='{version_id}'"
    )
    # print(f"STDERR: ENTERING get_build_logs for project_id='{project_id}', version_id='{version_id}'", file=sys.stderr)

    try:
        project_uuid = uuid.UUID(project_id)
        version_uuid = uuid.UUID(version_id)
        logger.debug(
            f"UUIDs created: project_uuid='{project_uuid}', version_uuid='{version_uuid}'"
        )
        # print(f"STDERR: UUIDs created: project_uuid='{project_uuid}', version_uuid='{version_uuid}'", file=sys.stderr)
    except Exception as e:
        logger.error(f"Invalid UUID format: {e}", exc_info=True)
        # print(f"STDERR: Invalid UUID format: {e}", file=sys.stderr)
        raise HTTPException(status_code=400, detail="Invalid UUID format")

    # Check if project exists
    project = db.query(Project).filter_by(id=project_uuid).first()
    if not project:
        logger.warning(f"Project not found for project_uuid='{project_uuid}'")
        # print(f"STDERR: Project not found for project_uuid='{project_uuid}'", file=sys.stderr)
        raise HTTPException(status_code=404, detail="Project not found")
    logger.info(f"Project found: {project.id}")
    # print(f"STDERR: Project found: {project.id}", file=sys.stderr)

    # Check if user is a team member or admin
    # Assuming 'project.members' is the correct way to get team members for the project
    # This part might need adjustment based on your actual TeamMember model and relationship
    is_member = False
    if hasattr(project, "team") and project.team and hasattr(project.team, "members"):
        is_member = current_user.id in [m.user_id for m in project.team.members]

    if not IS_ADMIN(current_user) and not is_member:
        logger.warning(
            f"User {current_user.id} not authorized for project {project_id}"
        )
        # print(f"STDERR: User {current_user.id} not authorized for project {project_id}", file=sys.stderr)
        raise HTTPException(status_code=403, detail="Not authorized")
    logger.info(f"User {current_user.id} authorized.")
    # print(f"STDERR: User {current_user.id} authorized.", file=sys.stderr)

    # Debug: Log IDs und Query-Parameter
    logger.info(f"Build-Log-Request: project_id={project_id}, version_id={version_id}")
    # Get version by ID and project_id in einem Query
    version = (
        db.query(ProjectVersion)
        .filter(
            ProjectVersion.id == version_uuid, ProjectVersion.project_id == project_uuid
        )
        .first()
    )
    if not version:
        logger.warning(
            f"Version not found for project_id={project_uuid}, version_id={version_uuid}"
        )
        raise HTTPException(
            status_code=404, detail="Version not found (by project_id and version_id)"
        )
    logger.info(f"Build-Log-Request: Version gefunden: {version.id}")

    logger.info(
        f"Successfully found version '{version.id}' for project '{project.id}'. Returning build_logs."
    )
    # print(f"STDERR: Successfully found version '{version.id}' for project '{project.id}'. Returning build_logs.", file=sys.stderr)
    # print(f"STDERR: ACTUAL BUILD_LOGS VALUE: {repr(version.build_logs)}", file=sys.stderr)
    return {"build_logs": version.build_logs or ""}


# --- Project Template Endpoints (Admin-focused, basic implementation) ---
@router.post(
    "/templates/",
    response_model=ProjectTemplateRead,
    status_code=status.HTTP_201_CREATED,
    tags=["project-templates"],
)
def create_project_template(
    template_in: ProjectTemplateCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        get_current_user
    ),  # Assuming admin check will be added
):
    """
    Create a new project template. (Protected - for admins)
    """
    # Add role check here: if current_user.role != "admin": throw HTTPException
    if not IS_ADMIN(current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to create templates",
        )
    try:
        db_template = ProjectTemplate(**template_in.model_dump())
        db.add(db_template)
        db.commit()
        db.refresh(db_template)
        return db_template
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Project template name already exists.",
        )


@router.get(
    "/templates/", response_model=List[ProjectTemplateRead], tags=["project-templates"]
)
def list_project_templates(
    skip: int = 0, limit: int = 100, db: Session = Depends(get_db)
):
    """
    List all project templates.
    """
    templates = db.query(ProjectTemplate).offset(skip).limit(limit).all()
    return templates


# --- Project Endpoints ---
@router.post(
    "/",
    response_model=ProjectRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[require_roles([UserRole.ADMIN, UserRole.ORGANIZER])],
)
def create_project_endpoint(
    project_in: ProjectCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Create a new project. Only accessible by admin or organizer users.
    """
    return create_project(db, project_in, current_user)


@router.get("/", response_model=List[ProjectRead])
def list_projects(
    skip: int = 0,
    limit: int = 100,
    hackathon_id: Optional[uuid.UUID] = None,
    db: Session = Depends(get_db),
):
    """List all projects. Can be filtered by hackathon."""
    query = db.query(Project)
    if hackathon_id:
        query = query.filter(Project.hackathon_id == hackathon_id)
    projects = query.offset(skip).limit(limit).all()
    return projects


@router.get("/{project_id}", response_model=ProjectRead)
def get_project(project_id: uuid.UUID, db: Session = Depends(get_db)):
    """Get details of a specific project."""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project


@router.put("/{project_id}", response_model=ProjectRead)
def update_project(
    project_id: uuid.UUID,
    project_in: ProjectUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update a project. Only accessible by admin, organizer, or team owner."""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Check if user has permission to update
    is_admin = any(r.role == UserRole.ADMIN for r in current_user.roles_association)
    is_organizer = any(
        r.role == UserRole.ORGANIZER for r in current_user.roles_association
    )

    if not (is_admin or is_organizer):
        # Check if user is team owner
        team_member = (
            db.query(TeamMember)
            .filter(
                TeamMember.team_id == project.team_id,
                TeamMember.user_id == current_user.id,
                TeamMember.role == TeamMemberRole.owner,
            )
            .first()
        )
        if not team_member:
            raise HTTPException(
                status_code=403, detail="Not authorized to update this project"
            )

    update_data = project_in.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(project, key, value)

    db.add(project)
    db.commit()
    db.refresh(project)
    return project


@router.delete(
    "/{project_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[require_roles([UserRole.ADMIN, UserRole.ORGANIZER])],
)
def delete_project(project_id: uuid.UUID, db: Session = Depends(get_db)):
    """
    Delete a project. Only accessible by admin or organizer users.
    """
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Project not found"
        )
    db.delete(project)
    db.commit()
    return


@router.post("/{project_id}/submit_version", response_model=ProjectVersionRead)
async def submit_project_version_endpoint(
    project_id: str,
    file: UploadFile = File(...),
    version_notes: Optional[str] = Form(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Submit a new version of a project."""
    try:
        project = db.query(Project).filter(Project.id == project_id).first()
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")

        # Authorization Check:
        can_submit = False
        if project.team_id:
            # Project is part of a team
            team_member_record = (
                db.query(TeamMember)
                .filter(
                    TeamMember.team_id == project.team_id,
                    TeamMember.user_id == current_user.id,
                )
                .first()
            )
            if team_member_record and team_member_record.role in [
                TeamMemberRole.owner,
                TeamMemberRole.admin,
                TeamMemberRole.member,
            ]:
                can_submit = True
        elif project.owner_id == current_user.id:
            # Project is a solo project, and current user is the owner
            can_submit = True

        if not can_submit:
            raise HTTPException(
                status_code=403,
                detail="Not authorized to submit versions for this project",
            )

        hackathon = (
            db.query(Hackathon).filter(Hackathon.id == project.hackathon_id).first()
        )
        if not hackathon or hackathon.status != HackathonStatus.ACTIVE:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Project version cannot be submitted: Hackathon is not active.",
            )

        version = submit_project_version(
            db, project_id, file, version_notes, current_user
        )
        return ProjectVersionRead.model_validate(version)
    except Exception as e:
        logger.error(f"Fehler beim Projekt-Upload: {e}", exc_info=True)
        # Optional: Build-Log auslesen und als detail mitgeben, falls vorhanden
        detail = str(e)
        raise HTTPException(status_code=422, detail=detail)


@router.get("/{project_id}/versions", response_model=List[ProjectVersionRead])
def list_project_versions(
    project_id: uuid.UUID,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
):
    """List all versions of a project."""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    versions = (
        db.query(ProjectVersion)
        .filter(ProjectVersion.project_id == project_id)
        .order_by(ProjectVersion.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )

    return versions


@router.get("/{project_id}/versions/{version_id}", response_model=ProjectVersionRead)
def get_project_version(
    project_id: uuid.UUID, version_id: uuid.UUID, db: Session = Depends(get_db)
):
    """Get details of a specific project version."""
    version = (
        db.query(ProjectVersion)
        .filter(
            ProjectVersion.project_id == project_id, ProjectVersion.id == version_id
        )
        .first()
    )
    if not version:
        raise HTTPException(status_code=404, detail="Project version not found")
    return version
