# models/project.py
import uuid
import enum
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any # TYPE_CHECKING removed

from sqlalchemy import Column, String, DateTime, ForeignKey, Enum as SQLEnum, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship, Mapped, mapped_column

from app.database import Base
from .submission import Submission # Assuming submission.py exists in the same models directory
from app.schemas.project import ProjectStatus # Import for model usage
# We will use string literals for forward references to avoid direct imports for relationships.

class ProjectTemplate(Base):
    __tablename__ = "templates"
    __table_args__ = {"schema": "projects"}

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    description: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    tech_stack: Mapped[List[str]] = mapped_column(JSON, nullable=True)
    repository_url: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    live_url: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    projects = relationship("Project", back_populates="template")

class Project(Base):
    __tablename__ = "projects"
    __table_args__ = {"schema": "projects"}

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    # team_id is removed, project is now linked via HackathonRegistration
    project_template_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("projects.templates.id"), nullable=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    description: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    status: Mapped[ProjectStatus] = mapped_column(SQLEnum(ProjectStatus, name="project_status_enum", create_type=False), nullable=False, default=ProjectStatus.DRAFT)
    repository_url: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    # hackathon_id is removed, project is now linked via HackathonRegistration
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    # team relationship is removed
    template = relationship("ProjectTemplate", foreign_keys=[project_template_id], back_populates="projects")
    submissions = relationship("Submission", back_populates="project", cascade="all, delete-orphan")

    # New relationship to HackathonRegistration (one-to-one as project_id is unique in HackathonRegistration)
    registration: Mapped[Optional["HackathonRegistration"]] = relationship(
        "HackathonRegistration", # String literal
        back_populates="project"
        # uselist=False is implied by Mapped[Optional[...]] not Mapped[List[...]]
    )

# Pydantic Schemas (ProjectTemplateBase, ..., ProjectRead) and ProjectStatus enum
# have been moved to app.schemas.project.py
