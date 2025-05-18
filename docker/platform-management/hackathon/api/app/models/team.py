# models/team.py
import uuid
from datetime import datetime, timezone
from typing import List, Optional
import enum

from sqlalchemy import Column, String, DateTime, ForeignKey, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship, Mapped, mapped_column

from app.database import Base
from app.schemas.team import TeamMemberRole

class Team(Base):
    __tablename__ = "teams"
    __table_args__ = {"schema": "teams"}

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    description: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    is_open: Mapped[bool] = mapped_column(default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    members = relationship("TeamMember", back_populates="team", cascade="all, delete-orphan")
    join_requests = relationship("JoinRequest", back_populates="team", cascade="all, delete-orphan")
    invites = relationship("TeamInvite", back_populates="team", cascade="all, delete-orphan")

class TeamMember(Base):
    __tablename__ = "members"
    __table_args__ = {"schema": "teams"}

    team_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("teams.teams.id"), primary_key=True)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("auth.users.id"), primary_key=True)
    role: Mapped[TeamMemberRole] = mapped_column(SQLEnum(TeamMemberRole, name="team_member_role_enum", create_type=False), nullable=False, default=TeamMemberRole.member)
    joined_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))

    team = relationship("Team", back_populates="members")
    user = relationship("User")

class JoinRequestStatus(str, enum.Enum):
    pending = "pending"
    accepted = "accepted"
    rejected = "rejected"

class JoinRequest(Base):
    __tablename__ = "join_requests"
    __table_args__ = {"schema": "teams"}

    team_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("teams.teams.id"), primary_key=True)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("auth.users.id"), primary_key=True)
    status: Mapped[JoinRequestStatus] = mapped_column(SQLEnum(JoinRequestStatus, name="join_request_status_enum", create_type=False), default=JoinRequestStatus.pending, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))

    team = relationship("Team", back_populates="join_requests")
    user = relationship("User")

class TeamInviteStatus(str, enum.Enum):
    pending = "pending"
    accepted = "accepted"
    rejected = "rejected"

class TeamInvite(Base):
    __tablename__ = "invites"
    __table_args__ = {"schema": "teams"}

    team_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("teams.teams.id"), primary_key=True)
    email: Mapped[str] = mapped_column(String(255), primary_key=True)
    status: Mapped[TeamInviteStatus] = mapped_column(SQLEnum(TeamInviteStatus, name="team_invite_status_enum", create_type=False), default=TeamInviteStatus.pending, nullable=False)
    token: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))

    team = relationship("Team", back_populates="invites")

# Pydantic Schemas (TeamBase, TeamCreate, TeamUpdate, TeamMemberRead, TeamRead)
# and TeamMemberRole enum have been moved to app.schemas.team.py 