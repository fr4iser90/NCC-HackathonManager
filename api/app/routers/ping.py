from fastapi import APIRouter, Depends
from app.auth import get_current_user
from app.models.user import User, UserRole
from app.middleware import require_roles

router = APIRouter(tags=["ping"])

@router.get("/", dependencies=[Depends(require_roles([UserRole.ADMIN]))])
def ping(current_user: User = Depends(get_current_user)):
    """Ping endpoint. Only accessible by admin users."""
    return {"ok": True} 