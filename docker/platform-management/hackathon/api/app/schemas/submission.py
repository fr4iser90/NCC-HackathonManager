import uuid
import enum
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field

# Assuming UserRead will be in schemas.user
from .user import UserRead
# from .project import ProjectRead # Assuming ProjectRead in schemas.project - for nested project info

class SubmissionContentType(str, enum.Enum):
    LINK = "link"
    TEXT = "text"
    FILE_PATH = "file_path" # Placeholder for when file uploads are integrated

class SubmissionBase(BaseModel):
    content_type: SubmissionContentType
    content_value: str = Field(..., min_length=1)
    description: Optional[str] = None

class SubmissionCreate(SubmissionBase):
    project_id: uuid.UUID # project_id is required at creation

class SubmissionUpdate(BaseModel):
    content_type: Optional[SubmissionContentType] = None
    content_value: Optional[str] = Field(None, min_length=1)
    description: Optional[str] = None

class SubmissionRead(SubmissionBase):
    id: uuid.UUID
    project_id: uuid.UUID
    user_id: uuid.UUID # Submitter ID
    submitted_at: datetime
    updated_at: datetime
    submitter: Optional[UserRead] = None # Details of the user who submitted
    # project: Optional[ProjectRead] = None # Example for nesting project info

    model_config = {"from_attributes": True} 