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

router = APIRouter()

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
    existing = db.query(User).filter(User.email == user_in.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    user = User(
        email=user_in.email,
        hashed_password=get_password_hash(user_in.password),
        full_name=user_in.full_name,
        username=user_in.username,
        github_id=user_in.github_id,
        role=UserRole.PARTICIPANT
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

@router.post("/login")
def login(email: EmailStr = Form(...), password: str = Form(...), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == email).first()
    if not user or not verify_password(password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    access_token = create_access_token({"sub": str(user.id)})
    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/me", response_model=UserRead)
def get_me(current_user: User = Depends(get_current_user)):
    return current_user

@router.put("/me", response_model=UserRead)
def update_own_profile(
    user_in: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
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
    for field, value in update_data.items():
        setattr(current_user, field, value)
    db.add(current_user)
    db.commit()
    db.refresh(current_user)
    return current_user

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
    # Nur Bilddateien erlauben (Content-Type und Magic Bytes)
    if not file.content_type.startswith("image/"):
        print("[Avatar-Upload] Kein Bild-Content-Type:", file.content_type)
        raise HTTPException(status_code=400, detail="Nur Bilddateien erlaubt.")
    contents = file.file.read()
    if len(contents) > 2 * 1024 * 1024:
        print("[Avatar-Upload] Bild zu groß:", len(contents))
        raise HTTPException(status_code=400, detail="Bild zu groß (max 2MB)")
    try:
        img = Image.open(io.BytesIO(contents))
        img.verify()  # Prüft, ob es ein echtes Bild ist
    except Exception as e:
        print("[Avatar-Upload] Ungültige Bilddatei:", e)
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
    print(f"[Avatar-Upload] Speichere Avatar nach: {file_path}")
    try:
        img.save(file_path, format="PNG")
    except Exception as e:
        print(f"[Avatar-Upload] Fehler beim Speichern: {e}")
        raise HTTPException(status_code=500, detail="Fehler beim Speichern des Avatars.")
    avatar_url_value = avatar_url(filename)
    current_user.avatar_url = avatar_url_value
    db.add(current_user)
    db.commit()
    db.refresh(current_user)
    return {"avatar_url": avatar_url_value}

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
def get_my_teams(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """
    Return all teams the current user is a member of.
    """
    from app.models.team import Team, TeamMember
    memberships = db.query(TeamMember).filter(TeamMember.user_id == current_user.id).all()
    team_ids = [m.team_id for m in memberships]
    teams = db.query(Team).filter(Team.id.in_(team_ids)).all() if team_ids else []
    return teams

@router.get("/me/projects", response_model=List[ProjectRead])
def get_my_projects(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """
    Return all projects the current user is associated with, either as a solo participant
    or as a member of a team that is registered for a hackathon.
    """
    from app.models.project import Project
    from app.models.team import TeamMember

    project_ids = set()

    # 1. Get projects where the user is a solo participant
    solo_registrations = db.query(HackathonRegistration).filter(HackathonRegistration.user_id == current_user.id).all()
    for reg in solo_registrations:
        project_ids.add(reg.project_id)

    # 2. Get projects for teams the user is a member of
    memberships = db.query(TeamMember).filter(TeamMember.user_id == current_user.id).all()
    user_team_ids = [m.team_id for m in memberships]

    if user_team_ids:
        team_registrations = db.query(HackathonRegistration).filter(HackathonRegistration.team_id.in_(user_team_ids)).all()
        for reg in team_registrations:
            project_ids.add(reg.project_id)

    # 3. Fetch all unique projects
    if project_ids:
        projects = db.query(Project).filter(Project.id.in_(list(project_ids))).all()
    else:
        projects = []
        
    return projects
