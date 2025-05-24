import os
from typing import Optional, Dict, Union
from datetime import datetime, timedelta, timezone
from jose import JWTError, jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User
from app.models.team import Team, TeamMember, TeamMemberRole
from app.models.project import Project
from app.models.submission import Submission
import uuid
from pydantic import BaseModel
from passlib.context import CryptContext

# Only use NEXTAUTH_SECRET, fail if not set
NEXTAUTH_SECRET = os.getenv("NEXTAUTH_SECRET")
if not NEXTAUTH_SECRET:
    raise RuntimeError("NEXTAUTH_SECRET must be set in the backend environment for authentication to work.")

ALGORITHM = "HS256"

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=60)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, NEXTAUTH_SECRET, algorithm=ALGORITHM)
    return encoded_jwt

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/users/login")

class TokenData(BaseModel):
    user_id: Optional[str] = None

def get_current_user(db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, NEXTAUTH_SECRET, algorithms=[ALGORITHM])
        user_id_str: str = payload.get("sub")
        if user_id_str is None:
            raise credentials_exception
        token_data = TokenData(user_id=user_id_str)
    except JWTError:
        raise credentials_exception

    user_id_as_uuid = uuid.UUID(token_data.user_id)
    user = db.query(User).filter(User.id == user_id_as_uuid).first()
    if user is None:
        raise credentials_exception
    return user

def get_current_user_or_admin_for_profile_update(
    user_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> User:
    target_user = db.query(User).filter(User.id == user_id).first()
    if not target_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    if current_user.id == target_user.id or current_user.role == "admin":
        return target_user
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Not authorized to update this user's profile"
    )

# --- Team Authorization Dependencies ---

def get_team_owner_or_admin(
    team_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Union[TeamMember, None]:
    team = db.query(Team).filter(Team.id == team_id).first()
    if not team:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Team not found")

    membership = db.query(TeamMember).filter(
        TeamMember.team_id == team_id,
        TeamMember.user_id == current_user.id
    ).first()

    if current_user.role == "admin":
        return membership

    if not membership or membership.role != TeamMemberRole.owner:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User is not the team owner or an administrator."
        )
    return membership

def get_team_member_or_admin(
    team_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Union[TeamMember, None]:
    team = db.query(Team).filter(Team.id == team_id).first()
    if not team:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Team not found")

    membership = db.query(TeamMember).filter(
        TeamMember.team_id == team_id,
        TeamMember.user_id == current_user.id
    ).first()

    if current_user.role == "admin":
        return membership

    if not membership:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User is not a member of this team or an administrator."
        )
    return membership

def ensure_is_team_member(
    team_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> TeamMember:
    team = db.query(Team).filter(Team.id == team_id).first()
    if not team:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Team not found")

    membership = db.query(TeamMember).filter(
        TeamMember.team_id == team_id,
        TeamMember.user_id == current_user.id
    ).first()

    if not membership:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User is not a member of this team."
        )
    return membership

def get_team_owner_admin_or_self_for_member_removal(
    team_id: uuid.UUID,
    user_id_to_remove: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> TeamMember:
    team = db.query(Team).filter(Team.id == team_id).first()
    if not team:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Team not found")

    membership_to_remove = db.query(TeamMember).filter(
        TeamMember.team_id == team_id,
        TeamMember.user_id == user_id_to_remove
    ).first()

    if not membership_to_remove:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Member to remove not found in this team.")

    if current_user.id == user_id_to_remove:
        if membership_to_remove.role == TeamMemberRole.owner:
            owner_count = db.query(TeamMember).filter(
                TeamMember.team_id == team_id,
                TeamMember.role == TeamMemberRole.owner
            ).count()
            if owner_count <= 1:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST, 
                    detail="Sole owner cannot remove themselves via this endpoint. Use leave team or delete team."
                )
        return membership_to_remove

    if current_user.role == "admin":
        return membership_to_remove

    current_user_membership = db.query(TeamMember).filter(
        TeamMember.team_id == team_id,
        TeamMember.user_id == current_user.id
    ).first()

    if current_user_membership and current_user_membership.role == TeamMemberRole.owner:
        return membership_to_remove
    
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Not authorized to remove this team member."
    )

# --- Project Authorization Dependencies ---

def get_project_team_member_or_admin(
    project_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> User:
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")

    if current_user.role == "admin":
        return current_user

    membership = db.query(TeamMember).filter(
        TeamMember.team_id == project.team_id,
        TeamMember.user_id == current_user.id
    ).first()

    if not membership:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User is not a member of the project's team or an administrator."
        )
    return current_user

def get_project_team_owner_or_admin(
    project_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Union[TeamMember, None]:
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")

    if current_user.role == "admin":
        membership = db.query(TeamMember).filter(
            TeamMember.team_id == project.team_id,
            TeamMember.user_id == current_user.id,
        ).first()
        return membership

    membership = db.query(TeamMember).filter(
        TeamMember.team_id == project.team_id,
        TeamMember.user_id == current_user.id,
        TeamMember.role == TeamMemberRole.owner
    ).first()

    if not membership:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User is not an owner of the project's team or an administrator."
        )
    return membership 

def get_submission_owner_project_team_member_or_admin(
    submission_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Submission:
    submission = db.query(Submission).filter(Submission.id == submission_id).first()
    if not submission:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Submission not found")

    if submission.user_id == current_user.id:
        return submission

    if current_user.role == "admin":
        return submission

    project = db.query(Project).filter(Project.id == submission.project_id).first()
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project associated with submission not found")

    team_membership = db.query(TeamMember).filter(
        TeamMember.team_id == project.team_id,
        TeamMember.user_id == current_user.id
    ).first()

    if team_membership:
        return submission

    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="User is not the submitter, a member of the project's team, or an administrator."
    )

def get_submission_owner_project_team_owner_or_admin(
    submission_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Submission:
    submission = db.query(Submission).filter(Submission.id == submission_id).first()
    if not submission:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Submission not found")

    if submission.user_id == current_user.id:
        return submission

    if current_user.role == "admin":
        return submission

    project = db.query(Project).filter(Project.id == submission.project_id).first()
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project associated with submission not found")

    team_ownership = db.query(TeamMember).filter(
        TeamMember.team_id == project.team_id,
        TeamMember.user_id == current_user.id,
        TeamMember.role == TeamMemberRole.owner
    ).first()

    if team_ownership:
        return submission

    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="User is not the submitter, an owner of the project's team, or an administrator."
    )
