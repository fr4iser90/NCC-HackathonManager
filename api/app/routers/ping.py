from fastapi import APIRouter, Depends
from app.auth import get_current_user
from app.models.user import User

router = APIRouter()

@router.get("/")
def ping(current_user: User = Depends(get_current_user)):
    return {"ok": True} 