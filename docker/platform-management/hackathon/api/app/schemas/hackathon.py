# schemas/hackathon.py
import uuid
import enum
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field

# Forward declaration for UserRead if needed, or direct import
# from .user import UserRead # Assuming UserRead will be in schemas.user

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
    mode: str = "TEAM_RECOMMENDED"
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
    mode: Optional[str] = None
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
from .user import UserRead # Assuming schemas/user.py is created

class HackathonRead(HackathonBase):
    id: uuid.UUID
    created_at: datetime
    updated_at: datetime
    organizer: Optional[UserRead] = None
    # teams: List[uuid.UUID] = [] # Placeholder for future

    model_config = {"from_attributes": True} 