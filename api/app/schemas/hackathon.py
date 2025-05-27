# schemas/hackathon.py
import uuid
import enum
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, model_validator  # Added model_validator

# Forward declaration for UserRead if needed, or direct import
# from .user import UserRead # Assuming UserRead will be in schemas.user


class HackathonMode(str, enum.Enum):
    SOLO_PRIMARY = "SOLO_PRIMARY"  # Default: Solo is primary, teams allowed
    TEAM_RECOMMENDED = "TEAM_RECOMMENDED"  # Teams are encouraged, solo allowed
    SOLO_ONLY = "SOLO_ONLY"  # Only individuals
    TEAM_ONLY = "TEAM_ONLY"  # Only teams (min_team_size > 1)


class HackathonStatus(str, enum.Enum):
    UPCOMING = "upcoming"
    ACTIVE = "active"
    COMPLETED = "completed"
    ARCHIVED = "archived"


class HackathonBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    start_date: datetime
    end_date: datetime
    status: HackathonStatus = HackathonStatus.UPCOMING
    location: Optional[str] = Field(None, max_length=255)
    organizer_id: Optional[uuid.UUID] = None
    mode: HackathonMode = HackathonMode.SOLO_PRIMARY  # Updated to use the enum
    requirements: List[str] = []
    category: Optional[str] = None
    tags: Optional[List[str]] = []
    max_team_size: Optional[int] = None
    min_team_size: Optional[int] = None
    registration_deadline: Optional[datetime] = None
    is_public: Optional[bool] = True
    banner_image_url: Optional[str] = None
    rules_url: Optional[str] = None
    sponsor: Optional[str] = None
    prizes: Optional[str] = None
    contact_email: Optional[str] = None
    allow_individuals: Optional[bool] = True
    allow_multiple_projects_per_team: Optional[bool] = False
    custom_fields: Optional[dict] = None


class HackathonCreate(HackathonBase):
    pass


class HackathonUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    status: Optional[HackathonStatus] = None
    location: Optional[str] = Field(None, max_length=255)
    organizer_id: Optional[uuid.UUID] = None
    mode: Optional[HackathonMode] = None  # Updated to use the enum
    requirements: Optional[List[str]] = None
    category: Optional[str] = None
    tags: Optional[List[str]] = None
    max_team_size: Optional[int] = None
    min_team_size: Optional[int] = None
    registration_deadline: Optional[datetime] = None
    is_public: Optional[bool] = None
    banner_image_url: Optional[str] = None
    rules_url: Optional[str] = None
    sponsor: Optional[str] = None
    prizes: Optional[str] = None
    contact_email: Optional[str] = None
    allow_individuals: Optional[bool] = None
    allow_multiple_projects_per_team: Optional[bool] = None
    custom_fields: Optional[dict] = None


# To avoid circular imports, we define UserRead as a forward reference if it's complex
# For now, let's try importing it. If it causes issues, we can use forward refs.
from .user import UserRead  # Assuming schemas/user.py is created
from .project import (
    ProjectRead,
)  # Assuming schemas/project.py exists and has ProjectRead
from .team import TeamRead  # Assuming schemas/team.py exists and has TeamRead


# New schema for reading individual hackathon registrations
class HackathonRegistrationRead(BaseModel):
    id: uuid.UUID
    hackathon_id: uuid.UUID
    project_id: uuid.UUID
    user_id: Optional[uuid.UUID] = None
    team_id: Optional[uuid.UUID] = None
    registered_at: datetime
    status: str

    # Optionally, include nested representations of the user, team, or project
    # For now, keeping it simple with IDs. Can be expanded later if needed.
    # user: Optional[UserRead] = None
    # team: Optional[TeamRead] = None
    # project: Optional[ProjectRead] = None # Or just project_id

    model_config = {"from_attributes": True}


class HackathonRead(HackathonBase):
    id: uuid.UUID
    created_at: datetime
    updated_at: datetime
    organizer: Optional[UserRead] = None
    registrations: List[HackathonRegistrationRead] = (
        []
    )  # Updated to use the new registration schema

    model_config = {"from_attributes": True}


# The old HackathonTeamRegistrationRead is no longer needed, replaced by HackathonRegistrationRead


# New schema for creating a hackathon registration (solo or team)
class ParticipantRegistrationCreate(BaseModel):
    user_id: Optional[uuid.UUID] = None
    team_id: Optional[uuid.UUID] = None

    @model_validator(mode="before")
    @classmethod
    def check_exclusive_participant(cls, values):
        user_id, team_id = values.get("user_id"), values.get("team_id")
        if not (
            (user_id is not None and team_id is None)
            or (user_id is None and team_id is not None)
        ):
            raise ValueError(
                "Either user_id or team_id must be provided, but not both."
            )
        return values
