# models/judging.py
import uuid
import enum
from datetime import datetime, timezone
from typing import Optional, List
from decimal import Decimal

from sqlalchemy import (
    Column,
    String,
    DateTime,
    ForeignKey,
    Enum as SQLEnum,
    Integer,
    Text,
    Numeric,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship, Mapped, mapped_column

from app.database import Base  # Import Base from your database setup


class Criterion(Base):
    __tablename__ = "criteria"
    __table_args__ = {"schema": "judging"}

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(
        String(255), nullable=False, unique=True, index=True
    )
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    max_score: Mapped[int] = mapped_column(Integer, nullable=False)
    weight: Mapped[Decimal] = mapped_column(
        Numeric, nullable=False, default=1.0
    )  # As per init.sql
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    scores = relationship("Score", back_populates="criterion")


class Score(Base):
    __tablename__ = "scores"
    __table_args__ = (
        UniqueConstraint(
            "project_id", "criteria_id", "judge_id", name="uq_project_criterion_judge"
        ),
        {"schema": "judging"},
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    project_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("projects.projects.id"), nullable=False
    )
    criteria_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("judging.criteria.id"), nullable=False
    )
    judge_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("auth.users.id"), nullable=False
    )
    score: Mapped[int] = mapped_column(Integer, nullable=False)
    comment: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    submitted_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    project = relationship("Project")  # Basic relationship, could be configured more
    criterion = relationship("Criterion", back_populates="scores")
    judge = relationship("User")  # Basic relationship


# Pydantic Schemas for Criterion and Score have been moved to app.schemas.judging
