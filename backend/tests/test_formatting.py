#!/usr/bin/env python3
"""Test script for paragraph splitting and markdown removal functionality."""

import asyncio
import logging
import sys
import os

# Add the backend directory to the path
sys.path.append('/app/backend')

from app.services.ai.ai_recommendation_service import AIRecommendationService
from app.services.ai.prompt_service import PromptService

# Set up logging to see debug messages
logging.basicConfig(level=logging.DEBUG, format='%(levelname)s: %(message)s')

async def test_formatting():
    """Test the formatting function directly."""
    print("=" * 60)
    print("TESTING PARAGRAPH SPLITTING AND MARKDOWN REMOVAL")
    print("=" * 60)

    prompt_service = PromptService()
    ai_service = AIRecommendationService(prompt_service)

    # Test content with markdown and long paragraphs
    test_content = '''**John Doe** is an excellent developer with *strong skills* in Python and JavaScript. He has worked on multiple projects and consistently delivers high-quality code. His technical expertise is impressive and he always goes above and beyond. He demonstrates excellent problem-solving abilities and works well in team environments. His commitment to code quality is evident in his detailed commit messages and thorough testing approach. He has contributed significantly to open source projects and maintains a strong presence in the developer community. His ability to learn new technologies quickly makes him a valuable asset to any team.'''

    print('=== ORIGINAL CONTENT ===')
    print(test_content)
    print()

    # Test the formatting
    formatted = ai_service._format_recommendation_output(
        content=test_content,
        length_guideline='medium',
        generation_params={'tone': 'professional'}
    )

    print('=== FORMATTED CONTENT (WITH NEWLINES VISIBLE) ===')
    print(repr(formatted))
    print()

    print('=== FORMATTED CONTENT (READABLE) ===')
    print(formatted)
    print()

    # Count paragraphs
    paragraphs = [p.strip() for p in formatted.split('\n\n') if p.strip()]
    print(f'✅ Number of paragraphs: {len(paragraphs)} (target: 3)')
    for i, para in enumerate(paragraphs, 1):
        word_count = len(para.split())
        print(f'   Paragraph {i}: {word_count} words')

    # Check for markdown removal
    has_bold = '**' in formatted
    has_italic = '*' in formatted or '_' in formatted

    print()
    print('=== MARKDOWN REMOVAL CHECK ===')
    print(f'✅ Bold markdown removed: {"YES" if not has_bold else "NO"}')
    print(f'✅ Italic markdown removed: {"YES" if not has_italic else "NO"}')

    # Check for paragraph structure
    has_double_newlines = '\n\n' in formatted
    print(f'✅ Contains paragraph breaks: {"YES" if has_double_newlines else "NO"}')

    print()
    print("=" * 60)
    print("TEST COMPLETED")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(test_formatting())

