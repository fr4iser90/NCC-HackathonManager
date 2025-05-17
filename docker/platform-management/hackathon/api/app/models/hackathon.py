import uuid
import enum
from datetime import datetime, timezone
from typing import Optional, List

from sqlalchemy import Column, String, DateTime, ForeignKey, Enum as SQLEnum
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

    organizer = relationship("User", lazy="selectin")
    # teams = relationship("Team", secondary="hackathon_teams", back_populates="hackathons")

# Pydantic Schemas (HackathonBase, HackathonCreate, HackathonUpdate, HackathonRead)
# and HackathonStatus enum have been moved to app.schemas.hackathon.py 