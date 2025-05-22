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
    admin = "admin"
    member = "member"
    viewer = "viewer"

class TeamStatus(str, enum.Enum):
    active = "active"
    archived = "archived"
    disbanded = "disbanded"

class TeamBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    is_open: bool = True
    status: TeamStatus = TeamStatus.active

class TeamCreate(TeamBase):
    hackathon_id: uuid.UUID  # Required - all teams are hackathon-specific

class TeamUpdate(TeamBase):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    is_open: Optional[bool] = None
    status: Optional[TeamStatus] = None

class TeamMemberRead(BaseModel):
    user_id: uuid.UUID
    role: TeamMemberRole
    joined_at: datetime
    user: Optional[UserRead] = None  # Populated user details

    model_config = {"from_attributes": True}

class JoinRequestStatus(str, enum.Enum):
    pending = "pending"
    accepted = "accepted"
    rejected = "rejected"

class JoinRequestRead(BaseModel):
    team_id: uuid.UUID
    user_id: uuid.UUID
    status: JoinRequestStatus
    created_at: datetime

    model_config = {"from_attributes": True}

class TeamInviteStatus(str, enum.Enum):
    pending = "pending"
    accepted = "accepted"
    rejected = "rejected"
    expired = "expired"

class TeamInviteRead(BaseModel):
    team_id: uuid.UUID
    email: str
    status: TeamInviteStatus
    created_at: datetime

    model_config = {"from_attributes": True}

class TeamRead(TeamBase):
    id: uuid.UUID
    hackathon_id: uuid.UUID  # Required - all teams are hackathon-specific
    status: TeamStatus
    created_at: datetime
    updated_at: datetime
    members: List[TeamMemberRead] = []
    join_requests: Optional[List[JoinRequestRead]] = None
    invites: Optional[List[TeamInviteRead]] = None

    model_config = {"from_attributes": True}

class TeamHistoryBase(BaseModel):
    name: str
    description: Optional[str] = None
    status: TeamStatus
    hackathon_id: uuid.UUID  # Required - all teams are hackathon-specific

class TeamHistoryCreate(TeamHistoryBase):
    team_id: uuid.UUID

class TeamHistoryRead(TeamHistoryBase):
    id: uuid.UUID
    team_id: uuid.UUID
    created_at: datetime
    archived_at: datetime

    model_config = {"from_attributes": True}

class MemberHistoryBase(BaseModel):
    user_id: uuid.UUID
    role: TeamMemberRole
    joined_at: datetime
    left_at: datetime

class MemberHistoryCreate(MemberHistoryBase):
    team_history_id: uuid.UUID

class MemberHistoryRead(MemberHistoryBase):
    id: uuid.UUID
    team_history_id: uuid.UUID

    model_config = {"from_attributes": True}
