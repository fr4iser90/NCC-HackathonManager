from fastapi import APIRouter, Depends, HTTPException, status, Form, UploadFile, File
from sqlalchemy.orm import Session
from app.models.user import User, UserRole # SQLAlchemy model
from app.schemas.user import UserCreate, UserRead, UserUpdate # Pydantic schemas
from app.database import get_db
from app.auth import get_password_hash, verify_password, create_access_token, get_current_user, get_current_user_or_admin_for_profile_update
from pydantic import EmailStr
import uuid
from typing import List # Import List for response_model
import os
from fastapi.responses import FileResponse
from PIL import Image
import io
from app.schemas.team import TeamRead
from app.schemas.project import ProjectRead
from app.static import avatar_url, avatar_path
from app.models.hackathon_registration import HackathonRegistration # Added import
from app.logger import get_logger
from app.services.user_service import register_user, login_user, update_profile, upload_avatar_file, get_my_teams, get_my_projects

router = APIRouter()
logger = get_logger("users_router")

# Dependency for admin check (can be refined later)
async def get_admin_user(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to access this resource."
        )
    return current_user

@router.post("/register", response_model=UserRead, status_code=status.HTTP_201_CREATED)
def register(user_in: UserCreate, db: Session = Depends(get_db)):
    return register_user(db, user_in)

@router.post("/login")
def login(email: EmailStr = Form(...), password: str = Form(...), db: Session = Depends(get_db)):
    return login_user(db, email, password)

@router.get("/me", response_model=UserRead)
def get_me(current_user: User = Depends(get_current_user)):
    return current_user

@router.put("/me", response_model=UserRead)
def update_own_profile(
    user_in: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return update_profile(db, user_in, current_user)

@router.get("/", response_model=List[UserRead], dependencies=[Depends(get_admin_user)]) # New endpoint for listing users
def list_users(db: Session = Depends(get_db)):
    """
    Retrieve all users. Only accessible by admin users.
    """
    users = db.query(User).all()
    return users

@router.get("/{user_id}", response_model=UserRead, dependencies=[Depends(get_admin_user)])
def read_user_by_id(user_id: uuid.UUID, db: Session = Depends(get_db)):
    """
    Retrieve a specific user by their ID. Only accessible by admin users.
    """
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    user_dict = user.to_dict()
    user_dict["avatar_url"] = avatar_url(user.avatar_filename)
    return user_dict

@router.put("/{user_id}", response_model=UserRead)
def update_user_profile(
    user_id: uuid.UUID, 
    user_in: UserUpdate,
    db: Session = Depends(get_db),
    target_user: User = Depends(get_current_user_or_admin_for_profile_update) 
):
    """
    Update a user's profile.
    A user can update their own profile. An admin can update any profile.
    """
    update_data = user_in.model_dump(exclude_unset=True)
    
    if "username" in update_data and update_data["username"] != target_user.username:
        existing_user = db.query(User).filter(User.username == update_data["username"]).first()
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already taken."
            )

    for field, value in update_data.items():
        setattr(target_user, field, value)
    
    db.add(target_user)
    db.commit()
    db.refresh(target_user)
    return target_user 

@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(get_admin_user)])
def delete_user_by_admin(
    user_id: uuid.UUID,
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_admin_user) # We need the current admin user to check for self-deletion
):
    """
    Delete a specific user by their ID. Only accessible by admin users.
    An admin cannot delete themselves.
    """
    if admin_user.id == user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin users cannot delete their own account."
        )

    user_to_delete = db.query(User).filter(User.id == user_id).first()
    if user_to_delete is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    db.delete(user_to_delete)
    db.commit()
    return # Return No Content 

@router.post("/me/avatar")
def upload_avatar(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return upload_avatar_file(db, file, current_user)

@router.delete("/me/avatar")
def delete_avatar(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if not current_user.avatar_url:
        raise HTTPException(status_code=404, detail="Kein Profilbild vorhanden.")
    file_path = avatar_path(os.path.basename(current_user.avatar_url))
    if os.path.exists(file_path):
        os.remove(file_path)
    current_user.avatar_url = None
    db.add(current_user)
    db.commit()
    db.refresh(current_user)
    return {"detail": "Profilbild entfernt."}

@router.get("/me/avatar")
def get_avatar(current_user: User = Depends(get_current_user)):
    if not current_user.avatar_url:
        raise HTTPException(status_code=404, detail="Kein Profilbild vorhanden.")
    file_path = avatar_path(os.path.basename(current_user.avatar_url))
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Datei nicht gefunden.")
    return FileResponse(file_path)

@router.get("/me/teams", response_model=List[TeamRead])
def get_my_teams_endpoint(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return get_my_teams(db, current_user)

@router.get("/me/projects", response_model=List[ProjectRead])
def get_my_projects_endpoint(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return get_my_projects(db, current_user)
