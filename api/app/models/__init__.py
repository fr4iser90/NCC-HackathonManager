# This file makes Python treat the directory as a package.
# It's also a good place to ensure all models are imported so SQLAlchemy can discover them.

from .user import User
from .session import Session
from .project import Project, ProjectTemplate, ProjectVersion
from .team import Team, TeamMember, TeamHistory, MemberHistory, JoinRequest, TeamInvite
from .hackathon import Hackathon
from .hackathon_registration import HackathonRegistration
from .judging import Criterion, Score
from .submission import Submission

__all__ = [
    "User",
    "Session",
    "Project",
    "ProjectTemplate",
    "ProjectVersion",
    "Team",
    "TeamMember",
    "TeamHistory",
    "MemberHistory",
    "JoinRequest",
    "TeamInvite",
    "Hackathon",
    "HackathonRegistration",
    "Criterion",
    "Score",
    "Submission",
]
