# routers/projects.py
import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Body, UploadFile, File
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
from app.models.project import Project, ProjectTemplate # SQLAlchemy models
from app.models.hackathon import Hackathon # Need Hackathon model
from app.models.submission import Submission # Need Submission model
from app.schemas.project import ( # Pydantic schemas
    ProjectCreate, ProjectRead, ProjectUpdate, ProjectStatus, # Added ProjectStatus
    ProjectTemplateCreate, ProjectTemplateRead
)
from app.schemas.hackathon import HackathonStatus # HackathonStatus enum
from app.schemas.submission import SubmissionContentType, SubmissionRead # Submission schemas
from app.auth import (
    get_current_user,
    get_team_member_or_admin, # For create_project
    get_project_team_member_or_admin, # For update_project
    get_project_team_owner_or_admin # For delete_project
)

router = APIRouter()

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
    Create a new project. User must be a member of the specified team.
    """
    # Verify hackathon exists
    hackathon = db.query(Hackathon).filter(Hackathon.id == project_in.hackathon_id).first()
    if not hackathon:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Hackathon not found")

    # Verify project template exists if provided
    db_template = None
    if project_in.project_template_id:
        db_template = db.query(ProjectTemplate).filter(ProjectTemplate.id == project_in.project_template_id).first()
        if not db_template:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Template with id {project_in.project_template_id} not found")

    db_project = Project(**project_in.model_dump())
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
    db: Session = Depends(get_db)
):
    """
    List projects. Can be filtered by team_id.
    """
    query = db.query(Project)
    if team_id:
        query = query.filter(Project.team_id == team_id)
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
    Update a project. User must be a member of the project's team or an admin.
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

@router.post("/{project_id}/submit_version", tags=["projects"])
async def submit_project_version(
    project_id: uuid.UUID,
    file: UploadFile = File(...),
    description: Optional[str] = Body(None), # Optional description for the submission
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Submits a new version (ZIP file) for an existing project within a hackathon.
    The project must be linked to an active hackathon, and the user must have submission rights.
    """
    from app.logger import get_logger
    logger = get_logger("project_submission_version")

    # 1. Fetch Project, Team, and Hackathon
    db_project = db.query(Project).filter(Project.id == project_id).first()
    if not db_project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    registration = db_project.registration
    if not registration or not registration.hackathon_id or not registration.team_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Project is not properly associated with a hackathon and team.")

    db_hackathon = db.query(Hackathon).filter(Hackathon.id == registration.hackathon_id).first()
    if not db_hackathon:
        # Should not happen if registration.hackathon_id is valid, but good check
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Associated hackathon not found")

    db_team = db.query(Team).filter(Team.id == registration.team_id).first()
    if not db_team:
        # Should not happen if registration.team_id is valid
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Associated team not found")

    # 2. Authorization
    team_membership = db.query(TeamMember).filter(
        TeamMember.team_id == registration.team_id,
        TeamMember.user_id == current_user.id
    ).first()

    # Allow submission if user is team owner or admin, or platform admin
    can_submit = False
    if team_membership and team_membership.role in [TeamMemberRole.owner, TeamMemberRole.admin]:
        can_submit = True
    elif current_user.role == "admin":
        can_submit = True

    if not can_submit:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User does not have permission to submit for this project's team.")

    # 3. Validation
    if db_hackathon.status != HackathonStatus.ACTIVE:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Hackathon is not currently active. Submissions are closed.")
    
    # Using end_date as the submission deadline for now.
    # A more specific submission_deadline field could be added to Hackathon model later.
    if db_hackathon.end_date < datetime.now(timezone.utc):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Hackathon submission deadline has passed.")

    temp_dir = None
    try:
        logger.info(f"Starting submission for project {project_id} by user {current_user.username}")
        temp_dir = tempfile.mkdtemp(prefix="project-submit-version-")
        zip_path = os.path.join(temp_dir, "upload.zip")
        
        CHUNK_SIZE = 1024 * 1024  # 1MB
        with open(zip_path, "wb") as buffer:
            while True:
                chunk = await file.read(CHUNK_SIZE)
                if not chunk:
                    break
                buffer.write(chunk)
        logger.info(f"File saved to {zip_path}, size: {os.path.getsize(zip_path)} bytes")

        project_files_dir = os.path.join(temp_dir, "project_files")
        os.makedirs(project_files_dir, exist_ok=True)
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(project_files_dir)
        logger.info(f"ZIP extracted to {project_files_dir}")

        image_tag = f"userproject-{db_project.id}-{uuid.uuid4().hex[:8]}" # More specific tag
        build_script = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../scripts/build_project_container.py'))
        cmd = ["python3", build_script, "--project-path", project_files_dir, "--tag", image_tag]
        
        logger.info(f"Executing build: {' '.join(cmd)}")
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        build_logs = ""
        for line in proc.stdout:
            build_logs += line
            logger.debug(f"Build log: {line.strip()}")
        proc.wait()

        build_status_str = "success" if proc.returncode == 0 else "error"
        logger.info(f"Build for project {project_id} completed with status: {build_status_str} (code: {proc.returncode})")

        if proc.returncode != 0:
            # Optionally, save failed build attempt as a submission with error status?
            # For now, just raise HTTP Exception with logs.
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, 
                                detail={"message": "Project build failed.", "logs": build_logs})

        # 4. Create Submission Record
        db_submission = Submission(
            project_id=project_id,
            user_id=current_user.id,
            content_type=SubmissionContentType.DOCKER_IMAGE_TAG,
            content_value=image_tag,
            description=description # Optional description from request
        )
        db.add(db_submission)

        # 5. Update Project Status
        db_project.status = ProjectStatus.SUBMITTED # Or a more specific status like "VERSION_SUBMITTED"
        db.add(db_project)
        
        db.commit()
        db.refresh(db_submission)
        db.refresh(db_project) # Refresh project to get updated status if needed by response

        # Populate submitter for the response
        # db_submission.submitter = current_user # This would work if relationship is configured for immediate population
        # For SubmissionRead, it will be populated by SQLAlchemy if lazy loading is appropriate or eager loading is set.
        # Let's ensure the UserRead schema can be resolved for the submitter field.
        
        # Construct the response manually if direct refresh doesn't populate nested UserRead for submitter
        # This is often needed if the relationship isn't eagerly loaded in this specific query path.
        # However, Pydantic's from_attributes should handle it if the ORM object is correct.
        
        from app.schemas.submission import SubmissionRead
        return {
            "submission": SubmissionRead.model_validate(db_submission),
            "status": build_status_str,
            "logs": build_logs
        }

    except HTTPException: # Re-raise HTTPExceptions to preserve status code and detail
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error during project submission version for project {project_id}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
                            detail=f"An unexpected error occurred: {str(e)}")
    finally:
        if temp_dir and os.path.exists(temp_dir):
            try:
                shutil.rmtree(temp_dir)
                logger.info(f"Cleaned up temp directory: {temp_dir}")
            except Exception as e:
                logger.error(f"Failed to clean up temp directory {temp_dir}: {str(e)}", exc_info=True)
                # Optionally, log this error but don't raise it. Cleanup is best effort.
