"""Recommendation API endpoints."""

import logging
from typing import Optional, Union

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.auth import get_current_active_user
from app.core.dependencies import (
    AnonymousUser,
    PaginationParams,
    check_generation_limit,
    get_current_user_optional,
    get_database_session,
    get_pagination_params,
    get_recommendation_service,
    increment_generation_count,
)
from app.models.user import User
from app.schemas.recommendation import (
    KeywordRefinementRequest,
    KeywordRefinementResponse,
    ReadmeGenerationRequest,
    ReadmeGenerationResponse,
    RecommendationFromOptionRequest,
    RecommendationListResponse,
    RecommendationOptionsResponse,
    RecommendationRequest,
    RecommendationResponse,
    RecommendationVersionHistoryResponse,
    RevertToVersionRequest,
    SkillGapAnalysisRequest,
    SkillGapAnalysisResponse,
    VersionComparisonResponse,
)
from app.services.recommendation_service import RecommendationService

logger = logging.getLogger(__name__)

router = APIRouter()

# Role-based recommendation limits
DEFAULT_LIMITS = {"free": 5, "premium": 10, "admin": float("inf"), "anonymous": 3}  # Updated limits


async def check_recommendation_limit_only(
    db: AsyncSession,
    user: Union[User, AnonymousUser],
) -> None:
    """Checks user's daily recommendation limit WITHOUT incrementing the counter."""
    # Use the new unified limit checking function
    await check_generation_limit(user, db)


async def increment_recommendation_count(
    db: AsyncSession,
    user: Union[User, AnonymousUser],
    request: Request,
) -> None:
    """Increments the user's recommendation count after successful generation."""
    # Use the new unified increment function
    await increment_generation_count(user, request, db)


async def check_and_update_recommendation_limit(
    db: AsyncSession,
    user: Union[User, AnonymousUser],
    request: Request,
) -> None:
    """Legacy function - kept for backward compatibility."""
    await check_recommendation_limit_only(db, user)
    await increment_recommendation_count(db, user, request)


@router.post("/generate", response_model=RecommendationResponse)
async def generate_recommendation(
    request: RecommendationRequest,
    req: Request,
    db: AsyncSession = Depends(get_database_session),
    recommendation_service: RecommendationService = Depends(get_recommendation_service),
    current_user: Union[User, AnonymousUser] = Depends(get_current_user_optional),
) -> RecommendationResponse:
    """Generate a new LinkedIn recommendation."""

    # Check limit but don't increment yet
    await check_recommendation_limit_only(db, current_user)

    user_type = "authenticated" if isinstance(current_user, User) else "anonymous"
    user_id = current_user.id if isinstance(current_user, User) else None

    logger.info("=" * 80)
    logger.info("🚀 RECOMMENDATION GENERATION STARTED")
    logger.info("=" * 80)
    logger.info(f"👤 User: {current_user.username} (ID: {current_user.id}, Type: {user_type})")
    logger.info("📋 Request Details:")
    logger.info(f"   • GitHub Username: {request.github_username}")
    logger.info(f"   • Type: {request.recommendation_type}")
    logger.info(f"   • Tone: {request.tone}")
    logger.info(f"   • Length: {request.length}")
    logger.info(f"   • Custom Prompt: {'Yes' if request.custom_prompt else 'No'}")
    logger.info(f"   • Specific Skills: " f"{len(request.include_specific_skills or [])} skills")

    try:
        logger.info("🎯 Starting recommendation creation process...")
        recommendation = await recommendation_service.create_recommendation(
            db=db,
            user_id=user_id,  # Can be None for anonymous users
            github_username=request.github_username,
            recommendation_type=request.recommendation_type,
            tone=request.tone,
            length=request.length,
            custom_prompt=request.custom_prompt,
            target_role=request.target_role,
            specific_skills=request.include_specific_skills,
            include_keywords=request.include_keywords,
            exclude_keywords=request.exclude_keywords,
        )

        # Only increment after successful generation
        await increment_recommendation_count(db, current_user, req)

        logger.info("✅ RECOMMENDATION GENERATION COMPLETED SUCCESSFULLY")
        logger.info("📊 Final Stats:")
        logger.info(f"   • Word Count: {recommendation.word_count}")
        logger.info(f"   • Title: {recommendation.title[:50]}...")
        logger.info("=" * 80)

        return recommendation

    except ValueError as e:
        logger.error(f"❌ Validation Error: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise  # Re-raise HTTPException directly
    except Exception as e:
        logger.error(f"💥 CRITICAL ERROR generating recommendation: {e}")
        logger.error("=" * 80)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/generate-options", response_model=RecommendationOptionsResponse)
async def generate_recommendation_options(
    request: RecommendationRequest,
    req: Request,
    db: AsyncSession = Depends(get_database_session),
    recommendation_service: RecommendationService = Depends(get_recommendation_service),
    current_user: Union[User, AnonymousUser] = Depends(get_current_user_optional),
) -> RecommendationOptionsResponse:
    """Generate multiple recommendation options."""

    # Check limit but don't increment yet
    await check_recommendation_limit_only(db, current_user)

    user_type = "authenticated" if isinstance(current_user, User) else "anonymous"
    user_id = current_user.id if isinstance(current_user, User) else None

    logger.info("=" * 80)
    logger.info("🎭 MULTIPLE RECOMMENDATION OPTIONS GENERATION STARTED")
    logger.info("=" * 80)
    logger.info(f"👤 User: {current_user.username} (ID: {current_user.id}, Type: {user_type})")
    logger.info("📋 Request Details:")
    logger.info(f"   • GitHub Username: {request.github_username}")
    logger.info(f"   • Type: {request.recommendation_type}")
    logger.info(f"   • Tone: {request.tone}")
    logger.info(f"   • Length: {request.length}")
    logger.info(f"   • Custom Prompt: {'Yes' if request.custom_prompt else 'No'}")

    try:
        logger.info("🎯 Starting multiple options generation process...")
        options_response = await recommendation_service.create_recommendation_options(
            db=db,
            user_id=user_id,  # Can be None for anonymous users
            github_username=request.github_username,
            recommendation_type=request.recommendation_type,
            tone=request.tone,
            length=request.length,
            custom_prompt=request.custom_prompt,
            target_role=request.target_role,
            specific_skills=request.include_specific_skills,
            include_keywords=request.include_keywords,
            exclude_keywords=request.exclude_keywords,
            analysis_context_type=getattr(request, "analysis_context_type", "profile"),
            repository_url=getattr(request, "repository_url", None),
        )

        # Only increment after successful generation
        await increment_recommendation_count(db, current_user, req)

        logger.info("✅ MULTIPLE OPTIONS GENERATION COMPLETED SUCCESSFULLY")
        logger.info("📊 Final Stats:")
        logger.info(f"   • Options Generated: {len(options_response.options)}")
        logger.info("=" * 80)

        return options_response

    except ValueError as e:
        logger.error(f"❌ Validation Error: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise  # Re-raise HTTPException directly
    except Exception as e:
        logger.error(f"💥 CRITICAL ERROR generating options: {e}")
        logger.error("=" * 80)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/refine-keywords", response_model=KeywordRefinementResponse)
async def refine_recommendation_with_keywords(
    request: KeywordRefinementRequest,
    db: AsyncSession = Depends(get_database_session),
    recommendation_service: RecommendationService = Depends(get_recommendation_service),
):
    """Refine an existing recommendation based on keyword constraints."""
    try:
        logger.info("🔧 KEYWORD REFINEMENT API REQUEST")
        logger.info("=" * 80)
        logger.info(f"📝 Recommendation ID: {request.recommendation_id}")
        logger.info(f"➕ Include keywords: {request.include_keywords}")
        logger.info(f"➖ Exclude keywords: {request.exclude_keywords}")

        refined_recommendation = await recommendation_service.refine_recommendation_with_keywords(
            db=db,
            recommendation_id=request.recommendation_id,
            include_keywords=request.include_keywords,
            exclude_keywords=request.exclude_keywords,
            refinement_instructions=request.refinement_instructions,
        )

        logger.info("✅ KEYWORD REFINEMENT API COMPLETED SUCCESSFULLY")
        logger.info("📊 Final Results:")
        logger.info(f"   • Refined recommendation ID: {refined_recommendation['id']}")
        logger.info("=" * 80)

        return refined_recommendation

    except ValueError as e:
        logger.error(f"❌ Validation Error: {e}")
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"💥 CRITICAL ERROR in keyword refinement: {e}")
        logger.error("=" * 80)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/generate-readme", response_model=ReadmeGenerationResponse)
async def generate_repository_readme(
    request: ReadmeGenerationRequest,
    recommendation_service: RecommendationService = Depends(get_recommendation_service),
):
    """Generate a README.md file for a GitHub repository."""
    try:
        logger.info("📖 README GENERATION API REQUEST")
        logger.info("=" * 80)
        logger.info(f"📁 Repository: {request.repository_full_name}")
        logger.info(f"🎨 Style: {request.style}")
        logger.info(f"👥 Target Audience: {request.target_audience}")
        logger.info(f"📋 Include Sections: {request.include_sections or []}")

        readme_result = await recommendation_service.generate_repository_readme(
            repository_full_name=request.repository_full_name,
            style=request.style,
            include_sections=request.include_sections,
            target_audience=request.target_audience or "developers",
        )

        logger.info("✅ README GENERATION API COMPLETED SUCCESSFULLY")
        logger.info("📊 Final Results:")
        logger.info(f"   • Repository: {readme_result['repository_full_name']}")
        logger.info(f"   • Generated Content: {readme_result['word_count']} words")
        logger.info(f"   • Sections: {len(readme_result['sections'])}")
        logger.info("=" * 80)

        return ReadmeGenerationResponse(
            repository_name=readme_result["repository_name"],
            repository_full_name=readme_result["repository_full_name"],
            generated_content=readme_result["generated_content"],
            sections=readme_result["sections"],
            word_count=readme_result["word_count"],
            generation_parameters=readme_result["generation_parameters"],
            analysis_summary=readme_result["analysis_summary"],
        )

    except ValueError as e:
        logger.error(f"❌ Validation Error: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"💥 CRITICAL ERROR in README generation: {e}")
        logger.error("=" * 80)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/analyze-skill-gaps", response_model=SkillGapAnalysisResponse)
async def analyze_skill_gaps(
    request: SkillGapAnalysisRequest,
    recommendation_service: RecommendationService = Depends(get_recommendation_service),
):
    """Analyze skill gaps for a target role."""
    try:
        logger.info("📊 SKILL GAP ANALYSIS API REQUEST")
        logger.info("=" * 80)
        logger.info(f"👤 GitHub Username: {request.github_username}")
        logger.info(f"🎯 Target Role: {request.target_role}")
        logger.info(f"🏢 Industry: {request.industry}")
        logger.info(f"📈 Experience Level: {request.experience_level}")

        skill_analysis = await recommendation_service.analyze_skill_gaps(request)

        logger.info("✅ SKILL GAP ANALYSIS COMPLETED SUCCESSFULLY")
        logger.info("📊 Final Results:")
        logger.info(f"   • Overall Match Score: {skill_analysis.overall_match_score}%")
        logger.info(f"   • Strengths Identified: {len(skill_analysis.strengths)}")
        logger.info(f"   • Gaps Identified: {len(skill_analysis.gaps)}")
        logger.info(f"   • Recommendations: {len(skill_analysis.recommendations)}")
        logger.info("=" * 80)

        return skill_analysis

    except ValueError as e:
        logger.error(f"❌ Validation Error: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"💥 CRITICAL ERROR in skill gap analysis: {e}")
        logger.error("=" * 80)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/{recommendation_id}/versions", response_model=RecommendationVersionHistoryResponse)
async def get_recommendation_version_history(
    recommendation_id: int,
    db: AsyncSession = Depends(get_database_session),
    recommendation_service: RecommendationService = Depends(get_recommendation_service),
):
    """Get the version history for a recommendation."""
    try:
        logger.info(f"📖 VERSION HISTORY REQUEST for recommendation {recommendation_id}")

        version_history = await recommendation_service.get_recommendation_version_history(
            db=db,
            recommendation_id=recommendation_id,
        )

        logger.info(f"✅ VERSION HISTORY RETRIEVED: {version_history.total_versions} versions")
        return version_history

    except ValueError as e:
        logger.error(f"❌ Validation Error: {e}")
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"💥 CRITICAL ERROR retrieving version history: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/{recommendation_id}/versions/compare", response_model=VersionComparisonResponse)
async def compare_recommendation_versions(
    recommendation_id: int,
    version_a_id: int,
    version_b_id: int,
    db: AsyncSession = Depends(get_database_session),
    recommendation_service: RecommendationService = Depends(get_recommendation_service),
):
    """Compare two versions of a recommendation."""
    try:
        logger.info(f"🔍 VERSION COMPARISON REQUEST for recommendation {recommendation_id}")
        logger.info(f"   • Version A: {version_a_id}")
        logger.info(f"   • Version B: {version_b_id}")

        comparison = await recommendation_service.compare_recommendation_versions(
            db=db,
            recommendation_id=recommendation_id,
            version_a_id=version_a_id,
            version_b_id=version_b_id,
        )

        logger.info("✅ VERSION COMPARISON COMPLETED")
        return comparison

    except ValueError as e:
        logger.error(f"❌ Validation Error: {e}")
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"💥 CRITICAL ERROR comparing versions: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/{recommendation_id}/versions/revert", response_model=RecommendationResponse)
async def revert_recommendation_to_version(
    recommendation_id: int,
    request: RevertToVersionRequest,
    db: AsyncSession = Depends(get_database_session),
    recommendation_service: RecommendationService = Depends(get_recommendation_service),
):
    """Revert a recommendation to a specific version."""
    try:
        logger.info(f"🔄 VERSION REVERT REQUEST for recommendation {recommendation_id}")
        logger.info(f"   • Target Version: {request.version_id}")
        logger.info(f"   • Reason: {request.revert_reason or 'Not specified'}")

        reverted_recommendation = await recommendation_service.revert_recommendation_to_version(
            db=db,
            recommendation_id=recommendation_id,
            version_id=request.version_id,
            revert_reason=request.revert_reason,
        )

        logger.info(f"✅ RECOMMENDATION REVERTED to version (ID: {request.version_id})")
        return reverted_recommendation

    except ValueError as e:
        logger.error(f"❌ Validation Error: {e}")
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"💥 CRITICAL ERROR reverting version: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/create-from-option", response_model=RecommendationResponse)
async def create_recommendation_from_option(
    request: RecommendationFromOptionRequest,
    req: Request,
    db: AsyncSession = Depends(get_database_session),
    recommendation_service: RecommendationService = Depends(get_recommendation_service),
    current_user: Union[User, AnonymousUser] = Depends(get_current_user_optional),
) -> RecommendationResponse:
    """Create a recommendation from a selected option."""

    # Check limit but don't increment yet
    await check_recommendation_limit_only(db, current_user)

    user_type = "authenticated" if isinstance(current_user, User) else "anonymous"
    user_id = current_user.id if isinstance(current_user, User) else None

    logger.info("=" * 80)
    logger.info("🎯 RECOMMENDATION CREATION FROM SELECTED OPTION STARTED")
    logger.info("=" * 80)
    logger.info(f"👤 User: {current_user.username} (ID: {current_user.id}, Type: {user_type})")
    logger.info("📋 Request Details:")
    logger.info(f"   • GitHub Username: {request.github_username}")
    logger.info(f"   • Selected Option: {request.selected_option.name}")
    logger.info(f"   • Option Focus: {request.selected_option.focus}")
    logger.info(f"   • Total Options Generated: {len(request.all_options)}")

    try:
        logger.info("🎯 Starting recommendation creation from selected option...")
        recommendation = await recommendation_service.create_recommendation_from_option(
            db=db,
            user_id=user_id,  # Can be None for anonymous users
            github_username=request.github_username,
            selected_option=request.selected_option.model_dump(),
            all_options=[option.model_dump() for option in request.all_options],
            analysis_context_type=request.analysis_context_type or "profile",
            repository_url=request.repository_url,
        )

        # Only increment after successful generation
        await increment_recommendation_count(db, current_user, req)

        logger.info("✅ RECOMMENDATION CREATION FROM OPTION COMPLETED SUCCESSFULLY")
        logger.info("📊 Final Stats:")
        logger.info(f"   • Word Count: {recommendation.word_count}")
        logger.info(f"   • Selected Option: {request.selected_option.name}")
        logger.info("=" * 80)

        return recommendation

    except ValueError as e:
        logger.error(f"❌ Validation Error: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise  # Re-raise HTTPException directly
    except Exception as e:
        logger.error(f"💥 CRITICAL ERROR creating recommendation from option: {e}")
        logger.error("=" * 80)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/regenerate", response_model=RecommendationResponse)
async def regenerate_recommendation(
    request: dict,  # Will contain original content and refinement instructions
    req: Request,
    db: AsyncSession = Depends(get_database_session),
    recommendation_service: RecommendationService = Depends(get_recommendation_service),
    current_user: Union[User, AnonymousUser] = Depends(get_current_user_optional),
) -> RecommendationResponse:
    """Regenerate a recommendation with refinement instructions."""

    # Check limit but don't increment yet
    await check_recommendation_limit_only(db, current_user)

    user_type = "authenticated" if isinstance(current_user, User) else "anonymous"
    user_id = current_user.id if isinstance(current_user, User) else None

    logger.info("=" * 80)
    logger.info("🔄 RECOMMENDATION REGENERATION STARTED")
    logger.info("=" * 80)
    logger.info(f"👤 User: {current_user.username} (ID: {current_user.id}, Type: {user_type})")

    try:
        original_content = request.get("original_content")
        refinement_instructions = request.get("refinement_instructions")
        github_username = request.get("github_username")
        recommendation_type = request.get("recommendation_type", "professional")
        tone = request.get("tone", "professional")
        length = request.get("length", "medium")

        if not original_content or not refinement_instructions or not github_username:
            raise HTTPException(status_code=400, detail="Missing required fields")

        logger.info("📋 Regeneration Details:")
        logger.info(f"   • GitHub Username: {github_username}")
        logger.info(f"   • Type: {recommendation_type}")
        logger.info(f"   • Tone: {tone}")
        logger.info(f"   • Length: {length}")
        logger.info(f"   • Original Content Length: {len(original_content)} characters")
        logger.info(f"   • Refinement Instructions: {refinement_instructions[:100]}...")

        recommendation = await recommendation_service.regenerate_recommendation(
            db=db,
            user_id=user_id,  # Can be None for anonymous users
            original_content=original_content,
            refinement_instructions=refinement_instructions,
            github_username=github_username,
            recommendation_type=recommendation_type,
            tone=tone,
            length=length,
        )

        # Only increment after successful generation
        await increment_recommendation_count(db, current_user, req)

        logger.info("✅ RECOMMENDATION REGENERATION COMPLETED SUCCESSFULLY")
        logger.info("📊 Final Stats:")
        logger.info(f"   • Word Count: {recommendation.word_count}")
        logger.info("=" * 80)

        return recommendation

    except ValueError as e:
        logger.error(f"❌ Validation Error: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise  # Re-raise HTTPException directly
    except Exception as e:
        logger.error(f"💥 CRITICAL ERROR regenerating recommendation: {e}")
        logger.error("=" * 80)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/", response_model=RecommendationListResponse)
async def list_recommendations(
    github_username: Optional[str] = Query(None, description="Filter by GitHub username"),
    recommendation_type: Optional[str] = Query(None, description="Filter by recommendation type"),
    pagination: PaginationParams = Depends(get_pagination_params),
    db: AsyncSession = Depends(get_database_session),
    recommendation_service: RecommendationService = Depends(get_recommendation_service),
    current_user: User = Depends(get_current_active_user),
) -> RecommendationListResponse:
    """List recommendations with optional filtering."""

    try:
        recommendations = await recommendation_service.get_recommendations(
            db=db,
            user_id=current_user.id,  # type: ignore # Filter by user ID
            github_username=github_username,
            recommendation_type=recommendation_type,
            limit=pagination.limit,
            offset=pagination.offset,
        )

        # TODO: Get total count for proper pagination
        total = len(recommendations)  # Simplified for now

        return RecommendationListResponse(
            recommendations=recommendations,
            total=total,
            page=pagination.page,
            page_size=pagination.page_size,
        )

    except Exception as e:
        logger.error(f"Error listing recommendations: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/{recommendation_id}", response_model=RecommendationResponse)
async def get_recommendation(
    recommendation_id: int,
    db: AsyncSession = Depends(get_database_session),
    recommendation_service: RecommendationService = Depends(get_recommendation_service),
    current_user: User = Depends(get_current_active_user),
) -> RecommendationResponse:
    """Get a specific recommendation by ID."""

    try:
        recommendation = await recommendation_service.get_recommendation_by_id(db=db, recommendation_id=recommendation_id, user_id=current_user.id)  # type: ignore

        if not recommendation:
            raise HTTPException(
                status_code=404,
                detail=f"Recommendation with ID {recommendation_id} not found",
            )

        return recommendation

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting recommendation {recommendation_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.delete("/{recommendation_id}")
async def delete_recommendation(
    recommendation_id: int,
    db: AsyncSession = Depends(get_database_session),
    recommendation_service: RecommendationService = Depends(get_recommendation_service),
    current_user: User = Depends(get_current_active_user),
) -> dict:
    """Delete a recommendation."""

    try:
        # TODO: Implement deletion logic
        raise HTTPException(status_code=501, detail="Not implemented yet")

    except Exception as e:
        logger.error(f"Error deleting recommendation {recommendation_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
