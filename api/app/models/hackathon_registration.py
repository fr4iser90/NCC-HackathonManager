# app/models/hackathon_registration.py
import uuid
from datetime import datetime, timezone
from typing import Optional, TYPE_CHECKING

from sqlalchemy import String, DateTime, ForeignKey, CheckConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship, Mapped, mapped_column

from app.database import Base

if TYPE_CHECKING:
    from .hackathon import Hackathon
    from .project import Project
    from .user import User
    from .team import Team


class HackathonRegistration(Base):
    __tablename__ = "hackathon_registrations"
    __table_args__ = (
        CheckConstraint(
            "(user_id IS NOT NULL AND team_id IS NULL) OR (user_id IS NULL AND team_id IS NOT NULL)",
            name="chk_participant_type",
        ),
        {"schema": "hackathons"},
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    hackathon_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("hackathons.hackathons.id", ondelete="CASCADE"), nullable=False
    )
    project_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("projects.projects.id", ondelete="RESTRICT"),
        nullable=False,
        unique=True,
    )

    user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("auth.users.id", ondelete="CASCADE"), nullable=True
    )
    team_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("teams.teams.id", ondelete="CASCADE"), nullable=True
    )

    registered_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    status: Mapped[str] = mapped_column(
        String(50), default="registered", nullable=False
    )  # e.g., registered, withdrawn

    # Relationships
    hackathon: Mapped["Hackathon"] = relationship(back_populates="registrations")
    project: Mapped["Project"] = relationship(
        back_populates="registration", uselist=False
    )
    user: Mapped[Optional["User"]] = relationship(
        back_populates="hackathon_registrations"
    )
    team: Mapped[Optional["Team"]] = relationship(
        back_populates="hackathon_registrations"
    )
