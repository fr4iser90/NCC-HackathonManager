# schemas/project.py
import uuid
import enum
from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

# Assuming TeamRead will be in schemas.team
from .team import TeamRead

class ProjectStatus(str, enum.Enum):
    PENDING = "pending"
    DRAFT = "draft"
    ACTIVE = "active"
    SUBMITTED = "submitted"
    COMPLETED = "completed"
    ARCHIVED = "archived"
    FAILED = "failed"

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

class ProjectCreate(ProjectBase):
    project_template_id: Optional[uuid.UUID] = None # Ensure this is explicit, matches model

class ProjectUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = None
    status: Optional[ProjectStatus] = None
    # team_id: Optional[uuid.UUID] = None # Removed
    project_template_id: Optional[uuid.UUID] = None # Added for admin update
    repository_url: Optional[str] = Field(None, max_length=255) # Added for admin update

class ProjectRead(ProjectBase): # ProjectBase no longer has team_id
    id: uuid.UUID
    created_at: datetime
    updated_at: datetime
    # team: Optional[TeamRead] = None # Removed, team info is via HackathonRegistration if applicable
    template: Optional[ProjectTemplateRead] = None # Populated template details
    # If we want to show registration details directly on a project, we'd add a field here
    # for HackathonRegistrationRead, but it might be better to access it via the hackathon.

    model_config = {"from_attributes": True}
