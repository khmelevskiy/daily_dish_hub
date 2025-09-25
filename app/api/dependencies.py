"""API dependencies for authentication and authorization."""

import logging

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.db import session_scope
from app.models.user import User
from app.services import UserService


logger = logging.getLogger(__name__)

security = HTTPBearer(auto_error=False)


async def verify_admin_token(request: Request, credentials: HTTPAuthorizationCredentials = Depends(security)) -> User:
    """Verify token for admin endpoints."""
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization required",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = credentials.credentials
    token_data = UserService.verify_token(token=token)

    if token_data is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    async with session_scope() as session:
        if token_data.user_id is None:
            logger.error("Token user ID is missing")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token",
                headers={"WWW-Authenticate": "Bearer"},
            )
        user = await UserService.get_user_by_id(session=session, user_id=token_data.user_id)
        if user is None:
            logger.error(f"User not found for ID {token_data.user_id}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found",
                headers={"WWW-Authenticate": "Bearer"},
            )
        if not user.is_active:
            logger.error("Inactive user attempted access")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User is inactive",
                headers={"WWW-Authenticate": "Bearer"},
            )
        if not user.is_admin:
            logger.error("Admin access required but user is not admin")
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")
        # Attach current user to request.state for downstream use (no extra DB call)
        try:
            setattr(request.state, "current_user", user)
        except Exception:
            pass

        return user
