#!/usr/bin/env python3
"""Test script for different length settings."""

import asyncio
import logging
import sys

sys.path.append("/app/backend")

from app.services.ai.ai_recommendation_service import AIRecommendationService
from app.services.ai.prompt_service import PromptService

logging.basicConfig(level=logging.INFO, format="%(message)s")


async def test_different_lengths():
    print("=" * 60)
    print("TESTING DIFFERENT LENGTH SETTINGS")
    print("=" * 60)

    prompt_service = PromptService()
    ai_service = AIRecommendationService(prompt_service)

    test_content = """John Doe is an excellent developer with strong skills in Python and JavaScript. He has worked on multiple projects and consistently delivers high-quality code. His technical expertise is impressive and he always goes above and beyond. He demonstrates excellent problem-solving abilities and works well in team environments. His commitment to code quality is evident in his detailed commit messages and thorough testing approach. He has contributed significantly to open source projects and maintains a strong presence in the developer community. His ability to learn new technologies quickly makes him a valuable asset to any team. He also has experience with React, Node.js, and cloud technologies. His collaborative approach and willingness to mentor junior developers make him an outstanding team member. He consistently demonstrates leadership in technical discussions and helps drive project success through his innovative solutions and dedication to best practices."""

    lengths = ["short", "medium", "long"]

    for length in lengths:
        print(f"\n--- TESTING {length.upper()} LENGTH ---")

        formatted = ai_service._format_recommendation_output(content=test_content, length_guideline=length, generation_params={"tone": "professional"})

        paragraphs = [p.strip() for p in formatted.split("\n\n") if p.strip()]
        target_paragraphs = {"short": 2, "medium": 3, "long": 4}[length]

        print(f"✅ Target paragraphs: {target_paragraphs}, Actual: {len(paragraphs)}")

        for i, para in enumerate(paragraphs, 1):
            word_count = len(para.split())
            print(f"   Paragraph {i}: {word_count} words")

        # Check if we achieved the target
        success = len(paragraphs) == target_paragraphs
        print(f'✅ Length target achieved: {"YES" if success else "NO"}')


if __name__ == "__main__":
    asyncio.run(test_different_lengths())
