"""Recommendation Engine Service for generating and managing recommendations."""

import logging
from typing import Any, Dict, List, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.recommendation import Recommendation
from app.schemas.recommendation import (
    RecommendationCreate,
    RecommendationOption,
    RecommendationOptionsResponse,
    RecommendationResponse,
)

logger = logging.getLogger(__name__)


class RecommendationEngineService:
    """Service for generating and managing recommendation content."""

    def __init__(self, ai_service: Any) -> None:
        """Initialize recommendation engine service."""
        self.ai_service = ai_service
        logger.info("🔧 RecommendationEngineService initialized")

    async def generate_recommendation(
        self,
        github_data: Dict[str, Any],
        recommendation_type: str = "professional",
        tone: str = "professional",
        length: str = "medium",
        custom_prompt: Optional[str] = None,
        target_role: Optional[str] = None,
        specific_skills: Optional[List[str]] = None,
        exclude_keywords: Optional[List[str]] = None,
        analysis_context_type: str = "profile",
        repository_url: Optional[str] = None,
        force_refresh: bool = False,
    ) -> Dict[str, Any]:
        """Generate a new recommendation using AI."""
        logger.info("🤖 Generating AI recommendation...")

        ai_result = await self.ai_service.generate_recommendation(
            github_data=github_data,
            recommendation_type=recommendation_type,
            tone=tone,
            length=length,
            custom_prompt=custom_prompt,
            target_role=target_role,
            specific_skills=specific_skills,
            exclude_keywords=exclude_keywords,
            analysis_context_type=analysis_context_type,
            repository_url=repository_url,
            force_refresh=force_refresh,
        )

        logger.info("✅ AI recommendation generated successfully")
        return ai_result

    async def regenerate_recommendation(
        self,
        original_content: str,
        refinement_instructions: str,
        github_data: Dict[str, Any],
        recommendation_type: str = "professional",
        tone: str = "professional",
        length: str = "medium",
        analysis_context_type: str = "profile",
        repository_url: Optional[str] = None,
        force_refresh: bool = False,
        display_name: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Regenerate a recommendation with refinement instructions."""
        logger.info("🔄 Regenerating AI recommendation...")

        ai_result = await self.ai_service.regenerate_recommendation(
            original_content=original_content,
            refinement_instructions=refinement_instructions,
            github_data=github_data,
            recommendation_type=recommendation_type,
            tone=tone,
            length=length,
            display_name=display_name,
        )

        logger.info("✅ AI recommendation regenerated successfully")
        return ai_result

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
    ) -> Dict[str, Any]:
        """Refine a recommendation with keywords."""
        logger.info("🔧 Refining AI recommendation with keywords...")

        ai_result = await self.ai_service.refine_recommendation_with_keywords(
            original_content=original_content,
            refinement_instructions=refinement_instructions,
            github_data=github_data,
            recommendation_type=recommendation_type,
            tone=tone,
            length=length,
            include_keywords=include_keywords,
            exclude_keywords=exclude_keywords,
        )

        logger.info("✅ AI recommendation refined successfully")
        return ai_result

    def create_recommendation_data(
        self,
        ai_result: Dict[str, Any],
        github_profile_id: int,
        recommendation_type: str,
        tone: str,
        length: str,
    ) -> RecommendationCreate:
        """Create recommendation data structure from AI result."""
        logger.info("📝 Creating recommendation data structure...")

        recommendation_data = RecommendationCreate(
            github_profile_id=github_profile_id,
            title=ai_result.get("title", "LinkedIn Recommendation"),
            content=ai_result.get("content", "Recommendation content not available"),
            recommendation_type=recommendation_type,
            tone=tone,
            length=length,
            ai_model=ai_result.get("generation_parameters", {}).get("model", "unknown"),
            generation_prompt=ai_result.get("generation_prompt"),
            generation_parameters=ai_result.get("generation_parameters", {}),
            word_count=ai_result.get("word_count", 0),
        )

        logger.info("✅ Recommendation data structure created")
        return recommendation_data

    async def generate_recommendation_options(
        self,
        github_data: Dict[str, Any],
        base_recommendation_type: str = "professional",
        base_tone: str = "professional",
        base_length: str = "medium",
        target_role: Optional[str] = None,
        specific_skills: Optional[List[str]] = None,
        force_refresh: bool = False,
    ) -> RecommendationOptionsResponse:
        """Generate multiple recommendation options with variations."""
        logger.info("🎯 Generating recommendation options...")

        options = []
        variations = [
            {"tone": "professional", "length": "medium"},
            {"tone": "friendly", "length": "medium"},
            {"tone": "formal", "length": "long"},
            {"tone": "casual", "length": "short"},
        ]

        for i, variation in enumerate(variations, 1):
            logger.info(f"📝 Generating option {i}...")

            ai_result = await self.ai_service.generate_recommendation(
                github_data=github_data,
                recommendation_type=base_recommendation_type,
                tone=variation["tone"],
                length=variation["length"],
                target_role=target_role,
                specific_skills=specific_skills,
                force_refresh=force_refresh,  # Pass force_refresh
            )

            option = RecommendationOption(
                id=i,
                name=ai_result.get("name", f"Option {i}"),
                title=ai_result.get("title", f"Recommendation Option {i}"),
                content=ai_result.get("content", "Recommendation content not available"),
                focus=ai_result.get("focus", f"{variation['tone']} focus"),
                explanation=ai_result.get("explanation", f"Best for {variation['tone']} communications"),
                word_count=ai_result.get("word_count", 0),
            )
            options.append(option)

        logger.info(f"✅ Generated {len(options)} recommendation options")
        return RecommendationOptionsResponse(options=options)

    async def create_recommendation_from_option(
        self,
        db: AsyncSession,
        github_profile_id: int,
        option: RecommendationOption,
        recommendation_type: str = "professional",
    ) -> RecommendationResponse:
        """Create a recommendation from a selected option."""
        logger.info("💾 Creating recommendation from selected option...")

        recommendation_data = RecommendationCreate(
            github_profile_id=github_profile_id,
            title=option.title,
            content=option.content,
            recommendation_type=recommendation_type,
            ai_model="test-model",  # Default model since option doesn't have generation_parameters
            generation_parameters={"model": "test-model"},
            word_count=option.word_count,
        )

        recommendation = Recommendation(**recommendation_data.dict())
        db.add(recommendation)
        await db.commit()
        await db.refresh(recommendation)

        response = RecommendationResponse.from_orm(recommendation)
        logger.info("✅ Recommendation created from option")
        return response

    def analyze_recommendation_quality(self, content: str, word_count: int) -> Dict[str, Any]:
        """Analyze the quality of generated recommendation content."""
        logger.info("📊 Analyzing recommendation quality...")

        # Basic quality metrics
        quality_score = 0
        issues = []
        suggestions = []

        # Length analysis
        if word_count < 50:
            issues.append("Content is too short")
            suggestions.append("Consider adding more specific examples from the profile")
            quality_score -= 20
        elif word_count > 500:
            issues.append("Content is too long")
            suggestions.append("Consider condensing to focus on key strengths")
            quality_score -= 10
        else:
            quality_score += 10

        # Content analysis
        if len(content.split(".")) < 3:
            issues.append("Content lacks structure")
            suggestions.append("Consider breaking content into clear paragraphs")
            quality_score -= 15

        # Placeholder for more sophisticated analysis
        if "GitHub" not in content and "repository" not in content:
            suggestions.append("Consider mentioning specific GitHub projects or contributions")

        if "skills" not in content.lower() and "technologies" not in content.lower():
            suggestions.append("Consider highlighting technical skills more prominently")

        # Calculate final score
        quality_score = max(0, min(100, 70 + quality_score))  # Base score of 70

        result = {
            "quality_score": quality_score,
            "issues": issues,
            "suggestions": suggestions,
            "structure_score": len(content.split(".")) * 5,  # Rough structure metric
        }

        logger.info(f"✅ Quality analysis complete - Score: {quality_score}")
        return result
