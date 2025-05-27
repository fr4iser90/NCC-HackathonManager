import uuid
import enum

# import enum # No longer needed here directly if HackathonStatus is the only enum from this model's perspective
from datetime import datetime, timezone
from typing import Optional, List, TYPE_CHECKING

from sqlalchemy import (
    Table,
    Column,
    String,
    DateTime,
    ForeignKey,
    Enum as SQLEnum,
    JSON,
    Boolean,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship, Mapped, mapped_column

from app.database import Base
from app.schemas.hackathon import HackathonStatus, HackathonMode  # Import HackathonMode

# from .team import Team # This will cause circular import if Team also imports Hackathon.
if TYPE_CHECKING:
    from .hackathon_registration import HackathonRegistration  # Import for relationship
    from .team import Team


class VotingType(str, enum.Enum):
    judges_only = "judges_only"
    users = "users"
    public = "public"
    mixed = "mixed"


class Hackathon(Base):
    __tablename__ = "hackathons"
    __table_args__ = {"schema": "hackathons"}

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(
        String(255), unique=True, nullable=False, index=True
    )
    description: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    start_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    end_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    status: Mapped[HackathonStatus] = mapped_column(
        SQLEnum(HackathonStatus, name="hackathon_status_enum", create_type=False),
        nullable=False,
        default=HackathonStatus.UPCOMING,
    )
    location: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    organizer_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("auth.users.id"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )
    mode: Mapped[HackathonMode] = mapped_column(
        SQLEnum(HackathonMode, name="hackathon_mode_enum", create_type=False),
        nullable=False,
        default=HackathonMode.SOLO_ONLY,
    )
    requirements: Mapped[List[str]] = mapped_column(JSON, default=list)
    category: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    tags: Mapped[Optional[List[str]]] = mapped_column(JSON, default=list)
    max_team_size: Mapped[Optional[int]] = mapped_column(nullable=True)
    min_team_size: Mapped[Optional[int]] = mapped_column(nullable=True)
    registration_deadline: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    is_public: Mapped[bool] = mapped_column(nullable=False, default=True)
    banner_image_url: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    rules_url: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    sponsor: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    prizes: Mapped[Optional[str]] = mapped_column(nullable=True)
    contact_email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    allow_individuals: Mapped[bool] = mapped_column(nullable=False, default=True)
    allow_multiple_projects_per_team: Mapped[bool] = mapped_column(
        nullable=False, default=False
    )
    custom_fields: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    # --- Judging/Voting Config ---
    voting_type: Mapped[str] = mapped_column(
        String(32), nullable=False, default="judges_only"
    )
    judging_criteria: Mapped[Optional[list]] = mapped_column(
        JSON, nullable=True
    )  # List of criteria dicts
    voting_start: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    voting_end: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    anonymous_votes: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    allow_multiple_votes: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False
    )

    organizer = relationship("User", lazy="selectin")
    # Relationship to the new HackathonRegistration table
    registrations: Mapped[List["HackathonRegistration"]] = relationship(
        back_populates="hackathon", cascade="all, delete-orphan", lazy="selectin"
    )
    teams: Mapped[List["Team"]] = relationship(
        back_populates="hackathon", cascade="all, delete-orphan", lazy="selectin"
    )
    projects = relationship("Project", back_populates="hackathon")


# Pydantic Schemas (HackathonBase, HackathonCreate, HackathonUpdate, HackathonRead)
# and HackathonStatus enum have been moved to app.schemas.hackathon.py

# hackathon_teams_table is no longer needed as its role is replaced by HackathonRegistration model
