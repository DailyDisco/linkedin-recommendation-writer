import logging
from typing import Any, Dict, Optional

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.models.user import User

logger = logging.getLogger(__name__)


class UserService:
    """Service for managing user-related operations."""

    async def get_user_by_id(self, db: AsyncSession, user_id: int) -> Optional[User]:
        """Retrieve a user by their ID."""
        query = select(User).where(User.id == user_id)
        result = await db.execute(query)
        user = result.scalar_one_or_none()
        return user

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

    async def update_user_profile(self, db: AsyncSession, user_id: int, user_data: Dict[str, Any]) -> Optional[User]:
        """Update a user's profile by ID."""
        logger.info(f"🔧 UserService.update_user_profile called for user_id: {user_id}")
        logger.info(f"🔧 Update data: {user_data}")

        try:
            stmt = update(User).where(User.id == user_id).values(**user_data).returning(User)
            logger.info(f"🔧 Executing SQL statement: {stmt}")

            result = await db.execute(stmt)
            logger.info("🔧 SQL execution completed")

            updated_user = result.scalar_one_or_none()
            logger.info(f"🔧 Updated user result: {updated_user}")

            if not updated_user:
                logger.error(f"❌ No user returned from update for user_id: {user_id}")
                raise NotFoundError("User", str(user_id))

            logger.info(f"✅ User profile updated successfully for user_id: {user_id}")
            return updated_user

        except Exception as e:
            logger.error(f"❌ UserService.update_user_profile failed: {str(e)}")
            logger.error(f"❌ Error type: {type(e).__name__}")
            import traceback

            logger.error(f"❌ Full traceback: {traceback.format_exc()}")
            raise
