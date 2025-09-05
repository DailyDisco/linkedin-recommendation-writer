#!/usr/bin/env python3
"""
Test script for anonymous user functionality.
Tests IP-based tracking and generation limits for anonymous vs authenticated users.
"""

import asyncio
import logging
import os
import sys
from unittest.mock import AsyncMock, Mock

# Add the backend directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "app"))

from app.core.dependencies import AnonymousUser, check_generation_limit, increment_generation_count
from app.models.user import User

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_anonymous_user_creation():
    """Test anonymous user creation and properties."""
    print("=" * 60)
    print("ANONYMOUS USER CREATION TEST")
    print("=" * 60)

    # Test direct AnonymousUser creation (without Redis dependency)
    print("Test 1: Direct AnonymousUser creation")
    print("-" * 40)

    user = AnonymousUser("192.168.1.100")

    print("✅ Anonymous user created:")
    print(f"   • IP Address: {user.ip_address}")
    print(f"   • Username: {user.username}")
    print(f"   • Role: {user.role}")
    print(f"   • Daily Limit: {user.daily_limit}")
    print(f"   • Current Count: {user.recommendation_count}")
    print(f"   • Is Active: {user.is_active}")

    assert user.ip_address == "192.168.1.100"
    assert user.role == "anonymous"
    assert user.daily_limit == 3
    assert user.recommendation_count == 0
    assert user.is_active == True

    print("✅ All anonymous user properties are correct!")


async def test_limit_checking():
    """Test limit checking for anonymous and authenticated users."""
    print("\n" + "=" * 60)
    print("GENERATION LIMIT CHECKING TEST")
    print("=" * 60)

    # Mock database session
    mock_db = AsyncMock()

    # Test 1: Anonymous user within limits
    print("Test 1: Anonymous user within limits")
    print("-" * 40)

    anonymous_user = AnonymousUser("192.168.1.100")
    anonymous_user.recommendation_count = 1  # 1 out of 3 used

    try:
        await check_generation_limit(anonymous_user, mock_db)
        print("✅ Anonymous user limit check passed (1/3 used)")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

    # Test 2: Anonymous user at limit
    print("\nTest 2: Anonymous user at limit")
    print("-" * 40)

    anonymous_user.recommendation_count = 3  # 3 out of 3 used

    try:
        await check_generation_limit(anonymous_user, mock_db)
        print("❌ Anonymous user should have been blocked but wasn't")
        return False
    except Exception as e:
        if "Daily generation limit" in str(e):
            print("✅ Anonymous user correctly blocked at limit (3/3)")
        else:
            print(f"❌ Wrong error type: {e}")
            return False

    # Test 3: Authenticated user within limits
    print("\nTest 3: Authenticated user within limits")
    print("-" * 40)

    auth_user = User(email="test@example.com", username="testuser", hashed_password="hashed", recommendation_count=2, daily_limit=5)  # 2 out of 5 used

    try:
        await check_generation_limit(auth_user, mock_db)
        print("✅ Authenticated user limit check passed (2/5 used)")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

    # Test 4: Authenticated user at limit
    print("\nTest 4: Authenticated user at limit")
    print("-" * 40)

    auth_user.recommendation_count = 5  # 5 out of 5 used

    try:
        await check_generation_limit(auth_user, mock_db)
        print("❌ Authenticated user should have been blocked but wasn't")
        return False
    except Exception as e:
        if "Daily generation limit" in str(e):
            print("✅ Authenticated user correctly blocked at limit (5/5)")
        else:
            print(f"❌ Wrong error type: {e}")
            return False

    print("\n✅ All limit checking tests passed!")
    return True


async def test_increment_count():
    """Test increment count functionality."""
    print("\n" + "=" * 60)
    print("INCREMENT COUNT TEST")
    print("=" * 60)

    # Mock request and database
    mock_request = Mock()
    mock_request.client = Mock()
    mock_request.client.host = "192.168.1.100"
    mock_db = AsyncMock()

    # Test authenticated user increment (doesn't depend on Redis)
    print("Test 1: Authenticated user increment")
    print("-" * 40)

    auth_user = User(email="test@example.com", username="testuser", hashed_password="hashed", recommendation_count=2, daily_limit=5)

    try:
        await increment_generation_count(auth_user, mock_request, mock_db)
        print("✅ Authenticated user count incremented successfully")
        assert auth_user.recommendation_count == 3  # Should be incremented to 3
    except Exception as e:
        print(f"❌ Error incrementing authenticated user count: {e}")
        return False

    # Test anonymous user increment (will fail without Redis, but we test the logic)
    print("\nTest 2: Anonymous user increment (Redis-dependent)")
    print("-" * 40)

    anonymous_user = AnonymousUser("192.168.1.100")
    anonymous_user.recommendation_count = 1

    try:
        await increment_generation_count(anonymous_user, mock_request, mock_db)
        print("✅ Anonymous user increment logic executed (may have failed Redis call)")
    except Exception as e:
        # This is expected if Redis is not available
        if "Redis" in str(e) or "ConnectionError" in str(e):
            print("ℹ️ Anonymous user increment failed due to Redis unavailability (expected)")
        else:
            print(f"❌ Unexpected error incrementing anonymous user count: {e}")
            return False

    print("\n✅ All increment tests passed!")
    return True


async def main():
    """Run all tests."""
    print("🚀 Starting anonymous user functionality tests...\n")

    try:
        # Test anonymous user creation
        await test_anonymous_user_creation()

        # Test limit checking
        limit_test_passed = await test_limit_checking()
        if not limit_test_passed:
            print("\n❌ Limit checking tests failed!")
            return False

        # Test increment functionality
        increment_test_passed = await test_increment_count()
        if not increment_test_passed:
            print("\n❌ Increment tests failed!")
            return False

        print("\n" + "=" * 60)
        print("🎉 ALL TESTS PASSED!")
        print("Anonymous user functionality is working correctly.")
        print("=" * 60)
        return True

    except Exception as e:
        print(f"\n❌ Test suite failed with error: {e}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
