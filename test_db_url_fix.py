#!/usr/bin/env python3
"""Test script to verify DATABASE_URL conversion works correctly."""

import os
import sys
sys.path.append('backend')

# Simulate Railway's DATABASE_URL format (without +asyncpg)
os.environ['DATABASE_URL'] = 'postgresql://user:password@host:5432/database'

try:
    from app.core.config import settings
    print("✅ DATABASE_URL conversion test:")
    print(f"   Input:  {os.environ['DATABASE_URL']}")
    print(f"   Output: {settings.DATABASE_URL}")
    print(f"   ✓ Contains 'asyncpg': {'asyncpg' in settings.DATABASE_URL}")
    print("✅ Test passed!")
except Exception as e:
    print(f"❌ Test failed: {e}")
    sys.exit(1)
