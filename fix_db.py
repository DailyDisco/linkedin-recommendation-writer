#!/usr/bin/env python3
"""Add missing columns to users table."""
import os
from sqlalchemy import create_engine, text, inspect

db_url = os.getenv('DATABASE_URL', '').replace('postgresql+asyncpg://', 'postgresql://')
engine = create_engine(db_url)

print("Checking current columns...")
with engine.connect() as conn:
    inspector = inspect(conn)
    columns = inspector.get_columns('users')
    column_names = [col['name'] for col in columns]
    print(f"Found {len(column_names)} columns")
    
    required = ['bio', 'email_notifications_enabled', 'default_tone', 'language']
    missing = [c for c in required if c not in column_names]
    
    if not missing:
        print("✅ All columns already exist!")
    else:
        print(f"Adding missing columns: {missing}")
        
        with conn.begin():
            if 'bio' in missing:
                conn.execute(text("ALTER TABLE users ADD COLUMN bio TEXT"))
                print("  ✅ Added: bio")
            
            if 'email_notifications_enabled' in missing:
                conn.execute(text("ALTER TABLE users ADD COLUMN email_notifications_enabled BOOLEAN NOT NULL DEFAULT true"))
                print("  ✅ Added: email_notifications_enabled")
            
            if 'default_tone' in missing:
                conn.execute(text("ALTER TABLE users ADD COLUMN default_tone VARCHAR NOT NULL DEFAULT 'professional'"))
                print("  ✅ Added: default_tone")
            
            if 'language' in missing:
                conn.execute(text("ALTER TABLE users ADD COLUMN language VARCHAR NOT NULL DEFAULT 'en'"))
                print("  ✅ Added: language")
        
        print("\n✅ Database fixed!")

engine.dispose()

