#!/usr/bin/env python3
"""Test the full pipeline to see what's being sent to frontend."""

import asyncio
import logging
import sys
sys.path.append('/app/backend')

from app.services.ai.ai_recommendation_service import AIRecommendationService
from app.services.ai.prompt_service import PromptService

logging.basicConfig(level=logging.DEBUG, format='%(levelname)s: %(message)s')

async def test_full_pipeline():
    print('=' * 60)
    print('TESTING FULL PIPELINE - WHAT FRONTEND RECEIVES')
    print('=' * 60)

    prompt_service = PromptService()
    ai_service = AIRecommendationService(prompt_service)

    # Test GitHub data
    github_data = {
        'user_data': {'github_username': 'rajakrishna', 'login': 'rajakrishna'},
        'repository_info': {
            'name': 'smart-gym',
            'description': 'A fitness tracking application',
            'language': 'TypeScript'
        },
        'languages': [{'language': 'TypeScript', 'percentage': 60.0}],
        'skills': {
            'technical_skills': ['React', 'TypeScript', 'Node.js'],
            'frameworks': ['React', 'Express'],
            'domains': ['Web Development']
        },
        'analysis_context_type': 'repo_only'
    }

    print("Generating full recommendation options...")
    try:
        result_generator = ai_service.generate_recommendation_stream(
            github_data=github_data,
            recommendation_type='professional',
            tone='professional',
            length='medium',
            custom_prompt='Working Relationship: We created FitMax\nNotable Skills Observed: React and ShadCN\nTime Period: 2 months\nKey Achievements: Built responsive UI components',
            target_role='Repository: smart-gym',
            specific_skills=['React', 'ShadCN'],
            analysis_context_type='repo_only',
            repository_url='https://github.com/rajakrishna/smart-gym',
            force_refresh=True
        )

        # Collect all progress updates
        final_result = None
        async for update in result_generator:
            print(f"Progress: {update.get('stage', 'Unknown')}")
            if update.get('status') == 'complete':
                final_result = update.get('result')
                break

        if final_result:
            print("\n" + "=" * 60)
            print("FINAL RESULT SENT TO FRONTEND")
            print("=" * 60)

            options = final_result.get('options', [])
            for i, option in enumerate(options, 1):
                print(f"\n--- OPTION {i} ---")
                content = option.get('content', '')
                print(f"Raw content length: {len(content)}")
                double_newlines = '\n\n'
                print(f"Contains double newlines: {double_newlines in content}")
                print(f"Paragraph count: {len(content.split(double_newlines))}")

                # Show first 200 chars with visible newlines
                preview = content[:200].replace('\n', '\\n')
                print(f"Content preview: {preview}...")

                print("\nActual display (as frontend would see it):")
                print("-" * 40)
                print(content)
                print("-" * 40)

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_full_pipeline())
