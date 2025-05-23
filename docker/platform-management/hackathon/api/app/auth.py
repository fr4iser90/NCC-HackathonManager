import os
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Union
from jose import JWTError, jwt
from passlib.context import CryptContext
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

# Define OAuth2 scheme here instead of in a separate file
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/users/login")

# Pydantic model for token data
class TokenData(BaseModel):
    user_id: Optional[str] = None

SECRET_KEY = os.getenv("JWT_SECRET", "supersecret")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))

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
        expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def get_current_user(db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
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
        return membership # Admin is authorized. Return their specific membership if they have one, else None.

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
        return membership # Admin is authorized. Return their specific membership if they have one, else None.

    if not membership:
        # If not admin and no membership, then forbidden.
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User is not a member of this team or an administrator."
        )
    return membership # Regular user who is a member

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
) -> TeamMember: # Returns the membership of the user to be removed
    team = db.query(Team).filter(Team.id == team_id).first()
    if not team:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Team not found")

    membership_to_remove = db.query(TeamMember).filter(
        TeamMember.team_id == team_id,
        TeamMember.user_id == user_id_to_remove
    ).first()

    if not membership_to_remove:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Member to remove not found in this team.")

    # Case 1: User is removing themselves
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
        return membership_to_remove # Allowed to remove self if not sole owner, or if member

    # Case 2: Current user is an admin (and not self-removing, handled above)
    if current_user.role == "admin":
        return membership_to_remove

    # Case 3: Current user is team owner removing someone else
    current_user_membership = db.query(TeamMember).filter(
        TeamMember.team_id == team_id,
        TeamMember.user_id == current_user.id
    ).first()

    if current_user_membership and current_user_membership.role == TeamMemberRole.owner:
        # Owner removing another member (or another owner if multiple owners were allowed and logic was different)
        # The check for removing the *last* owner was for self-removal. 
        # An owner cannot remove another owner if that would leave the team ownerless (unless we implement promotion).
        # For now, an owner can remove any other member. Removing another owner is not explicitly blocked here
        # but would be complex if it's the last one. Assume current tests cover valid owner actions.
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

    # Admins are always authorized
    if current_user.role == "admin":
        return current_user # Return the admin User object

    # Check if the current user is a member of the project's team
    membership = db.query(TeamMember).filter(
        TeamMember.team_id == project.team_id,
        TeamMember.user_id == current_user.id
    ).first()

    if not membership:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User is not a member of the project's team or an administrator."
        )
    return current_user # Return the User object if they are a team member

def get_project_team_owner_or_admin(
    project_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Union[TeamMember, None]:
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")

    # Admins are always authorized
    if current_user.role == "admin":
        membership = db.query(TeamMember).filter(
            TeamMember.team_id == project.team_id,
            TeamMember.user_id == current_user.id,
            # Optionally, check if admin is also an owner if that info is needed by endpoint
            # TeamMember.role == TeamMemberRole.owner 
        ).first()
        return membership

    # Check if the current user is an owner of the project's team
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

# --- Submission Authorization Dependencies ---

def get_submission_owner_project_team_member_or_admin(
    submission_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Submission: # Returns the submission if authorized, else raises HTTPException
    submission = db.query(Submission).filter(Submission.id == submission_id).first()
    if not submission:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Submission not found")

    # Allow if current user is the submitter
    if submission.user_id == current_user.id:
        return submission

    # Allow if current user is an admin
    if current_user.role == "admin":
        return submission

    # Allow if current user is a member of the project's team
    project = db.query(Project).filter(Project.id == submission.project_id).first()
    if not project: # Should not happen if submission exists with valid project_id
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project associated with submission not found")

    team_membership = db.query(TeamMember).filter(
        TeamMember.team_id == project.team_id,
        TeamMember.user_id == current_user.id
    ).first()

    if team_membership:
        return submission
    
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="User is not the submitter, a member of the project\'s team, or an administrator."
    )

def get_submission_owner_project_team_owner_or_admin(
    submission_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Submission: # Returns the submission if authorized, else raises HTTPException
    submission = db.query(Submission).filter(Submission.id == submission_id).first()
    if not submission:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Submission not found")

    # Allow if current user is the submitter
    if submission.user_id == current_user.id:
        return submission

    # Allow if current user is an admin
    if current_user.role == "admin":
        return submission

    # Allow if current user is an owner of the project's team
    project = db.query(Project).filter(Project.id == submission.project_id).first()
    if not project: # Should not happen
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
        detail="User is not the submitter, an owner of the project\'s team, or an administrator."
    ) 