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
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    members = relationship("TeamMember", back_populates="team", cascade="all, delete-orphan")

class TeamMember(Base):
    __tablename__ = "members"
    __table_args__ = {"schema": "teams"}

    team_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("teams.teams.id"), primary_key=True)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("auth.users.id"), primary_key=True)
    role: Mapped[TeamMemberRole] = mapped_column(SQLEnum(TeamMemberRole, name="team_member_role_enum", create_type=False), nullable=False, default=TeamMemberRole.member)
    joined_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))

    team = relationship("Team", back_populates="members")
    user = relationship("User")

# Pydantic Schemas (TeamBase, TeamCreate, TeamUpdate, TeamMemberRead, TeamRead)
# and TeamMemberRole enum have been moved to app.schemas.team.py 