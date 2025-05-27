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


class TeamStatus(str, enum.Enum):
    active = "active"
    archived = "archived"
    disbanded = "disbanded"


class Team(Base):
    __tablename__ = "teams"
    __table_args__ = {"schema": "teams"}

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    hackathon_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("hackathons.hackathons.id", ondelete="CASCADE"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    description: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    is_open: Mapped[bool] = mapped_column(default=True, nullable=False)
    status: Mapped[TeamStatus] = mapped_column(
        SQLEnum(TeamStatus), default=TeamStatus.active, nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    # Relationships
    hackathon = relationship("Hackathon", back_populates="teams")
    members = relationship(
        "TeamMember",
        back_populates="team",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    users = relationship(
        "User", secondary="teams.members", back_populates="teams", viewonly=True
    )
    join_requests = relationship(
        "JoinRequest",
        back_populates="team",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    invites = relationship(
        "TeamInvite",
        back_populates="team",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    history = relationship(
        "TeamHistory",
        back_populates="team",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    hackathon_registrations = relationship(
        "HackathonRegistration",
        back_populates="team",
        cascade="all, delete-orphan",
        lazy="selectin",
    )


class TeamMember(Base):
    __tablename__ = "members"
    __table_args__ = {"schema": "teams"}

    team_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("teams.teams.id"), primary_key=True
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("auth.users.id"), primary_key=True
    )
    role: Mapped[TeamMemberRole] = mapped_column(
        SQLEnum(TeamMemberRole), default=TeamMemberRole.member, nullable=False
    )
    joined_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )

    team = relationship("Team", back_populates="members")
    user = relationship("User", back_populates="team_memberships")


class TeamHistory(Base):
    __tablename__ = "team_history"
    __table_args__ = {"schema": "teams"}

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    team_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("teams.teams.id", ondelete="CASCADE")
    )
    hackathon_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("hackathons.hackathons.id", ondelete="CASCADE")
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    status: Mapped[TeamStatus] = mapped_column(SQLEnum(TeamStatus), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )
    archived_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )

    team = relationship("Team", back_populates="history")
    hackathon = relationship("Hackathon")
    member_history = relationship(
        "MemberHistory", back_populates="team_history", cascade="all, delete-orphan"
    )


class MemberHistory(Base):
    __tablename__ = "member_history"
    __table_args__ = {"schema": "teams"}

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    team_history_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("teams.team_history.id", ondelete="CASCADE")
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("auth.users.id", ondelete="CASCADE")
    )
    role: Mapped[TeamMemberRole] = mapped_column(
        SQLEnum(TeamMemberRole), nullable=False
    )
    joined_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    left_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )

    team_history = relationship("TeamHistory", back_populates="member_history")
    user = relationship("User")


class JoinRequestStatus(str, enum.Enum):
    pending = "pending"
    accepted = "accepted"
    rejected = "rejected"


class JoinRequest(Base):
    __tablename__ = "join_requests"
    __table_args__ = {"schema": "teams"}

    team_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("teams.teams.id"), primary_key=True
    )
    sender_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("auth.users.id"), primary_key=True
    )
    recipient_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("auth.users.id"), nullable=False
    )
    status: Mapped[JoinRequestStatus] = mapped_column(
        SQLEnum(JoinRequestStatus), default=JoinRequestStatus.pending, nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )

    team = relationship("Team", back_populates="join_requests")
    sender = relationship(
        "User", foreign_keys=[sender_id], back_populates="sent_join_requests"
    )
    recipient = relationship(
        "User", foreign_keys=[recipient_id], back_populates="received_join_requests"
    )


class TeamInviteStatus(str, enum.Enum):
    pending = "pending"
    accepted = "accepted"
    rejected = "rejected"
    expired = "expired"


class TeamInvite(Base):
    __tablename__ = "invites"
    __table_args__ = {"schema": "teams"}

    team_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("teams.teams.id"), primary_key=True
    )
    email: Mapped[str] = mapped_column(String(255), primary_key=True)
    sender_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("auth.users.id"), nullable=False
    )
    recipient_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("auth.users.id"), nullable=True
    )
    status: Mapped[TeamInviteStatus] = mapped_column(
        SQLEnum(TeamInviteStatus), default=TeamInviteStatus.pending, nullable=False
    )
    token: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )

    team = relationship("Team", back_populates="invites")
    sender = relationship(
        "User", foreign_keys=[sender_id], back_populates="sent_invites"
    )
    recipient = relationship(
        "User", foreign_keys=[recipient_id], back_populates="received_invites"
    )


# Pydantic Schemas (TeamBase, TeamCreate, TeamUpdate, TeamMemberRead, TeamRead)
# and TeamMemberRole enum have been moved to app.schemas.team.py
