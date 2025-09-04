"""Application lifecycle management."""

import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI

from app.core.config import settings
from app.core.database import init_database, run_migrations
from app.core.redis_client import init_redis

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan manager."""
    # Startup
    logger.info("🚀 Starting LinkedIn Recommendation Writer Backend...")

    # Log environment info
    logger.info(f"📊 Environment: {settings.ENVIRONMENT}")
    logger.info(f"🔌 API Host: {settings.API_HOST}")
    logger.info(f"🔌 API Port: {settings.API_PORT}")
    logger.info(f"🐛 Debug Mode: {settings.API_DEBUG}")

    # Validate required environment variables
    await _validate_environment()

    # Initialize services
    await _initialize_database()
    await _initialize_redis()

    logger.info("🎉 Application startup complete - ready to serve requests!")

    yield

    # Shutdown
    logger.info("🔄 Shutting down application...")


async def _validate_environment() -> None:
    """Validate required environment variables."""
    # Check database URL
    if settings.DATABASE_URL:
        logger.info("✅ DATABASE_URL is configured")
    else:
        logger.error("❌ DATABASE_URL is not configured!")
        raise ValueError("DATABASE_URL environment variable is required")

    # Check Redis URL
    if settings.REDIS_URL:
        logger.info("✅ REDIS_URL is configured")
    else:
        logger.warning("⚠️ REDIS_URL is not configured - caching will be disabled")

    # Check API keys
    if settings.GITHUB_TOKEN:
        logger.info("✅ GITHUB_TOKEN is configured")
    else:
        logger.error("❌ GITHUB_TOKEN is not configured!")
        raise ValueError("GITHUB_TOKEN environment variable is required")

    if settings.GEMINI_API_KEY:
        logger.info("✅ GEMINI_API_KEY is configured")
    else:
        logger.error("❌ GEMINI_API_KEY is not configured!")
        raise ValueError("GEMINI_API_KEY environment variable is required")


async def _initialize_database() -> None:
    """Initialize database connection and run migrations if needed."""
    try:
        if settings.RUN_MIGRATIONS:
            logger.info("🗄️ Running database migrations...")
            await run_migrations()
            logger.info("✅ Database migrations completed successfully")
        elif settings.INIT_DB:
            logger.info("🗄️ Initializing database...")
            await init_database()
            logger.info("✅ Database initialized successfully")
        else:
            logger.info("⏭️ Skipping database initialization")
    except Exception as e:
        logger.error(f"❌ Database initialization failed: {e}")
        raise


async def _initialize_redis() -> None:
    """Initialize Redis connection."""
    try:
        logger.info("🔄 Initializing Redis...")
        await init_redis()
        logger.info("✅ Redis initialized successfully")
    except Exception as e:
        logger.error(f"❌ Redis initialization failed: {e}")
        # Redis is not critical, don't raise error
