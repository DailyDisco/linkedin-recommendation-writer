import logging
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User

logger = logging.getLogger(__name__)


class UserService:
    """Service for managing user-related operations."""

    async def get_user_by_id(self, db: AsyncSession, user_id: int) -> Optional[User]:
        """Retrieve a user by their ID."""
        query = select(User).where(User.id == user_id)
        result = await db.execute(query)
        return result.scalar_one_or_none()

    async def get_user_by_username(self, db: AsyncSession, username: str) -> Optional[User]:
        """Retrieve a user by their username."""
        query = select(User).where(User.username == username)
        result = await db.execute(query)
        return result.scalar_one_or_none()

    async def get_user_by_email(self, db: AsyncSession, email: str) -> Optional[User]:
        """Retrieve a user by their email."""
        query = select(User).where(User.email == email)
        result = await db.execute(query)
        return result.scalar_one_or_none()
