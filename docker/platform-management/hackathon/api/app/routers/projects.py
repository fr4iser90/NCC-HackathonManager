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

router = APIRouter(prefix="/projects", tags=["projects"])

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
async def create_project(
    project_in: ProjectCreate, 
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_user)
):
    """
    Create a new project with storage and deployment options.
    """
    db_project = Project(
        name=project_in.name,
        description=project_in.description,
        hackathon_id=project_in.hackathon_id,
        project_template_id=project_in.project_template_id,
        status=project_in.status,
        storage_type=project_in.storage_type,
        github_url=project_in.github_url,
        gitlab_url=project_in.gitlab_url,
        bitbucket_url=project_in.bitbucket_url,
        server_url=project_in.server_url,
        docker_url=project_in.docker_url,
        kubernetes_url=project_in.kubernetes_url,
        cloud_url=project_in.cloud_url,
        archive_url=project_in.archive_url,
        docker_archive_url=project_in.docker_archive_url,
        backup_url=project_in.backup_url,
        docker_image=project_in.docker_image,
        docker_tag=project_in.docker_tag,
        docker_registry=project_in.docker_registry
    )
    try:
        db.add(db_project)
        db.commit()
        db.refresh(db_project)
        return db_project
    except IntegrityError: # Should not happen if name is not unique in Project table itself, but good practice
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
    # Auth: current_user must be a member of the project's team or an admin
    authorized_member: TeamMember = Depends(get_project_team_member_or_admin) 
):
    """
    Update a project with new storage or deployment information.
    """
    db_project = db.query(Project).filter(Project.id == project_id).first()
    if not db_project:
        # This check is technically redundant due to get_project_team_member_or_admin,
        # but kept for clarity / defense in depth.
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")

    # The dependency authorized_member already confirms user is part of team or admin.
    # If admin and not direct member, authorized_member might be None, handled by dependency logic.

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
    # Auth: current_user must be an owner of the project's team or an admin
    authorized_owner_or_admin: TeamMember = Depends(get_project_team_owner_or_admin) 
):
    """
    Delete a project. User must be an owner of the project's team or an admin.
    """
    db_project = db.query(Project).filter(Project.id == project_id).first()
    if not db_project:
        # Redundant check, dependency handles it.
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")

    # Dependency authorized_owner_or_admin ensures correct permissions.

    db.delete(db_project)
    db.commit()
    return 

@router.post("/{project_id}/submit_version", response_model=ProjectVersionRead)
async def submit_project_version(
    project_id: str,
    file: UploadFile = File(...),
    version_notes: Optional[str] = Form(None),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Submit a new version of a project."""
    # Get project
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Verify file type
    if not file.filename.endswith('.zip'):
        raise HTTPException(status_code=400, detail="Only ZIP files are allowed")

    # Create upload directory if it doesn't exist
    upload_dir = os.path.join("uploads", "projects", str(project_id))
    os.makedirs(upload_dir, exist_ok=True)

    # Generate unique filename
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    filename = f"version_{timestamp}_{uuid.uuid4()}.zip"
    file_path = os.path.join(upload_dir, filename)

    try:
        # Save file
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # Create version record
        version = ProjectVersion(
            id=uuid.uuid4(),
            project_id=project_id,
            version_number=len(project.versions) + 1,
            file_path=file_path,
            version_notes=version_notes,
            submitted_by=current_user.id,
            status="pending"
        )
        db.add(version)
        db.commit()
        db.refresh(version)

        # Update project status
        project.status = "building"
        db.commit()

        return version

    except Exception as e:
        # Clean up file if there was an error
        if os.path.exists(file_path):
            os.remove(file_path)
        raise HTTPException(status_code=500, detail=str(e))

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
    version = db.query(ProjectVersion).filter(
        ProjectVersion.project_id == project_id,
        ProjectVersion.id == version_id
    ).first()
    
    if not version:
        raise HTTPException(status_code=404, detail="Version not found")

    return version
