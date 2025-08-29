"""AI service for generating recommendations using Google Gemini."""

import logging
from typing import Any, Dict, List, Optional, TypedDict

from app.services.ai_recommendation_service import AIRecommendationService
from app.services.confidence_scorer_service import ConfidenceScorerService
from app.services.keyword_refinement_service import KeywordRefinementService
from app.services.multi_contributor_service import MultiContributorService
from app.services.prompt_service import PromptService
from app.services.readme_generation_service import READMEGenerationService

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
        self.confidence_scorer = ConfidenceScorerService()
        self.readme_service = READMEGenerationService(self.prompt_service)
        self.multi_contributor_service = MultiContributorService(self.prompt_service)
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

            # Update confidence scores using the confidence scorer
            for option in result.get("options", []):
                if "confidence_score" in option:
                    option["confidence_score"] = self.confidence_scorer.calculate_confidence_score(github_data, option["content"])

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
        include_keywords: Optional[List[str]] = None,
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
            include_keywords=include_keywords,
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

    # Multi-contributor methods
    async def _generate_multi_contributor_recommendation(
        self,
        repository_data: Dict[str, Any],
        contributors: List[Dict[str, Any]],
        team_highlights: List[str],
        collaboration_insights: List[str],
        technical_diversity: Dict[str, int],
        recommendation_type: str = "professional",
        tone: str = "professional",
        length: str = "medium",
        focus_areas: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Generate a recommendation highlighting multiple contributors."""
        return await self.multi_contributor_service.generate_multi_contributor_recommendation(
            repository_data=repository_data,
            contributors=contributors,
            team_highlights=team_highlights,
            collaboration_insights=collaboration_insights,
            technical_diversity=technical_diversity,
            recommendation_type=recommendation_type,
            tone=tone,
            length=length,
            focus_areas=focus_areas,
        )

    # Confidence scoring methods
    def calculate_confidence_score(self, github_data: Dict[str, Any], generated_content: str, prompt: Optional[str] = None, generation_params: Optional[Dict[str, Any]] = None) -> int:
        """Calculate confidence score for generated content."""
        return self.confidence_scorer.calculate_confidence_score(github_data, generated_content, prompt, generation_params)

    def calculate_readme_confidence_score(self, content: str, repository_data: Dict[str, Any], repository_analysis: Dict[str, Any]) -> int:
        """Calculate confidence score for generated README."""
        return self.confidence_scorer.calculate_readme_confidence_score(content, repository_data, repository_analysis)

    def calculate_multi_contributor_confidence_score(self, content: str, contributors: List[Dict[str, Any]], team_highlights: List[str]) -> int:
        """Calculate confidence score for multi-contributor recommendations."""
        return self.confidence_scorer.calculate_multi_contributor_confidence_score(content, contributors, team_highlights)

    def validate_keyword_compliance(self, content: str, include_keywords: Optional[List[str]] = None, exclude_keywords: Optional[List[str]] = None) -> Dict[str, Any]:
        """Validate keyword compliance in content."""
        return self.confidence_scorer.validate_keyword_compliance(content, include_keywords, exclude_keywords)

    def generate_refinement_summary(self, validation: Dict[str, Any]) -> str:
        """Generate a summary of the refinement process."""
        return self.confidence_scorer.generate_refinement_summary(validation)

    # Backwards compatibility methods
    def _get_length_guideline(self, length: str) -> str:
        """Get word count guideline for different lengths."""
        return self.prompt_service._get_length_guideline(length)

    def _extract_commit_examples(self, commit_analysis: Dict[str, Any]) -> List[str]:
        """Extract specific, concrete examples from commit analysis."""
        return self.prompt_service._extract_commit_examples(commit_analysis)

    def _extract_title(self, content: str, username: str) -> str:
        """Extract or generate a title for the recommendation."""
        return self.prompt_service.extract_title(content, username)
