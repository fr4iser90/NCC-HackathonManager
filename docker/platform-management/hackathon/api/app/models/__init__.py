# This file makes Python treat the directory as a package.
# It's also a good place to ensure all models are imported so SQLAlchemy can discover them.

from .user import User
from .team import Team, TeamMember, JoinRequest, TeamInvite
from .hackathon import Hackathon
from .project import Project, ProjectTemplate
from .submission import Submission
from .judging import Criterion, Score # Corrected import names
from .hackathon_registration import HackathonRegistration

__all__ = [
    "User",
    "Team",
    "TeamMember",
    "JoinRequest",
    "TeamInvite",
    "Hackathon",
    "Project",
    "ProjectTemplate",
    "Submission",
    "Criterion", # Corrected class name
    "Score",     # Corrected class name
    # "JudgeAssignment", # This class was not found in judging.py, removing for now
    "HackathonRegistration",
]
