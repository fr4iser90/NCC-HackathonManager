from .users import router as users_router
from .teams import router as teams_router
from .projects import router as projects_router
from .judging import router as judging_router
from .hackathons import router as hackathons_router
from .submissions import router as submissions_router

__all__ = [
    "users_router",
    "teams_router",
    "projects_router",
    "judging_router",
    "hackathons_router",
    "submissions_router",
]
