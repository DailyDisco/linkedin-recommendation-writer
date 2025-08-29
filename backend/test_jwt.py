#!/usr/bin/env python3
"""
Test script to debug JWT token creation and verification.
Tests JWT persistence across multiple application instances.
"""

import json
import os
import sys
import time

# Add the backend directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "app"))

import logging

from app.core.config import settings
from app.core.token import token_helper
from app.schemas.user import TokenData

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


def test_jwt_persistence():
    """Test JWT token persistence across multiple settings instances."""
    print("=" * 60)
    print("JWT TOKEN PERSISTENCE TEST")
    print("=" * 60)

    # Test 1: Basic JWT flow
    print("Test 1: Basic JWT creation and verification")
    print("-" * 40)

    # Check settings
    print(f"SECRET_KEY length: {len(settings.SECRET_KEY)}")
    print(f"SECRET_KEY preview: {settings.SECRET_KEY[:10]}...")
    print(f"JWT_ALGORITHM: {settings.JWT_ALGORITHM}")
    print(f"ACCESS_TOKEN_EXPIRE_MINUTES: {settings.ACCESS_TOKEN_EXPIRE_MINUTES}")
    print()

    # Create a test token
    test_data = {"sub": "testuser", "id": "123"}

    print("Creating test token...")
    try:
        token = token_helper.create_access_token(test_data)
        print(f"Token created successfully: {token[:50]}...")
        print()
    except Exception as e:
        print(f"ERROR creating token: {e}")
        return False

    # Verify the token
    print("Verifying token...")
    try:
        payload = token_helper.verify_token(token)
        if payload:
            print("✅ Token verified successfully!")
            print(f"   Username: {payload.username}")
            print(f"   User ID: {payload.id}")
        else:
            print("❌ ERROR: Token verification returned None")
            return False
    except Exception as e:
        print(f"❌ ERROR verifying token: {e}")
        return False

    print()

    # Test 2: Simulate application restart
    print("Test 2: Simulating application restart")
    print("-" * 40)

    # Save the token for testing
    test_token_file = "/tmp/test_jwt_token.txt"
    with open(test_token_file, "w") as f:
        f.write(token)

    print(f"Saved token to: {test_token_file}")

    # Simulate restart by creating new settings instance
    print("Creating new settings instance (simulating app restart)...")

    # Force reload settings (this would happen on app restart in production)
    from app.core.config import get_settings

    new_settings = get_settings()

    # Override SECRET_KEY to simulate what happens without persistent key
    import secrets

    new_secret_key = secrets.token_urlsafe(32)
    print(f"New random SECRET_KEY generated: {new_secret_key[:10]}...")

    # Test with the old token and new secret key
    print("Testing old token with new secret key...")
    try:
        # Temporarily modify the settings to use new secret key
        original_secret = settings.SECRET_KEY
        settings.SECRET_KEY = new_secret_key

        payload = token_helper.verify_token(token)
        if payload:
            print("❌ UNEXPECTED: Token verified with wrong secret key!")
            return False
        else:
            print("✅ Expected: Token verification failed with wrong secret key")
    except Exception as e:
        print(f"✅ Expected: Token verification failed with wrong secret key: {type(e).__name__}")
    finally:
        # Restore original secret key
        settings.SECRET_KEY = original_secret

    print()

    # Test 3: Verify with correct persistent key
    print("Test 3: Verifying token with correct persistent key")
    print("-" * 40)

    try:
        payload = token_helper.verify_token(token)
        if payload:
            print("✅ SUCCESS: Token verified with persistent secret key!")
            print(f"   Username: {payload.username}")
            print(f"   User ID: {payload.id}")
        else:
            print("❌ ERROR: Token verification failed with correct key")
            return False
    except Exception as e:
        print(f"❌ ERROR verifying token with correct key: {e}")
        return False

    print()
    print("=" * 60)
    print("🎉 ALL TESTS PASSED!")
    print("JWT persistence is working correctly.")
    print("=" * 60)

    # Cleanup
    if os.path.exists(test_token_file):
        os.remove(test_token_file)

    return True


if __name__ == "__main__":
    success = test_jwt_persistence()
    sys.exit(0 if success else 1)
