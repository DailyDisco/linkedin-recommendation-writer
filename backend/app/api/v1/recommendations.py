"""Recommendation API endpoints."""

import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import PaginationParams, get_database_session, get_pagination_params, get_recommendation_service
from app.schemas.recommendation import (
    RecommendationFromOptionRequest,
    RecommendationListResponse,
    RecommendationOptionsResponse,
    RecommendationRequest,
    RecommendationResponse,
)
from app.services.recommendation_service import RecommendationService

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/generate", response_model=RecommendationResponse)
async def generate_recommendation(
    request: RecommendationRequest,
    db: AsyncSession = Depends(get_database_session),
    recommendation_service: RecommendationService = Depends(get_recommendation_service),
) -> RecommendationResponse:
    """Generate a new LinkedIn recommendation."""

    logger.info("=" * 80)
    logger.info("🚀 RECOMMENDATION GENERATION STARTED")
    logger.info("=" * 80)
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
            github_username=request.github_username,
            recommendation_type=request.recommendation_type,
            tone=request.tone,
            length=request.length,
            custom_prompt=request.custom_prompt,
            target_role=request.target_role,
            specific_skills=request.include_specific_skills,
        )

        logger.info("✅ RECOMMENDATION GENERATION COMPLETED SUCCESSFULLY")
        logger.info("📊 Final Stats:")
        logger.info(f"   • Word Count: {recommendation.word_count}")
        logger.info(f"   • Confidence Score: {recommendation.confidence_score}")
        logger.info(f"   • Title: {recommendation.title[:50]}...")
        logger.info("=" * 80)

        return recommendation

    except ValueError as e:
        logger.error(f"❌ Validation Error: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"💥 CRITICAL ERROR generating recommendation: {e}")
        logger.error("=" * 80)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/generate-options", response_model=RecommendationOptionsResponse)
async def generate_recommendation_options(
    request: RecommendationRequest,
    db: AsyncSession = Depends(get_database_session),
    recommendation_service: RecommendationService = Depends(get_recommendation_service),
) -> RecommendationOptionsResponse:
    """Generate multiple recommendation options."""

    logger.info("=" * 80)
    logger.info("🎭 MULTIPLE RECOMMENDATION OPTIONS GENERATION STARTED")
    logger.info("=" * 80)
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
            github_username=request.github_username,
            recommendation_type=request.recommendation_type,
            tone=request.tone,
            length=request.length,
            custom_prompt=request.custom_prompt,
            target_role=request.target_role,
            specific_skills=request.include_specific_skills,
            analysis_type=getattr(request, "analysis_type", "profile"),
            repository_url=getattr(request, "repository_url", None),
        )

        logger.info("✅ MULTIPLE OPTIONS GENERATION COMPLETED SUCCESSFULLY")
        logger.info("📊 Final Stats:")
        logger.info(f"   • Options Generated: {len(options_response.options)}")
        logger.info("=" * 80)

        return options_response

    except ValueError as e:
        logger.error(f"❌ Validation Error: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"💥 CRITICAL ERROR generating options: {e}")
        logger.error("=" * 80)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/create-from-option", response_model=RecommendationResponse)
async def create_recommendation_from_option(
    request: RecommendationFromOptionRequest,
    db: AsyncSession = Depends(get_database_session),
    recommendation_service: RecommendationService = Depends(get_recommendation_service),
) -> RecommendationResponse:
    """Create a recommendation from a selected option."""

    logger.info("=" * 80)
    logger.info("🎯 RECOMMENDATION CREATION FROM SELECTED OPTION STARTED")
    logger.info("=" * 80)
    logger.info("📋 Request Details:")
    logger.info(f"   • GitHub Username: {request.github_username}")
    logger.info(f"   • Selected Option: {request.selected_option.name}")
    logger.info(f"   • Option Focus: {request.selected_option.focus}")
    logger.info(f"   • Total Options Generated: {len(request.all_options)}")

    try:
        logger.info("🎯 Starting recommendation creation from selected option...")
        recommendation = await recommendation_service.create_recommendation_from_option(
            db=db,
            github_username=request.github_username,
            selected_option=request.selected_option.model_dump(),
            all_options=[option.model_dump() for option in request.all_options],
            analysis_type=request.analysis_type or "profile",
            repository_url=request.repository_url,
        )

        logger.info("✅ RECOMMENDATION CREATION FROM OPTION COMPLETED SUCCESSFULLY")
        logger.info("📊 Final Stats:")
        logger.info(f"   • Word Count: {recommendation.word_count}")
        logger.info(f"   • Confidence Score: {recommendation.confidence_score}")
        logger.info(f"   • Selected Option: {request.selected_option.name}")
        logger.info("=" * 80)

        return recommendation

    except ValueError as e:
        logger.error(f"❌ Validation Error: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"💥 CRITICAL ERROR creating recommendation from option: {e}")
        logger.error("=" * 80)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/regenerate", response_model=RecommendationResponse)
async def regenerate_recommendation(
    request: dict,  # Will contain original content and refinement instructions
    db: AsyncSession = Depends(get_database_session),
    recommendation_service: RecommendationService = Depends(get_recommendation_service),
) -> RecommendationResponse:
    """Regenerate a recommendation with refinement instructions."""

    logger.info("=" * 80)
    logger.info("🔄 RECOMMENDATION REGENERATION STARTED")
    logger.info("=" * 80)

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
            original_content=original_content,
            refinement_instructions=refinement_instructions,
            github_username=github_username,
            recommendation_type=recommendation_type,
            tone=tone,
            length=length,
        )

        logger.info("✅ RECOMMENDATION REGENERATION COMPLETED SUCCESSFULLY")
        logger.info("📊 Final Stats:")
        logger.info(f"   • Word Count: {recommendation.word_count}")
        logger.info(f"   • Confidence Score: {recommendation.confidence_score}")
        logger.info("=" * 80)

        return recommendation

    except ValueError as e:
        logger.error(f"❌ Validation Error: {e}")
        raise HTTPException(status_code=400, detail=str(e))
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
) -> RecommendationListResponse:
    """List recommendations with optional filtering."""

    try:
        recommendations = await recommendation_service.get_recommendations(
            db=db,
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
) -> RecommendationResponse:
    """Get a specific recommendation by ID."""

    try:
        recommendation = await recommendation_service.get_recommendation_by_id(db=db, recommendation_id=recommendation_id)

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
) -> dict:
    """Delete a recommendation."""

    try:
        # TODO: Implement deletion logic
        raise HTTPException(status_code=501, detail="Not implemented yet")

    except Exception as e:
        logger.error(f"Error deleting recommendation {recommendation_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
