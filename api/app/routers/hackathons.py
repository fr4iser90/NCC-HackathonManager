import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.database import get_db
from datetime import datetime, timezone # Added timezone
from app.models.user import User
from app.models.hackathon import Hackathon # hackathon_teams_table removed
from app.models.hackathon_registration import HackathonRegistration # Added
from app.models.team import Team, TeamMember, TeamMemberRole # Team models
from app.models.project import Project # Project model
from app.schemas.project import ProjectStatus # ProjectStatus enum
from app.schemas.hackathon import (
    HackathonCreate, HackathonRead, HackathonUpdate, HackathonStatus,
    HackathonRegistrationRead, ParticipantRegistrationCreate # Added ParticipantRegistrationCreate
) # Pydantic schemas
from app.auth import get_current_user
# from app.static import banner_url # This was unused
# If you have a specific get_current_active_admin_user, import that instead for admin routes

router = APIRouter(
    tags=["hackathons"]
)

# Helper function for admin check (can be moved to a shared auth utils if used elsewhere)
def get_current_active_admin_user(current_user: User = Depends(get_current_user)) -> User:
    if not any(r.role == "admin" for r in getattr(current_user, 'roles_association', [])):
        raise HTTPException(status_code=403, detail="Not authorized")
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
    return hackathon

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

@router.delete("/{hackathon_id}/registration", status_code=status.HTTP_204_NO_CONTENT)
def withdraw_registration(
    hackathon_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Withdraw the current user's registration (solo or team) for a hackathon, before the deadline.
    """
    db_hackathon = db.query(Hackathon).filter(Hackathon.id == hackathon_id).first()
    if not db_hackathon:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Hackathon not found")

    # Check deadline
    if db_hackathon.registration_deadline and db_hackathon.registration_deadline < datetime.now(timezone.utc):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Registration deadline has passed.")

    # Try to find solo registration
    reg = db.query(HackathonRegistration).filter(
        HackathonRegistration.hackathon_id == hackathon_id,
        HackathonRegistration.user_id == current_user.id
    ).first()

    # If not found, try to find team registration where user is owner/admin
    if not reg:
        user_team_ids = [
            m.team_id for m in db.query(TeamMember).filter(
                TeamMember.user_id == current_user.id,
                TeamMember.role.in_([TeamMemberRole.owner, TeamMemberRole.admin])
            ).all()
        ]
        if user_team_ids:
            reg = db.query(HackathonRegistration).filter(
                HackathonRegistration.hackathon_id == hackathon_id,
                HackathonRegistration.team_id.in_(user_team_ids)
            ).first()

    if not reg:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No registration found for user or their teams.")

    db.delete(reg)
    db.commit()
    return

@router.post("/{hackathon_id}/register", response_model=HackathonRegistrationRead, status_code=status.HTTP_201_CREATED)
def register_participant_for_hackathon(
    hackathon_id: uuid.UUID,
    registration_in: ParticipantRegistrationCreate, # Use the new schema for request body
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Register a participant (solo user or a team) for a specific hackathon.
    - If registering a user: current_user must match user_id in request or be an admin.
    - If registering a team: current_user must be an owner/admin of the team or be a platform admin.
    A new project for the participant in this hackathon will be created.
    """
    db_hackathon = db.query(Hackathon).filter(Hackathon.id == hackathon_id).first()
    if not db_hackathon:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Hackathon not found")

    # --- Validation Checks for Hackathon ---
    if db_hackathon.status not in [HackathonStatus.UPCOMING, HackathonStatus.ACTIVE]:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Hackathon is not open for registration.")
    if db_hackathon.registration_deadline and db_hackathon.registration_deadline < datetime.now(timezone.utc):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Registration deadline has passed.")

    participant_name_for_project = ""
    db_user_to_register = None
    db_team_to_register = None

    if registration_in.user_id:
        # --- SOLO REGISTRATION ---
        if not db_hackathon.allow_individuals:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Solo participation is not allowed for this hackathon.")

        db_user_to_register = db.query(User).filter(User.id == registration_in.user_id).first()
        if not db_user_to_register:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User to register not found.")

        # Authorization: Current user must be the user being registered or an admin
        if current_user.id != db_user_to_register.id and not any(r.role == "admin" for r in getattr(current_user, 'roles_association', [])):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to register this user.")
        
        # Check if user is already registered (solo)
        existing_solo_registration = db.query(HackathonRegistration).filter(
            HackathonRegistration.hackathon_id == hackathon_id,
            HackathonRegistration.user_id == db_user_to_register.id
        ).first()
        if existing_solo_registration:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User is already registered solo for this hackathon.")

        # Check if user is part of any team already registered for this hackathon
        user_teams = db.query(TeamMember).filter(TeamMember.user_id == db_user_to_register.id).all()
        user_team_ids = [ut.team_id for ut in user_teams]
        if user_team_ids:
            existing_team_registration_for_user = db.query(HackathonRegistration).filter(
                HackathonRegistration.hackathon_id == hackathon_id,
                HackathonRegistration.team_id.in_(user_team_ids)
            ).first()
            if existing_team_registration_for_user:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User is already participating in this hackathon with a team.")
        
        participant_name_for_project = db_user_to_register.username

    elif registration_in.team_id:
        # --- TEAM REGISTRATION ---
        db_team_to_register = db.query(Team).filter(Team.id == registration_in.team_id).first()
        if not db_team_to_register:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Team to register not found.")

        # Authorization: Check if current_user is an owner of the team or a platform admin
        team_membership = db.query(TeamMember).filter(
            TeamMember.team_id == db_team_to_register.id,
            TeamMember.user_id == current_user.id
        ).first()
        
        is_team_owner = team_membership and team_membership.role == TeamMemberRole.owner
        is_platform_admin = any(r.role == "admin" for r in getattr(current_user, 'roles_association', []))

        if not (is_team_owner or is_platform_admin):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User must be an owner of the team or a platform admin to register it.")

        # Team size constraints
        if db_hackathon.min_team_size and len(db_team_to_register.members) < db_hackathon.min_team_size:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Team size is less than the minimum of {db_hackathon.min_team_size}.")
        if db_hackathon.max_team_size and len(db_team_to_register.members) > db_hackathon.max_team_size:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Team size exceeds the maximum of {db_hackathon.max_team_size}.")

        # Check if team is already registered
        existing_team_registration = db.query(HackathonRegistration).filter(
            HackathonRegistration.hackathon_id == hackathon_id,
            HackathonRegistration.team_id == db_team_to_register.id
        ).first()
        if existing_team_registration:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Team is already registered for this hackathon.")

        # Check if any member of this team is already registered solo for this hackathon
        team_member_user_ids = [member.user_id for member in db_team_to_register.members]
        if team_member_user_ids:
            existing_solo_registration_for_member = db.query(HackathonRegistration).filter(
                HackathonRegistration.hackathon_id == hackathon_id,
                HackathonRegistration.user_id.in_(team_member_user_ids)
            ).first()
            if existing_solo_registration_for_member:
                # Find which user to include in the error message
                offending_user = db.query(User).filter(User.id == existing_solo_registration_for_member.user_id).first()
                offending_username = offending_user.username if offending_user else "A team member"
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"{offending_username} is already registered solo for this hackathon. Cannot register team.")
            
        participant_name_for_project = db_team_to_register.name
    
    else:
        # Should be caught by Pydantic model_validator, but as a safeguard:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid registration data: user_id or team_id must be provided.")

    # --- Create Project and Registration ---
    project_name = f"{participant_name_for_project}'s entry for {db_hackathon.name}"
    db_project = Project(
        name=project_name,
        status=ProjectStatus.DRAFT
    )
    
    try:
        db.add(db_project)
        db.flush() 

        db_registration = HackathonRegistration(
            hackathon_id=hackathon_id,
            user_id=db_user_to_register.id if db_user_to_register else None,
            team_id=db_team_to_register.id if db_team_to_register else None,
            project_id=db_project.id,
            status="registered"
        )
        db.add(db_registration)
        
        db.commit()
        db.refresh(db_registration)
        return db_registration

    except IntegrityError as e:
        db.rollback()
        # This could happen if the project name isn't unique (if we add such a constraint per hackathon)
        # or other DB integrity issues.
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Database integrity error during registration: {e}")
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"An unexpected error occurred: {e}")
