#!/usr/bin/env python3
"""
Script to clear cached user data from Redis cache.
This removes cached GitHub profiles and other user-related cached data.
"""

import asyncio
import logging
import sys
from typing import Any, Dict, List

# Add the backend directory to the Python path
sys.path.insert(0, "/home/day/ProgrammingProjects/github_repo_linkedin_recommendation_writer_app/backend")

from app.core.redis_client import get_redis, init_redis

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


async def clear_cached_users() -> Dict[str, Any]:
    """Clear all cached user data from Redis."""
    try:
        # Initialize Redis connection
        await init_redis()
        redis_client = await get_redis()

        # Find all user-related keys
        user_keys = []

        # Get all keys and filter for user-related ones
        all_keys = await redis_client.keys("*")

        for key in all_keys:
            key_str = key.decode("utf-8") if isinstance(key, bytes) else key
            # Look for user-related patterns
            if any(pattern in key_str.lower() for pattern in ["user", "profile", "github_profile", "anonymous"]):
                user_keys.append(key_str)

        logger.info(f"Found {len(user_keys)} cached user keys")

        # Show what will be deleted
        if user_keys:
            logger.info("Keys to be deleted:")
            for key in user_keys[:10]:  # Show first 10
                logger.info(f"  - {key}")
            if len(user_keys) > 10:
                logger.info(f"  ... and {len(user_keys) - 10} more")

        # Delete the keys
        if user_keys:
            deleted_count = await redis_client.delete(*user_keys)
            logger.info(f"Successfully deleted {deleted_count} cached user keys")
        else:
            logger.info("No cached user keys found to delete")
            deleted_count = 0

        # Verify deletion
        remaining_keys = await redis_client.keys("*user*")
        remaining_count = len(remaining_keys)

        return {
            "success": True,
            "keys_found": len(user_keys),
            "keys_deleted": deleted_count,
            "remaining_user_keys": remaining_count,
            "deleted_keys": user_keys[:20],  # Show first 20 for reference
            "message": f"Successfully cleared {deleted_count} cached user entries from Redis",
        }

    except Exception as e:
        logger.error(f"Failed to clear cached users: {e}")
        return {"success": False, "error": str(e), "message": "Failed to clear cached users"}


async def show_cached_users() -> Dict[str, Any]:
    """Show information about cached users without deleting them."""
    try:
        # Initialize Redis connection
        await init_redis()
        redis_client = await get_redis()

        # Find all user-related keys
        user_keys = []
        all_keys = await redis_client.keys("*")

        for key in all_keys:
            key_str = key.decode("utf-8") if isinstance(key, bytes) else key
            if any(pattern in key_str.lower() for pattern in ["user", "profile", "github_profile", "anonymous"]):
                user_keys.append(key_str)

        # Get some sample data
        sample_data = {}
        for key in user_keys[:3]:  # Get first 3 keys
            try:
                data = await redis_client.get(key)
                if data:
                    # Try to parse as JSON for better display
                    import json

                    try:
                        parsed_data = json.loads(data.decode("utf-8") if isinstance(data, bytes) else data)
                        if "user_data" in parsed_data and "full_name" in parsed_data["user_data"]:
                            sample_data[key] = {"type": "github_profile", "name": parsed_data["user_data"]["full_name"], "username": parsed_data["user_data"]["github_username"]}
                        else:
                            sample_data[key] = {"type": "cached_data", "size": len(data)}
                    except:
                        sample_data[key] = {"type": "raw_data", "size": len(data)}
            except Exception as e:
                sample_data[key] = {"error": str(e)}

        return {
            "success": True,
            "total_cached_keys": len(all_keys),
            "user_related_keys": len(user_keys),
            "sample_cached_users": sample_data,
            "all_user_keys": user_keys[:10],  # Show first 10
            "message": f"Found {len(user_keys)} cached user-related keys out of {len(all_keys)} total keys",
        }

    except Exception as e:
        logger.error(f"Failed to show cached users: {e}")
        return {"success": False, "error": str(e), "message": "Failed to retrieve cached user information"}


async def main():
    """Main function to run the cache clearing script."""
    print("🔄 LinkedIn Recommendation Writer - Clear Cached Users Script")
    print("=" * 65)

    # First show what cached users exist
    print("\n📊 Current Cached User Data:")
    show_result = await show_cached_users()

    if show_result["success"]:
        print(f"   📁 Total Redis keys: {show_result['total_cached_keys']}")
        print(f"   👤 User-related keys: {show_result['user_related_keys']}")

        if show_result["user_related_keys"] > 0:
            print("\n   Cached user profiles found:")
            for key, info in show_result["sample_cached_users"].items():
                if info.get("type") == "github_profile":
                    print(f"     • {info['name']} ({info['username']}) - {key}")
                else:
                    print(f"     • {key} ({info.get('type', 'unknown')})")

            if len(show_result["all_user_keys"]) > 3:
                print(f"     ... and {len(show_result['all_user_keys']) - 3} more")

            # Automatically proceed with clearing if users are found
            print("\n🗑️  Starting cache clearing process...")
            result = await clear_cached_users()

            if result["success"]:
                print("✅ Cache clearing completed successfully!")
                print(f"   Deleted: {result['keys_deleted']} cached user keys")
                print(f"   Remaining user keys: {result['remaining_user_keys']}")

                if result["keys_deleted"] > 0:
                    print("\n   Deleted keys include:")
                    for key in result["deleted_keys"][:5]:  # Show first 5
                        print(f"     • {key}")
                    if len(result["deleted_keys"]) > 5:
                        print(f"     ... and {len(result['deleted_keys']) - 5} more")
            else:
                print(f"❌ Cache clearing failed: {result.get('error', 'Unknown error')}")
        else:
            print("   ℹ️  No cached user data found.")
            return

    else:
        print(f"❌ Failed to check cached users: {show_result.get('error', 'Unknown error')}")
        return

    print("\n🏁 Cache clearing script execution completed.")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n⚠️  Script interrupted by user.")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        sys.exit(1)
