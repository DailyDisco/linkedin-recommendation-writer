"""Dependency injection container and providers."""

import logging
import re
from datetime import date
from typing import Any, AsyncGenerator, TypeVar, Union, cast

from fastapi import Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import AsyncSessionLocal
from app.core.exceptions import DatabaseError
from app.core.redis_client import get_redis
from app.models.user import User
from app.services.ai.ai_service_new import AIService
from app.services.analysis.profile_analysis_service import ProfileAnalysisService
from app.services.github.github_commit_service import GitHubCommitService
from app.services.github.github_repository_service import GitHubRepositoryService
from app.services.github.github_user_service import GitHubUserService
from app.services.infrastructure.user_service import UserService
from app.services.recommendation.recommendation_engine_service import RecommendationEngineService
from app.services.recommendation.recommendation_service import RecommendationService

T = TypeVar("T")

logger = logging.getLogger(__name__)


# Database Dependencies
async def get_database_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency that provides a database session.
    Handles connection lifecycle and error management.
    """
    session = AsyncSessionLocal()
    try:
        yield session
        await session.commit()
    except Exception as e:
        await session.rollback()

        # Don't wrap HTTPException (401 auth errors) in DatabaseError
        from fastapi import HTTPException

        if isinstance(e, HTTPException):
            logger.warning(f"HTTP exception in database session: {e.status_code}: {e.detail}")
            raise e

        logger.error(f"Database session error: {type(e).__name__}: {e}")
        logger.error(f"Error details: {repr(e)}")
        # Log more context for debugging
        import traceback

        logger.error(f"Traceback: {traceback.format_exc()}")
        raise DatabaseError("transaction", str(e))
    finally:
        await session.close()


# Redis Dependencies
async def get_redis_client() -> Any:
    """Dependency that provides Redis client."""
    try:
        return await get_redis()
    except Exception as e:
        logger.warning(f"Redis unavailable: {e}")
        return None  # Redis is non-critical


# Request Context Dependencies
def get_request_id(request: Request) -> str:
    """Get request ID from request state."""
    return getattr(request.state, "request_id", "unknown")


# Service Dependencies
class ServiceContainer:
    """Service container for dependency injection with proper lifecycle management."""

    _instances: dict = {}

    @classmethod
    def _get_service(cls, service_name: str, service_class: type[T], *args, **kwargs) -> T:
        """Generic service getter with singleton pattern."""
        if service_name not in cls._instances:
            logger.info(f"Initializing {service_name} service")
            cls._instances[service_name] = service_class(*args, **kwargs)
        return cast(T, cls._instances[service_name])

    @classmethod
    def get_github_service(cls) -> GitHubUserService:
        """Get or create GitHub service instance."""
        # GitHubUserService requires GitHubCommitService
        return cls._get_service("github_user", GitHubUserService, GitHubCommitService())

    @classmethod
    def get_ai_service(cls) -> AIService:
        """Get or create AI service instance."""
        return cls._get_service("ai", AIService)

    @classmethod
    def get_recommendation_service(cls) -> RecommendationService:
        """Get or create recommendation service instance."""
        return cls._get_service("recommendation", RecommendationService)

    @classmethod
    def get_recommendation_engine_service(cls) -> RecommendationEngineService:
        """Get or create recommendation engine service instance."""
        ai_service = cls.get_ai_service()
        return cls._get_service("recommendation_engine", RecommendationEngineService, ai_service)

    @classmethod
    def get_repository_service(cls) -> GitHubRepositoryService:
        """Get or create repository service instance."""
        # GitHubRepositoryService requires GitHubCommitService
        return cls._get_service("github_repository", GitHubRepositoryService, GitHubCommitService())

    @classmethod
    def get_profile_analysis_service(cls) -> ProfileAnalysisService:
        """Get or create profile analysis service instance."""
        return cls._get_service("profile_analysis", ProfileAnalysisService)

    @classmethod
    def get_user_service(cls) -> UserService:
        """Get or create user service instance."""
        return cls._get_service("user", UserService)

    @classmethod
    def clear_instances(cls) -> None:
        """Clear all service instances (useful for testing)."""
        cls._instances.clear()


# Service provider functions
def get_github_service() -> GitHubUserService:
    """Dependency injector for GitHubUserService."""
    return ServiceContainer.get_github_service()


def get_ai_service() -> AIService:
    """Dependency provider for AI service."""
    return ServiceContainer.get_ai_service()


def get_recommendation_service() -> RecommendationService:
    """Dependency provider for recommendation service."""
    return ServiceContainer.get_recommendation_service()


def get_recommendation_engine_service() -> RecommendationEngineService:
    """Dependency provider for recommendation engine service."""
    return ServiceContainer.get_recommendation_engine_service()


def get_repository_service() -> GitHubRepositoryService:
    """Dependency injector for GitHubRepositoryService."""
    return ServiceContainer.get_repository_service()


def get_profile_analysis_service() -> ProfileAnalysisService:
    """Dependency provider for profile analysis service."""
    return ServiceContainer.get_profile_analysis_service()


def get_user_service() -> UserService:
    """Dependency provider for user service."""
    return ServiceContainer.get_user_service()


# Validation Dependencies
async def validate_github_username(username: str) -> str:
    """Validate GitHub username format."""
    if not username or len(username) < 1 or len(username) > 39:
        raise HTTPException(
            status_code=400,
            detail="GitHub username must be between 1 and 39 characters",
        )

    # Basic validation for allowed characters (GitHub username rules)
    # Must start and end with alphanumeric, can contain hyphens in middle
    if not re.match(r"^[a-zA-Z0-9][a-zA-Z0-9-]*[a-zA-Z0-9]$|^[a-zA-Z0-9]$", username):
        raise HTTPException(status_code=400, detail="Invalid GitHub username format")

    return username


# Pagination Dependencies
class PaginationParams:
    """Pagination parameters."""

    def __init__(self, page: int = 1, page_size: int = 10):
        if page < 1:
            raise HTTPException(status_code=400, detail="Page must be >= 1")
        if page_size < 1 or page_size > 100:
            raise HTTPException(status_code=400, detail="Page size must be between 1 and 100")

        self.page = page
        self.page_size = page_size
        self.offset = (page - 1) * page_size
        self.limit = page_size


def get_pagination_params(page: int = 1, page_size: int = 10) -> PaginationParams:
    """Dependency provider for pagination parameters."""
    return PaginationParams(page, page_size)


# Anonymous User Support
class AnonymousUser:
    """Represents an anonymous user with IP-based tracking."""

    def __init__(self, ip_address: str):
        self.ip_address = ip_address
        self.id = f"anonymous_{ip_address}"
        self.username = f"anonymous_{ip_address}"
        self.role = "anonymous"
        self.daily_limit = 3  # Anonymous users get 3 generations per day
        self.recommendation_count = 0
        self.last_recommendation_date = None
        self.is_active = True

    def __repr__(self) -> str:
        return f"<AnonymousUser(ip={self.ip_address}, count={self.recommendation_count}/{self.daily_limit})>"


async def get_anonymous_user_data(request: Request) -> AnonymousUser:
    """Get anonymous user data from Redis based on IP address."""
    # Get client IP address
    client_ip = request.client.host if request.client else "unknown"

    # Handle localhost/development IPs
    if client_ip in ["127.0.0.1", "localhost", "::1"]:
        client_ip = "localhost"

    logger.debug(f"Anonymous user IP: {client_ip}")

    user = AnonymousUser(client_ip)

    # Try to get data from Redis
    redis = await get_redis()
    if redis:
        try:
            today = date.today().isoformat()
            redis_key = f"anonymous:{client_ip}:recommendations"

            # Get current count and date
            stored_data = await redis.hgetall(redis_key)

            if stored_data:
                stored_date = stored_data.get(b"date", b"").decode("utf-8")
                stored_count = int(stored_data.get(b"count", b"0").decode("utf-8"))

                # Reset count if it's a new day
                if stored_date != today:
                    user.recommendation_count = 0
                    user.last_recommendation_date = date.today()
                    # Update Redis with reset data
                    await redis.hset(redis_key, mapping={"count": "0", "date": today})
                else:
                    user.recommendation_count = stored_count
                    user.last_recommendation_date = date.fromisoformat(stored_date)
            else:
                # No data in Redis, initialize
                user.recommendation_count = 0
                user.last_recommendation_date = date.today()
                await redis.hset(redis_key, mapping={"count": "0", "date": today})

        except Exception as e:
            logger.warning(f"Failed to get anonymous user data from Redis: {e}")
            # Fall back to default values

    return user


async def get_current_user_optional(
    request: Request,
    db: AsyncSession = Depends(get_database_session),
) -> Union[User, AnonymousUser]:
    """Get current user if authenticated, otherwise return anonymous user."""
    from app.api.v1.auth import oauth2_scheme

    try:
        # Try to get token from request
        token = await oauth2_scheme(request)
        if token:
            # Import here to avoid circular imports
            from app.api.v1.auth import get_current_user

            user = await get_current_user(db=db, token=token)
            return user
    except Exception:
        # Token validation failed, user is not authenticated
        pass

    # Return anonymous user
    return await get_anonymous_user_data(request)


async def increment_anonymous_user_count(request: Request) -> None:
    """Increment the recommendation count for an anonymous user."""
    client_ip = request.client.host if request.client else "unknown"
    if client_ip in ["127.0.0.1", "localhost", "::1"]:
        client_ip = "localhost"

    redis = await get_redis()
    if redis:
        try:
            today = date.today().isoformat()
            redis_key = f"anonymous:{client_ip}:recommendations"

            # Increment count
            await redis.hincrby(redis_key, "count", 1)
            await redis.hset(redis_key, "date", today)

            logger.info(f"Anonymous user {client_ip} count incremented")
        except Exception as e:
            logger.warning(f"Failed to increment anonymous user count: {e}")


async def check_generation_limit(user: Union[User, AnonymousUser], db: AsyncSession) -> None:
    """Check generation limits for both authenticated and anonymous users.

    Uses subscription tier limits for authenticated users:
    - free: 3/day
    - pro: 50/day
    - team: unlimited
    - admin: unlimited
    """
    today = date.today()

    # Reset count if it's a new day for authenticated users
    if isinstance(user, User) and user.last_recommendation_date:
        if user.last_recommendation_date.date() < today:
            user.recommendation_count = 0  # type: ignore
            user.last_recommendation_date = today  # type: ignore
            await db.commit()
            await db.refresh(user)

    # Get effective daily limit based on subscription tier
    if isinstance(user, User):
        daily_limit = user.effective_daily_limit
        # -1 means unlimited (team/admin tiers)
        if daily_limit == -1:
            return
    else:
        daily_limit = user.daily_limit  # Anonymous users use default limit

    if user.recommendation_count >= daily_limit:
        user_type = "anonymous" if isinstance(user, AnonymousUser) else "authenticated"
        tier_info = ""
        if isinstance(user, User):
            tier_info = f" (tier: {user.effective_tier})"
        raise HTTPException(
            status_code=429,  # Too Many Requests
            detail=f"Daily generation limit ({daily_limit}) exceeded for {user_type} user{tier_info}. Please upgrade or try again tomorrow.",
            headers={"X-Upgrade-URL": "/pricing"},
        )


async def increment_generation_count(user: Union[User, AnonymousUser], request: Request, db: AsyncSession) -> None:
    """Increment generation count for both authenticated and anonymous users."""
    if isinstance(user, User):
        # Authenticated user - increment in database
        user.recommendation_count += 1  # type: ignore
        await db.commit()
        await db.refresh(user)

        daily_limit = user.effective_daily_limit
        limit_display = "unlimited" if daily_limit == -1 else str(daily_limit)
        logger.info(f"User {user.username} (ID: {user.id}, tier: {user.effective_tier}) has used {user.recommendation_count}/{limit_display} generations today")
    else:
        # Anonymous user - increment in Redis
        await increment_anonymous_user_count(request)

        logger.info(f"Anonymous user {user.ip_address} has used {user.recommendation_count + 1}/{user.daily_limit} generations today")
