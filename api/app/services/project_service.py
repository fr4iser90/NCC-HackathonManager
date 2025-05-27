"""
Service layer for project-related business logic.
"""

from sqlalchemy.orm import Session
from app.models.project import Project, ProjectVersion, ProjectTemplate
from app.models.user import User
from app.schemas.project import ProjectCreate, ProjectUpdate
from fastapi import HTTPException, status, UploadFile
from typing import Optional
import uuid, os, shutil, tempfile, zipfile, subprocess
from datetime import datetime
from app.static import project_image_path as project_file_path, SCRIPTS_DIR
from app.logger import get_logger

logger = get_logger("project_service")


def create_project(
    db: Session, project_in: ProjectCreate, current_user: User
) -> Project:
    """
    Create a new project instance and persist it to the database.
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
        owner_id=current_user.id,
        team_id=project_in.team_id,
    )
    db.add(db_project)
    db.commit()
    db.refresh(db_project)
    return db_project


def submit_project_version(
    db: Session,
    project_id: str,
    file: UploadFile,
    version_notes: Optional[str],
    current_user: User,
) -> ProjectVersion:
    """
    Handle the submission of a new project version, including file storage and build process.
    """
    try:
        project_uuid = uuid.UUID(str(project_id))
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid project_id format")
    project = db.query(Project).filter(Project.id == project_uuid).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    if not file.filename.endswith(".zip"):
        raise HTTPException(status_code=400, detail="Only ZIP files are allowed")
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    filename = f"version_{timestamp}_{uuid.uuid4()}.zip"
    file_path = os.path.abspath(project_file_path(filename))
    file_path = file_path.replace("/app/app/static", "/app/static")
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    file.file.close()
    version = ProjectVersion(
        id=uuid.uuid4(),
        project_id=project_uuid,
        version_number=len(project.versions) + 1 if hasattr(project, "versions") else 1,
        file_path=filename,
        version_notes=version_notes,
        submitted_by=current_user.id,
        status="pending",
    )
    db.add(version)
    db.commit()
    db.expire_all()
    db.refresh(version)
    temp_dir = tempfile.mkdtemp()
    try:
        with zipfile.ZipFile(file_path, "r") as zip_ref:
            zip_ref.extractall(temp_dir)
        build_script = os.path.join(SCRIPTS_DIR, "build_image.py")
        # Use project name from ZIP filename (without .zip), username/email, and version number
        project_name = os.path.splitext(os.path.basename(file.filename))[0]
        user_name = (
            getattr(current_user, "username", None)
            or getattr(current_user, "email", None)
            or "unknown"
        )
        version_str = str(version.version_number)
        process = subprocess.run(
            [
                "python3",
                build_script,
                "--project-path",
                temp_dir,
                "--project-name",
                project_name,
                "--user-name",
                user_name,
                "--version",
                version_str,
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            check=False,
        )
        build_output = (
            process.stdout if process.stdout else "No output from build process"
        )
        if process.returncode == 0:
            version.status = "built"
            project.status = "built"
        else:
            version.status = "failed"
            project.status = "failed"
        version.build_logs = build_output
        db.commit()
        db.expire_all()
        db.refresh(version)
    except zipfile.BadZipFile:
        version.status = "failed"
        version.build_logs = "Upload is not a valid ZIP file."
        db.commit()
        db.expire_all()
        db.refresh(version)
        raise HTTPException(
            status_code=400, detail="Uploaded file is not a valid ZIP archive."
        )
    except Exception as e:
        version.status = "failed"
        version.build_logs = f"Build failed: {str(e)}"
        db.commit()
        db.expire_all()
        db.refresh(version)
        raise HTTPException(status_code=400, detail=f"Build failed: {str(e)}")
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)
    return version
