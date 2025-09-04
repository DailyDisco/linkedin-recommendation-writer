"""AI service for generating recommendations using Google Gemini."""

import logging
from typing import Any, Dict, List, Optional, TypedDict

from app.services.ai.ai_recommendation_service import AIRecommendationService
from app.services.ai.prompt_service import PromptService
from app.services.ai.readme_generation_service import READMEGenerationService
from app.services.analysis.keyword_refinement_service import KeywordRefinementService

logger = logging.getLogger(__name__)


class RecommendationValidationResult(TypedDict):
    is_valid: bool
    issues: List[str]
    suggestions: List[str]
    structure_score: int


class AIService:
    """Main AI service that orchestrates all AI-related functionality."""

    def __init__(self) -> None:
        """Initialize AI service with all specialized services."""
        # Initialize the core prompt service
        self.prompt_service = PromptService()

        # Initialize specialized AI services
        self.recommendation_service = AIRecommendationService(self.prompt_service)
        self.readme_service = READMEGenerationService(self.prompt_service)
        self.keyword_refinement_service = KeywordRefinementService(self.prompt_service)

    async def generate_recommendation(
        self,
        github_data: Dict[str, Any],
        recommendation_type: str = "professional",
        tone: str = "professional",
        length: str = "medium",
        custom_prompt: Optional[str] = None,
        target_role: Optional[str] = None,
        specific_skills: Optional[list] = None,
        exclude_keywords: Optional[list] = None,
    ) -> Dict[str, Any]:
        """Generate a LinkedIn recommendation using AI."""
        try:
            # Delegate to the specialized recommendation service
            result = await self.recommendation_service.generate_recommendation(
                github_data=github_data,
                recommendation_type=recommendation_type,
                tone=tone,
                length=length,
                custom_prompt=custom_prompt,
                target_role=target_role,
                specific_skills=specific_skills,
                exclude_keywords=exclude_keywords,
            )

            return result

        except Exception as e:
            logger.error(f"Error generating AI recommendation: {e}")
            raise

    # Prompt building methods
    def build_prompt(
        self,
        github_data: Dict[str, Any],
        recommendation_type: str,
        tone: str,
        length: str,
        custom_prompt: Optional[str] = None,
        target_role: Optional[str] = None,
        specific_skills: Optional[list] = None,
        exclude_keywords: Optional[list] = None,
    ) -> str:
        """Build the AI generation prompt - delegate to PromptService."""
        return self.prompt_service.build_prompt(
            github_data=github_data,
            recommendation_type=recommendation_type,
            tone=tone,
            length=length,
            custom_prompt=custom_prompt,
            target_role=target_role,
            specific_skills=specific_skills,
            exclude_keywords=exclude_keywords,
        )

    def _build_prompt(
        self,
        github_data: Dict[str, Any],
        recommendation_type: str,
        tone: str,
        length: str,
        custom_prompt: Optional[str] = None,
        target_role: Optional[str] = None,
        specific_skills: Optional[list] = None,
        exclude_keywords: Optional[list] = None,
    ) -> str:
        """Build the AI generation prompt - delegate to PromptService."""
        return self.build_prompt(
            github_data=github_data,
            recommendation_type=recommendation_type,
            tone=tone,
            length=length,
            custom_prompt=custom_prompt,
            target_role=target_role,
            specific_skills=specific_skills,
            exclude_keywords=exclude_keywords,
        )

    # Recommendation generation methods
    async def regenerate_recommendation(
        self,
        original_content: str,
        refinement_instructions: str,
        github_data: Dict[str, Any],
        recommendation_type: str = "professional",
        tone: str = "professional",
        length: str = "medium",
        exclude_keywords: Optional[list] = None,
    ) -> Dict[str, Any]:
        """Regenerate a recommendation with refinement instructions."""
        return await self.recommendation_service.regenerate_recommendation(
            original_content=original_content,
            refinement_instructions=refinement_instructions,
            github_data=github_data,
            recommendation_type=recommendation_type,
            tone=tone,
            length=length,
            exclude_keywords=exclude_keywords,
        )

    # Keyword refinement methods
    async def refine_recommendation_with_keywords(
        self,
        original_content: str,
        refinement_instructions: str,
        github_data: Dict[str, Any],
        recommendation_type: str,
        tone: str,
        length: str,
        exclude_keywords: Optional[List[str]] = None,
        regeneration_params: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Refine a generated recommendation based on keywords."""
        return await self.keyword_refinement_service.refine_recommendation_with_keywords(
            original_content=original_content,
            refinement_instructions=refinement_instructions,
            github_data=github_data,
            recommendation_type=recommendation_type,
            tone=tone,
            length=length,
            exclude_keywords=exclude_keywords,
            regeneration_params=regeneration_params,
        )

    # README generation methods
    async def generate_repository_readme(
        self,
        repository_data: Dict[str, Any],
        repository_analysis: Dict[str, Any],
        style: str = "comprehensive",
        include_sections: Optional[List[str]] = None,
        target_audience: str = "developers",
    ) -> Dict[str, Any]:
        """Generate a README for a GitHub repository."""
        return await self.readme_service.generate_repository_readme(
            repository_data=repository_data,
            repository_analysis=repository_analysis,
            style=style,
            include_sections=include_sections,
            target_audience=target_audience,
        )

    # Backwards compatibility methods
    def _get_length_guideline(self, length: str) -> str:
        """Get word count guideline for different lengths."""
        return self.prompt_service._get_length_guideline(length)

    def _extract_commit_examples(self, commit_analysis: Dict[str, Any]) -> List[str]:
        """Extract specific, concrete examples from commit analysis."""
        return self.prompt_service._extract_commit_examples(commit_analysis)

    def _extract_title(self, content: str, username: str, first_name: Optional[str] = None) -> str:
        """Extract or generate a title for the recommendation."""
        return self.prompt_service.extract_title(content, username, first_name)
