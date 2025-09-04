#!/usr/bin/env python3
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

async def test_ai_generation():
    print('=' * 60)
    print('TESTING AI GENERATION DIRECTLY')
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

    # Test the single option generation
    print("Testing single option generation...")
    try:
        result = await ai_service._generate_single_option(
            prompt="Write a LinkedIn recommendation for rajakrishna based on their work in the smart-gym repository. Focus on their React and TypeScript skills. IMPORTANT: Create distinct paragraphs with DOUBLE LINE BREAKS (\\n\\n) between each paragraph. Each paragraph must be separated by exactly two newline characters to create proper paragraph formatting.",
            temperature_modifier=0.1,
            length="medium",
            generation_params={
                'github_username': 'rajakrishna',
                'recommendation_type': 'professional',
                'tone': 'professional',
                'length': 'medium',
                'focus': 'technical_expertise'
            }
        )

        print("\n✅ AI Generation Result:")
        print(f"Length: {len(result)} characters")
        double_newlines = '\n\n'
        print(f"Paragraph count: {len(result.split(double_newlines))}")
        print(f"Contains double newlines: {double_newlines in result}")
        print("\n--- FORMATTED RESULT ---")
        print(repr(result))  # Show raw representation to see newlines
        print("\n--- DISPLAY RESULT ---")
        print(result)

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_ai_generation())
