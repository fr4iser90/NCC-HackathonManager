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

router = APIRouter(tags=["projects"])

logger = logging.getLogger(__name__)

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
    
    logger.info(f"ENTERING: get_build_logs for project_id='{project_id}', version_id='{version_id}'")
    print(f"STDERR: ENTERING get_build_logs for project_id='{project_id}', version_id='{version_id}'", file=sys.stderr)

    try:
        project_uuid = uuid.UUID(project_id)
        version_uuid = uuid.UUID(version_id)
        logger.info(f"UUIDs created: project_uuid='{project_uuid}', version_uuid='{version_uuid}'")
        print(f"STDERR: UUIDs created: project_uuid='{project_uuid}', version_uuid='{version_uuid}'", file=sys.stderr)
    except Exception as e:
        logger.error(f"Invalid UUID format: {e}", exc_info=True)
        print(f"STDERR: Invalid UUID format: {e}", file=sys.stderr)
        raise HTTPException(status_code=400, detail="Invalid UUID format")

    # Check if project exists
    project = db.query(Project).filter_by(id=project_uuid).first()
    if not project:
        logger.warning(f"Project not found for project_uuid='{project_uuid}'")
        print(f"STDERR: Project not found for project_uuid='{project_uuid}'", file=sys.stderr)
        raise HTTPException(status_code=404, detail="Project not found")
    logger.info(f"Project found: {project.id}")
    print(f"STDERR: Project found: {project.id}", file=sys.stderr)

    # Check if user is a team member or admin
    # Assuming 'project.members' is the correct way to get team members for the project
    # This part might need adjustment based on your actual TeamMember model and relationship
    is_member = False
    if hasattr(project, 'team') and project.team and hasattr(project.team, 'members'):
        is_member = current_user.id in [m.user_id for m in project.team.members]
    
    if current_user.role != "admin" and not is_member: # Simplified for now, ensure project.members or equivalent is correct
        logger.warning(f"User {current_user.id} not authorized for project {project_id}")
        print(f"STDERR: User {current_user.id} not authorized for project {project_id}", file=sys.stderr)
        raise HTTPException(status_code=403, detail="Not authorized")
    logger.info(f"User {current_user.id} authorized.")
    print(f"STDERR: User {current_user.id} authorized.", file=sys.stderr)
    
    # Get version by ID only, then check project_id
    version = db.query(ProjectVersion).filter_by(id=version_uuid).first()
    
    version_id_from_db = getattr(version, 'id', None)
    version_project_id_from_db = getattr(version, 'project_id', None)
    
    logger.info(f"DEBUG CHECK: version_found_in_db={bool(version)}, "
                f"version.id_from_db='{version_id_from_db}' (type: {type(version_id_from_db)}), "
                f"version.project_id_from_db='{version_project_id_from_db}' (type: {type(version_project_id_from_db)}), "
                f"path_version_uuid='{version_uuid}' (type: {type(version_uuid)}), "
                f"path_project_uuid='{project_uuid}' (type: {type(project_uuid)})")
    print(f"STDERR: DEBUG CHECK: version_found_in_db={bool(version)}, "
          f"version.id_from_db='{version_id_from_db}', version.project_id_from_db='{version_project_id_from_db}', "
          f"path_version_uuid='{version_uuid}', path_project_uuid='{project_uuid}'", file=sys.stderr)

    if not version:
        logger.warning(f"Version not found in DB for version_uuid='{version_uuid}'")
        print(f"STDERR: Version not found in DB for version_uuid='{version_uuid}'", file=sys.stderr)
        raise HTTPException(status_code=404, detail="Version not found (lookup by version_uuid failed)")

    if str(version.project_id) != str(project_uuid):
        logger.warning(f"Project ID mismatch: version.project_id='{version.project_id}' (type: {type(version.project_id)}) "
                       f"!= path_project_uuid='{project_uuid}' (type: {type(project_uuid)})")
        print(f"STDERR: Project ID mismatch: version.project_id='{version.project_id}' != path_project_uuid='{project_uuid}'", file=sys.stderr)
        raise HTTPException(status_code=404, detail="Version not found (project_id mismatch)")
        
    logger.info(f"Successfully found version '{version.id}' for project '{project.id}'. Returning build_logs.")
    print(f"STDERR: Successfully found version '{version.id}' for project '{project.id}'. Returning build_logs.", file=sys.stderr)
    print(f"STDERR: ACTUAL BUILD_LOGS VALUE: {repr(version.build_logs)}", file=sys.stderr)
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
        docker_registry=project_in.docker_registry,
        owner_id=current_user.id  # Set owner_id from authenticated user
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

@router.post("/{project_id}/submit_version")
async def submit_project_version(
    project_id: str,
    file: UploadFile = File(...),
    version_notes: Optional[str] = Form(None),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Submit a new version of a project (synchronous, DB-based logging).
    """
    logger.info("DEBUG: Entered submit_project_version endpoint")
    import uuid
    import shutil
    import os
    from datetime import datetime

    # Convert project_id to UUID
    try:
        project_uuid = uuid.UUID(str(project_id))
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid project_id format")

    # Get project
    project = db.query(Project).filter(Project.id == project_uuid).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Verify file type
    if not file.filename.endswith('.zip'):
        raise HTTPException(status_code=400, detail="Only ZIP files are allowed")

    # Generate unique filename
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    filename = f"version_{timestamp}_{uuid.uuid4()}.zip"
    file_path = os.path.abspath(project_file_path(filename))
    file_path = file_path.replace("/app/app/static", "/app/static")
    os.makedirs(os.path.dirname(file_path), exist_ok=True)

    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        file.file.close()

        # Create version record
        version = ProjectVersion(
            id=uuid.uuid4(),
            project_id=project_uuid,
            version_number=len(project.versions) + 1,
            file_path=filename,
            version_notes=version_notes,
            submitted_by=current_user.id,
            status="pending"
        )
        db.add(version)
        db.commit()
        db.refresh(version)

        # Extract ZIP file to a temporary directory
        temp_dir = tempfile.mkdtemp()
        try:
            logger.info("DEBUG: Before ZIP extraction...")
            print("DEBUG: Before ZIP extraction...", flush=True)
            with zipfile.ZipFile(file_path, 'r') as zip_ref:
                zip_ref.extractall(temp_dir)
            logger.info("DEBUG: After ZIP extraction...")
            print("DEBUG: After ZIP extraction...", flush=True)

            # Start build process synchronously
            build_script = os.path.join(SCRIPTS_DIR, "build_project_container.py")
            tag = f"hackathon-project-{project_id}-{version.id}"

            print("DEBUG: Starting build process...", flush=True)
            process = subprocess.run(
                [sys.executable, build_script, "--project-path", temp_dir, "--tag", tag],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                check=False
            )
            print("DEBUG: Build process finished.", flush=True)

            build_output = process.stdout if process.stdout else "No output from build process"
            if process.returncode == 0:
                version.status = "built"
                project.status = "built"
            else:
                version.status = "failed"
                project.status = "failed"

            version.build_logs = build_output
            db.commit()
            db.refresh(version)
            db.refresh(project)

            return {
                "version_id": str(version.id),
                "project_id": str(project_id),
                "status": version.status,
                "build_logs": build_output
            }
        finally:
            try:
                shutil.rmtree(temp_dir)
            except Exception:
                pass

    except Exception as e:
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
            except Exception:
                pass
        raise HTTPException(status_code=500, detail=f"Exception in submit_project_version: {e}")


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
