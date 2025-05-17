# schemas/team.py
import uuid
from datetime import datetime
from typing import List, Optional
import enum
from pydantic import BaseModel, Field

# Assuming UserRead will be in schemas.user
from .user import UserRead

class TeamMemberRole(str, enum.Enum):
    owner = "owner"
    member = "member"

class TeamBase(BaseModel):
    name: str
    description: Optional[str] = None

class TeamCreate(TeamBase):
    pass

class TeamUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None

class TeamMemberRead(BaseModel):
    user_id: uuid.UUID # Should this be id (PK of TeamMember) or user_id?
    role: TeamMemberRole
    joined_at: datetime
    user: Optional[UserRead] = None # Populated user details
    # team_id: uuid.UUID # Usually not needed if fetching members of a specific team

    model_config = {"from_attributes": True}

class TeamRead(TeamBase):
    id: uuid.UUID
    created_at: datetime
    updated_at: datetime
    members: List[TeamMemberRead] = []

    model_config = {"from_attributes": True} 