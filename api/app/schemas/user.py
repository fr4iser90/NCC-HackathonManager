# schemas/user.py
import uuid
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, Field
from app.models.user import UserRole


class UserCreate(BaseModel):
    email: EmailStr
    password: str
    username: str
    full_name: str | None = None
    github_id: str | None = None
    roles: Optional[list[UserRole]] = None


class UserRead(BaseModel):
    id: uuid.UUID
    email: EmailStr
    username: str
    full_name: str | None = None
    roles: list[UserRole]
    github_id: str | None = None
    avatar_url: str | None = None
    is_active: bool = True
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}

    @classmethod
    def from_orm(cls, user):
        data = super().from_orm(user).__dict__
        data["roles"] = user.roles
        return cls(**data)


class UserUpdate(BaseModel):
    username: Optional[str] = Field(None, min_length=3, max_length=50)
    full_name: Optional[str] = Field(None, max_length=100)
    avatar_url: Optional[str] = None
    github_id: Optional[str] = None
    password: Optional[str] = Field(None, min_length=8)
    current_password: Optional[str] = None
    roles: Optional[list[UserRole]] = None
    # email: Optional[EmailStr] = None # Add if email updates are allowed
    # password: Optional[str] = Field(None, min_length=8) # Add if password updates are allowed
