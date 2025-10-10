#!/usr/bin/env python3
"""Quick script to check production database schema without applying migrations.

Usage:
    export DATABASE_URL="postgresql+asyncpg://..."
    python check_db_schema.py
"""

import os
import sys
from pathlib import Path

# Add backend to path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from sqlalchemy import create_engine, inspect, text
from alembic.config import Config
from alembic.script import ScriptDirectory
from alembic.runtime.migration import MigrationContext


def get_sync_url(async_url: str) -> str:
    """Convert async URL to sync."""
    return async_url.replace("postgresql+asyncpg://", "postgresql://")


def main():
    database_url = os.getenv("DATABASE_URL")
    
    if not database_url:
        print("❌ DATABASE_URL not set")
        print("Usage: export DATABASE_URL='postgresql+asyncpg://...' && python check_db_schema.py")
        sys.exit(1)
    
    sync_url = get_sync_url(database_url)
    
    print("=" * 80)
    print("DATABASE SCHEMA CHECK")
    print("=" * 80)
    print()
    
    try:
        engine = create_engine(sync_url)
        
        with engine.connect() as conn:
            # Get current migration version
            context = MigrationContext.configure(conn)
            current_rev = context.get_current_revision()
            
            print(f"📊 Migration Version: {current_rev or 'None (empty database)'}")
            print()
            
            # Get tables
            inspector = inspect(conn)
            tables = inspector.get_table_names()
            
            print(f"📋 Tables ({len(tables)}):")
            for table in sorted(tables):
                print(f"   - {table}")
            print()
            
            # Check users table specifically
            if 'users' in tables:
                columns = inspector.get_columns('users')
                column_names = [col['name'] for col in columns]
                
                print(f"👤 Users Table Columns ({len(column_names)}):")
                for col_name in sorted(column_names):
                    print(f"   - {col_name}")
                print()
                
                # Check for required columns
                required = ['bio', 'email_notifications_enabled', 'default_tone', 'language']
                missing = [c for c in required if c not in column_names]
                
                if missing:
                    print(f"❌ Missing Required Columns ({len(missing)}):")
                    for col in missing:
                        print(f"   - {col}")
                    print()
                    print("⚠️  Migration 20251010122401 needs to be applied")
                else:
                    print("✅ All required columns present!")
            else:
                print("❌ Users table does not exist - initial migration needed")
            
            print()
            
            # Check what migrations are available
            alembic_cfg = Config(str(backend_dir / "alembic.ini"))
            script = ScriptDirectory.from_config(alembic_cfg)
            head = script.get_current_head()
            
            print(f"🎯 Target Migration Version: {head}")
            
            if current_rev != head:
                print(f"⚠️  Database needs to be upgraded from {current_rev or 'None'} to {head}")
                print()
                print("To apply pending migrations:")
                print("  python scripts/apply_production_migration.py")
            else:
                print("✅ Database is up to date!")
        
        engine.dispose()
        print()
        print("=" * 80)
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

