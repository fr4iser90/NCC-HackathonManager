from fastapi import APIRouter, Depends, HTTPException, status, Form
from sqlalchemy.orm import Session
from app.models.user import User # SQLAlchemy model
from app.schemas.user import UserCreate, UserRead, UserUpdate # Pydantic schemas
from app.database import get_db
from app.auth import get_password_hash, verify_password, create_access_token, get_current_user, get_current_user_or_admin_for_profile_update
from pydantic import EmailStr
import uuid

router = APIRouter()

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