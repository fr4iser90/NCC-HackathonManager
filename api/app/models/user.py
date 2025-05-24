import uuid
from datetime import datetime, timezone
from typing import Optional, List
import enum

from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, Enum, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.database import Base
from .session import Session

class UserRole(str, enum.Enum):
    ADMIN = "admin"
    ORGANIZER = "organizer"
    JUDGE = "judge"
    MENTOR = "mentor"
    PARTICIPANT = "participant"

class UserRoleAssociation(Base):
    __tablename__ = "user_roles"
    __table_args__ = {"schema": "auth"}
    user_id = Column(UUID(as_uuid=True), ForeignKey("auth.users.id", ondelete="CASCADE"), primary_key=True)
    role = Column(String(50), primary_key=True)
    user = relationship("User", back_populates="roles_association")

class User(Base):
    __tablename__ = "users"
    __table_args__ = {"schema": "auth"}

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    username = Column(String(255), unique=True, index=True, nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(100), nullable=False)
    full_name = Column(String(100))
    github_id = Column(String(100), unique=True, nullable=True)
    avatar_url = Column(String(255), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Multi-Role Relationship
    roles_association = relationship("UserRoleAssociation", back_populates="user", cascade="all, delete-orphan")

    # Relationships
    sessions = relationship("Session", back_populates="user", cascade="all, delete-orphan")
    team_memberships: Mapped[List["TeamMember"]] = relationship(
        "TeamMember",
        back_populates="user",
        cascade="all, delete-orphan",
        primaryjoin="User.id==TeamMember.user_id"
    )
    teams: Mapped[List["Team"]] = relationship(
        "Team",
        secondary="teams.members",
        back_populates="users",
        viewonly=True
    )
    owned_teams: Mapped[List["Team"]] = relationship(
        "Team",
        primaryjoin="and_(User.id==TeamMember.user_id, TeamMember.role=='owner')",
        secondary="teams.members",
        viewonly=True
    )
    projects = relationship("Project", back_populates="owner", foreign_keys="Project.owner_id", cascade="all, delete-orphan")
    submissions = relationship("Submission", back_populates="submitter", cascade="all, delete-orphan")
    scores = relationship("Score", back_populates="judge", cascade="all, delete-orphan")
    hackathon_registrations = relationship("HackathonRegistration", back_populates="user", cascade="all, delete-orphan")
    sent_invites = relationship("TeamInvite", back_populates="sender", foreign_keys="TeamInvite.sender_id", cascade="all, delete-orphan")
    received_invites = relationship("TeamInvite", back_populates="recipient", foreign_keys="TeamInvite.recipient_id", cascade="all, delete-orphan")
    sent_join_requests = relationship("JoinRequest", back_populates="sender", foreign_keys="JoinRequest.sender_id", cascade="all, delete-orphan")
    received_join_requests = relationship("JoinRequest", back_populates="recipient", foreign_keys="JoinRequest.recipient_id", cascade="all, delete-orphan")
    project_versions = relationship("ProjectVersion", back_populates="submitter", cascade="all, delete-orphan")

    @property
    def roles(self) -> list[UserRole]:
        return [r.role for r in self.roles_association]

# Pydantic Schemas (UserCreate, UserRead, UserUpdate) have been moved to app.schemas.user.py
