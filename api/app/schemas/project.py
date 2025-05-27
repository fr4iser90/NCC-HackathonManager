# schemas/project.py
import uuid
import enum
from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

# Assuming TeamRead will be in schemas.team
from .team import TeamRead


class ProjectStatus(str, enum.Enum):
    # Basis-Status
    DRAFT = "draft"
    ACTIVE = "active"
    COMPLETED = "completed"
    ARCHIVED = "archived"
    FAILED = "failed"

    # Deployment-Status
    BUILDING = "building"
    BUILT = "built"
    DEPLOYING = "deploying"
    DEPLOYED = "deployed"


class ProjectStorageType(str, enum.Enum):
    # Code-Speicherung
    GITHUB = "github"
    GITLAB = "gitlab"
    BITBUCKET = "bitbucket"
    LOCAL = "local"

    # Deployment-Typen
    SERVER = "server"
    DOCKER = "docker"
    KUBERNETES = "kubernetes"
    CLOUD = "cloud"

    # Archive-Typen
    ARCHIVE = "archive"
    DOCKER_ARCHIVE = "docker_archive"
    BACKUP = "backup"

    # Kombinationen
    HYBRID = "hybrid"
    DOCKER_HYBRID = "docker_hybrid"


# Pydantic Schemas for ProjectTemplate
class ProjectTemplateBase(BaseModel):
    name: str = Field(..., max_length=255)
    description: Optional[str] = None
    tech_stack: List[str] = Field(default_factory=list)
    repository_url: Optional[str] = None
    live_url: Optional[str] = None


class ProjectTemplateCreate(ProjectTemplateBase):
    pass


class ProjectTemplateRead(ProjectTemplateBase):
    id: uuid.UUID
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# Pydantic Schemas for Project
class ProjectBase(BaseModel):
    name: str = Field(..., max_length=255)
    description: Optional[str] = None
    hackathon_id: uuid.UUID
    project_template_id: Optional[uuid.UUID] = None
    status: ProjectStatus = ProjectStatus.DRAFT
    storage_type: ProjectStorageType = ProjectStorageType.GITHUB

    # Optional URLs
    github_url: Optional[str] = None
    gitlab_url: Optional[str] = None
    bitbucket_url: Optional[str] = None
    server_url: Optional[str] = None
    docker_url: Optional[str] = None
    kubernetes_url: Optional[str] = None
    cloud_url: Optional[str] = None
    archive_url: Optional[str] = None
    docker_archive_url: Optional[str] = None
    backup_url: Optional[str] = None

    # Docker-spezifische Felder
    docker_image: Optional[str] = None
    docker_tag: Optional[str] = None
    docker_registry: Optional[str] = None
    # Team support
    team_id: Optional[uuid.UUID] = None


class ProjectCreate(ProjectBase):
    pass


class ProjectUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = None
    status: Optional[ProjectStatus] = None
    storage_type: Optional[ProjectStorageType] = None
    project_template_id: Optional[uuid.UUID] = None

    # Optional URLs
    github_url: Optional[str] = None
    gitlab_url: Optional[str] = None
    bitbucket_url: Optional[str] = None
    server_url: Optional[str] = None
    docker_url: Optional[str] = None
    kubernetes_url: Optional[str] = None
    cloud_url: Optional[str] = None
    archive_url: Optional[str] = None
    docker_archive_url: Optional[str] = None
    backup_url: Optional[str] = None

    # Docker-spezifische Felder
    docker_image: Optional[str] = None
    docker_tag: Optional[str] = None
    docker_registry: Optional[str] = None
    # Team support
    team_id: Optional[uuid.UUID] = None


class ProjectRead(ProjectBase):
    id: uuid.UUID
    created_at: datetime
    updated_at: datetime
    build_status: Optional[str] = None
    last_build_date: Optional[datetime] = None
    last_deploy_date: Optional[datetime] = None
    template: Optional[ProjectTemplateRead] = None
    team: Optional[TeamRead] = None

    model_config = {"from_attributes": True}


class ProjectVersionStatus(str, enum.Enum):
    PENDING = "pending"
    BUILDING = "building"
    BUILT = "built"
    FAILED = "failed"
    DEPLOYED = "deployed"


class ProjectVersionBase(BaseModel):
    version_notes: Optional[str] = None


class ProjectVersionCreate(ProjectVersionBase):
    pass


class ProjectVersionUpdate(ProjectVersionBase):
    status: Optional[ProjectVersionStatus] = None
    build_logs: Optional[str] = None


class ProjectVersionRead(ProjectVersionBase):
    id: uuid.UUID
    project_id: uuid.UUID
    version_number: int
    file_path: str
    submitted_by: uuid.UUID
    status: ProjectVersionStatus
    build_logs: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
