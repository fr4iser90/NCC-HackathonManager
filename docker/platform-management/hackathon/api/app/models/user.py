import uuid
from datetime import datetime, timezone
from typing import Optional, List # Added List for Mapped

from sqlalchemy import Column, String, DateTime, Boolean # Added Boolean for is_active if needed
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship # Added relationship

from app.database import Base
# We will use string literals for forward references to avoid direct imports for relationships.

class User(Base):
    __tablename__ = "users"
    __table_args__ = {"schema": "auth"}

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    username: Mapped[str] = mapped_column(String(100), unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    role: Mapped[str] = mapped_column(String(50), nullable=False, default="participant") # Roles: participant, judge, admin
    github_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, unique=True)
    avatar_url: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    # is_active: Mapped[bool] = mapped_column(Boolean, default=True) # Decided to keep is_active out of DB model for now, can be derived or managed in schemas if needed.
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    # Relationship to HackathonRegistration
    hackathon_registrations: Mapped[List["HackathonRegistration"]] = relationship(
        "HackathonRegistration", # String literal for the class name
        back_populates="user",
        cascade="all, delete-orphan",
        lazy="selectin"
    )

    # Relationship to TeamMember
    team_memberships: Mapped[List["TeamMember"]] = relationship(
        "TeamMember",
        back_populates="user",
        cascade="all, delete-orphan",
        lazy="selectin"
    )

# Pydantic Schemas (UserCreate, UserRead, UserUpdate) have been moved to app.schemas.user.py
