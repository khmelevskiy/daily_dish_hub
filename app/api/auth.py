import logging

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.db import session_scope
from app.models.user import User
from app.schemas.auth import LoginRequest, LoginResponse, UserCreate, UserListResponse, UserResponse, UserUpdate
from app.schemas.common import SuccessResponse
from app.services import UserService


logger = logging.getLogger(__name__)

router = APIRouter()
security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> User:
    """Get current user from token."""
    token = credentials.credentials
    token_data = UserService.verify_token(token=token)

    if token_data is None:
        logger.error("Token verification failed")
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

        return user


async def get_current_admin_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """Get current admin user."""
    if not current_user.is_admin:
        logger.error("Admin access required but user is not admin")
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")

    return current_user


@router.post(
    "/login",
    response_model=LoginResponse,
    summary="Login",
    description="Authenticate user and return JWT access token.",
)
async def login(login_data: LoginRequest):
    """Login."""
    async with session_scope() as session:
        user = await UserService.authenticate_user(
            session=session, username=login_data.username, password=login_data.password
        )
        if not user:
            logger.error("Failed login attempt")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid username or password",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Update last login time
        await UserService.update_last_login(session=session, user_id=user.id)

        # Create JWT token
        access_token = UserService.create_access_token(data={"sub": user.username, "user_id": user.id})

        return LoginResponse(
            access_token=access_token,
            token_type="bearer",
            user=UserResponse(
                id=user.id,
                username=user.username,
                is_active=user.is_active,
                is_admin=user.is_admin,
                created_at=user.created_at,
                last_login=user.last_login,
            ),
        )


@router.post(
    "/register",
    response_model=SuccessResponse,
    summary="Register User (admin)",
    description="Create a new user account (administrators only).",
)
async def register(user_data: UserCreate, current_admin: User = Depends(get_current_admin_user)):
    """Register a new user (admins only)."""
    async with session_scope() as session:
        try:
            user = await UserService.create_user(session=session, user_data=user_data)

            return SuccessResponse(
                message="User created successfully",
                data={"id": user.id, "username": user.username},
            )
        except ValueError as e:
            logger.error("User registration failed")
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Current User",
    description="Return information about the currently authenticated user.",
)
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """Get current user info."""
    return UserResponse(
        id=current_user.id,
        username=current_user.username,
        is_active=current_user.is_active,
        is_admin=current_user.is_admin,
        created_at=current_user.created_at,
        last_login=current_user.last_login,
    )


@router.get(
    "/users",
    response_model=UserListResponse,
    summary="List Users (admin)",
    description="List all users (administrators only).",
)
async def list_users(current_admin: User = Depends(get_current_admin_user)):
    """List all users (admins only)."""
    async with session_scope() as session:
        users = await UserService.get_all_users(session=session)
        users_list = [
            UserResponse(
                id=user.id,
                username=user.username,
                is_active=user.is_active,
                is_admin=user.is_admin,
                created_at=user.created_at,
                last_login=user.last_login,
            )
            for user in users
        ]
        return UserListResponse(users=users_list, total=len(users_list))


@router.get(
    "/users/{user_id}",
    response_model=UserResponse,
    summary="Get User (admin)",
    description="Get user information by ID (administrators only).",
)
async def get_user(user_id: int, current_admin: User = Depends(get_current_admin_user)):
    """Get user info (admins only)."""
    async with session_scope() as session:
        user = await UserService.get_user_by_id(session=session, user_id=user_id)
        if not user:
            logger.error(f"User not found for ID {user_id}")
            raise HTTPException(status_code=404, detail="User not found")

        return UserResponse(
            id=user.id,
            username=user.username,
            is_active=user.is_active,
            is_admin=user.is_admin,
            created_at=user.created_at,
            last_login=user.last_login,
        )


@router.put(
    "/users/{user_id}",
    response_model=SuccessResponse,
    summary="Update User (admin)",
    description="Update user fields (administrators only).",
)
async def update_user(
    user_id: int,
    user_data: UserUpdate,
    current_admin: User = Depends(get_current_admin_user),
):
    """Update user (admins only)."""
    async with session_scope() as session:
        try:
            user = await UserService.update_user(session=session, user_id=user_id, user_data=user_data)
            if not user:
                logger.error(f"User not found for ID {user_id}")
                raise HTTPException(status_code=404, detail="User not found")

            return SuccessResponse(
                message="User updated successfully",
                data={"id": user.id, "username": user.username},
            )
        except ValueError as e:
            logger.error("User update failed")
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.delete(
    "/users/{user_id}",
    response_model=SuccessResponse,
    summary="Delete User (admin)",
    description="Delete a user by ID (administrators only).",
)
async def delete_user(user_id: int, current_admin: User = Depends(get_current_admin_user)):
    """Delete user (admins only)."""
    if user_id == current_admin.id:
        logger.error("User attempted to delete themselves")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot delete yourself")

    async with session_scope() as session:
        success = await UserService.delete_user(session=session, user_id=user_id)
        if not success:
            raise HTTPException(status_code=404, detail="User not found")

        return SuccessResponse(message="User deleted successfully")
