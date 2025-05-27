# models/project.py
import uuid
import enum
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any  # TYPE_CHECKING removed

from sqlalchemy import Column, String, DateTime, ForeignKey, Enum as SQLEnum, JSON, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship, Mapped, mapped_column

from app.database import Base
from .submission import (
    Submission,
)  # Assuming submission.py exists in the same models directory
from app.schemas.project import (
    ProjectStatus,
    ProjectStorageType,
)  # Import for model usage

# We will use string literals for forward references to avoid direct imports for relationships.


class ProjectTemplate(Base):
    __tablename__ = "templates"
    __table_args__ = {"schema": "projects"}

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(
        String(255), unique=True, nullable=False, index=True
    )
    description: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    tech_stack: Mapped[List[str]] = mapped_column(JSON, nullable=True)
    repository_url: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    live_url: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    projects = relationship("Project", back_populates="template")


class Project(Base):
    __tablename__ = "projects"
    __table_args__ = {"schema": "projects"}

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    project_template_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("projects.templates.id"), nullable=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    description: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    status: Mapped[ProjectStatus] = mapped_column(
        SQLEnum(ProjectStatus), nullable=False, default=ProjectStatus.DRAFT
    )

    # Neue Felder für Storage und Deployment
    storage_type: Mapped[ProjectStorageType] = mapped_column(
        SQLEnum(ProjectStorageType), nullable=False, default=ProjectStorageType.GITHUB
    )

    # Repository URLs
    github_url: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    gitlab_url: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    bitbucket_url: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    # Deployment URLs
    server_url: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    docker_url: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    kubernetes_url: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    cloud_url: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    # Archive URLs
    archive_url: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    docker_archive_url: Mapped[Optional[str]] = mapped_column(
        String(255), nullable=True
    )
    backup_url: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    # Docker-spezifische Felder
    docker_image: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    docker_tag: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    docker_registry: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    # Deployment-Status
    build_status: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    last_build_date: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    last_deploy_date: Mapped[Optional[datetime]] = mapped_column(
        DateTime, nullable=True
    )

    # Bestehende Felder
    hackathon_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("hackathons.hackathons.id"), nullable=False
    )
    owner_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("auth.users.id"), nullable=False
    )
    team_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("teams.teams.id"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    # Relationships
    template = relationship("ProjectTemplate", back_populates="projects")
    submissions = relationship(
        "Submission", back_populates="project", cascade="all, delete-orphan"
    )
    hackathon = relationship("Hackathon", back_populates="projects")
    registration = relationship("HackathonRegistration", back_populates="project")
    versions = relationship(
        "ProjectVersion", back_populates="project", cascade="all, delete-orphan"
    )
    owner = relationship("User", back_populates="projects", foreign_keys=[owner_id])
    team = relationship("Team", backref="projects")


class ProjectVersionStatus(str, enum.Enum):
    PENDING = "pending"
    BUILDING = "building"
    BUILT = "built"
    FAILED = "failed"
    DEPLOYED = "deployed"


class ProjectVersion(Base):
    __tablename__ = "project_versions"
    __table_args__ = {"schema": "projects"}

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    project_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("projects.projects.id"), nullable=False
    )
    version_number: Mapped[int] = mapped_column(nullable=False)
    file_path: Mapped[Optional[str]] = mapped_column(String, nullable=False)
    version_notes: Mapped[Optional[str]] = mapped_column(String)
    submitted_by: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("auth.users.id"), nullable=False
    )
    status: Mapped[ProjectVersionStatus] = mapped_column(
        SQLEnum(ProjectVersionStatus), default=ProjectVersionStatus.PENDING
    )
    build_logs: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    # Relationships
    project = relationship("Project", back_populates="versions")
    submitter = relationship("User", back_populates="project_versions")


# Pydantic Schemas (ProjectTemplateBase, ..., ProjectRead) and ProjectStatus enum
# have been moved to app.schemas.project.py
