#!/usr/bin/env python3
"""Debug script to test repo_only functionality."""

import asyncio
import logging
import os
import sys

# Add the current directory to the path
sys.path.insert(0, os.path.dirname(__file__))

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", handlers=[logging.StreamHandler(sys.stdout)])

logger = logging.getLogger(__name__)


async def test_repo_only():
    """Test the repo_only functionality."""
    logger.info("🧪 STARTING REPO_ONLY DEBUG TEST")
    logger.info("=" * 60)

    # Test parameters
    github_username = "DailyDisco"
    repository_url = "https://github.com/microsoft/vscode"
    analysis_context_type = "repo_only"

    logger.info("📋 Test Parameters:")
    logger.info(f"   • github_username: {github_username}")
    logger.info(f"   • repository_url: {repository_url}")
    logger.info(f"   • analysis_context_type: {analysis_context_type}")

    # Test the condition check
    condition_check = analysis_context_type == "repo_only" and repository_url is not None
    logger.info(f"🔍 Condition check result: {condition_check}")

    if condition_check:
        logger.info("✅ Would take repo_only path")
    else:
        logger.info("❌ Would NOT take repo_only path")

    logger.info("=" * 60)
    logger.info("🧪 REPO_ONLY DEBUG TEST COMPLETED")


if __name__ == "__main__":
    asyncio.run(test_repo_only())
