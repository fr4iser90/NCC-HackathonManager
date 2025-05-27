"""
Service layer for team-related business logic.
"""

from sqlalchemy.orm import Session
from app.models.team import (
    Team,
    TeamMember,
    JoinRequest,
    JoinRequestStatus,
    TeamInvite,
    TeamInviteStatus,
    TeamStatus,
)
from app.models.hackathon import Hackathon
from app.models.user import User
from app.schemas.team import TeamCreate, TeamUpdate, TeamMemberRole
from app.schemas.hackathon import HackathonStatus
from fastapi import HTTPException, status
import secrets
import uuid

IS_ADMIN = lambda user: any(
    r.role == "admin" for r in getattr(user, "roles_association", [])
)


def create_team(db: Session, team_in: TeamCreate, current_user: User) -> Team:
    """Create a new team for a specific hackathon. The creator becomes the team leader."""
    hackathon = db.query(Hackathon).filter(Hackathon.id == team_in.hackathon_id).first()
    if not hackathon:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Hackathon not found"
        )
    if hackathon.status != HackathonStatus.ACTIVE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot create team for inactive hackathon",
        )
    try:
        db_team = Team(
            name=team_in.name,
            description=team_in.description,
            is_open=team_in.is_open,
            hackathon_id=team_in.hackathon_id,
            status=TeamStatus.active,
        )
        db.add(db_team)
        db.flush()
        team_leader = TeamMember(
            team_id=db_team.id, user_id=current_user.id, role=TeamMemberRole.owner
        )
        db.add(team_leader)
        db.commit()
        db.refresh(db_team)
        return db_team
    except Exception:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Team name already exists for this hackathon.",
        )


def update_team(db: Session, team_id: uuid.UUID, team_in: TeamUpdate) -> Team:
    """Update a team's details."""
    db_team = db.query(Team).filter(Team.id == team_id).first()
    if not db_team:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Team not found"
        )
    hackathon = db.query(Hackathon).filter(Hackathon.id == db_team.hackathon_id).first()
    if not hackathon or hackathon.status != HackathonStatus.ACTIVE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot update team for inactive hackathon",
        )
    update_data = team_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_team, field, value)
    try:
        db.add(db_team)
        db.commit()
        db.refresh(db_team)
        return db_team
    except Exception:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Team name already exists for this hackathon or other integrity violation.",
        )


def join_team(db: Session, team_id: uuid.UUID, current_user: User):
    """Allow the current user to join an existing team as a member."""
    team = db.query(Team).filter(Team.id == team_id).first()
    if not team:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Team not found"
        )
    hackathon = db.query(Hackathon).filter(Hackathon.id == team.hackathon_id).first()
    if not hackathon or hackathon.status != HackathonStatus.ACTIVE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot join team for inactive hackathon",
        )
    existing_member = (
        db.query(TeamMember)
        .filter(TeamMember.team_id == team_id, TeamMember.user_id == current_user.id)
        .first()
    )
    if existing_member:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User is already a member of this team",
        )
    new_member = TeamMember(
        team_id=team_id, user_id=current_user.id, role=TeamMemberRole.member
    )
    db.add(new_member)
    db.commit()
    return


def leave_team(db: Session, team_id: uuid.UUID, membership_to_delete: TeamMember):
    """Allow the current user to leave a team they are a member of."""
    team = db.query(Team).filter(Team.id == team_id).first()
    if not team:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Team not found"
        )
    if membership_to_delete.role == TeamMemberRole.owner:
        owner_count = (
            db.query(TeamMember)
            .filter(
                TeamMember.team_id == team_id, TeamMember.role == TeamMemberRole.owner
            )
            .count()
        )
        if owner_count <= 1:
            team.status = TeamStatus.disbanded
            db.add(team)
    db.delete(membership_to_delete)
    db.commit()
    return


def request_join(db: Session, team_id: uuid.UUID, current_user: User):
    """Request to join a team."""
    team = db.query(Team).filter(Team.id == team_id).first()
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
    hackathon = db.query(Hackathon).filter(Hackathon.id == team.hackathon_id).first()
    if not hackathon or hackathon.status != HackathonStatus.ACTIVE:
        raise HTTPException(
            status_code=400, detail="Cannot request to join team for inactive hackathon"
        )
    if not team.is_open:
        raise HTTPException(
            status_code=400, detail="Team is closed. Only invited users can join."
        )
    existing = (
        db.query(JoinRequest)
        .filter_by(team_id=team_id, user_id=current_user.id)
        .first()
    )
    if existing:
        raise HTTPException(status_code=400, detail="Join request already exists.")
    join_req = JoinRequest(team_id=team_id, user_id=current_user.id)
    db.add(join_req)
    db.commit()
    return {"detail": "Join request sent."}


def accept_join_request(
    db: Session, team_id: uuid.UUID, user_id: uuid.UUID, current_user: User
):
    """Accept a join request for a team."""
    team = db.query(Team).filter(Team.id == team_id).first()
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
    hackathon = db.query(Hackathon).filter(Hackathon.id == team.hackathon_id).first()
    if not hackathon or hackathon.status != HackathonStatus.ACTIVE:
        raise HTTPException(
            status_code=400, detail="Cannot accept join request for inactive hackathon"
        )
    owner = (
        db.query(TeamMember)
        .filter_by(team_id=team_id, user_id=current_user.id, role=TeamMemberRole.owner)
        .first()
    )
    if not owner and not IS_ADMIN(current_user):
        raise HTTPException(status_code=403, detail="Not authorized")
    join_req = (
        db.query(JoinRequest)
        .filter_by(team_id=team_id, user_id=user_id, status=JoinRequestStatus.pending)
        .first()
    )
    if not join_req:
        raise HTTPException(status_code=404, detail="Join request not found")
    join_req.status = JoinRequestStatus.accepted
    db.add(TeamMember(team_id=team_id, user_id=user_id, role=TeamMemberRole.member))
    db.commit()
    return {"detail": "Join request accepted."}
