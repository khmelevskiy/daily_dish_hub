from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class UserCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=50, description="Username")
    password: str = Field(..., min_length=8, description="Password")
    is_admin: bool = Field(False, description="Is administrator")


class UserUpdate(BaseModel):
    username: str | None = Field(None, min_length=3, max_length=50, description="Username")
    password: str | None = Field(None, min_length=8, description="Password")
    is_active: bool | None = Field(None, description="Is user active")
    is_admin: bool | None = Field(None, description="Is administrator")


class UserResponse(BaseModel):
    id: int
    username: str
    is_active: bool
    is_admin: bool
    created_at: datetime
    last_login: datetime | None

    model_config = ConfigDict(from_attributes=True)


class UserListResponse(BaseModel):
    users: list[UserResponse]
    total: int


class LoginRequest(BaseModel):
    username: str = Field(..., description="Username")
    password: str = Field(..., description="Password")


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


class TokenData(BaseModel):
    username: str | None = None
    user_id: int | None = None


__all__ = [
    "UserCreate",
    "UserUpdate",
    "UserResponse",
    "UserListResponse",
    "LoginRequest",
    "LoginResponse",
    "TokenData",
]
