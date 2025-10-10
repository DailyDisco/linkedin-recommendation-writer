#!/usr/bin/env python3
"""Quick check if columns exist in users table."""
import os
import sys

try:
    from sqlalchemy import create_engine, inspect
    
    db_url = os.getenv('DATABASE_URL', '')
    if not db_url:
        print("❌ DATABASE_URL not set")
        sys.exit(1)
    
    # Convert async to sync
    sync_url = db_url.replace('postgresql+asyncpg://', 'postgresql://')
    
    engine = create_engine(sync_url)
    
    with engine.connect() as conn:
        inspector = inspect(conn)
        columns = inspector.get_columns('users')
        column_names = [col['name'] for col in columns]
        
        print('Users table columns:')
        for col in sorted(column_names):
            print(f'  - {col}')
        
        required = ['bio', 'email_notifications_enabled', 'default_tone', 'language']
        missing = [c for c in required if c not in column_names]
        
        if missing:
            print(f'\n❌ MISSING: {", ".join(missing)}')
            sys.exit(1)
        else:
            print('\n✅ All required columns present!')
            sys.exit(0)
            
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

