import uuid
import enum
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import Column, String, DateTime, ForeignKey, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship, Mapped, mapped_column

from app.database import Base
from app.schemas.submission import SubmissionContentType # Import for model usage

class Submission(Base):
    __tablename__ = "submissions"
    __table_args__ = {"schema": "projects"}

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("projects.projects.id"), nullable=False)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("auth.users.id", ondelete="CASCADE"), nullable=False)
    
    content_type: Mapped[SubmissionContentType] = mapped_column(SQLEnum(SubmissionContentType, name="submission_content_type_enum", create_type=False), nullable=False)
    content_value: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String, nullable=True)

    submitted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    project = relationship("Project", back_populates="submissions")
    submitter = relationship("User", back_populates="submissions")

# Pydantic Schemas (SubmissionBase, ..., SubmissionRead) and SubmissionContentType enum
# have been moved to app.schemas.submission.py 