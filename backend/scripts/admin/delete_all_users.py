#!/usr/bin/env python3
"""
Database management script to delete all users from the PostgreSQL database.
This script safely handles user deletion with proper cascade operations.
"""

import asyncio
import logging
import sys
from typing import Any, Dict

from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

# Add the backend directory to the Python path
sys.path.insert(0, "/home/day/ProgrammingProjects/github_repo_linkedin_recommendation_writer_app/backend")

from app.core.database import AsyncSessionLocal, test_database_connection
from app.models.github_profile import GitHubProfile
from app.models.recommendation import Recommendation
from app.models.user import User

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


class UserDeletionManager:
    """Manages the deletion of all users from the database."""

    def __init__(self):
        self.db_session = None

    async def __aenter__(self):
        self.db_session = AsyncSessionLocal()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.db_session:
            await self.db_session.close()

    async def get_database_stats(self) -> Dict[str, Any]:
        """Get current database statistics before deletion."""
        try:
            # Count users
            user_count_result = await self.db_session.execute(select(func.count(User.id)))
            user_count = user_count_result.scalar()

            # Count recommendations
            recommendation_count_result = await self.db_session.execute(select(func.count(Recommendation.id)))
            recommendation_count = recommendation_count_result.scalar()

            # Count GitHub profiles
            github_profile_count_result = await self.db_session.execute(select(func.count(GitHubProfile.id)))
            github_profile_count = github_profile_count_result.scalar()

            # Get user details
            users_result = await self.db_session.execute(select(User.id, User.username, User.email, User.created_at).order_by(User.created_at))
            users = users_result.fetchall()

            return {
                "user_count": user_count,
                "recommendation_count": recommendation_count,
                "github_profile_count": github_profile_count,
                "users": [{"id": user.id, "username": user.username, "email": user.email, "created_at": user.created_at.isoformat() if user.created_at else None} for user in users],
            }

        except Exception as e:
            logger.error(f"Failed to get database stats: {e}")
            return {"error": str(e)}

    async def delete_all_users(self) -> Dict[str, Any]:
        """Delete all users and their related data."""
        try:
            logger.info("Starting user deletion process...")

            # Get counts before deletion
            stats_before = await self.get_database_stats()
            logger.info(f"Before deletion: {stats_before['user_count']} users, " f"{stats_before['recommendation_count']} recommendations, " f"{stats_before['github_profile_count']} GitHub profiles")

            # Delete in proper order to handle foreign key constraints
            # 1. Delete recommendations (they reference users)
            deleted_recommendations = await self.db_session.execute(text("DELETE FROM recommendations"))
            recommendations_deleted = deleted_recommendations.rowcount
            logger.info(f"Deleted {recommendations_deleted} recommendations")

            # 2. Delete GitHub profiles (they reference users)
            deleted_profiles = await self.db_session.execute(text("DELETE FROM github_profiles"))
            profiles_deleted = deleted_profiles.rowcount
            logger.info(f"Deleted {profiles_deleted} GitHub profiles")

            # 3. Delete users
            deleted_users = await self.db_session.execute(text("DELETE FROM users"))
            users_deleted = deleted_users.rowcount
            logger.info(f"Deleted {users_deleted} users")

            # Commit the transaction
            await self.db_session.commit()
            logger.info("Transaction committed successfully")

            # Get stats after deletion
            stats_after = await self.get_database_stats()

            return {
                "success": True,
                "stats_before": stats_before,
                "stats_after": stats_after,
                "deleted": {"users": users_deleted, "recommendations": recommendations_deleted, "github_profiles": profiles_deleted},
                "message": f"Successfully deleted {users_deleted} users, " f"{recommendations_deleted} recommendations, and " f"{profiles_deleted} GitHub profiles",
            }

        except Exception as e:
            # Rollback on error
            await self.db_session.rollback()
            logger.error(f"Failed to delete users: {e}")
            return {"success": False, "error": str(e), "message": "User deletion failed and was rolled back"}

    async def verify_deletion(self) -> Dict[str, Any]:
        """Verify that all users have been deleted."""
        try:
            stats = await self.get_database_stats()

            if stats.get("user_count") == 0:
                return {
                    "verified": True,
                    "message": "✅ Verification successful: All users have been deleted",
                    "remaining_counts": {"users": stats.get("user_count", 0), "recommendations": stats.get("recommendation_count", 0), "github_profiles": stats.get("github_profile_count", 0)},
                }
            else:
                return {
                    "verified": False,
                    "message": f"❌ Verification failed: {stats.get('user_count', 0)} users still remain",
                    "remaining_counts": {"users": stats.get("user_count", 0), "recommendations": stats.get("recommendation_count", 0), "github_profiles": stats.get("github_profile_count", 0)},
                }

        except Exception as e:
            logger.error(f"Failed to verify deletion: {e}")
            return {"verified": False, "error": str(e), "message": "Verification failed due to error"}


async def main():
    """Main function to run the user deletion script."""
    print("🔄 LinkedIn Recommendation Writer - User Deletion Script")
    print("=" * 60)

    # Test database connection first
    print("🔗 Testing database connection...")
    connection_result = await test_database_connection()

    if not connection_result.get("connection_test") == "success":
        print(f"❌ Database connection failed: {connection_result.get('error_message', 'Unknown error')}")
        print(f"💡 Recommendations: {', '.join(connection_result.get('recommendations', []))}")
        return

    print("✅ Database connection successful")

    # Get current database stats
    async with UserDeletionManager() as manager:
        print("\n📊 Current Database Statistics:")
        stats = await manager.get_database_stats()

        if "error" in stats:
            print(f"❌ Failed to get database stats: {stats['error']}")
            return

        print(f"   👥 Users: {stats['user_count']}")
        print(f"   📝 Recommendations: {stats['recommendation_count']}")
        print(f"   🔗 GitHub Profiles: {stats['github_profile_count']}")

        if stats["user_count"] == 0:
            print("\nℹ️  No users found in the database. Nothing to delete.")
            return

        # Show user details
        print("\n👤 Current Users:")
        for user in stats["users"][:10]:  # Show first 10 users
            print(f"   ID: {user['id']}, Username: {user['username'] or 'N/A'}, " f"Email: {user['email'] or 'N/A'}")
        if len(stats["users"]) > 10:
            print(f"   ... and {len(stats['users']) - 10} more users")

        # Confirm deletion
        print("\n⚠️  WARNING: This will permanently delete ALL users and their associated data!")
        print("   This includes all recommendations and GitHub profiles.")
        print("   This action CANNOT be undone!")

        response = input("\n❓ Are you sure you want to delete ALL users? (type 'YES' to confirm): ")

        if response.strip().upper() != "YES":
            print("❌ Deletion cancelled by user.")
            return

        # Proceed with deletion
        print("\n🗑️  Starting deletion process...")
        result = await manager.delete_all_users()

        if result["success"]:
            print("✅ Deletion completed successfully!")
            print(f"   Deleted: {result['deleted']['users']} users")
            print(f"   Deleted: {result['deleted']['recommendations']} recommendations")
            print(f"   Deleted: {result['deleted']['github_profiles']} GitHub profiles")

            # Verify deletion
            print("\n🔍 Verifying deletion...")
            verification = await manager.verify_deletion()

            if verification["verified"]:
                print("✅ Verification successful: All users have been deleted")
            else:
                print("❌ Verification failed: Some data may still remain")
                print(f"   Remaining: {verification['remaining_counts']}")

        else:
            print(f"❌ Deletion failed: {result.get('error', 'Unknown error')}")

    print("\n🏁 Script execution completed.")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n⚠️  Script interrupted by user.")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        sys.exit(1)
