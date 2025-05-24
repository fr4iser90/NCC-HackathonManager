"""
Service layer for user-related business logic.
"""
from sqlalchemy.orm import Session
from app.models.user import User, UserRole, UserRoleAssociation
from app.schemas.user import UserCreate, UserUpdate
from app.auth import get_password_hash, verify_password, create_access_token
from fastapi import HTTPException, status, UploadFile
from typing import Optional
from app.static import avatar_url, avatar_path
from PIL import Image
import io
import uuid
from app.models.hackathon_registration import HackathonRegistration
from app.models.team import Team, TeamMember
from app.models.project import Project
import os

def register_user(db: Session, user_in: UserCreate) -> User:
    """Register a new user."""
    existing = db.query(User).filter(User.email == user_in.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    user = User(
        email=user_in.email,
        hashed_password=get_password_hash(user_in.password),
        full_name=user_in.full_name,
        username=user_in.username,
        github_id=user_in.github_id,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    # Rollen setzen
    roles = user_in.roles if user_in.roles else [UserRole.PARTICIPANT]
    for role in roles:
        assoc = UserRoleAssociation(user_id=user.id, role=role)
        db.add(assoc)
    db.commit()
    db.refresh(user)
    return user

def login_user(db: Session, email: str, password: str) -> dict:
    """Authenticate user and return access token."""
    user = db.query(User).filter(User.email == email).first()
    if not user or not verify_password(password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    access_token = create_access_token({"sub": str(user.id)})
    return {"access_token": access_token, "token_type": "bearer"}

def update_profile(db: Session, user_in: UserUpdate, current_user: User) -> User:
    """Update the current user's profile."""
    update_data = user_in.model_dump(exclude_unset=True)
    if "username" in update_data and update_data["username"] != current_user.username:
        existing_user = db.query(User).filter(User.username == update_data["username"]).first()
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already taken."
            )
    if "password" in update_data:
        if not update_data.get("current_password"):
            raise HTTPException(status_code=400, detail="Aktuelles Passwort erforderlich.")
        if not verify_password(update_data["current_password"], current_user.hashed_password):
            raise HTTPException(status_code=400, detail="Aktuelles Passwort ist falsch.")
        current_user.hashed_password = get_password_hash(update_data["password"])
        update_data.pop("password")
        update_data.pop("current_password")
    # Rollen aktualisieren
    if "roles" in update_data and update_data["roles"] is not None:
        db.query(UserRoleAssociation).filter(UserRoleAssociation.user_id == current_user.id).delete()
        for role in update_data["roles"]:
            assoc = UserRoleAssociation(user_id=current_user.id, role=role)
            db.add(assoc)
        update_data.pop("roles")
    for field, value in update_data.items():
        setattr(current_user, field, value)
    db.add(current_user)
    db.commit()
    db.refresh(current_user)
    return current_user

def upload_avatar_file(db: Session, file: UploadFile, current_user: User) -> dict:
    """Upload and process user avatar image."""
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Nur Bilddateien erlaubt.")
    contents = file.file.read()
    if len(contents) > 2 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="Bild zu groß (max 2MB)")
    try:
        img = Image.open(io.BytesIO(contents))
        img.verify()
    except Exception:
        raise HTTPException(status_code=400, detail="Ungültige Bilddatei.")
    img = Image.open(io.BytesIO(contents))
    min_side = min(img.size)
    left = (img.width - min_side) // 2
    top = (img.height - min_side) // 2
    right = left + min_side
    bottom = top + min_side
    img = img.crop((left, top, right, bottom))
    img = img.resize((256, 256))
    filename = f"{current_user.id}.png"
    file_path = avatar_path(filename)
    try:
        img.save(file_path, format="PNG")
    except Exception:
        raise HTTPException(status_code=500, detail="Fehler beim Speichern des Avatars.")
    avatar_url_value = avatar_url(filename)
    current_user.avatar_url = avatar_url_value
    db.add(current_user)
    db.commit()
    db.refresh(current_user)
    return {"avatar_url": avatar_url_value}

def get_my_teams(db: Session, current_user: User):
    """Return all teams the current user is a member of."""
    memberships = db.query(TeamMember).filter(TeamMember.user_id == current_user.id).all()
    team_ids = [m.team_id for m in memberships]
    teams = db.query(Team).filter(Team.id.in_(team_ids)).all() if team_ids else []
    return teams

def get_my_projects(db: Session, current_user: User):
    """Return all projects the current user is associated with."""
    project_ids = set()
    solo_registrations = db.query(HackathonRegistration).filter(HackathonRegistration.user_id == current_user.id).all()
    for reg in solo_registrations:
        project_ids.add(reg.project_id)
    memberships = db.query(TeamMember).filter(TeamMember.user_id == current_user.id).all()
    user_team_ids = [m.team_id for m in memberships]
    if user_team_ids:
        team_registrations = db.query(HackathonRegistration).filter(HackathonRegistration.team_id.in_(user_team_ids)).all()
        for reg in team_registrations:
            project_ids.add(reg.project_id)
    projects = db.query(Project).filter(Project.id.in_(list(project_ids))).all() if project_ids else []
    return projects 