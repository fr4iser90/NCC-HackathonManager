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
    is_open: bool = True

class TeamCreate(TeamBase):
    pass

class TeamUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    is_open: Optional[bool] = None

class TeamMemberRead(BaseModel):
    user_id: uuid.UUID # Should this be id (PK of TeamMember) or user_id?
    role: TeamMemberRole
    joined_at: datetime
    user: Optional[UserRead] = None # Populated user details
    # team_id: uuid.UUID # Usually not needed if fetching members of a specific team

    model_config = {"from_attributes": True}

class JoinRequestStatus(str, enum.Enum):
    pending = "pending"
    accepted = "accepted"
    rejected = "rejected"

class TeamInviteStatus(str, enum.Enum):
    pending = "pending"
    accepted = "accepted"
    rejected = "rejected"

class JoinRequestRead(BaseModel):
    team_id: uuid.UUID
    user_id: uuid.UUID
    status: JoinRequestStatus
    created_at: datetime
    model_config = {"from_attributes": True}

class TeamInviteRead(BaseModel):
    team_id: uuid.UUID
    email: str
    status: TeamInviteStatus
    created_at: datetime
    model_config = {"from_attributes": True}

class TeamRead(TeamBase):
    id: uuid.UUID
    created_at: datetime
    updated_at: datetime
    members: List[TeamMemberRead] = []
    join_requests: Optional[List[JoinRequestRead]] = None
    invites: Optional[List[TeamInviteRead]] = None
    model_config = {"from_attributes": True} 