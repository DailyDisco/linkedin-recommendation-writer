import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.auth import get_current_active_user
from app.core.dependencies import get_database_session
from app.models.user import User
from app.schemas.user import UserResponse
from app.services.user_service import UserService

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/me", response_model=UserResponse)
async def read_users_me(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_database_session),
    user_service: UserService = Depends(UserService),
) -> UserResponse:
    """Get current authenticated user details, including recommendation limits."""
    logger.info(f"Fetching details for current user: {current_user.username}")

    # Fetch the user again to ensure latest data including recommendation counts
    user_details = await user_service.get_user_by_id(db, current_user.id)

    if not user_details:
        logger.error(f"User {current_user.id} not found in DB after authentication.")
        raise HTTPException(status_code=404, detail="User not found")

    return UserResponse.from_orm(user_details)
