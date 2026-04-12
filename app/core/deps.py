from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from app.models.user import UserRole , User
from app.core.database import get_db
from app.core.security import verify_access_token
from app.services import user_service

# This tells FastAPI: "Look for Authorization: Bearer <token> header"
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
):
    """
    Runs BEFORE your route handler.
    Extracts token → verifies → looks up user → returns user object.
    """
    payload = verify_access_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
        )
    
    user = await user_service.get_user(db, UUID(user_id))
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or deactivated",
        )
    
    return user

from app.models.user import UserRole

def require_role(*allowed_roles: UserRole):
    """
    The Bouncer Factory. 
    Why a nested function? Because FastAPI's Depends() can't take extra arguments easily.
    By nesting, we "bake" the allowed roles into a custom function.
    This prevents the client from providing the permission list themselves!
    """
    async def role_checker(current_user: User = Depends(get_current_user)):
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to perform this action",
            )
        return current_user
    return role_checker

