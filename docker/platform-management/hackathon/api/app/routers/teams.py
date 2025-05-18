from typing import List
import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
import secrets

from app.database import get_db
from app.models.user import User
from app.models.team import Team, TeamMember, JoinRequest, JoinRequestStatus, TeamInvite, TeamInviteStatus # SQLAlchemy models
from app.schemas.team import TeamCreate, TeamRead, TeamUpdate, TeamMemberRole, JoinRequestRead, TeamInviteRead # Pydantic schemas
from app.auth import (
    get_current_user, 
    get_team_owner_or_admin,
    ensure_is_team_member,
    get_team_owner_admin_or_self_for_member_removal
)

router = APIRouter()

@router.post("/", response_model=TeamRead, status_code=status.HTTP_201_CREATED)
def create_team(team_in: TeamCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """
    Create a new team. The creator becomes the team leader.
    """
    try:
        db_team = Team(name=team_in.name, description=team_in.description, is_open=team_in.is_open)
        db.add(db_team)
        db.flush()  # Flush to get the db_team.id

        team_leader = TeamMember(
            team_id=db_team.id,
            user_id=current_user.id,
            role=TeamMemberRole.owner
        )
        db.add(team_leader)
        db.commit()
        db.refresh(db_team)
        return db_team
    except IntegrityError: # Catches unique constraint violation for team name
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Team name already exists."
        )

@router.get("/", response_model=List[TeamRead], dependencies=[Depends(get_current_user)])
def list_teams(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """
    List all teams.
    """
    teams = db.query(Team).offset(skip).limit(limit).all()
    return teams

@router.get("/{team_id}", response_model=TeamRead)
def get_team(team_id: uuid.UUID, db: Session = Depends(get_db)):
    """
    Get details of a specific team by ID.
    """
    team = db.query(Team).filter(Team.id == team_id).first()
    if not team:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Team not found")
    return team

@router.put("/{team_id}", response_model=TeamRead)
def update_team(
    team_id: uuid.UUID, 
    team_in: TeamUpdate, 
    db: Session = Depends(get_db), 
    # Auth: current_user must be team owner or admin
    # The dependency returns TeamMember or None (if admin not owner), 
    # but we primarily use it for the auth check here.
    # The actual team is re-fetched for update to ensure fresh data.
    _: TeamMember = Depends(get_team_owner_or_admin) 
):
    db_team = db.query(Team).filter(Team.id == team_id).first()
    if not db_team: # Should be caught by dependency, but good practice
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Team not found")

    update_data = team_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_team, field, value)
    
    try:
        db.add(db_team)
        db.commit()
        db.refresh(db_team)
        return db_team
    except IntegrityError: # Catches unique constraint violation for team name
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Team name already exists or other integrity violation."
        )

@router.delete("/{team_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_team(
    team_id: uuid.UUID, 
    db: Session = Depends(get_db), 
    # Auth: current_user must be team owner or admin
    _: TeamMember = Depends(get_team_owner_or_admin)
):
    db_team = db.query(Team).filter(Team.id == team_id).first()
    if not db_team: # Should be caught by dependency, but good practice
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Team not found")
    
    # Cascade delete for TeamMembers is handled by SQLAlchemy relationship config
    db.delete(db_team)
    db.commit()
    return

@router.post("/{team_id}/join", status_code=status.HTTP_204_NO_CONTENT)
def join_team(team_id: uuid.UUID, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """
    Allow the current user to join an existing team as a member.
    """
    team = db.query(Team).filter(Team.id == team_id).first()
    if not team:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Team not found")

    existing_member = db.query(TeamMember).filter(
        TeamMember.team_id == team_id, TeamMember.user_id == current_user.id
    ).first()
    if existing_member:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User is already a member of this team")

    new_member = TeamMember(
        team_id=team_id,
        user_id=current_user.id,
        role=TeamMemberRole.member
    )
    db.add(new_member)
    db.commit()
    return

@router.post("/{team_id}/leave", status_code=status.HTTP_204_NO_CONTENT)
def leave_team(
    team_id: uuid.UUID, 
    db: Session = Depends(get_db), 
    # Auth: current_user must be a member of this team.
    # Dependency returns the membership if valid.
    membership_to_delete: TeamMember = Depends(ensure_is_team_member) 
):
    """
    Allow the current user to leave a team they are a member of.
    If the owner leaves, and is the sole owner, specific logic in ensure_is_team_member might apply
    or further logic here could decide on team deletion/owner reassignment.
    """
    # Check if the user leaving is the sole owner.
    if membership_to_delete.role == TeamMemberRole.owner:
        owner_count = db.query(TeamMember).filter(
            TeamMember.team_id == team_id,
            TeamMember.role == TeamMemberRole.owner
        ).count()
        if owner_count <= 1:
            # This could be a place to enforce that a team must have an owner,
            # or trigger team deletion if the last owner leaves.
            # For now, we allow it, but this can be a point of future enhancement.
            # Consider raising an error or promoting another member if team shouldn't be ownerless.
            # raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot leave team as the sole owner. Delete the team or transfer ownership.")
            pass # Allowing sole owner to leave for now. Team becomes ownerless.

    db.delete(membership_to_delete)
    db.commit()
    return

@router.delete("/{team_id}/members/{user_id_to_remove}", status_code=status.HTTP_204_NO_CONTENT)
def remove_team_member(
    team_id: uuid.UUID, 
    user_id_to_remove: uuid.UUID,
    db: Session = Depends(get_db),
    # Auth: current_user must be team owner, admin, or the user_id_to_remove themselves.
    # Dependency returns the membership of the user to be removed.
    membership_to_delete: TeamMember = Depends(get_team_owner_admin_or_self_for_member_removal)
):
    """
    Remove a member from a team. 
    Allowed if the current user is the team owner, an admin, or the user themselves.
    Prevents owner from removing themselves if they are the sole owner (use /leave or delete team).
    """
    # The dependency already performed all necessary auth checks and found the membership_to_delete.
    # Special check from dependency: if owner tries to remove self as last owner, it would have raised an error.
    
    db.delete(membership_to_delete)
    db.commit()
    return 

@router.post("/{team_id}/request-join", status_code=201)
def request_join(team_id: uuid.UUID, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    team = db.query(Team).filter(Team.id == team_id).first()
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
    if not team.is_open:
        raise HTTPException(status_code=400, detail="Team is closed. Only invited users can join.")
    existing = db.query(JoinRequest).filter_by(team_id=team_id, user_id=current_user.id).first()
    if existing:
        raise HTTPException(status_code=400, detail="Join request already exists.")
    join_req = JoinRequest(team_id=team_id, user_id=current_user.id)
    db.add(join_req)
    db.commit()
    return {"detail": "Join request sent."}

@router.get("/{team_id}/join-requests", response_model=List[JoinRequestRead])
def list_join_requests(team_id: uuid.UUID, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    # Only owner/admin can see
    team = db.query(Team).filter(Team.id == team_id).first()
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
    owner = db.query(TeamMember).filter_by(team_id=team_id, user_id=current_user.id, role=TeamMemberRole.owner).first()
    if not owner and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Not authorized")
    return db.query(JoinRequest).filter_by(team_id=team_id, status=JoinRequestStatus.pending).all()

@router.post("/{team_id}/join-requests/{user_id}/accept", status_code=200)
def accept_join_request(team_id: uuid.UUID, user_id: uuid.UUID, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    team = db.query(Team).filter(Team.id == team_id).first()
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
    owner = db.query(TeamMember).filter_by(team_id=team_id, user_id=current_user.id, role=TeamMemberRole.owner).first()
    if not owner and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Not authorized")
    join_req = db.query(JoinRequest).filter_by(team_id=team_id, user_id=user_id, status=JoinRequestStatus.pending).first()
    if not join_req:
        raise HTTPException(status_code=404, detail="Join request not found")
    join_req.status = JoinRequestStatus.accepted
    db.add(TeamMember(team_id=team_id, user_id=user_id, role=TeamMemberRole.member))
    db.commit()
    return {"detail": "Join request accepted."}

@router.post("/{team_id}/join-requests/{user_id}/reject", status_code=200)
def reject_join_request(team_id: uuid.UUID, user_id: uuid.UUID, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    team = db.query(Team).filter(Team.id == team_id).first()
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
    owner = db.query(TeamMember).filter_by(team_id=team_id, user_id=current_user.id, role=TeamMemberRole.owner).first()
    if not owner and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Not authorized")
    join_req = db.query(JoinRequest).filter_by(team_id=team_id, user_id=user_id, status=JoinRequestStatus.pending).first()
    if not join_req:
        raise HTTPException(status_code=404, detail="Join request not found")
    join_req.status = JoinRequestStatus.rejected
    db.commit()
    return {"detail": "Join request rejected."}

@router.post("/{team_id}/invite", status_code=201)
def invite_user(team_id: uuid.UUID, email: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    team = db.query(Team).filter(Team.id == team_id).first()
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
    owner = db.query(TeamMember).filter_by(team_id=team_id, user_id=current_user.id, role=TeamMemberRole.owner).first()
    if not owner and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Not authorized")
    token = secrets.token_urlsafe(32)
    invite = TeamInvite(team_id=team_id, email=email, token=token)
    db.add(invite)
    db.commit()
    return {"detail": "Invite sent.", "token": token}

@router.get("/{team_id}/invites", response_model=List[TeamInviteRead])
def list_invites(team_id: uuid.UUID, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    team = db.query(Team).filter(Team.id == team_id).first()
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
    owner = db.query(TeamMember).filter_by(team_id=team_id, user_id=current_user.id, role=TeamMemberRole.owner).first()
    if not owner and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Not authorized")
    return db.query(TeamInvite).filter_by(team_id=team_id, status=TeamInviteStatus.pending).all()

@router.post("/{team_id}/invites/{email}/accept", status_code=200)
def accept_invite(team_id: uuid.UUID, email: str, token: str, db: Session = Depends(get_db)):
    invite = db.query(TeamInvite).filter_by(team_id=team_id, email=email, status=TeamInviteStatus.pending).first()
    if not invite or invite.token != token:
        raise HTTPException(status_code=404, detail="Invite not found or invalid token")
    invite.status = TeamInviteStatus.accepted
    # Find user by email
    user = db.query(User).filter_by(email=email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    db.add(TeamMember(team_id=team_id, user_id=user.id, role=TeamMemberRole.member))
    db.commit()
    return {"detail": "Invite accepted."}

@router.post("/{team_id}/invites/{email}/reject", status_code=200)
def reject_invite(team_id: uuid.UUID, email: str, token: str, db: Session = Depends(get_db)):
    invite = db.query(TeamInvite).filter_by(team_id=team_id, email=email, status=TeamInviteStatus.pending).first()
    if not invite or invite.token != token:
        raise HTTPException(status_code=404, detail="Invite not found or invalid token")
    invite.status = TeamInviteStatus.rejected
    db.commit()
    return {"detail": "Invite rejected."}

@router.delete("/{team_id}/join-requests/me", status_code=204)
def revoke_own_join_request(team_id: uuid.UUID, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    req = db.query(JoinRequest).filter_by(team_id=team_id, user_id=current_user.id, status=JoinRequestStatus.pending).first()
    if not req:
        raise HTTPException(status_code=404, detail="No pending join request found.")
    db.delete(req)
    db.commit()
    return 