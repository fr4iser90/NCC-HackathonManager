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
from app.models.user import User
from app.models.team import Team, TeamMember, TeamMemberRole
from app.models.project import Project, ProjectTemplate # SQLAlchemy models
from app.schemas.project import ( # Pydantic schemas
    ProjectCreate, ProjectRead, ProjectUpdate,
    ProjectTemplateCreate, ProjectTemplateRead
)
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
    # Verify team exists
    team = db.query(Team).filter(Team.id == project_in.team_id).first()
    if not team:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Team not found")

    # Verify current user is a member of the team (or admin)
    # Re-using logic of get_team_member_or_admin manually for this payload-dependent check:
    is_admin = current_user.role == "admin"
    membership = None
    if not is_admin:
        membership = db.query(TeamMember).filter(
            TeamMember.team_id == project_in.team_id,
            TeamMember.user_id == current_user.id
        ).first()
        if not membership:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User is not a member of the specified team and not an admin.")
    
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

@router.post("/submit", tags=["projects"])
async def submit_project(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user)
):
    """
    Nimmt ein ZIP-File entgegen, entpackt es, baut ein Docker-Image und gibt Build-Logs/Status zurück.
    """
    from app.logger import get_logger
    logger = get_logger("project_submission")
    
    temp_dir = None
    try:
        # 1. Temporäres Verzeichnis für Upload
        logger.info(f"Starting project submission for user {current_user.username}")
        temp_dir = tempfile.mkdtemp(prefix="project-upload-")
        logger.info(f"Created temp directory: {temp_dir}")
        
        zip_path = os.path.join(temp_dir, "upload.zip")
        logger.info(f"Saving uploaded file to {zip_path}")
        
        # Stream the file to disk in chunks instead of loading it all into memory
        CHUNK_SIZE = 1024 * 1024  # 1MB chunks
        with open(zip_path, "wb") as buffer:
            while True:
                chunk = await file.read(CHUNK_SIZE)
                if not chunk:
                    break
                buffer.write(chunk)
        
        logger.info(f"File saved successfully: {os.path.getsize(zip_path)} bytes")
        
        # 2. Entpacken
        project_dir = os.path.join(temp_dir, "project")
        os.makedirs(project_dir, exist_ok=True)
        logger.info(f"Created project directory: {project_dir}")
        
        try:
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(project_dir)
            logger.info(f"ZIP file extracted successfully to {project_dir}")
        except zipfile.BadZipFile as e:
            logger.error(f"Bad ZIP file: {str(e)}")
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, 
                                detail=f"Invalid ZIP file: {str(e)}")
        
        # 3. Build-Skript aufrufen
        tag = f"userproject-{uuid.uuid4()}"
        logger.info(f"Generated image tag: {tag}")
        
        build_script = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../scripts/build_project_container.py'))
        logger.info(f"Build script path: {build_script}")
        
        cmd = ["python3", build_script, "--project-path", project_dir, "--tag", tag]
        logger.info(f"Executing command: {' '.join(cmd)}")
        
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        logs = ""
        for line in proc.stdout:
            logs += line
            logger.debug(line.strip())
        
        proc.wait()
        status = "success" if proc.returncode == 0 else "error"
        logger.info(f"Build completed with status: {status}, return code: {proc.returncode}")
        
        return {"status": status, "logs": logs, "image_tag": tag if status == "success" else None}
    
    except Exception as e:
        logger.error(f"Error during project submission: {str(e)}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
                            detail=f"Error processing project submission: {str(e)}")
    
    finally:
        # 4. Aufräumen
        if temp_dir and os.path.exists(temp_dir):
            try:
                shutil.rmtree(temp_dir)
                logger.info(f"Cleaned up temp directory: {temp_dir}")
            except Exception as e:
                logger.error(f"Error cleaning up temp directory: {str(e)}")
