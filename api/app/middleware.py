from fastapi import Request, HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import List, Optional, Callable
from functools import wraps
from app.models.user import UserRole
from app.auth import get_current_user
from app.database import get_db
from sqlalchemy.orm import Session
from app.logger import get_logger

logger = get_logger("middleware")

security = HTTPBearer()


def require_roles(required_roles: List[UserRole]):
    """
    Decorator to require specific roles for accessing an endpoint.
    Usage: @require_roles([UserRole.ADMIN, UserRole.ORGANIZER])
    """
    async def dependency(request: Request, db: Session = Depends(get_db)):
        logger.info(f"require_roles: called for roles {required_roles}")
        
        try:
            user = await get_current_user(request, db)
        except Exception as e:
            logger.error(f"Error in get_current_user: {e}", exc_info=True)
            raise

        # Check if user has any of the required roles
        try:
            user_roles = [UserRole(role.role) for role in user.roles_association]
            if not any(role in required_roles for role in user_roles):
                logger.error(f"User lacks required roles: {user_roles} vs {required_roles}")
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Required roles: {[role.value for role in required_roles]}",
                )
        except Exception as e:
            logger.error(f"Error checking user roles: {e}", exc_info=True)
            raise

        return user

    return Depends(dependency)


# Role-specific middleware functions
def require_admin():
    """Require admin role for access"""
    return require_roles([UserRole.ADMIN])


def require_organizer():
    """Require organizer role for access"""
    return require_roles([UserRole.ADMIN, UserRole.ORGANIZER])


def require_judge():
    """Require judge role for access"""
    return require_roles([UserRole.ADMIN, UserRole.JUDGE])


def require_mentor():
    """Require mentor role for access"""
    return require_roles([UserRole.ADMIN, UserRole.MENTOR])


def require_participant():
    """Require participant role for access"""
    return require_roles([UserRole.ADMIN, UserRole.PARTICIPANT])


# Role-based permission checks
def has_role(user_roles: List[UserRole], required_role: UserRole) -> bool:
    """Check if user has a specific role"""
    return required_role in user_roles


def has_any_role(user_roles: List[UserRole], required_roles: List[UserRole]) -> bool:
    """Check if user has any of the required roles"""
    return any(role in required_roles for role in user_roles)


def has_all_roles(user_roles: List[UserRole], required_roles: List[UserRole]) -> bool:
    """Check if user has all of the required roles"""
    return all(role in required_roles for role in user_roles)
