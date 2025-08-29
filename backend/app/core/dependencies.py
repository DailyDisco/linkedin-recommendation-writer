"""Dependency injection container and providers."""

import logging
import re
from typing import Any, AsyncGenerator, TypeVar, cast

from fastapi import HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import AsyncSessionLocal
from app.core.exceptions import DatabaseError
from app.core.redis_client import get_redis
from app.services.ai_service import AIService
from app.services.github_commit_service import GitHubCommitService
from app.services.github_repository_service import GitHubRepositoryService
from app.services.github_user_service import GitHubUserService
from app.services.recommendation_service import RecommendationService
from app.services.user_service import UserService

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
    def get_repository_service(cls) -> GitHubRepositoryService:
        """Get or create repository service instance."""
        # GitHubRepositoryService requires GitHubCommitService
        return cls._get_service("github_repository", GitHubRepositoryService, GitHubCommitService())

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


def get_repository_service() -> GitHubRepositoryService:
    """Dependency injector for GitHubRepositoryService."""
    return ServiceContainer.get_repository_service()


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
