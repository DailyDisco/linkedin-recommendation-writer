#!/usr/bin/env python3
"""
Test script for background processing functionality.

This script tests the new background processing capabilities
for GitHub analysis to ensure they work correctly.
"""

import asyncio
import httpx
import json
import time
from typing import Optional


async def test_force_refresh_background():
    """Test background processing with force refresh."""

    base_url = "http://localhost:8000"
    test_username = "octocat"

    print("\n🔄 Testing background processing with force_refresh...")

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(
            f"{base_url}/api/v1/github/analyze",
            json={"username": test_username, "force_refresh": True}
        )

        if response.status_code == 200:
            result = response.json()

            if result.get('user_data', {}).get('processing'):
                # This is a background task response
                task_id = result.get('user_data', {}).get('task_id')
                print("✅ Background analysis started with force_refresh!")
                print(f"   Task ID: {task_id}")
                print("   Status: Processing (Background task started)")
                return task_id
            else:
                print("❌ Still got cached response even with force_refresh")
                return None
        else:
            print(f"❌ Failed to start analysis: {response.status_code}")
            return None


async def test_background_processing():
    """Test the background processing functionality."""

    base_url = "http://localhost:8000"
    test_username = "octocat"  # Public GitHub user for testing

    print("🧪 Testing Background Processing for GitHub Analysis")
    print("=" * 60)

    # Test 1: Start background analysis
    print("\n1️⃣ Starting background analysis...")
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{base_url}/api/v1/github/analyze",
                json={"username": test_username, "force_refresh": False}
            )

            if response.status_code == 200:
                result = response.json()
                print("✅ Background analysis started successfully!")

                # Check if this is a cached response (has full analysis) or background task response
                if result.get('user_data', {}).get('processing'):
                    # This is a background task response
                    task_id = result.get('user_data', {}).get('task_id')
                    print(f"   Task ID: {task_id}")
                    print(f"   Status: Processing (Background task started)")
                else:
                    # This is a cached response - force refresh to test background
                    print("   Note: Cached response returned. Testing background with force_refresh...")
                    return await test_force_refresh_background()

                if not task_id:
                    print("❌ No task ID returned!")
                    return False
            else:
                print(f"❌ Failed to start analysis: {response.status_code}")
                print(f"   Response: {response.text}")
                return False

    except Exception as e:
        print(f"❌ Error starting analysis: {e}")
        return False

    # Test 2: Poll task status
    print("\n2️⃣ Polling task status...")
    max_polls = 30  # Max 30 polls (30 seconds)
    poll_count = 0

    while poll_count < max_polls:
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(f"{base_url}/api/v1/github/task/{task_id}")

                if response.status_code == 200:
                    status_data = response.json()
                    status = status_data.get('status')
                    message = status_data.get('message', '')

                    print(f"   Poll {poll_count + 1}: {status} - {message}")

                    if status == "completed":
                        print("✅ Analysis completed successfully!")
                        if 'result' in status_data:
                            result = status_data['result']
                            print(f"   User: {result.get('user_data', {}).get('login', 'N/A')}")
                            print(f"   Repositories: {len(result.get('repositories', []))}")
                            print(f"   Languages: {len(result.get('languages', []))}")
                        return True
                    elif status == "failed":
                        print("❌ Analysis failed!")
                        print(f"   Error: {status_data.get('message', 'Unknown error')}")
                        return False
                    elif status == "processing":
                        print(f"   Still processing... ({poll_count + 1}/{max_polls})")
                else:
                    print(f"❌ Failed to get task status: {response.status_code}")

        except Exception as e:
            print(f"❌ Error polling status: {e}")

        poll_count += 1
        await asyncio.sleep(1)  # Wait 1 second between polls

    print(f"❌ Analysis timed out after {max_polls} polls")
    return False


async def test_sync_processing():
    """Test the synchronous processing endpoint."""

    base_url = "http://localhost:8000"
    test_username = "torvalds"  # Another public GitHub user

    print("\n🔄 Testing Synchronous Processing...")
    print("-" * 40)

    try:
        async with httpx.AsyncClient(timeout=60.0) as client:  # Longer timeout for sync
            response = await client.post(
                f"{base_url}/api/v1/github/analyze/sync",
                json={"username": test_username, "force_refresh": False}
            )

            if response.status_code == 200:
                result = response.json()
                print("✅ Synchronous analysis completed!")
                print(f"   User: {result.get('user_data', {}).get('login', 'N/A')}")
                print(f"   Repositories: {len(result.get('repositories', []))}")
                print(f"   Languages: {len(result.get('languages', []))}")
                return True
            else:
                print(f"❌ Synchronous analysis failed: {response.status_code}")
                print(f"   Response: {response.text}")
                return False

    except Exception as e:
        print(f"❌ Error in sync analysis: {e}")
        return False


async def test_health_check():
    """Test the health check endpoint."""

    base_url = "http://localhost:8000"

    print("\n🏥 Testing Health Check...")
    print("-" * 30)

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(f"{base_url}/health")

            if response.status_code == 200:
                health = response.json()
                print("✅ Health check passed!")
                print(f"   Status: {health.get('status', 'unknown')}")
                print(f"   API: {health.get('checks', {}).get('api', 'unknown')}")
                return True
            else:
                print(f"❌ Health check failed: {response.status_code}")
                return False

    except Exception as e:
        print(f"❌ Error checking health: {e}")
        return False


async def main():
    """Run all tests."""

    print("🚀 GitHub Background Processing Test Suite")
    print("=" * 60)

    # Test health first
    health_ok = await test_health_check()
    if not health_ok:
        print("\n❌ API is not healthy. Please start the server first:")
        print("   cd backend && uvicorn app.main:app --reload")
        return

    # Test background processing
    background_ok = await test_background_processing()

    # Test synchronous processing
    sync_ok = await test_sync_processing()

    # Summary
    print("\n" + "=" * 60)
    print("📊 Test Results Summary:")
    print(f"   Health Check: {'✅ PASSED' if health_ok else '❌ FAILED'}")
    print(f"   Background Processing: {'✅ PASSED' if background_ok else '❌ FAILED'}")
    print(f"   Sync Processing: {'✅ PASSED' if sync_ok else '❌ FAILED'}")

    if background_ok and sync_ok:
        print("\n🎉 All tests passed! Background processing is working correctly.")
    else:
        print("\n⚠️ Some tests failed. Check the output above for details.")


if __name__ == "__main__":
    asyncio.run(main())
