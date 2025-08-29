#!/usr/bin/env python3
"""
Test script to debug JWT token creation and verification.
"""

import sys
import os

# Add the backend directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from app.core.config import settings
from app.core.token import token_helper
from app.schemas.user import TokenData
import logging

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def test_jwt_flow():
    """Test JWT token creation and verification flow."""
    print("=" * 50)
    print("JWT TOKEN DEBUG TEST")
    print("=" * 50)

    # Check settings
    print(f"SECRET_KEY length: {len(settings.SECRET_KEY)}")
    print(f"JWT_ALGORITHM: {settings.JWT_ALGORITHM}")
    print(f"ACCESS_TOKEN_EXPIRE_MINUTES: {settings.ACCESS_TOKEN_EXPIRE_MINUTES}")
    print()

    # Create a test token
    test_data = {
        "sub": "testuser",
        "id": "123"
    }

    print("Creating test token...")
    try:
        token = token_helper.create_access_token(test_data)
        print(f"Token created successfully: {token[:50]}...")
        print()
    except Exception as e:
        print(f"ERROR creating token: {e}")
        return

    # Verify the token
    print("Verifying token...")
    try:
        payload = token_helper.verify_token(token)
        if payload:
            print(f"Token verified successfully!")
            print(f"Username: {payload.username}")
            print(f"User ID: {payload.id}")
        else:
            print("ERROR: Token verification returned None")
    except Exception as e:
        print(f"ERROR verifying token: {e}")

    print()
    print("=" * 50)

if __name__ == "__main__":
    test_jwt_flow()
