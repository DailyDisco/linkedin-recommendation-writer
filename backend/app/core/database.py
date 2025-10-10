"""Database configuration and utilities."""

import logging
import os
from typing import Any, AsyncGenerator, Dict

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.core.config import settings

logger = logging.getLogger(__name__)

# Create async engine with configuration from settings
engine = create_async_engine(settings.DATABASE_URL, **settings.get_database_config())

# Create async session maker
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


class Base(DeclarativeBase):
    """Base class for SQLAlchemy models."""

    pass


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency to get database session.
    DEPRECATED: Use get_database_session from dependencies module instead.
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_database() -> None:
    """Initialize database tables."""
    try:
        # Import all models here to ensure they are registered

        async with engine.begin() as conn:
            # Create all tables with checkfirst=True to avoid conflicts
            await conn.run_sync(lambda sync_conn: Base.metadata.create_all(sync_conn, checkfirst=True))
            logger.info("Database tables created successfully")

    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        raise


async def run_migrations() -> None:
    """Run database migrations using Alembic.
    
    This function runs Alembic migrations automatically on application startup.
    It includes retry logic for database connection issues and detailed logging.
    """
    import time
    
    max_retries = 3
    retry_delay = 2  # seconds
    
    for attempt in range(1, max_retries + 1):
        try:
            from alembic import command
            from alembic.config import Config
            from alembic.script import ScriptDirectory
            from alembic.runtime.migration import MigrationContext

            # Get the directory containing this file
            current_dir = os.path.dirname(os.path.abspath(__file__))
            backend_dir = os.path.dirname(os.path.dirname(current_dir))
            alembic_cfg_path = os.path.join(backend_dir, "alembic.ini")

            if not os.path.exists(alembic_cfg_path):
                logger.warning("Alembic configuration not found at %s, skipping migrations", alembic_cfg_path)
                return

            logger.info("🔄 Starting database migration process (attempt %d/%d)...", attempt, max_retries)
            
            # Load Alembic configuration
            alembic_cfg = Config(alembic_cfg_path)
            script = ScriptDirectory.from_config(alembic_cfg)
            
            # Check current database version
            async with engine.begin() as conn:
                context = MigrationContext.configure(conn.sync_connection)
                current_rev = context.get_current_revision()
                head_rev = script.get_current_head()
                
                if current_rev == head_rev:
                    logger.info("✅ Database is already at the latest version: %s", current_rev or "base")
                    return
                
                logger.info("📊 Current database version: %s", current_rev or "base")
                logger.info("📊 Target database version: %s", head_rev)
            
            # Run migrations
            logger.info("⚙️ Applying database migrations...")
            command.upgrade(alembic_cfg, "head")
            
            # Verify migration success
            async with engine.begin() as conn:
                context = MigrationContext.configure(conn.sync_connection)
                new_rev = context.get_current_revision()
                
                if new_rev == head_rev:
                    logger.info("✅ Database migrations completed successfully! Current version: %s", new_rev)
                else:
                    logger.error("❌ Migration verification failed. Expected: %s, Got: %s", head_rev, new_rev)
                    raise RuntimeError(f"Migration verification failed: expected {head_rev}, got {new_rev}")
            
            return  # Success, exit retry loop

        except ImportError as e:
            logger.warning("⚠️ Alembic not available: %s. Skipping migrations.", str(e))
            return
            
        except Exception as e:
            error_msg = str(e)
            logger.error("❌ Migration attempt %d/%d failed: %s", attempt, max_retries, error_msg)
            
            if attempt < max_retries:
                logger.info("⏳ Retrying in %d seconds...", retry_delay)
                time.sleep(retry_delay)
                retry_delay *= 2  # Exponential backoff
            else:
                logger.critical("❌ All migration attempts failed. Database may be in an inconsistent state!")
                logger.critical("💡 Suggested actions:")
                logger.critical("   1. Check database connectivity")
                logger.critical("   2. Verify migration files are valid")
                logger.critical("   3. Check alembic_version table in database")
                logger.critical("   4. Run 'alembic current' to check current version")
                logger.critical("   5. Run 'alembic upgrade head' manually")
                raise RuntimeError(f"Database migration failed after {max_retries} attempts: {error_msg}") from e


async def get_database_info() -> Dict[str, Any]:
    """Get database connection information."""
    try:
        async with AsyncSessionLocal() as session:
            result = await session.execute(text("SELECT version()"))
            version = result.scalar()

            result = await session.execute(text("SELECT current_database()"))
            database = result.scalar()

            return {
                "version": version,
                "database": database,
                "pool_size": getattr(engine.pool, "size", lambda: 0)(),
                "checked_out_connections": getattr(engine.pool, "checkedout", lambda: 0)(),
                "overflow": getattr(engine.pool, "overflow", lambda: 0)(),
            }
    except Exception as e:
        logger.error(f"Failed to get database info: {e}")
        return {"error": str(e)}


async def check_database_health() -> str:
    """Check database connectivity for health checks."""
    try:
        async with AsyncSessionLocal() as session:
            result = await session.execute(text("SELECT 1"))
            result.fetchone()
            return "ok"
    except Exception as e:
        logger.error(f"Database health check failed: {type(e).__name__}: {e}")
        logger.error(f"Error details: {repr(e)}")
        # Log more context for debugging
        import traceback

        logger.error(f"Database health check traceback: {traceback.format_exc()}")
        return f"error: {type(e).__name__}"


async def test_database_connection() -> dict:
    """Test database connection with detailed diagnostics."""
    from app.core.config import settings

    result = {
        "database_url_configured": bool(settings.DATABASE_URL),
        "database_url_preview": None,
        "connection_test": "not_attempted",
        "error_type": None,
        "error_message": None,
        "recommendations": [],
    }

    if settings.DATABASE_URL:
        # Show partial URL for debugging (hide credentials)
        try:
            from urllib.parse import urlparse

            parsed = urlparse(settings.DATABASE_URL)
            result["database_url_preview"] = f"{parsed.scheme}://{parsed.hostname}:{parsed.port}/{parsed.path}"
        except Exception:
            result["database_url_preview"] = "Could not parse URL"

        # Test connection
        try:
            logger.info("Testing database connection...")
            async with AsyncSessionLocal() as session:
                # Try a simple query
                db_result = await session.execute(text("SELECT version()"))
                version = db_result.scalar()
                result["connection_test"] = "success"
                result["database_version"] = version
                logger.info(f"Database connection successful: {version}")
        except Exception as e:
            result["connection_test"] = "failed"
            result["error_type"] = type(e).__name__
            result["error_message"] = str(e)
            logger.error(f"Database connection failed: {type(e).__name__}: {e}")

            # Provide specific recommendations based on error type
            if "authentication" in str(e).lower() or "401" in str(e):
                result["recommendations"].append("Check database username and password in DATABASE_URL")
                result["recommendations"].append("Verify database user has proper permissions")
            elif "connection" in str(e).lower():
                result["recommendations"].append("Check database server is running and accessible")
                result["recommendations"].append("Verify database host and port in DATABASE_URL")
            elif "timeout" in str(e).lower():
                result["recommendations"].append("Check network connectivity to database server")
                result["recommendations"].append("Verify firewall settings allow database connections")
            else:
                result["recommendations"].append("Check DATABASE_URL format and credentials")
                result["recommendations"].append("Verify database exists and is accessible")

    else:
        result["recommendations"].append("Set DATABASE_URL environment variable")

    return result
