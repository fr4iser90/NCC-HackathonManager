from fastapi import APIRouter, Depends, HTTPException, status, Form, UploadFile, File
from sqlalchemy.orm import Session
from app.models.user import User # SQLAlchemy model
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

router = APIRouter()

# Dependency for admin check (can be refined later)
async def get_admin_user(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role != "admin":
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
        role="participant"
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
    return user

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

AVATAR_DIR = "/static/avatars"

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
    file_path = os.path.join(AVATAR_DIR, filename)
    print(f"[Avatar-Upload] Speichere Avatar nach: {file_path}")
    try:
        img.save(file_path, format="PNG")
    except Exception as e:
        print(f"[Avatar-Upload] Fehler beim Speichern: {e}")
        raise HTTPException(status_code=500, detail="Fehler beim Speichern des Avatars.")
    avatar_url = f"/static/avatars/{filename}"
    current_user.avatar_url = avatar_url
    db.add(current_user)
    db.commit()
    db.refresh(current_user)
    return {"avatar_url": avatar_url}

@router.delete("/me/avatar")
def delete_avatar(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if not current_user.avatar_url:
        raise HTTPException(status_code=404, detail="Kein Profilbild vorhanden.")
    file_path = os.path.join(AVATAR_DIR, os.path.basename(current_user.avatar_url))
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
    file_path = os.path.join(AVATAR_DIR, os.path.basename(current_user.avatar_url))
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Datei nicht gefunden.")
    return FileResponse(file_path) 