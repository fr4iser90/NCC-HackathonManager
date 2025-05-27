import psutil
from fastapi import APIRouter, Depends, Request
from app.logger import get_logger

router = APIRouter(tags=["admin", "system-metrics"])
logger = get_logger("system_metrics")

from app.models.user import User
from fastapi import Depends
from app.auth import get_current_user

@router.get("/system-metrics")
async def get_system_metrics(
    request: Request,
    current_user: User = Depends(get_current_user)
):
    logger.info("system-metrics endpoint called")
    # Check if user is admin
    if not any(getattr(role, "role", None) == "admin" for role in getattr(current_user, "roles_association", [])):
        logger.error("User lacks admin role for /system-metrics")
        from fastapi import HTTPException, status
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required"
        )
    try:
        return {
            "cpu": {
                "usage": psutil.cpu_percent(),
                "cores": psutil.cpu_count()
            },
            "memory": {
                "total": psutil.virtual_memory().total,
                "used": psutil.virtual_memory().used,
                "free": psutil.virtual_memory().available
            },
            "storage": {
                "total": psutil.disk_usage('/').total,
                "used": psutil.disk_usage('/').used,
                "free": psutil.disk_usage('/').free
            }
        }
    except Exception as e:
        logger.error(f"Error in /system-metrics: {e}", exc_info=True)
        return {"error": "Internal server error. Check backend logs for details."}
