import uuid
import enum
from datetime import datetime, timezone
from typing import Optional, List

from sqlalchemy import Column, String, DateTime, ForeignKey, Enum as SQLEnum, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship, Mapped, mapped_column

from app.database import Base
from app.schemas.hackathon import HackathonStatus

class Hackathon(Base):
    __tablename__ = "hackathons"
    __table_args__ = {"schema": "hackathons"}

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    description: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    start_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    end_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    status: Mapped[HackathonStatus] = mapped_column(
        SQLEnum(HackathonStatus, name="hackathon_status_enum", create_type=False),
        nullable=False,
        default=HackathonStatus.UPCOMING
    )
    location: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    organizer_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("auth.users.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    mode: Mapped[str] = mapped_column(String(32), nullable=False, default="TEAM_RECOMMENDED")
    requirements: Mapped[List[str]] = mapped_column(JSON, default=list)
    category: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    tags: Mapped[Optional[List[str]]] = mapped_column(JSON, default=list)
    max_team_size: Mapped[Optional[int]] = mapped_column(nullable=True)
    min_team_size: Mapped[Optional[int]] = mapped_column(nullable=True)
    registration_deadline: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    is_public: Mapped[bool] = mapped_column(nullable=False, default=True)
    banner_image_url: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    rules_url: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    sponsor: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    prizes: Mapped[Optional[str]] = mapped_column(nullable=True)
    contact_email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    allow_individuals: Mapped[bool] = mapped_column(nullable=False, default=True)
    allow_multiple_projects_per_team: Mapped[bool] = mapped_column(nullable=False, default=False)
    custom_fields: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    organizer = relationship("User", lazy="selectin")
    # teams = relationship("Team", secondary="hackathon_teams", back_populates="hackathons")

# Pydantic Schemas (HackathonBase, HackathonCreate, HackathonUpdate, HackathonRead)
# and HackathonStatus enum have been moved to app.schemas.hackathon.py 