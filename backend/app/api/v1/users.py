import logging

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.auth import get_current_active_user
from app.core.dependencies import get_database_session
from app.models.user import User
from app.schemas.user import UserResponse, UserUpdate
from app.services.infrastructure.user_service import UserService

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/me", response_model=UserResponse)
async def read_users_me(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_database_session),
    user_service: UserService = Depends(UserService),
) -> UserResponse:
    """Get current user's profile."""
    return UserResponse.model_validate(current_user)


@router.put("/me", response_model=UserResponse)  # New endpoint for updating user profile
async def update_users_me(
    user_update: UserUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_database_session),
    user_service: UserService = Depends(UserService),
) -> UserResponse:
    """Update current user's profile."""
    logger.info(f"🔧 PROFILE UPDATE REQUEST: User {current_user.username} (ID: {current_user.id})")
    logger.info(f"🔧 Update data: {user_update.model_dump(exclude_unset=True)}")

    try:
        updated_user = await user_service.update_user_profile(db, current_user.id, user_update.model_dump(exclude_unset=True))
        logger.info(f"✅ PROFILE UPDATE SUCCESS: User {updated_user.username} updated")
        return UserResponse.model_validate(updated_user)
    except Exception as e:
        logger.error(f"❌ PROFILE UPDATE FAILED: {str(e)}")
        logger.error(f"❌ Error type: {type(e).__name__}")
        import traceback

        logger.error(f"❌ Full traceback: {traceback.format_exc()}")
        raise
