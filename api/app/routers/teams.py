from typing import List
import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
import secrets
from app.logger import get_logger

from app.database import get_db
from app.models.user import User
from app.models.team import Team, TeamMember, JoinRequest, JoinRequestStatus, TeamInvite, TeamInviteStatus, TeamStatus
from app.models.hackathon import Hackathon
from app.schemas.team import TeamCreate, TeamRead, TeamUpdate, TeamMemberRole, JoinRequestRead, TeamInviteRead
from app.auth import (
    get_current_user, 
    get_team_owner_or_admin,
    ensure_is_team_member,
    get_team_owner_admin_or_self_for_member_removal
)

# Initialize logger
logger = get_logger("teams_router")

router = APIRouter()

@router.get("/my-join-requests", response_model=List[JoinRequestRead], dependencies=[Depends(get_current_user)])
def list_my_join_requests(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    allowed = {JoinRequestStatus.pending, JoinRequestStatus.accepted, JoinRequestStatus.rejected}
    all_reqs = db.query(JoinRequest).filter(JoinRequest.user_id == current_user.id).all()
    filtered = [req for req in all_reqs if req.status in allowed]
    logger.debug(f"DEBUG JOINREQUESTS COUNT: {len(filtered)}")
    for req in filtered:
        logger.debug(f"DEBUG JOINREQUEST: team_id={req.team_id} ({type(req.team_id)}), user_id={req.user_id} ({type(req.user_id)}), status={req.status} ({type(req.status)}), created_at={req.created_at} ({type(req.created_at)})")
    return [JoinRequestRead.model_validate(req) for req in filtered]

@router.post("/", response_model=TeamRead, status_code=status.HTTP_201_CREATED)
def create_team(team_in: TeamCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """
    Create a new team for a specific hackathon. The creator becomes the team leader.
    """
    # Verify hackathon exists and is active
    hackathon = db.query(Hackathon).filter(Hackathon.id == team_in.hackathon_id).first()
    if not hackathon:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Hackathon not found")
    if hackathon.status != "active":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot create team for inactive hackathon")

    try:
        db_team = Team(
            name=team_in.name,
            description=team_in.description,
            is_open=team_in.is_open,
            hackathon_id=team_in.hackathon_id,
            status=TeamStatus.active
        )
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
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Team name already exists for this hackathon."
        )

@router.get("/", response_model=List[TeamRead], dependencies=[Depends(get_current_user)])
def list_teams(hackathon_id: uuid.UUID, skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """
    List all teams for a specific hackathon.
    """
    teams = db.query(Team).filter(
        Team.hackathon_id == hackathon_id,
        Team.status == TeamStatus.active
    ).offset(skip).limit(limit).all()
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

    # Verify hackathon is still active
    hackathon = db.query(Hackathon).filter(Hackathon.id == db_team.hackathon_id).first()
    if not hackathon or hackathon.status != "active":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot update team for inactive hackathon")

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
            detail="Team name already exists for this hackathon or other integrity violation."
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
    
    # Instead of deleting, mark as disbanded
    db_team.status = TeamStatus.disbanded
    db.add(db_team)
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
    
    # Verify hackathon is active
    hackathon = db.query(Hackathon).filter(Hackathon.id == team.hackathon_id).first()
    if not hackathon or hackathon.status != "active":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot join team for inactive hackathon")

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
    If the owner leaves, and is the sole owner, the team is marked as disbanded.
    """
    team = db.query(Team).filter(Team.id == team_id).first()
    if not team:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Team not found")

    # Check if the user leaving is the sole owner
    if membership_to_delete.role == TeamMemberRole.owner:
        owner_count = db.query(TeamMember).filter(
            TeamMember.team_id == team_id,
            TeamMember.role == TeamMemberRole.owner
        ).count()
        if owner_count <= 1:
            # Mark team as disbanded if last owner leaves
            team.status = TeamStatus.disbanded
            db.add(team)

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
    If removing the last owner, the team is marked as disbanded.
    """
    team = db.query(Team).filter(Team.id == team_id).first()
    if not team:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Team not found")

    # Check if removing the last owner
    if membership_to_delete.role == TeamMemberRole.owner:
        owner_count = db.query(TeamMember).filter(
            TeamMember.team_id == team_id,
            TeamMember.role == TeamMemberRole.owner
        ).count()
        if owner_count <= 1:
            # Mark team as disbanded if removing last owner
            team.status = TeamStatus.disbanded
            db.add(team)
    
    db.delete(membership_to_delete)
    db.commit()
    return

@router.post("/{team_id}/request-join", status_code=201)
def request_join(team_id: uuid.UUID, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    team = db.query(Team).filter(Team.id == team_id).first()
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
    
    # Verify hackathon is active
    hackathon = db.query(Hackathon).filter(Hackathon.id == team.hackathon_id).first()
    if not hackathon or hackathon.status != "active":
        raise HTTPException(status_code=400, detail="Cannot request to join team for inactive hackathon")

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
    team = db.query(Team).filter(Team.id == team_id).first()
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
    
    # Verify hackathon is active
    hackathon = db.query(Hackathon).filter(Hackathon.id == team.hackathon_id).first()
    if not hackathon or hackathon.status != "active":
        raise HTTPException(status_code=400, detail="Cannot view join requests for inactive hackathon")

    owner = db.query(TeamMember).filter_by(team_id=team_id, user_id=current_user.id, role=TeamMemberRole.owner).first()
    if not owner and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Not authorized")
    return db.query(JoinRequest).filter_by(team_id=team_id, status=JoinRequestStatus.pending).all()

@router.post("/{team_id}/join-requests/{user_id}/accept", status_code=200)
def accept_join_request(team_id: uuid.UUID, user_id: uuid.UUID, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    team = db.query(Team).filter(Team.id == team_id).first()
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
    
    # Verify hackathon is active
    hackathon = db.query(Hackathon).filter(Hackathon.id == team.hackathon_id).first()
    if not hackathon or hackathon.status != "active":
        raise HTTPException(status_code=400, detail="Cannot accept join request for inactive hackathon")

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
    
    # Verify hackathon is active
    hackathon = db.query(Hackathon).filter(Hackathon.id == team.hackathon_id).first()
    if not hackathon or hackathon.status != "active":
        raise HTTPException(status_code=400, detail="Cannot reject join request for inactive hackathon")

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
    
    # Verify hackathon is active
    hackathon = db.query(Hackathon).filter(Hackathon.id == team.hackathon_id).first()
    if not hackathon or hackathon.status != "active":
        raise HTTPException(status_code=400, detail="Cannot invite users for inactive hackathon")

    owner = db.query(TeamMember).filter_by(team_id=team_id, user_id=current_user.id, role=TeamMemberRole.owner).first()
    if not owner and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Not authorized")
    existing = db.query(TeamInvite).filter_by(team_id=team_id, email=email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Invite already exists")
    token = secrets.token_urlsafe(32)
    invite = TeamInvite(team_id=team_id, email=email, token=token)
    db.add(invite)
    db.commit()
    return {"detail": "Invite sent."}

@router.get("/{team_id}/invites", response_model=List[TeamInviteRead])
def list_invites(team_id: uuid.UUID, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    team = db.query(Team).filter(Team.id == team_id).first()
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
    
    # Verify hackathon is active
    hackathon = db.query(Hackathon).filter(Hackathon.id == team.hackathon_id).first()
    if not hackathon or hackathon.status != "active":
        raise HTTPException(status_code=400, detail="Cannot view invites for inactive hackathon")

    owner = db.query(TeamMember).filter_by(team_id=team_id, user_id=current_user.id, role=TeamMemberRole.owner).first()
    if not owner and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Not authorized")
    return db.query(TeamInvite).filter_by(team_id=team_id, status=TeamInviteStatus.pending).all()

@router.post("/{team_id}/invites/{email}/accept", status_code=200)
def accept_invite(team_id: uuid.UUID, email: str, token: str, db: Session = Depends(get_db)):
    team = db.query(Team).filter(Team.id == team_id).first()
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
    
    # Verify hackathon is active
    hackathon = db.query(Hackathon).filter(Hackathon.id == team.hackathon_id).first()
    if not hackathon or hackathon.status != "active":
        raise HTTPException(status_code=400, detail="Cannot accept invite for inactive hackathon")

    invite = db.query(TeamInvite).filter_by(team_id=team_id, email=email, token=token, status=TeamInviteStatus.pending).first()
    if not invite:
        raise HTTPException(status_code=404, detail="Invite not found")
    invite.status = TeamInviteStatus.accepted
    db.commit()
    return {"detail": "Invite accepted."}

@router.post("/{team_id}/invites/{email}/reject", status_code=200)
def reject_invite(team_id: uuid.UUID, email: str, token: str, db: Session = Depends(get_db)):
    team = db.query(Team).filter(Team.id == team_id).first()
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
    
    # Verify hackathon is active
    hackathon = db.query(Hackathon).filter(Hackathon.id == team.hackathon_id).first()
    if not hackathon or hackathon.status != "active":
        raise HTTPException(status_code=400, detail="Cannot reject invite for inactive hackathon")

    invite = db.query(TeamInvite).filter_by(team_id=team_id, email=email, token=token, status=TeamInviteStatus.pending).first()
    if not invite:
        raise HTTPException(status_code=404, detail="Invite not found")
    invite.status = TeamInviteStatus.rejected
    db.commit()
    return {"detail": "Invite rejected."}

@router.delete("/{team_id}/join-requests/me", status_code=204)
def revoke_own_join_request(team_id: uuid.UUID, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    team = db.query(Team).filter(Team.id == team_id).first()
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
    
    # Verify hackathon is active
    hackathon = db.query(Hackathon).filter(Hackathon.id == team.hackathon_id).first()
    if not hackathon or hackathon.status != "active":
        raise HTTPException(status_code=400, detail="Cannot revoke join request for inactive hackathon")

    join_req = db.query(JoinRequest).filter_by(team_id=team_id, user_id=current_user.id, status=JoinRequestStatus.pending).first()
    if not join_req:
        raise HTTPException(status_code=404, detail="Join request not found")
    db.delete(join_req)
    db.commit()
    return

@router.get("/{team_id}/join-requests/me", response_model=JoinRequestRead)
def get_own_join_request(team_id: uuid.UUID, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    team = db.query(Team).filter(Team.id == team_id).first()
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
    
    # Verify hackathon is active
    hackathon = db.query(Hackathon).filter(Hackathon.id == team.hackathon_id).first()
    if not hackathon or hackathon.status != "active":
        raise HTTPException(status_code=400, detail="Cannot view join request for inactive hackathon")

    join_req = db.query(JoinRequest).filter_by(team_id=team_id, user_id=current_user.id).first()
    if not join_req:
        raise HTTPException(status_code=404, detail="Join request not found")
    return join_req 