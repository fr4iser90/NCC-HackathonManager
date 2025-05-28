from fastapi import APIRouter, Depends
from app.models.user import User, UserRole
from app.middleware import require_roles

router = APIRouter(tags=["ping"])


@router.get("/", dependencies=[require_roles([UserRole.ADMIN])])
async def ping():
    """Ping endpoint. Only accessible by admin users."""
    return {"ok": True}
