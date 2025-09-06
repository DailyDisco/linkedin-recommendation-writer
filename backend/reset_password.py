#!/usr/bin/env python3
"""
Password reset script for LinkedIn Recommendation Writer
Resets a user's password when SECRET_KEY changes invalidate existing tokens
"""

import asyncio
import bcrypt
import secrets
import string
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

# Add the backend directory to the Python path
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from app.core.dependencies import get_database_session
from app.models.user import User


def generate_secure_password(length: int = 12) -> str:
    """Generate a secure random password."""
    characters = string.ascii_letters + string.digits + "!@#$%^&*"
    password = ''.join(secrets.choice(characters) for _ in range(length))
    return password


def hash_password(password: str) -> str:
    """Hash a password using bcrypt."""
    pwd_bytes = password.encode("utf-8")
    salt = bcrypt.gensalt()
    hashed_password = bcrypt.hashpw(password=pwd_bytes, salt=salt)
    return hashed_password.decode("utf-8")


async def list_users(db: AsyncSession) -> list[User]:
    """List all users in the database."""
    query = select(User)
    result = await db.execute(query)
    return result.scalars().all()


async def create_new_user(db: AsyncSession) -> dict:
    """Create a new user account."""
    print("\n📝 Creating new user account...")

    # Get user details
    username = input("   Enter username: ").strip()
    email = input("   Enter email: ").strip()
    full_name = input("   Enter full name (optional): ").strip() or None

    # Generate secure password
    password = generate_secure_password()

    # Check if user already exists
    existing_query = select(User).where(
        (User.username == username) | (User.email == email)
    )
    existing_result = await db.execute(existing_query)
    existing_user = existing_result.scalar_one_or_none()

    if existing_user:
        return {"success": False, "error": "User with this username or email already exists"}

    # Hash password and create user
    hashed_password = hash_password(password)

    new_user = User(
        username=username,
        email=email,
        full_name=full_name,
        hashed_password=hashed_password
    )

    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)

    return {
        "success": True,
        "user_id": new_user.id,
        "username": new_user.username,
        "email": new_user.email,
        "password": password,
        "message": f"User {username} created successfully"
    }


async def reset_user_password(db: AsyncSession, user_identifier: str, new_password: str = None) -> dict:
    """Reset a user's password by username or email."""
    # Generate new password if not provided
    if not new_password:
        new_password = generate_secure_password()

    # Find user by username or email
    query = select(User).where(
        (User.username == user_identifier) | (User.email == user_identifier)
    )
    result = await db.execute(query)
    user = result.scalar_one_or_none()

    if not user:
        return {"success": False, "error": f"User '{user_identifier}' not found"}

    # Hash the new password
    hashed_password = hash_password(new_password)

    # Update the user's password
    user.hashed_password = hashed_password
    await db.commit()

    return {
        "success": True,
        "user_id": user.id,
        "username": user.username,
        "email": user.email,
        "new_password": new_password,
        "message": f"Password reset successful for user {user.username}"
    }


async def main():
    """Main function to run the password reset script."""
    print("🔑 LinkedIn Recommendation Writer - Password Reset Script")
    print("=" * 60)

    async for db in get_database_session():
        try:
            # List all users first
            users = await list_users(db)
            print(f"\n👥 Found {len(users)} users in database:")

            if not users:
                print("   No users found.")
                create_choice = input("   Would you like to create a new user account? (y/n): ").strip().lower()
                if create_choice == 'y':
                    create_result = await create_new_user(db)
                    if create_result["success"]:
                        print(f"\n✅ User created successfully!")
                        print(f"   Username: {create_result['username']}")
                        print(f"   Email: {create_result['email']}")
                        print(f"   Password: {create_result['password']}")
                        print("\n⚠️  IMPORTANT: Save this password! It will only be shown once.")
                        users = [create_result]  # Use the newly created user
                    else:
                        print(f"❌ Failed to create user: {create_result.get('error', 'Unknown error')}")
                        return
                else:
                    print("   Please create a user first through the application or API.")
                    return

            for i, user in enumerate(users, 1):
                print(f"   {i}. ID: {user.id}, Username: {user.username or 'N/A'}, Email: {user.email or 'N/A'}")

            # Ask user which account to reset
            print("\n🔄 Password Reset Options:")
            print("   1. Reset password for specific user")
            print("   2. Reset all user passwords")
            print("   3. Create new secure password for first user")

            choice = input("\nEnter your choice (1-3): ").strip()

            if choice == "1":
                user_identifier = input("Enter username or email: ").strip()
                result = await reset_user_password(db, user_identifier)
            elif choice == "2":
                print("Resetting passwords for all users...")
                results = []
                for user in users:
                    identifier = user.username or user.email
                    result = await reset_user_password(db, identifier)
                    results.append(result)
                    print(f"   ✅ Reset password for {identifier}")
                print("\n📋 Password Summary:")
                for result in results:
                    if result["success"]:
                        print(f"   {result['username']}: {result['new_password']}")
                return
            elif choice == "3":
                if users:
                    first_user = users[0]
                    identifier = first_user.username or first_user.email
                    result = await reset_user_password(db, identifier)
                else:
                    print("❌ No users found")
                    return
            else:
                print("❌ Invalid choice")
                return

            # Display result
            if result["success"]:
                print("\n✅ Password reset successful!")
                print(f"   User: {result['username']}")
                print(f"   Email: {result['email']}")
                print(f"   New Password: {result['new_password']}")
                print("\n⚠️  IMPORTANT: Save this password! It will only be shown once.")
                print("   You should change it to something memorable after logging in.")
            else:
                print(f"❌ Password reset failed: {result.get('error', 'Unknown error')}")

        except Exception as e:
            print(f"❌ Error: {e}")
        finally:
            break


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n⚠️  Script interrupted by user.")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        sys.exit(1)
