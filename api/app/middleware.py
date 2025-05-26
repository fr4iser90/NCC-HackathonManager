from fastapi import Request, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import List, Optional, Callable
from functools import wraps
from app.models.user import UserRole
from app.auth import get_current_user
from app.database import get_db
from sqlalchemy.orm import Session

security = HTTPBearer()

def require_roles(required_roles: List[UserRole]):
    """
    Decorator to require specific roles for accessing an endpoint.
    Usage: @require_roles([UserRole.ADMIN, UserRole.ORGANIZER])
    """
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Get the request object from kwargs
            request = kwargs.get('request')
            if not request:
                for arg in args:
                    if isinstance(arg, Request):
                        request = arg
                        break
            
            if not request:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Request object not found"
                )

            # Get the current user
            db = next(get_db())
            user = await get_current_user(request, db)
            
            # Check if user has any of the required roles
            user_roles = [UserRole(role.role) for role in user.roles_association]
            if not any(role in required_roles for role in user_roles):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Required roles: {[role.value for role in required_roles]}"
                )
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator

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
    return all(role in user_roles for role in required_roles)
