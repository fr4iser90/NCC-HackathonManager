# routers/projects.py
import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Body, UploadFile, File, Query, Form
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
from datetime import datetime, timezone # Added datetime, timezone
from app.models.user import User
from app.models.team import Team, TeamMember, TeamMemberRole
from app.models.project import Project, ProjectTemplate, ProjectVersion # SQLAlchemy models
from app.models.hackathon import Hackathon # Need Hackathon model
from app.models.submission import Submission # Need Submission model
from app.schemas.project import ( # Pydantic schemas
    ProjectCreate, ProjectRead, ProjectUpdate, ProjectStatus, # Added ProjectStatus
    ProjectTemplateCreate, ProjectTemplateRead, # Added ProjectTemplateCreate, ProjectTemplateRead
    ProjectStorageType, ProjectVersionCreate, ProjectVersionRead
)
from app.schemas.hackathon import HackathonStatus # HackathonStatus enum
from app.schemas.submission import SubmissionContentType, SubmissionRead # Submission schemas
from app.auth import (
    get_current_user,
    get_team_member_or_admin, # For create_project
    get_project_team_member_or_admin, # For update_project
    get_project_team_owner_or_admin # For delete_project
)
from app.static import STATIC_DIR, project_image_path as project_file_path, project_image_url as project_file_url, SCRIPTS_DIR # Import project file functions and SCRIPTS_DIR
from app.logger import get_logger
from app.services.project_service import create_project, submit_project_version

router = APIRouter(tags=["projects"])

# Initialize logger
logger = get_logger("projects_router")

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
    
    logger.debug(f"ENTERING: get_build_logs for project_id='{project_id}', version_id='{version_id}'")
    # print(f"STDERR: ENTERING get_build_logs for project_id='{project_id}', version_id='{version_id}'", file=sys.stderr)

    try:
        project_uuid = uuid.UUID(project_id)
        version_uuid = uuid.UUID(version_id)
        logger.debug(f"UUIDs created: project_uuid='{project_uuid}', version_uuid='{version_uuid}'")
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
    if hasattr(project, 'team') and project.team and hasattr(project.team, 'members'):
        is_member = current_user.id in [m.user_id for m in project.team.members]
    
    if current_user.role != "admin" and not is_member: # Simplified for now, ensure project.members or equivalent is correct
        logger.warning(f"User {current_user.id} not authorized for project {project_id}")
        # print(f"STDERR: User {current_user.id} not authorized for project {project_id}", file=sys.stderr)
        raise HTTPException(status_code=403, detail="Not authorized")
    logger.info(f"User {current_user.id} authorized.")
    # print(f"STDERR: User {current_user.id} authorized.", file=sys.stderr)
    
    # Debug: Log IDs und Query-Parameter
    logger.info(f"Build-Log-Request: project_id={project_id}, version_id={version_id}")
    # Get version by ID and project_id in einem Query
    version = db.query(ProjectVersion).filter(
        ProjectVersion.id == version_uuid,
        ProjectVersion.project_id == project_uuid
    ).first()
    if not version:
        logger.warning(f"Version not found for project_id={project_uuid}, version_id={version_uuid}")
        raise HTTPException(status_code=404, detail="Version not found (by project_id and version_id)")
    logger.info(f"Build-Log-Request: Version gefunden: {version.id}")

    logger.info(f"Successfully found version '{version.id}' for project '{project.id}'. Returning build_logs.")
    # print(f"STDERR: Successfully found version '{version.id}' for project '{project.id}'. Returning build_logs.", file=sys.stderr)
    # print(f"STDERR: ACTUAL BUILD_LOGS VALUE: {repr(version.build_logs)}", file=sys.stderr)
    return {"build_logs": version.build_logs or ""}

# --- Project Template Endpoints (Admin-focused, basic implementation) ---
@router.post("/templates/", response_model=ProjectTemplateRead, status_code=status.HTTP_201_CREATED, tags=["project-templates"])
def create_project_template(
    template_in: ProjectTemplateCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user) # Assuming admin check will be added
):
    """
    Create a new project template. (Protected - for admins)
    """
    # Add role check here: if current_user.role != "admin": throw HTTPException
    if current_user.role not in ["admin"]:
         raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to create templates")
    try:
        db_template = ProjectTemplate(**template_in.model_dump())
        db.add(db_template)
        db.commit()
        db.refresh(db_template)
        return db_template
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Project template name already exists.")

@router.get("/templates/", response_model=List[ProjectTemplateRead], tags=["project-templates"])
def list_project_templates(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """
    List all project templates.
    """
    templates = db.query(ProjectTemplate).offset(skip).limit(limit).all()
    return templates

# --- Project Endpoints ---
@router.post("/", response_model=ProjectRead, status_code=status.HTTP_201_CREATED, tags=["projects"])
async def create_project_endpoint(
    project_in: ProjectCreate, 
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_user)
):
    """
    Create a new project with storage and deployment options.
    """
    try:
        db_project = create_project(db, project_in, current_user)
        return db_project
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Error creating project. Check input data.")

@router.get("/", response_model=List[ProjectRead], tags=["projects"])
def list_projects(
    team_id: Optional[uuid.UUID] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    status: Optional[ProjectStatus] = None,
    storage_type: Optional[ProjectStorageType] = None,
    hackathon_id: Optional[str] = None
):
    """
    List projects with optional filtering by status, storage type, and hackathon.
    """
    query = db.query(Project)
    if team_id:
        query = query.filter(Project.team_id == team_id)
    if status:
        query = query.filter(Project.status == status)
    if storage_type:
        query = query.filter(Project.storage_type == storage_type)
    if hackathon_id:
        query = query.filter(Project.hackathon_id == hackathon_id)
    projects = query.offset(skip).limit(limit).all()
    return projects

@router.get("/{project_id}", response_model=ProjectRead, tags=["projects"])
def get_project(project_id: uuid.UUID, db: Session = Depends(get_db)):
    """
    Get details of a specific project by ID.
    """
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    return project

@router.put("/{project_id}", response_model=ProjectRead, tags=["projects"])
def update_project(
    project_id: uuid.UUID,
    project_in: ProjectUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    db_project = db.query(Project).filter(Project.id == project_id).first()
    if not db_project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    # Check hackathon status
    hackathon = db.query(Hackathon).filter(Hackathon.id == db_project.hackathon_id).first()
    if not hackathon or hackathon.status != HackathonStatus.ACTIVE:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Project cannot be edited: Hackathon is not active.")
    # SOLO: Only owner can update
    if not db_project.team_id:
        if db_project.owner_id != current_user.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User is not the owner.")
    else:
        # TEAM: Only owner, admin, or member can update (no platform admin override)
        team_member = db.query(TeamMember).filter(TeamMember.team_id == db_project.team_id, TeamMember.user_id == current_user.id).first()
        if not team_member or team_member.role not in [TeamMemberRole.owner, TeamMemberRole.admin, TeamMemberRole.member]:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User is not a permitted team member (owner, admin, or member).")
    update_data = project_in.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_project, key, value)
    try:
        db.add(db_project)
        db.commit()
        db.refresh(db_project)
        return db_project
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Error updating project.")

@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["projects"])
def delete_project(
    project_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    db_project = db.query(Project).filter(Project.id == project_id).first()
    if not db_project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    # Check hackathon status
    hackathon = db.query(Hackathon).filter(Hackathon.id == db_project.hackathon_id).first()
    if not hackathon or hackathon.status != HackathonStatus.ACTIVE:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Project cannot be deleted: Hackathon is not active.")
    # SOLO: Only owner can delete
    if not db_project.team_id:
        if db_project.owner_id != current_user.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User is not the owner.")
    else:
        # TEAM: Only owner, admin, or member can delete (no platform admin override)
        team_member = db.query(TeamMember).filter(TeamMember.team_id == db_project.team_id, TeamMember.user_id == current_user.id).first()
        if not team_member or team_member.role not in [TeamMemberRole.owner, TeamMemberRole.admin, TeamMemberRole.member]:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User is not a permitted team member (owner, admin, or member).")
    db.delete(db_project)
    db.commit()
    return

@router.post("/{project_id}/submit_version", response_model=ProjectVersionRead)
async def submit_project_version_endpoint(
    project_id: str,
    file: UploadFile = File(...),
    version_notes: Optional[str] = Form(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Submit a new version of a project (synchronous, DB-based logging).
    """
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    hackathon = db.query(Hackathon).filter(Hackathon.id == project.hackathon_id).first()
    if not hackathon or hackathon.status != HackathonStatus.ACTIVE:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Project version cannot be submitted: Hackathon is not active.")
    version = submit_project_version(db, project_id, file, version_notes, current_user)
    return ProjectVersionRead.model_validate(version)

@router.get("/{project_id}/versions", response_model=list[ProjectVersionRead])
async def get_project_versions(
    project_id: str,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Get all versions of a project."""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    return project.versions

@router.get("/{project_id}/versions/{version_id}", response_model=ProjectVersionRead)
async def get_project_version(
    project_id: str,
    version_id: str,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Get a specific version of a project."""
    import uuid
    try:
        project_uuid = uuid.UUID(str(project_id))
        version_uuid = uuid.UUID(str(version_id))
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid UUID: {e}")

    version = db.query(ProjectVersion).filter(
        ProjectVersion.project_id == project_uuid,
        ProjectVersion.id == version_uuid
    ).first()
    
    if not version:
        raise HTTPException(status_code=404, detail="Version not found")

    return version
