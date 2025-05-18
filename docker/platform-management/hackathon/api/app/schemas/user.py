# schemas/user.py
import uuid
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, Field

class UserCreate(BaseModel):
    email: EmailStr
    password: str
    username: str
    full_name: str | None = None

class UserRead(BaseModel):
    id: uuid.UUID
    email: EmailStr
    username: str
    full_name: str | None = None
    role: str
    github_id: str | None = None
    avatar_url: str | None = None
    is_active: bool = True # Assuming this field is desired in UserRead, was present in model version
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}

class UserUpdate(BaseModel):
    username: Optional[str] = Field(None, min_length=3, max_length=100)
    full_name: Optional[str] = Field(None, max_length=255)
    avatar_url: Optional[str] = None
    password: Optional[str] = Field(None, min_length=8)
    current_password: Optional[str] = None
    # email: Optional[EmailStr] = None # Add if email updates are allowed
    # password: Optional[str] = Field(None, min_length=8) # Add if password updates are allowed 