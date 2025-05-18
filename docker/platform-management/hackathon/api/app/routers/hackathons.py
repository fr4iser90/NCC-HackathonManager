import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.database import get_db
from app.models.user import User
from app.models.hackathon import Hackathon # SQLAlchemy model
from app.schemas.hackathon import (
    HackathonCreate, HackathonRead, HackathonUpdate, HackathonStatus
) # Pydantic schemas
from app.auth import get_current_user # Assuming a general get_current_user
from app.static import banner_url
# If you have a specific get_current_active_admin_user, import that instead for admin routes

router = APIRouter(
    tags=["hackathons"]
)

# Helper function for admin check (can be moved to a shared auth utils if used elsewhere)
def get_current_active_admin_user(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="The user doesn't have enough privileges"
        )
    return current_user

@router.post("/", response_model=HackathonRead, status_code=status.HTTP_201_CREATED)
def create_hackathon(
    hackathon_in: HackathonCreate,
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_current_active_admin_user) # Ensures only admin can create
):
    """
    Create a new hackathon. Only accessible by admin users.
    If organizer_id is not provided in hackathon_in, it can be set to the admin_user's id or remain null based on logic.
    For now, it will be whatever is in hackathon_in (can be None).
    """
    # Check if start_date is before end_date
    if hackathon_in.start_date >= hackathon_in.end_date:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Start date must be before end date."
        )
        
    # Optional: Check if organizer_id exists if provided
    if hackathon_in.organizer_id:
        organizer = db.query(User).filter(User.id == hackathon_in.organizer_id).first()
        if not organizer:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Organizer with id {hackathon_in.organizer_id} not found."
            )

    db_hackathon = Hackathon(**hackathon_in.model_dump())
    try:
        db.add(db_hackathon)
        db.commit()
        db.refresh(db_hackathon)
        return db_hackathon
    except IntegrityError: # Handles unique constraint violation for hackathon name
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Hackathon name already exists or other integrity violation."
        )

@router.get("/", response_model=List[HackathonRead])
def list_hackathons(
    skip: int = 0,
    limit: int = 100,
    status_filter: Optional[HackathonStatus] = None, # Example filter
    db: Session = Depends(get_db)
):
    """
    List all hackathons. Can be filtered by status.
    """
    query = db.query(Hackathon)
    if status_filter:
        query = query.filter(Hackathon.status == status_filter)
    hackathons = query.order_by(Hackathon.start_date.desc()).offset(skip).limit(limit).all()
    return hackathons

@router.get("/{hackathon_id}", response_model=HackathonRead)
def get_hackathon(hackathon_id: uuid.UUID, db: Session = Depends(get_db)):
    """
    Get details of a specific hackathon by ID.
    """
    hackathon = db.query(Hackathon).filter(Hackathon.id == hackathon_id).first()
    if not hackathon:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Hackathon not found")
    hackathon_dict = hackathon.to_dict()
    hackathon_dict["banner_image_url"] = banner_url(hackathon.banner_filename)
    return hackathon_dict

@router.put("/{hackathon_id}", response_model=HackathonRead)
def update_hackathon(
    hackathon_id: uuid.UUID,
    hackathon_in: HackathonUpdate,
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_current_active_admin_user)
):
    """
    Update an existing hackathon. Only accessible by admin users.
    """
    db_hackathon = db.query(Hackathon).filter(Hackathon.id == hackathon_id).first()
    if not db_hackathon:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Hackathon not found")

    update_data = hackathon_in.model_dump(exclude_unset=True)
    
    # Validate dates if both are provided in the update
    new_start_date = update_data.get("start_date", db_hackathon.start_date)
    new_end_date = update_data.get("end_date", db_hackathon.end_date)
    if new_start_date >= new_end_date:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Start date must be before end date."
        )

    # Optional: Check if organizer_id exists if provided in update_data
    if "organizer_id" in update_data and update_data["organizer_id"] is not None:
        organizer = db.query(User).filter(User.id == update_data["organizer_id"]).first()
        if not organizer:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Organizer with id {update_data['organizer_id']} not found."
            )

    for key, value in update_data.items():
        setattr(db_hackathon, key, value)
    
    try:
        db.add(db_hackathon)
        db.commit()
        db.refresh(db_hackathon)
        return db_hackathon
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Hackathon name already exists or other integrity violation during update."
        )

@router.delete("/{hackathon_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_hackathon(
    hackathon_id: uuid.UUID,
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_current_active_admin_user)
):
    """
    Delete a hackathon. Only accessible by admin users.
    """
    db_hackathon = db.query(Hackathon).filter(Hackathon.id == hackathon_id).first()
    if not db_hackathon:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Hackathon not found")
    
    db.delete(db_hackathon)
    db.commit()
    return

# Placeholder for hackathon-related endpoints
# For example:
# @router.post("/", response_model=dict) # Replace dict with HackathonRead schema
# async def create_hackathon():
#     pass

# @router.get("/", response_model=list[dict]) # Replace dict with HackathonRead schema
# async def list_hackathons():
#     pass 