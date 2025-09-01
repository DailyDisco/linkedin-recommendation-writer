"""Database migration management service."""

import asyncio
import logging
import os
from typing import Any, Dict, Optional

from sqlalchemy import text

from alembic import command
from alembic.config import Config
from alembic.script import ScriptDirectory
from app.core.database import AsyncSessionLocal

logger = logging.getLogger(__name__)


class MigrationManager:
    """Manages database migrations using Alembic."""

    def __init__(self, alembic_config_path: Optional[str] = None):
        """Initialize the migration manager."""
        if alembic_config_path is None:
            # Default path relative to this file
            current_dir = os.path.dirname(os.path.abspath(__file__))
            backend_dir = os.path.dirname(os.path.dirname(current_dir))
            alembic_config_path = os.path.join(backend_dir, "alembic.ini")

        self.alembic_config_path = alembic_config_path
        self._config = None

    @property
    def config(self) -> Config:
        """Get the Alembic configuration."""
        if self._config is None:
            if os.path.exists(self.alembic_config_path):
                self._config = Config(self.alembic_config_path)
                # Set the database URL from environment
                from app.core.config import settings

                self._config.set_main_option("sqlalchemy.url", settings.DATABASE_URL)
            else:
                raise FileNotFoundError(f"Alembic config not found at {self.alembic_config_path}")

        return self._config

    async def get_migration_status(self) -> Dict[str, Any]:
        """Get current migration status."""
        try:
            async with AsyncSessionLocal() as session:
                # Check if alembic_version table exists
                result = await session.execute(
                    text(
                        """
                    SELECT EXISTS (
                        SELECT 1 FROM information_schema.tables
                        WHERE table_name = 'alembic_version'
                    )
                """
                    )
                )
                has_version_table = result.scalar()

                if not has_version_table:
                    return {"status": "not_initialized", "current_revision": None, "head_revision": None, "needs_upgrade": True, "message": "Database migrations not initialized"}

                # Get current revision
                result = await session.execute(text("SELECT version_num FROM alembic_version"))
                current_revision = result.scalar()

                # Get head revision from script
                script = ScriptDirectory.from_config(self.config)
                head_revision = script.get_current_head()

                needs_upgrade = current_revision != head_revision

                return {
                    "status": "initialized",
                    "current_revision": current_revision,
                    "head_revision": head_revision,
                    "needs_upgrade": needs_upgrade,
                    "message": "Migration status retrieved successfully",
                }

        except Exception as e:
            logger.error(f"Failed to get migration status: {e}")
            return {"status": "error", "error": str(e), "message": "Failed to retrieve migration status"}

    async def create_initial_migration(self) -> Dict[str, Any]:
        """Create initial migration from current schema."""
        try:
            # Check if migrations directory exists and has files
            script = ScriptDirectory.from_config(self.config)
            revisions = list(script.walk_revisions())

            if revisions:
                return {"status": "already_initialized", "message": "Migrations already exist"}

            # Generate initial migration
            def generate_migration():
                command.revision(self.config, "initial migration", autogenerate=True)

            # Run in a separate thread since alembic is synchronous
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, generate_migration)

            return {"status": "success", "message": "Initial migration created successfully"}

        except Exception as e:
            logger.error(f"Failed to create initial migration: {e}")
            return {"status": "error", "error": str(e), "message": "Failed to create initial migration"}

    async def run_migrations_online(self) -> Dict[str, Any]:
        """Run pending migrations."""
        try:

            def run_migrations():
                command.upgrade(self.config, "head")

            # Run in a separate thread since alembic is synchronous
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, run_migrations)

            logger.info("Database migrations completed successfully")
            return {"status": "success", "message": "Migrations completed successfully"}

        except Exception as e:
            logger.error(f"Failed to run migrations: {e}")
            return {"status": "error", "error": str(e), "message": "Failed to run migrations"}

    async def rollback_migration(self, target_revision: str = "-1") -> Dict[str, Any]:
        """Rollback to a specific migration revision."""
        try:

            def run_rollback():
                command.downgrade(self.config, target_revision)

            # Run in a separate thread since alembic is synchronous
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, run_rollback)

            logger.info(f"Database rolled back to revision: {target_revision}")
            return {"status": "success", "message": f"Rolled back to revision {target_revision}"}

        except Exception as e:
            logger.error(f"Failed to rollback migration: {e}")
            return {"status": "error", "error": str(e), "message": "Failed to rollback migration"}

    async def create_new_migration(self, message: str, autogenerate: bool = True) -> Dict[str, Any]:
        """Create a new migration."""
        try:

            def create_migration():
                command.revision(self.config, message, autogenerate=autogenerate)

            # Run in a separate thread since alembic is synchronous
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, create_migration)

            return {"status": "success", "message": f"Migration '{message}' created successfully"}

        except Exception as e:
            logger.error(f"Failed to create migration: {e}")
            return {"status": "error", "error": str(e), "message": "Failed to create migration"}

    async def get_migration_history(self, limit: int = 10) -> Dict[str, Any]:
        """Get migration history."""
        try:
            script = ScriptDirectory.from_config(self.config)
            revisions = list(script.walk_revisions())

            history = []
            for rev in revisions[:limit]:
                history.append({"revision": rev.revision, "down_revision": rev.down_revision, "message": rev.doc, "create_date": rev.date})

            return {"status": "success", "history": history, "total": len(revisions)}

        except Exception as e:
            logger.error(f"Failed to get migration history: {e}")
            return {"status": "error", "error": str(e), "message": "Failed to get migration history"}

    async def validate_migrations(self) -> Dict[str, Any]:
        """Validate migration integrity."""
        try:
            script = ScriptDirectory.from_config(self.config)
            revisions = list(script.walk_revisions())

            # Check for circular dependencies
            visited = set()
            for rev in revisions:
                if rev.revision in visited:
                    return {"status": "error", "message": f"Circular dependency detected at revision {rev.revision}"}
                visited.add(rev.revision)

            # Check revision chain integrity
            for rev in revisions:
                if rev.down_revision and rev.down_revision not in [r.revision for r in revisions]:
                    return {"status": "error", "message": f"Broken revision chain at {rev.revision} -> {rev.down_revision}"}

            return {"status": "success", "message": "Migration integrity validated", "total_revisions": len(revisions)}

        except Exception as e:
            logger.error(f"Failed to validate migrations: {e}")
            return {"status": "error", "error": str(e), "message": "Failed to validate migrations"}


# Global migration manager instance
migration_manager = MigrationManager()
