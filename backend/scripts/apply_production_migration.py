#!/usr/bin/env python3
"""Script to apply pending migrations to production database.

This script connects to the production database and applies any pending
Alembic migrations. It's useful when auto-migrations fail during deployment.

Usage:
    # Set the production DATABASE_URL environment variable
    export DATABASE_URL="postgresql+asyncpg://user:pass@host:port/dbname"
    
    # Run the script
    python apply_production_migration.py
    
    # Or provide DATABASE_URL inline
    DATABASE_URL="postgresql+asyncpg://..." python apply_production_migration.py
"""

import asyncio
import logging
import os
import sys
from pathlib import Path

# Add backend directory to Python path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from alembic import command
from alembic.config import Config
from alembic.script import ScriptDirectory
from alembic.runtime.migration import MigrationContext
from sqlalchemy import create_engine, inspect, text

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def get_sync_database_url(async_url: str) -> str:
    """Convert async database URL to sync version for Alembic."""
    return async_url.replace("postgresql+asyncpg://", "postgresql://")


def check_database_schema():
    """Check current database schema and migration status."""
    database_url = os.getenv("DATABASE_URL")
    
    if not database_url:
        logger.error("❌ DATABASE_URL environment variable is not set")
        logger.info("Please set it with:")
        logger.info("  export DATABASE_URL='postgresql+asyncpg://user:pass@host:port/dbname'")
        sys.exit(1)
    
    # Convert to sync URL for direct connection
    sync_url = get_sync_database_url(database_url)
    
    logger.info("=" * 70)
    logger.info("🔍 Checking Production Database Schema")
    logger.info("=" * 70)
    
    try:
        # Create sync engine for inspection
        engine = create_engine(sync_url)
        
        with engine.connect() as conn:
            # Check current migration version
            context = MigrationContext.configure(conn)
            current_revision = context.get_current_revision()
            
            logger.info(f"📊 Current migration version: {current_revision or 'None (empty database)'}")
            
            # Check if users table exists
            inspector = inspect(conn)
            tables = inspector.get_table_names()
            
            if 'users' in tables:
                logger.info("✅ Users table exists")
                
                # Get columns from users table
                columns = inspector.get_columns('users')
                column_names = [col['name'] for col in columns]
                
                logger.info(f"📋 Found {len(column_names)} columns in users table:")
                for col_name in sorted(column_names):
                    logger.info(f"   - {col_name}")
                
                # Check for missing columns
                required_columns = ['bio', 'email_notifications_enabled', 'default_tone', 'language']
                missing_columns = [col for col in required_columns if col not in column_names]
                
                if missing_columns:
                    logger.warning(f"⚠️  Missing columns: {', '.join(missing_columns)}")
                    logger.info("These columns will be added by migration 20251010122401")
                else:
                    logger.info("✅ All required columns are present")
            else:
                logger.warning("⚠️  Users table does not exist - initial migration needs to run")
        
        engine.dispose()
        
    except Exception as e:
        logger.error(f"❌ Error checking database: {e}")
        sys.exit(1)


def apply_migrations():
    """Apply pending migrations to the database."""
    database_url = os.getenv("DATABASE_URL")
    
    if not database_url:
        logger.error("❌ DATABASE_URL environment variable is not set")
        sys.exit(1)
    
    # Convert to sync URL for Alembic
    sync_url = get_sync_database_url(database_url)
    
    logger.info("=" * 70)
    logger.info("🚀 Applying Pending Migrations")
    logger.info("=" * 70)
    
    try:
        # Get Alembic config
        alembic_ini_path = backend_dir / "alembic.ini"
        
        if not alembic_ini_path.exists():
            logger.error(f"❌ Alembic config not found at {alembic_ini_path}")
            sys.exit(1)
        
        logger.info(f"📂 Using Alembic config: {alembic_ini_path}")
        
        # Load Alembic configuration
        alembic_cfg = Config(str(alembic_ini_path))
        alembic_cfg.set_main_option("sqlalchemy.url", sync_url)
        
        # Get script directory
        script = ScriptDirectory.from_config(alembic_cfg)
        
        # Get current and head revisions
        engine = create_engine(sync_url)
        with engine.connect() as conn:
            context = MigrationContext.configure(conn)
            current = context.get_current_revision()
            head = script.get_current_head()
            
            logger.info(f"📊 Current revision: {current or 'None'}")
            logger.info(f"📊 Target revision: {head}")
            
            if current == head:
                logger.info("✅ Database is already up to date - no migrations to apply")
                engine.dispose()
                return
        
        engine.dispose()
        
        # Apply migrations
        logger.info("🔄 Running migrations...")
        command.upgrade(alembic_cfg, "head")
        
        logger.info("=" * 70)
        logger.info("✅ Migrations Applied Successfully!")
        logger.info("=" * 70)
        
        # Verify migration was applied
        verify_migration()
        
    except Exception as e:
        logger.error(f"❌ Error applying migrations: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


def verify_migration():
    """Verify that the migration was applied successfully."""
    database_url = os.getenv("DATABASE_URL")
    sync_url = get_sync_database_url(database_url)
    
    logger.info("=" * 70)
    logger.info("🔍 Verifying Migration Results")
    logger.info("=" * 70)
    
    try:
        engine = create_engine(sync_url)
        
        with engine.connect() as conn:
            # Check migration version
            context = MigrationContext.configure(conn)
            current_revision = context.get_current_revision()
            
            logger.info(f"📊 New migration version: {current_revision}")
            
            # Check users table columns
            inspector = inspect(conn)
            columns = inspector.get_columns('users')
            column_names = [col['name'] for col in columns]
            
            # Verify required columns exist
            required_columns = ['bio', 'email_notifications_enabled', 'default_tone', 'language']
            missing_columns = [col for col in required_columns if col not in column_names]
            
            if missing_columns:
                logger.error(f"❌ Still missing columns: {', '.join(missing_columns)}")
                logger.error("Migration may not have completed successfully")
            else:
                logger.info("✅ All required columns are now present!")
                logger.info(f"📋 Total columns in users table: {len(column_names)}")
        
        engine.dispose()
        
    except Exception as e:
        logger.error(f"❌ Error verifying migration: {e}")


def main():
    """Main function."""
    logger.info("=" * 70)
    logger.info("Production Database Migration Tool")
    logger.info("=" * 70)
    logger.info("")
    
    # Step 1: Check current schema
    logger.info("Step 1: Checking current database schema...")
    check_database_schema()
    logger.info("")
    
    # Step 2: Ask for confirmation
    logger.info("Step 2: Ready to apply migrations")
    try:
        response = input("Do you want to proceed with applying migrations? (yes/no): ")
        if response.lower() not in ['yes', 'y']:
            logger.info("❌ Migration cancelled by user")
            sys.exit(0)
    except KeyboardInterrupt:
        logger.info("\n❌ Migration cancelled by user")
        sys.exit(0)
    
    logger.info("")
    
    # Step 3: Apply migrations
    logger.info("Step 3: Applying migrations...")
    apply_migrations()
    logger.info("")
    
    logger.info("=" * 70)
    logger.info("✅ All Done!")
    logger.info("=" * 70)
    logger.info("")
    logger.info("Next steps:")
    logger.info("1. Test user registration in production")
    logger.info("2. Test user login in production")
    logger.info("3. Check why auto-migrations didn't run (review Railway logs)")
    logger.info("4. Ensure RUN_MIGRATIONS=true is set in Railway environment")


if __name__ == "__main__":
    main()

