import re
from datetime import datetime, timedelta, timezone

import bcrypt
from jose import JWTError, jwt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.user import User
from app.schemas.auth import TokenData, UserCreate, UserUpdate
from app.services.base_service import BaseCRUDService


def hash_password_bcrypt(password: str) -> str:
    """Hash password using bcrypt."""
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password_bcrypt(password: str, hashed_password: str) -> bool:
    """Verify password using bcrypt."""
    try:
        return bcrypt.checkpw(password.encode("utf-8"), hashed_password.encode("utf-8"))
    except Exception:
        return False


class UserService(BaseCRUDService[User]):
    model = User

    @staticmethod
    def _validate_password_policy(password: str) -> None:
        """Basic password policy: at least 8 chars, contains letters and digits.

        Raise ValueError with a user-friendly message if policy is not met.
        """
        if password is None:
            raise ValueError("Password cannot be empty")
        if len(password) < 8:
            raise ValueError("Password too short (min 8 characters)")
        if not re.search(r"[A-Za-z]", password) or not re.search(r"\d", password):
            raise ValueError("Password must contain letters and numbers")

    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """Verify password using bcrypt only."""
        return verify_password_bcrypt(password=plain_password, hashed_password=hashed_password)

    @staticmethod
    def get_password_hash(password: str) -> str:
        """Hash password using bcrypt."""
        return hash_password_bcrypt(password=password)

    @staticmethod
    def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
        """Create a JWT token."""
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.now(timezone.utc) + expires_delta
        else:
            expire = datetime.now(timezone.utc) + timedelta(minutes=settings.access_token_expire_minutes)

        # Standard claims
        to_encode.update(
            {
                "exp": expire,
                "iat": datetime.now(timezone.utc),
            }
        )
        # Optional issuer/audience
        if settings.jwt_issuer:
            to_encode["iss"] = settings.jwt_issuer
        if settings.jwt_audience:
            to_encode["aud"] = settings.jwt_audience
        encoded_jwt = jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)

        return encoded_jwt

    @staticmethod
    def verify_token(token: str) -> TokenData | None:
        """Verify a JWT token."""
        try:
            decode_kwargs = {"algorithms": [settings.algorithm]}
            # Verify audience if configured
            if settings.jwt_audience:
                decode_kwargs["audience"] = settings.jwt_audience  # pyright: ignore[reportArgumentType]
            payload = jwt.decode(token, settings.secret_key, **decode_kwargs)  # pyright: ignore[reportArgumentType]
            username = payload.get("sub")
            user_id = payload.get("user_id")
            # Verify issuer if configured
            if settings.jwt_issuer and payload.get("iss") != settings.jwt_issuer:
                return None
            if username is None or user_id is None:
                return None
            return TokenData(username=str(username), user_id=int(user_id))
        except JWTError:
            return None

    @staticmethod
    async def authenticate_user(session: AsyncSession, username: str, password: str) -> User | None:
        """Authenticate a user."""
        result = await session.execute(select(User).where(User.username == username))
        user = result.scalar_one_or_none()

        if not user:
            return None
        if not UserService.verify_password(plain_password=password, hashed_password=user.hashed_password):
            return None
        if not user.is_active:
            return None

        return user

    @staticmethod
    async def get_user_by_username(session: AsyncSession, username: str) -> User | None:
        """Get user by username."""
        result = await session.execute(select(User).where(User.username == username))

        return result.scalar_one_or_none()

    @classmethod
    async def get_user_by_id(cls, session: AsyncSession, user_id: int) -> User | None:
        """Get user by ID."""
        return await cls.get_by_id(session=session, pk=user_id)

    @classmethod
    async def create_user(cls, session: AsyncSession, user_data: UserCreate) -> User:
        """Create a new user."""
        # Ensure username is unique
        existing_user = await UserService.get_user_by_username(session=session, username=user_data.username)
        if existing_user:
            raise ValueError("A user with this username already exists")

        # Validate password policy
        cls._validate_password_policy(password=user_data.password)

        hashed_password = UserService.get_password_hash(password=user_data.password)
        user = User(
            username=user_data.username,
            hashed_password=hashed_password,
            is_admin=user_data.is_admin,
        )

        session.add(user)
        await cls.add_flush_refresh(session=session, obj=user)

        return user

    @classmethod
    async def update_user(cls, session: AsyncSession, user_id: int, user_data: UserUpdate) -> User | None:
        """Update a user."""
        user = await cls.get_user_by_id(session=session, user_id=user_id)
        if not user:
            return None

        # Update fields
        if user_data.username is not None:
            # Ensure the new username is not taken
            existing_user = await UserService.get_user_by_username(session=session, username=user_data.username)
            if existing_user and existing_user.id != user_id:
                raise ValueError("A user with this username already exists")
            user.username = user_data.username

        if user_data.password is not None:
            cls._validate_password_policy(password=user_data.password)
            user.hashed_password = UserService.get_password_hash(password=user_data.password)

        if user_data.is_active is not None:
            user.is_active = user_data.is_active

        if user_data.is_admin is not None:
            user.is_admin = user_data.is_admin

        await cls.add_flush_refresh(session=session, obj=user)

        return user

    @staticmethod
    async def update_last_login(session: AsyncSession, user_id: int) -> None:
        """Update the last login time."""
        user = await UserService.get_user_by_id(session=session, user_id=user_id)
        if user:
            user.last_login = datetime.now(timezone.utc)
            await session.flush()

    @classmethod
    async def get_all_users(cls, session: AsyncSession) -> list[User]:
        """Get all users."""
        result = await session.execute(select(User).order_by(User.created_at.desc()))

        return list(result.scalars().all())

    @classmethod
    async def delete_user(cls, session: AsyncSession, user_id: int) -> bool:
        """Delete a user."""
        user = await cls.get_user_by_id(session=session, user_id=user_id)
        if not user:
            return False

        await session.delete(user)
        await session.flush()

        return True
