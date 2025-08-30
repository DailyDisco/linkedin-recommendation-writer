"""Service for managing recommendations."""

import logging
import time
from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.github_profile import GitHubProfile
from app.models.recommendation import Recommendation, RecommendationVersion
from app.schemas.recommendation import (
    ContributorInfo,
    MultiContributorRequest,
    MultiContributorResponse,
    RecommendationCreate,
    RecommendationOptionsResponse,
    RecommendationResponse,
    RecommendationVersionDetail,
    RecommendationVersionHistoryResponse,
    RecommendationVersionInfo,
    SkillGapAnalysisRequest,
    SkillGapAnalysisResponse,
    SkillMatch,
    VersionComparisonResponse,
)
from app.services.ai_service import AIService
from app.services.github_commit_service import GitHubCommitService
from app.services.github_repository_service import GitHubRepositoryService
from app.services.github_user_service import GitHubUserService

logger = logging.getLogger(__name__)


def parse_datetime(dt: Any) -> Any:
    """Parse datetime string or object, ensuring offset-naive result."""
    if isinstance(dt, str):
        parsed_dt = datetime.fromisoformat(dt)
        # Remove timezone info to make it offset-naive for PostgreSQL
        if parsed_dt.tzinfo is not None:
            parsed_dt = parsed_dt.replace(tzinfo=None)
        return parsed_dt
    elif isinstance(dt, datetime):
        # If it's already a datetime object, ensure it's offset-naive
        if dt.tzinfo is not None:
            return dt.replace(tzinfo=None)
        return dt
    return dt


class RecommendationService:
    """Service for managing recommendations."""

    def __init__(self) -> None:
        """Initialize recommendation service."""
        self.github_service = GitHubUserService(GitHubCommitService())
        self.repository_service = GitHubRepositoryService(GitHubCommitService())
        self.ai_service = AIService()

    async def create_recommendation(
        self,
        db: AsyncSession,
        github_username: str,
        user_id: Optional[int] = None,  # Added user_id
        recommendation_type: str = "professional",
        tone: str = "professional",
        length: str = "medium",
        custom_prompt: Optional[str] = None,
        target_role: Optional[str] = None,
        specific_skills: Optional[List[str]] = None,
        include_keywords: Optional[List[str]] = None,
        exclude_keywords: Optional[List[str]] = None,
    ) -> RecommendationResponse:
        """Create a new recommendation."""

        import time

        start_time = time.time()

        try:
            logger.info("🔍 STEP 1: GITHUB PROFILE ANALYSIS")
            logger.info("-" * 50)
            github_start = time.time()

            # Analyze GitHub profile
            github_data = await self.github_service.analyze_github_profile(username=github_username, force_refresh=False)

            github_end = time.time()
            logger.info(f"⏱️  GitHub analysis completed in {github_end - github_start:.2f} seconds")

            if not github_data:
                logger.error(f"❌ Failed to analyze GitHub profile for {github_username}")
                raise ValueError(f"Could not analyze GitHub profile for {github_username}")

            logger.info("✅ GitHub analysis successful:")
            logger.info(f"   • Repositories: {len(github_data.get('repositories', []))}")
            logger.info(f"   • Languages: {len(github_data.get('languages', []))}")
            logger.info(f"   • Commits analyzed: {github_data.get('commit_analysis', {}).get('total_commits_analyzed', 0)}")
            logger.debug(f"➡️ GitHub data used for recommendation: {github_data}")  # Log github_data

            # Get or create GitHub profile record
            logger.info("💾 STEP 2: DATABASE OPERATIONS")
            logger.info("-" * 50)
            db_start = time.time()

            github_profile = await self._get_or_create_github_profile(db, github_data)

            db_end = time.time()
            logger.info(f"⏱️  Database operations completed in {db_end - db_start:.2f} seconds")
            logger.info(f"✅ GitHub profile record: {'Updated' if github_profile else 'Created'}")

            # Generate AI recommendation
            logger.info("🤖 STEP 3: AI RECOMMENDATION GENERATION")
            logger.info("-" * 50)
            ai_start = time.time()

            ai_result = await self.ai_service.generate_recommendation(
                github_data=github_data,
                recommendation_type=recommendation_type,
                tone=tone,
                length=length,
                custom_prompt=custom_prompt,
                target_role=target_role,
                specific_skills=specific_skills,
                exclude_keywords=exclude_keywords,
            )

            ai_end = time.time()
            logger.info(f"⏱️  AI generation completed in {ai_end - ai_start:.2f} seconds")
            logger.info("✅ AI recommendation generated:")
            logger.info(f"   • Content length: {len(ai_result['content'])} characters")
            logger.info(f"   • Word count: {ai_result['word_count']}")
            logger.info(f"   • Confidence score: {ai_result['confidence_score']}")

            # Create recommendation record
            logger.info("💾 STEP 4: SAVING RECOMMENDATION")
            logger.info("-" * 50)
            save_start = time.time()

            recommendation_data = RecommendationCreate(
                github_profile_id=github_profile.id,  # type: ignore
                title=ai_result["title"],
                content=ai_result["content"],
                recommendation_type=recommendation_type,
                tone=tone,
                length=length,
                ai_model=ai_result["generation_parameters"]["model"],
                generation_prompt=ai_result.get("generation_prompt"),
                generation_parameters=ai_result["generation_parameters"],
                confidence_score=ai_result["confidence_score"],
                word_count=ai_result["word_count"],
            )

            recommendation = Recommendation(**recommendation_data.dict())
            db.add(recommendation)
            await db.commit()
            await db.refresh(recommendation)

            save_end = time.time()
            logger.info(f"⏱️  Database save completed in {save_end - save_start:.2f} seconds")
            logger.info(f"✅ Recommendation saved with ID: {recommendation.id}")

            # Convert to response
            response = RecommendationResponse.from_orm(recommendation)
            response.github_username = github_username

            end_time = time.time()
            total_time = end_time - start_time

            logger.info("🎉 RECOMMENDATION CREATION SUMMARY")
            logger.info("-" * 50)
            logger.info(f"⏱️  Total processing time: {total_time:.2f} seconds")
            logger.info("📊 Breakdown:")
            logger.info(f"   • GitHub Analysis: {github_end - github_start:.2f}s ({((github_end - github_start)/total_time)*100:.1f}%)")
            logger.info(f"   • Database Ops: {db_end - db_start:.2f}s ({((db_end - db_start)/total_time)*100:.1f}%)")
            logger.info(f"   • AI Generation: {ai_end - ai_start:.2f}s ({((ai_end - ai_start)/total_time)*100:.1f}%)")
            logger.info(f"   • Save Record: {save_end - save_start:.2f}s ({((save_end - save_start)/total_time)*100:.1f}%)")

            return response

        except Exception as e:
            logger.error(f"💥 ERROR in recommendation creation for {github_username}: {e}")
            logger.error(f"⏱️  Failed after {time.time() - start_time:.2f} seconds")
            await db.rollback()
            raise

    async def get_recommendations(
        self,
        db: AsyncSession,
        github_username: Optional[str] = None,
        user_id: Optional[int] = None,  # Added user_id
        recommendation_type: Optional[str] = None,
        limit: int = 10,
        offset: int = 0,
    ) -> List[RecommendationResponse]:
        """Get recommendations with optional filtering."""

        query = select(Recommendation).join(GitHubProfile)

        if user_id:
            query = query.where(Recommendation.user_id == user_id)

        if github_username:
            query = query.where(GitHubProfile.github_username == github_username)

        if recommendation_type:
            query = query.where(Recommendation.recommendation_type == recommendation_type)

        query = query.order_by(desc(Recommendation.created_at)).limit(limit).offset(offset)

        result = await db.execute(query)
        recommendations = result.scalars().all()

        # Convert to responses
        response_list = []
        for rec in recommendations:
            response = RecommendationResponse.from_orm(rec)
            # Get GitHub username
            github_profile_result = await db.execute(select(GitHubProfile.github_username).where(GitHubProfile.id == rec.github_profile_id))
            github_username = github_profile_result.scalar_one_or_none()
            response.github_username = github_username
            response_list.append(response)

        return response_list

    async def get_recommendation_by_id(self, db: AsyncSession, recommendation_id: int, user_id: Optional[int] = None) -> Optional[RecommendationResponse]:
        """Get a specific recommendation by ID."""

        query = select(Recommendation).where(Recommendation.id == recommendation_id)
        if user_id:
            query = query.where(Recommendation.user_id == user_id)

        result = await db.execute(query)
        recommendation = result.scalar_one_or_none()

        if not recommendation:
            return None

        response = RecommendationResponse.from_orm(recommendation)

        # Get GitHub username
        github_profile_result = await db.execute(select(GitHubProfile.github_username).where(GitHubProfile.id == recommendation.github_profile_id))
        github_username = github_profile_result.scalar_one_or_none()
        response.github_username = github_username

        return response

    async def _get_or_create_github_profile(self, db: AsyncSession, github_data: Dict[str, Any]) -> GitHubProfile:
        """Get existing or create new GitHub profile record."""

        # Handle merged repository-contributor data
        if github_data.get("analysis_context_type") == "repository_contributor":
            user_data = github_data["user_data"]
            username = github_data.get("contributor_username", user_data["github_username"])
        else:
            user_data = github_data["user_data"]
            username = user_data["github_username"]

        # Check if profile exists
        query = select(GitHubProfile).where(GitHubProfile.github_username == username)
        result = await db.execute(query)
        existing_profile = result.scalar_one_or_none()

        if existing_profile:
            # Update existing profile - exclude datetime fields for direct assignment
            datetime_fields = {"created_at", "updated_at", "last_analyzed"}
            for key, value in user_data.items():
                if hasattr(existing_profile, key) and key not in datetime_fields:
                    setattr(existing_profile, key, value)

            # Handle datetime fields separately
            if "created_at" in user_data:
                existing_profile.created_at = parse_datetime(user_data["created_at"])
            if "updated_at" in user_data:
                existing_profile.updated_at = parse_datetime(user_data["updated_at"])

            # Update analysis data
            existing_profile.repositories_data = github_data["repositories"]
            existing_profile.languages_data = github_data["languages"]
            existing_profile.skills_analysis = github_data["skills"]
            existing_profile.last_analyzed = parse_datetime(github_data["analyzed_at"])

            await db.commit()
            await db.refresh(existing_profile)
            return existing_profile

        else:
            # Create new profile
            new_profile = GitHubProfile(
                github_username=user_data["github_username"],
                github_id=user_data["github_id"],
                full_name=user_data.get("full_name"),
                bio=user_data.get("bio"),
                company=user_data.get("company"),
                location=user_data.get("location"),
                email=user_data.get("email"),
                blog=user_data.get("blog"),
                avatar_url=user_data.get("avatar_url"),
                public_repos=user_data.get("public_repos", 0),
                followers=user_data.get("followers", 0),
                following=user_data.get("following", 0),
                public_gists=user_data.get("public_gists", 0),
                repositories_data=github_data["repositories"],
                languages_data=github_data["languages"],
                skills_analysis=github_data["skills"],
                last_analyzed=parse_datetime(github_data["analyzed_at"]),
                created_at=(parse_datetime(user_data.get("created_at")) if user_data.get("created_at") else None),
                updated_at=(parse_datetime(user_data.get("updated_at")) if user_data.get("updated_at") else None),
            )

            db.add(new_profile)
            await db.commit()
            await db.refresh(new_profile)
            return new_profile

    async def create_recommendation_options(
        self,
        db: AsyncSession,
        github_username: str,
        user_id: Optional[int] = None,  # Added user_id
        recommendation_type: str = "professional",
        tone: str = "professional",
        length: str = "medium",
        custom_prompt: Optional[str] = None,
        target_role: Optional[str] = None,
        specific_skills: Optional[List[str]] = None,
        include_keywords: Optional[List[str]] = None,
        exclude_keywords: Optional[List[str]] = None,
        analysis_context_type: str = "profile",
        repository_url: Optional[str] = None,
    ) -> RecommendationOptionsResponse:
        """Create multiple recommendation options."""

        import time
        from typing import Optional

        start_time = time.time()

        try:
            logger.info("🎭 STEP 1: GITHUB ANALYSIS")
            logger.info("-" * 50)
            github_start = time.time()

            # Determine analysis type and get GitHub data
            github_data: Optional[Dict[str, Any]] = None
            if analysis_context_type == "repo_only" and repository_url:
                logger.info(f"📁 Analyzing repository: {repository_url}")
                # Extract repository name from URL
                if "/" in repository_url:
                    repo_parts = repository_url.split("/")
                    repo_name = repo_parts[-2] + "/" + repo_parts[-1]
                else:
                    repo_name = repository_url

                # Analyze the repository
                repository_data = await self.repository_service.analyze_repository(repository_full_name=repo_name, force_refresh=False)

                # Analyze the specific contributor's profile
                logger.info(f"👤 Analyzing contributor profile: {github_username}")
                contributor_data = await self.github_service.analyze_github_profile(username=github_username, force_refresh=False)

                # Merge repository and contributor data
                if contributor_data and repository_data:
                    github_data = self._merge_repository_and_contributor_data(repository_data, contributor_data, github_username)
                elif contributor_data:
                    github_data = contributor_data
                else:
                    github_data = repository_data
            else:
                logger.info(f"👤 Analyzing profile: {github_username}")
                github_data = await self.github_service.analyze_github_profile(username=github_username, force_refresh=False)

            github_end = time.time()
            logger.info(f"⏱️  GitHub analysis completed in {github_end - github_start:.2f} seconds")

            if not github_data:
                if analysis_context_type == "repo_only":
                    logger.error(f"❌ Failed to analyze GitHub repository: {repository_url}")
                    raise ValueError(f"Could not analyze GitHub repository: {repository_url}")
                else:
                    logger.error(f"❌ Failed to analyze GitHub profile for {github_username}")
                    raise ValueError(f"Could not analyze GitHub profile for {github_username}")

            if analysis_context_type == "repo_only":
                logger.info("✅ Repository analysis successful:")
                logger.info(f"   • Repository: {github_data.get('repository_info', {}).get('name', 'N/A')}")
                logger.info(f"   • Language: {github_data.get('repository_info', {}).get('language', 'N/A')}")
                logger.info(f"   • Commits analyzed: {len(github_data.get('commits', []))}")
            else:
                logger.info("✅ Profile analysis successful:")
                logger.info(f"   • Repositories: {len(github_data.get('repositories', []))}")
                logger.info(f"   • Languages: {len(github_data.get('languages', []))}")
                logger.info(f"   • Commits analyzed: {github_data.get('commit_analysis', {}).get('total_commits_analyzed', 0)}")
            logger.debug(f"➡️ GitHub data used for recommendation options: {github_data}")  # Log github_data

            # Get or create GitHub profile record
            logger.info("💾 STEP 2: DATABASE OPERATIONS")
            logger.info("-" * 50)
            db_start = time.time()

            github_profile = await self._get_or_create_github_profile(db, github_data)

            db_end = time.time()
            logger.info(f"⏱️  Database operations completed in {db_end - db_start:.2f} seconds")
            logger.info(f"✅ GitHub profile record: {'Updated' if github_profile else 'Created'}")

            # Generate AI recommendation options
            logger.info("🤖 STEP 3: AI RECOMMENDATION OPTIONS GENERATION")
            logger.info("-" * 50)
            ai_start = time.time()

            ai_result = await self.ai_service.generate_recommendation(
                github_data=github_data,
                recommendation_type=recommendation_type,
                tone=tone,
                length=length,
                custom_prompt=custom_prompt,
                target_role=target_role,
                specific_skills=specific_skills,
                exclude_keywords=exclude_keywords,
            )

            ai_end = time.time()
            logger.info(f"⏱️  AI generation completed in {ai_end - ai_start:.2f} seconds")
            logger.info("✅ AI recommendation options generated:")
            logger.info(f"   • Options: {len(ai_result['options'])}")

            end_time = time.time()
            total_time = end_time - start_time

            logger.info("🎉 RECOMMENDATION OPTIONS CREATION SUMMARY")
            logger.info("-" * 50)
            logger.info(f"⏱️  Total processing time: {total_time:.2f} seconds")
            logger.info("📊 Breakdown:")
            logger.info(f"   • GitHub Analysis: {github_end - github_start:.2f}s ({((github_end - github_start)/total_time)*100:.1f}%)")
            logger.info(f"   • Database Ops: {db_end - db_start:.2f}s ({((db_end - db_start)/total_time)*100:.1f}%)")
            logger.info(f"   • AI Generation: {ai_end - ai_start:.2f}s ({((ai_end - ai_start)/total_time)*100:.1f}%)")

            # Convert to response
            response = RecommendationOptionsResponse(
                options=ai_result["options"],
                generation_parameters=ai_result["generation_parameters"],
                generation_prompt=ai_result.get("generation_prompt"),
            )

            return response

        except Exception as e:
            logger.error(f"💥 ERROR in recommendation options creation for {github_username}: {e}")
            logger.error(f"⏱️  Failed after {time.time() - start_time:.2f} seconds")
            await db.rollback()
            raise

    async def regenerate_recommendation(
        self,
        db: AsyncSession,
        original_content: str,
        refinement_instructions: str,
        github_username: str,
        user_id: Optional[int] = None,  # Added user_id
        recommendation_type: str = "professional",
        tone: str = "professional",
        length: str = "medium",
    ) -> RecommendationResponse:
        """Regenerate a recommendation with refinement instructions."""

        import time

        start_time = time.time()

        try:
            logger.info("🔄 STEP 1: GITHUB PROFILE ANALYSIS")
            logger.info("-" * 50)
            github_start = time.time()

            # Analyze GitHub profile
            github_data = await self.github_service.analyze_github_profile(username=github_username, force_refresh=False)

            github_end = time.time()
            logger.info(f"⏱️  GitHub analysis completed in {github_end - github_start:.2f} seconds")

            if not github_data:
                logger.error(f"❌ Failed to analyze GitHub profile for {github_username}")
                raise ValueError(f"Could not analyze GitHub profile for {github_username}")
            logger.debug(f"➡️ GitHub data used for recommendation regeneration: {github_data}")  # Log github_data

            # Get or create GitHub profile record
            logger.info("💾 STEP 2: DATABASE OPERATIONS")
            logger.info("-" * 50)
            db_start = time.time()

            github_profile = await self._get_or_create_github_profile(db, github_data)

            db_end = time.time()
            logger.info(f"⏱️  Database operations completed in {db_end - db_start:.2f} seconds")

            # Generate refined AI recommendation
            logger.info("🤖 STEP 3: AI RECOMMENDATION REGENERATION")
            logger.info("-" * 50)
            ai_start = time.time()

            ai_result = await self.ai_service.regenerate_recommendation(
                original_content=original_content,
                refinement_instructions=refinement_instructions,
                github_data=github_data,
                recommendation_type=recommendation_type,
                tone=tone,
                length=length,
            )

            ai_end = time.time()
            logger.info(f"⏱️  AI regeneration completed in {ai_end - ai_start:.2f} seconds")
            logger.info("✅ AI recommendation regenerated:")
            logger.info(f"   • Content length: {len(ai_result['content'])} characters")
            logger.info(f"   • Word count: {ai_result['word_count']}")
            logger.info(f"   • Confidence score: {ai_result['confidence_score']}")

            # Create recommendation record
            logger.info("💾 STEP 4: SAVING RECOMMENDATION")
            logger.info("-" * 50)
            save_start = time.time()

            recommendation_data = RecommendationCreate(
                github_profile_id=int(github_profile.id),
                title=ai_result["title"],
                content=ai_result["content"],
                recommendation_type=recommendation_type,
                tone=tone,
                length=length,
                ai_model=ai_result["generation_parameters"]["model"],
                generation_prompt=refinement_instructions,
                generation_parameters=ai_result["generation_parameters"],
                confidence_score=ai_result["confidence_score"],
                word_count=ai_result["word_count"],
            )

            recommendation = Recommendation(**recommendation_data.dict())
            db.add(recommendation)
            await db.commit()
            await db.refresh(recommendation)

            save_end = time.time()
            logger.info(f"⏱️  Database save completed in {save_end - save_start:.2f} seconds")
            logger.info(f"✅ Recommendation saved with ID: {recommendation.id}")

            # Convert to response
            response = RecommendationResponse.from_orm(recommendation)
            response.github_username = github_username

            end_time = time.time()
            total_time = end_time - start_time

            logger.info("🎉 RECOMMENDATION REGENERATION SUMMARY")
            logger.info("-" * 50)
            logger.info(f"⏱️  Total processing time: {total_time:.2f} seconds")
            logger.info("📊 Breakdown:")
            logger.info(f"   • GitHub Analysis: {github_end - github_start:.2f}s ({((github_end - github_start)/total_time)*100:.1f}%)")
            logger.info(f"   • Database Ops: {db_end - db_start:.2f}s ({((db_end - db_start)/total_time)*100:.1f}%)")
            logger.info(f"   • AI Regeneration: {ai_end - ai_start:.2f}s ({((ai_end - ai_start)/total_time)*100:.1f}%)")
            logger.info(f"   • Save Record: {save_end - save_start:.2f}s ({((save_end - save_start)/total_time)*100:.1f}%)")

            return response

        except Exception as e:
            logger.error(f"💥 ERROR in recommendation regeneration for {github_username}: {e}")
            logger.error(f"⏱️  Failed after {time.time() - start_time:.2f} seconds")
            await db.rollback()
            raise

    async def refine_recommendation_with_keywords(
        self,
        db: AsyncSession,
        recommendation_id: int,
        include_keywords: Optional[List[str]] = None,
        exclude_keywords: Optional[List[str]] = None,
        refinement_instructions: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Refine an existing recommendation based on keyword constraints."""
        try:
            logger.info("🔧 KEYWORD REFINEMENT STARTED")
            logger.info("=" * 60)
            logger.info(f"📝 Recommendation ID: {recommendation_id}")
            logger.info(f"➕ Include keywords: {include_keywords}")
            logger.info(f"➖ Exclude keywords: {exclude_keywords}")

            # Get the original recommendation
            query = select(Recommendation).where(Recommendation.id == recommendation_id)
            result = await db.execute(query)
            original_recommendation = result.scalar_one_or_none()

            if not original_recommendation:
                logger.error(f"❌ Recommendation with ID {recommendation_id} not found")
                raise ValueError(f"Recommendation with ID {recommendation_id} not found")

            # Get GitHub profile data for context
            github_profile_query = select(GitHubProfile).where(GitHubProfile.id == original_recommendation.github_profile_id)
            github_profile_result = await db.execute(github_profile_query)
            github_profile = github_profile_result.scalar_one_or_none()

            if not github_profile:
                logger.error(f"❌ GitHub profile not found for recommendation {recommendation_id}")
                raise ValueError(f"GitHub profile not found for recommendation {recommendation_id}")

            # Reconstruct GitHub data for AI processing
            github_data: Dict[str, Any] = {
                "user_data": {
                    "github_username": github_profile.github_username,
                    "github_id": github_profile.github_id,
                    "full_name": github_profile.full_name,
                    "bio": github_profile.bio,
                    "company": github_profile.company,
                    "location": github_profile.location,
                    "email": github_profile.email,
                    "blog": github_profile.blog,
                    "avatar_url": github_profile.avatar_url,
                    "public_repos": github_profile.public_repos,
                    "followers": github_profile.followers,
                    "following": github_profile.following,
                    "public_gists": github_profile.public_gists,
                },
                "repositories": github_profile.repositories_data or [],
                "languages": github_profile.languages_data or [],
                "skills": github_profile.skills_analysis or {},
                "analysis_context_type": "profile",
            }

            # Extract original parameters
            original_params: Dict[str, Any] = original_recommendation.generation_parameters or {}  # type: ignore
            recommendation_type = original_params.get("recommendation_type", "professional")
            tone = original_params.get("tone", "professional")
            length = original_params.get("length", "medium")

            # Generate refined recommendation
            logger.info("🤖 STEP 1: AI KEYWORD REFINEMENT")
            logger.info("-" * 50)
            ai_start = time.time()

            ai_result = await self.ai_service.refine_recommendation_with_keywords(
                original_content=original_recommendation.content,  # type: ignore
                github_data=github_data,
                include_keywords=include_keywords,
                exclude_keywords=exclude_keywords,
                refinement_instructions=refinement_instructions or "",
                recommendation_type=recommendation_type,
                tone=tone,
                length=length,
            )

            ai_end = time.time()
            logger.info(f"⏱️  AI refinement completed in {ai_end - ai_start:.2f} seconds")
            logger.info("✅ Keyword refinement successful:")
            logger.info(f"   • Word count: {ai_result['word_count']}")
            logger.info(f"   • Confidence score: {ai_result['confidence_score']}")
            if ai_result.get("include_keywords_used"):
                logger.info(f"   • Keywords included: {len(ai_result['include_keywords_used'])}")
            if ai_result.get("exclude_keywords_avoided"):
                logger.info(f"   • Exclude keywords avoided: {len(ai_result['exclude_keywords_avoided'])}")

            # Save the refined recommendation as a new version
            new_recommendation = await self._create_recommendation_version(
                db=db,
                recommendation=original_recommendation,
                change_type="keyword_refinement",
                change_description=ai_result["refinement_summary"],
                content=ai_result["refined_content"],
                title=ai_result["refined_title"],
                confidence_score=ai_result["confidence_score"],
                word_count=ai_result["word_count"],
                include_keywords_used=ai_result.get("include_keywords_used"),
                exclude_keywords_avoided=ai_result.get("exclude_keywords_avoided"),
            )

            return {
                "id": new_recommendation.id,
                "original_recommendation_id": original_recommendation.id,  # Added this line
                "refined_content": new_recommendation.content,
                "refined_title": new_recommendation.title,
                "word_count": new_recommendation.word_count,
                "confidence_score": new_recommendation.confidence_score,
                "exclude_keywords_avoided": new_recommendation.exclude_keywords_avoided or [],
                "include_keywords_used": new_recommendation.include_keywords_used or [],
                "refinement_summary": ai_result["refinement_summary"],
                "validation_issues": ai_result["validation_issues"],
                "generation_parameters": ai_result["generation_parameters"],
            }
        except Exception as e:
            logger.error(f"💥 ERROR in keyword refinement for recommendation {recommendation_id}: {e}")
            raise e

    async def generate_repository_readme(
        self,
        repository_full_name: str,
        style: str = "comprehensive",
        include_sections: Optional[List[str]] = None,
        target_audience: str = "developers",
    ) -> Dict[str, Any]:
        """Generate a README for a GitHub repository."""
        import time

        start_time = time.time()

        try:
            logger.info("📖 README GENERATION STARTED")
            logger.info("=" * 60)
            logger.info(f"📁 Repository: {repository_full_name}")
            logger.info(f"🎨 Style: {style}")
            logger.info(f"👥 Target Audience: {target_audience}")

            # Analyze the repository using GitHub service
            logger.info("🔍 STEP 1: REPOSITORY ANALYSIS")
            logger.info("-" * 50)
            repo_start = time.time()

            repository_data = await self.repository_service.analyze_repository(repository_full_name=repository_full_name, force_refresh=False)

            if not repository_data:
                logger.error(f"❌ Failed to analyze repository {repository_full_name}")
                raise ValueError(f"Could not analyze repository {repository_full_name}")

            repo_end = time.time()
            logger.info(f"⏱️  Repository analysis completed in {repo_end - repo_start:.2f} seconds")
            logger.info("✅ Repository analysis successful:")
            logger.info(f"   • Repository: {repository_data.get('repository_info', {}).get('name', 'N/A')}")
            logger.info(f"   • Language: {repository_data.get('repository_info', {}).get('language', 'N/A')}")
            logger.info(f"   • Stars: {repository_data.get('repository_info', {}).get('stars', 0)}")

            # Perform additional README-specific analysis
            logger.info("🔧 STEP 2: README-SPECIFIC ANALYSIS")
            logger.info("-" * 50)
            analysis_start = time.time()

            # Get repository object for deeper analysis
            if not self.github_service.github_client:
                raise ValueError("GitHub client not configured")

            try:
                owner, repo_name = repository_full_name.split("/", 1)
                repo = self.github_service.github_client.get_repo(repository_full_name)

                # Perform README-specific analysis
                repository_analysis = self.github_service._analyze_repository_content_for_readme(repository_data.get("repository_info", {}), repo)

                # Extract API endpoints if applicable
                main_files = repository_analysis.get("main_files", [])
                if main_files:
                    api_endpoints = self.github_service._extract_api_endpoints_from_code(repo, main_files)
                    repository_analysis["api_endpoints"] = api_endpoints

            except Exception as e:
                logger.warning(f"Could not perform deep repository analysis: {e}")
                repository_analysis = {
                    "existing_readme": False,
                    "readme_content": None,
                    "main_files": [],
                    "documentation_files": [],
                    "configuration_files": [],
                    "source_directories": [],
                    "license_info": None,
                    "has_tests": False,
                    "has_ci_cd": False,
                    "has_docker": False,
                    "api_endpoints": [],
                    "key_features": [],
                }

            analysis_end = time.time()
            logger.info(f"⏱️  README-specific analysis completed in {analysis_end - analysis_start:.2f} seconds")
            logger.info("✅ README analysis successful:")
            logger.info(f"   • Existing README: {repository_analysis.get('existing_readme', False)}")
            logger.info(f"   • Main files: {len(repository_analysis.get('main_files', []))}")
            logger.info(f"   • Has tests: {repository_analysis.get('has_tests', False)}")
            logger.info(f"   • Has CI/CD: {repository_analysis.get('has_ci_cd', False)}")

            # Generate README content
            logger.info("🤖 STEP 3: AI README GENERATION")
            logger.info("-" * 50)
            ai_start = time.time()

            ai_result = self.ai_service._generate_readme_content(
                repository_data=repository_data,
                repository_analysis=dict(repository_analysis),
                style=style,
                include_sections=include_sections,
                target_audience=target_audience,
            )

            ai_end = time.time()
            logger.info(f"⏱️  AI README generation completed in {ai_end - ai_start:.2f} seconds")
            logger.info("✅ README generation successful:")
            logger.info(f"   • Content length: {ai_result['word_count']} words")
            logger.info(f"   • Sections: {len(ai_result['sections'])}")
            logger.info(f"   • Confidence score: {ai_result['confidence_score']}")

            end_time = time.time()
            total_time = end_time - start_time

            logger.info("🎉 README GENERATION COMPLETED")
            logger.info("-" * 50)
            logger.info(f"⏱️  Total processing time: {total_time:.2f} seconds")
            logger.info("📊 Final Results:")
            logger.info(f"   • Repository: {repository_full_name}")
            logger.info(f"   • Style: {style}")
            logger.info(f"   • Confidence Score: {ai_result['confidence_score']}")
            logger.info("=" * 60)

            return {
                "repository_name": repository_data.get("repository_info", {}).get("name", ""),
                "repository_full_name": repository_full_name,
                "generated_content": ai_result["generated_content"],
                "sections": ai_result["sections"],
                "word_count": ai_result["word_count"],
                "confidence_score": ai_result["confidence_score"],
                "generation_parameters": ai_result["generation_parameters"],
                "analysis_summary": ai_result["analysis_summary"],
                "repository_analysis": repository_analysis,
            }

        except Exception as e:
            logger.error(f"💥 ERROR in README generation for {repository_full_name}: {e}")
            logger.error(f"⏱️  Failed after {time.time() - start_time:.2f} seconds")
            raise

    async def _create_recommendation_version(
        self,
        db: AsyncSession,
        recommendation: Recommendation,
        change_type: str,
        change_description: Optional[str] = None,
        content: Optional[str] = None,
        title: Optional[str] = None,
        confidence_score: Optional[int] = None,
        word_count: Optional[int] = None,
        created_by: str = "system",
        include_keywords_used: Optional[List[str]] = None,
        exclude_keywords_avoided: Optional[List[str]] = None,
    ) -> RecommendationVersion:
        """Create a new version entry for a recommendation."""
        # Get the next version number
        query = select(RecommendationVersion).where(RecommendationVersion.recommendation_id == recommendation.id).order_by(desc(RecommendationVersion.version_number)).limit(1)

        result = await db.execute(query)
        last_version = result.scalar_one_or_none()

        next_version_number = 1 if not last_version else last_version.version_number + 1

        # Create the version entry
        version = RecommendationVersion(
            recommendation_id=recommendation.id,
            version_number=next_version_number,
            change_type=change_type,
            change_description=change_description,
            title=title if title is not None else recommendation.title,
            content=content if content is not None else recommendation.content,
            generation_parameters=recommendation.generation_parameters,
            confidence_score=confidence_score if confidence_score is not None else recommendation.confidence_score,
            word_count=word_count if word_count is not None else recommendation.word_count,
            created_by=created_by,
            include_keywords_used=include_keywords_used,
            exclude_keywords_avoided=exclude_keywords_avoided,
        )

        db.add(version)
        await db.commit()
        await db.refresh(version)

        logger.info(f"📝 Created version {next_version_number} for recommendation {recommendation.id}")
        return version

    async def get_recommendation_version_history(self, db: AsyncSession, recommendation_id: int) -> RecommendationVersionHistoryResponse:
        """Get the version history for a recommendation."""
        # Get the recommendation
        query = select(Recommendation).where(Recommendation.id == recommendation_id)
        result = await db.execute(query)
        recommendation = result.scalar_one_or_none()

        if not recommendation:
            raise ValueError(f"Recommendation with ID {recommendation_id} not found")

        # Get all versions
        versions_query = select(RecommendationVersion).where(RecommendationVersion.recommendation_id == recommendation_id).order_by(desc(RecommendationVersion.version_number))

        versions_result = await db.execute(versions_query)
        versions = versions_result.scalars().all()

        # Convert to response format
        version_infos = []
        for version in versions:
            version_infos.append(
                RecommendationVersionInfo(
                    id=version.id,  # type: ignore
                    version_number=version.version_number,  # type: ignore
                    change_type=version.change_type,  # type: ignore
                    change_description=version.change_description,  # type: ignore
                    confidence_score=version.confidence_score,  # type: ignore
                    word_count=version.word_count,  # type: ignore
                    created_at=version.created_at,  # type: ignore
                    created_by=version.created_by,  # type: ignore
                    include_keywords_used=version.include_keywords_used,  # Added
                    exclude_keywords_avoided=version.exclude_keywords_avoided,  # Added
                )
            )

        # Get current version number (latest)
        current_version = max([v.version_number for v in versions]) if versions else 1  # type: ignore

        return RecommendationVersionHistoryResponse(
            recommendation_id=recommendation_id,
            total_versions=len(versions),
            current_version=current_version,  # type: ignore
            versions=version_infos,
        )

    async def compare_recommendation_versions(self, db: AsyncSession, recommendation_id: int, version_a_id: int, version_b_id: int) -> VersionComparisonResponse:
        """Compare two versions of a recommendation."""
        # Get both versions
        version_query = select(RecommendationVersion).where(RecommendationVersion.recommendation_id == recommendation_id, RecommendationVersion.id.in_([version_a_id, version_b_id]))

        version_result = await db.execute(version_query)
        versions = version_result.scalars().all()

        if len(versions) != 2:
            raise ValueError("One or both versions not found")

        version_a = next(v for v in versions if v.id == version_a_id)
        version_b = next(v for v in versions if v.id == version_b_id)

        # Convert to detailed format
        version_a_detail = RecommendationVersionDetail(
            id=version_a.id,  # type: ignore
            recommendation_id=version_a.recommendation_id,  # type: ignore
            version_number=version_a.version_number,  # type: ignore
            change_type=version_a.change_type,  # type: ignore
            change_description=version_a.change_description,  # type: ignore
            title=version_a.title,  # type: ignore
            content=version_a.content,  # type: ignore
            generation_parameters=version_a.generation_parameters,  # type: ignore
            confidence_score=version_a.confidence_score,  # type: ignore
            word_count=version_a.word_count,  # type: ignore
            created_at=version_a.created_at,  # type: ignore
            created_by=version_a.created_by,  # type: ignore
        )

        version_b_detail = RecommendationVersionDetail(
            id=version_b.id,  # type: ignore
            recommendation_id=version_b.recommendation_id,  # type: ignore
            version_number=version_b.version_number,  # type: ignore
            change_type=version_b.change_type,  # type: ignore
            change_description=version_b.change_description,  # type: ignore
            title=version_b.title,  # type: ignore
            content=version_b.content,  # type: ignore
            generation_parameters=version_b.generation_parameters,  # type: ignore
            confidence_score=version_b.confidence_score,  # type: ignore
            word_count=version_b.word_count,  # type: ignore
            created_at=version_b.created_at,  # type: ignore
            created_by=version_b.created_by,  # type: ignore
        )

        # Calculate differences
        differences = self._calculate_version_differences(version_a_detail, version_b_detail)

        return VersionComparisonResponse(
            recommendation_id=recommendation_id,
            version_a=version_a_detail,
            version_b=version_b_detail,
            differences=differences,
        )

    def _calculate_version_differences(self, version_a: RecommendationVersionDetail, version_b: RecommendationVersionDetail) -> Dict[str, Any]:
        """Calculate differences between two recommendation versions."""
        differences = {}

        # Title differences
        if version_a.title != version_b.title:
            differences["title"] = {"version_a": version_a.title, "version_b": version_b.title, "changed": True}

        # Content differences (basic word count comparison)
        if version_a.word_count != version_b.word_count:
            differences["content_length"] = {
                "version_a_words": version_a.word_count,
                "version_b_words": version_b.word_count,
                "difference": version_b.word_count - version_a.word_count,
            }

        # Confidence score differences
        if version_a.confidence_score != version_b.confidence_score:
            differences["confidence_score"] = {
                "version_a": version_a.confidence_score,
                "version_b": version_b.confidence_score,
                "improvement": version_b.confidence_score - version_a.confidence_score,
            }

        # Generation parameters differences
        if version_a.generation_parameters != version_b.generation_parameters:
            differences["generation_parameters"] = {
                "version_a": version_a.generation_parameters,
                "version_b": version_b.generation_parameters,
                "changed": True,
            }

        # Change type differences
        if version_a.change_type != version_b.change_type:
            differences["change_type"] = {"version_a": version_a.change_type, "version_b": version_b.change_type, "changed": True}

        return differences

    async def revert_recommendation_to_version(self, db: AsyncSession, recommendation_id: int, version_id: int, revert_reason: Optional[str] = None) -> RecommendationResponse:
        """Revert a recommendation to a specific version."""
        # Get the target version
        version_query = select(RecommendationVersion).where(RecommendationVersion.id == version_id, RecommendationVersion.recommendation_id == recommendation_id)
        version_result = await db.execute(version_query)
        target_version = version_result.scalar_one_or_none()

        if not target_version:
            raise ValueError(f"Version {version_id} not found for recommendation {recommendation_id}")

        # Get the current recommendation
        rec_query = select(Recommendation).where(Recommendation.id == recommendation_id)
        rec_result = await db.execute(rec_query)
        recommendation = rec_result.scalar_one_or_none()

        if not recommendation:
            raise ValueError(f"Recommendation {recommendation_id} not found")

        # Create a version of the current state before reverting
        await self._create_recommendation_version(
            db=db,
            recommendation=recommendation,
            change_type="revert_backup",
            change_description=f"Backup before reverting to version {target_version.version_number}",
            created_by="system",
        )

        # Update the recommendation with the target version's content
        recommendation.title = target_version.title
        recommendation.content = target_version.content
        recommendation.generation_parameters = target_version.generation_parameters
        recommendation.confidence_score = target_version.confidence_score
        recommendation.word_count = target_version.word_count

        # Create a new version entry for the revert
        await self._create_recommendation_version(
            db=db,
            recommendation=recommendation,
            change_type="reverted",
            change_description=revert_reason or f"Reverted to version {target_version.version_number}",
            created_by="user",
        )

        await db.commit()
        await db.refresh(recommendation)

        # Convert to response
        response = RecommendationResponse.from_orm(recommendation)

        # Get GitHub username
        github_profile_query = select(GitHubProfile.github_username).where(GitHubProfile.id == recommendation.github_profile_id)
        github_result = await db.execute(github_profile_query)
        github_username = github_result.scalar_one_or_none()
        response.github_username = github_username

        logger.info(f"🔄 Successfully reverted recommendation {recommendation_id} to version {target_version.version_number}")
        return response

    def _get_role_skill_requirements(self, role: str, experience_level: str = "mid") -> Dict[str, Any]:
        """Get skill requirements for common job roles."""
        role_requirements = {
            "frontend_developer": {
                "junior": {
                    "required": ["HTML", "CSS", "JavaScript"],
                    "preferred": ["React", "Vue", "Angular", "Git", "Responsive Design"],
                    "nice_to_have": ["TypeScript", "Webpack", "Testing", "Node.js"],
                },
                "mid": {
                    "required": ["HTML", "CSS", "JavaScript", "React/Vue/Angular", "Git"],
                    "preferred": ["TypeScript", "Testing", "Build Tools", "Performance Optimization"],
                    "nice_to_have": ["GraphQL", "Mobile Development", "Design Systems", "CI/CD"],
                },
                "senior": {
                    "required": ["HTML", "CSS", "JavaScript", "React/Vue/Angular", "TypeScript", "Testing"],
                    "preferred": ["Architecture", "Performance", "Mentoring", "Code Review", "CI/CD"],
                    "nice_to_have": ["Leadership", "System Design", "DevOps", "Product Management"],
                },
            },
            "backend_developer": {
                "junior": {
                    "required": ["Python/Java/Node.js", "SQL", "REST APIs"],
                    "preferred": ["Git", "Testing", "Linux/Unix", "Docker"],
                    "nice_to_have": ["ORM", "Caching", "Security", "Microservices"],
                },
                "mid": {
                    "required": ["Python/Java/Node.js", "SQL", "REST APIs", "Testing", "Git"],
                    "preferred": ["ORM", "Caching", "Security", "Docker", "AWS/GCP/Azure"],
                    "nice_to_have": ["Microservices", "GraphQL", "Message Queues", "Monitoring"],
                },
                "senior": {
                    "required": ["Python/Java/Node.js", "SQL", "REST APIs", "Testing", "Architecture"],
                    "preferred": ["Microservices", "Cloud Platforms", "Security", "Performance", "Mentoring"],
                    "nice_to_have": ["System Design", "DevOps", "Leadership", "Product Strategy"],
                },
            },
            "fullstack_developer": {
                "junior": {
                    "required": ["HTML", "CSS", "JavaScript", "Python/Java/Node.js", "SQL"],
                    "preferred": ["React/Vue", "Git", "REST APIs", "Testing"],
                    "nice_to_have": ["TypeScript", "Docker", "AWS/GCP", "Responsive Design"],
                },
                "mid": {
                    "required": ["HTML", "CSS", "JavaScript", "Python/Java/Node.js", "SQL", "REST APIs"],
                    "preferred": ["React/Vue", "TypeScript", "Testing", "Docker", "AWS/GCP"],
                    "nice_to_have": ["GraphQL", "Microservices", "CI/CD", "Performance Optimization"],
                },
                "senior": {
                    "required": ["HTML", "CSS", "JavaScript", "Python/Java/Node.js", "SQL", "Architecture"],
                    "preferred": ["TypeScript", "Microservices", "Cloud Platforms", "Testing", "Performance"],
                    "nice_to_have": ["Leadership", "System Design", "DevOps", "Product Management"],
                },
            },
            "data_scientist": {
                "junior": {
                    "required": ["Python", "SQL", "Statistics", "Pandas", "NumPy"],
                    "preferred": ["Machine Learning", "Matplotlib", "Jupyter", "Git"],
                    "nice_to_have": ["R", "TensorFlow", "Scikit-learn", "Tableau"],
                },
                "mid": {
                    "required": ["Python", "SQL", "Statistics", "Machine Learning", "Pandas", "NumPy"],
                    "preferred": ["TensorFlow/PyTorch", "Scikit-learn", "Data Visualization", "Big Data"],
                    "nice_to_have": ["Deep Learning", "Spark", "AWS/GCP", "Experimentation"],
                },
                "senior": {
                    "required": ["Python", "SQL", "Statistics", "Machine Learning", "Deep Learning"],
                    "preferred": ["Big Data", "MLOps", "Experimentation", "Leadership", "Strategy"],
                    "nice_to_have": ["System Design", "Product Management", "Research", "Publications"],
                },
            },
            "devops_engineer": {
                "junior": {
                    "required": ["Linux/Unix", "Git", "Docker", "CI/CD"],
                    "preferred": ["AWS/GCP/Azure", "Kubernetes", "Terraform", "Monitoring"],
                    "nice_to_have": ["Python", "Shell Scripting", "Security", "Networking"],
                },
                "mid": {
                    "required": ["Linux/Unix", "Docker", "Kubernetes", "CI/CD", "AWS/GCP/Azure"],
                    "preferred": ["Terraform", "Monitoring", "Security", "Python", "Shell Scripting"],
                    "nice_to_have": ["Service Mesh", "GitOps", "Site Reliability", "Automation"],
                },
                "senior": {
                    "required": ["Linux/Unix", "Docker", "Kubernetes", "CI/CD", "Infrastructure as Code"],
                    "preferred": ["Site Reliability", "Security", "Automation", "Leadership", "Strategy"],
                    "nice_to_have": ["Platform Engineering", "Multi-cloud", "Compliance", "Cost Optimization"],
                },
            },
        }

        # Normalize role name
        normalized_role = role.lower().replace(" ", "_").replace("-", "_")

        # Find matching role or use closest match
        if normalized_role in role_requirements:
            return role_requirements[normalized_role].get(experience_level, role_requirements[normalized_role]["mid"])
        else:
            # Try to find partial matches
            for role_key in role_requirements:
                if role_key in normalized_role or normalized_role in role_key:
                    return role_requirements[role_key].get(experience_level, role_requirements[role_key]["mid"])

            # Default fallback
            return {
                "required": ["Programming", "Git", "Communication"],
                "preferred": ["Testing", "Documentation", "Teamwork"],
                "nice_to_have": ["Leadership", "Problem Solving", "Continuous Learning"],
            }

    def _analyze_skill_match(self, user_skill: str, required_skills: List[str], github_data: Dict[str, Any]) -> SkillMatch:
        """Analyze how well a user's skill matches job requirements."""
        # Extract user's skills from the nested skills structure
        skills_data = github_data.get("skills", {})
        user_technical_skills = set(skills_data.get("technical_skills", []))
        user_frameworks = set(skills_data.get("frameworks", []))
        user_tools = set(skills_data.get("tools", []))
        user_domains = set(skills_data.get("domains", []))
        user_dependencies = set(skills_data.get("dependencies_found", []))

        # Combine all user skills for matching
        all_user_skills = user_technical_skills | user_frameworks | user_tools | user_domains | user_dependencies

        # Extract additional data sources
        starred_technologies = github_data.get("starred_technologies", {})
        commit_analysis = github_data.get("commit_analysis", {})

        # Get starred languages and topics
        starred_languages = set(starred_technologies.get("languages", {}).keys())
        starred_topics = set(starred_technologies.get("topics", []))

        # Add starred technologies to skill set
        all_user_skills.update(starred_languages)
        all_user_skills.update(starred_topics)

        # Normalize skills for comparison
        user_skill_lower = user_skill.lower()
        user_skills_lower = {skill.lower() for skill in all_user_skills}

        # Find matches
        evidence = []
        match_score = 0

        # Direct match in skills
        if user_skill_lower in user_skills_lower:
            match_score += 40
            evidence.append("Direct match found in profile")

        # Check starred technologies
        if user_skill_lower in starred_languages:
            match_score += 25
            evidence.append("Interest shown through starred repositories")
        elif user_skill_lower in starred_topics:
            match_score += 20
            evidence.append("Technology interest indicated by repository topics")

        # Partial matches in skills
        for user_skill_name in all_user_skills:
            user_skill_name_lower = user_skill_name.lower()
            if (user_skill_lower in user_skill_name_lower or user_skill_name_lower in user_skill_lower) and user_skill_lower != user_skill_name_lower:
                match_score += 20
                evidence.append(f"Related skill: {user_skill_name}")
                break

        # Check commit analysis for evidence of expertise
        primary_strength = commit_analysis.get("excellence_areas", {}).get("primary_strength", "")
        if primary_strength and (user_skill_lower in primary_strength.lower() or primary_strength.lower() in user_skill_lower):
            match_score += 30
            evidence.append(f"Primary strength based on commit analysis: {primary_strength.replace('_', ' ').title()}")

        # Check commit patterns for relevant skills
        patterns = commit_analysis.get("excellence_areas", {}).get("patterns", {})
        for pattern_name, pattern_data in patterns.items():
            pattern_percentage = pattern_data.get("percentage", 0)
            # If pattern has significant percentage (>15%) and matches skill
            if pattern_percentage > 15 and (user_skill_lower in pattern_name.lower() or pattern_name.lower() in user_skill_lower):
                match_score += min(int(pattern_percentage), 25)  # Cap at 25 points
                evidence.append(f"Strong commit pattern in {pattern_name.replace('_', ' ')} ({pattern_percentage}%)")
                break

        # Check if user has relevant tools/frameworks from commit analysis
        tools_and_features = commit_analysis.get("tools_and_features", {})
        tools_by_category = tools_and_features.get("tools_by_category", {})
        for category, tools in tools_by_category.items():
            for tool in tools:
                if user_skill_lower in tool.lower() or tool.lower() in user_skill_lower:
                    match_score += 20
                    evidence.append(f"Experience with {tool} based on commit history")
                    break

        # Check for related technologies
        related_tech = self._get_related_technologies(user_skill)
        for tech in related_tech:
            if tech.lower() in user_skills_lower:
                match_score += 15
                evidence.append(f"Related technology: {tech}")
            elif tech.lower() in starred_languages:
                match_score += 10
                evidence.append(f"Related technology interest: {tech}")

        # Determine match level
        if match_score >= 40:
            match_level = "strong"
        elif match_score >= 20:
            match_level = "moderate"
        elif match_score >= 5:
            match_level = "weak"
        else:
            match_level = "missing"
            evidence.append("No relevant skills found in profile")

        # Boost confidence for strong evidence
        confidence_score = min(match_score + 20, 100)

        return SkillMatch(skill=user_skill, match_level=match_level, evidence=evidence, confidence_score=confidence_score)

    def _get_related_technologies(self, skill: str) -> List[str]:
        """Get related technologies for a given skill."""
        related_tech_map = {
            "javascript": ["node.js", "express", "react", "vue", "angular"],
            "python": ["django", "flask", "fastapi", "pandas", "numpy", "tensorflow"],
            "java": ["spring", "hibernate", "maven", "gradle"],
            "react": ["javascript", "typescript", "redux", "next.js"],
            "docker": ["kubernetes", "containerization", "devops"],
            "aws": ["cloud", "ec2", "s3", "lambda", "terraform"],
            "testing": ["jest", "pytest", "junit", "selenium", "cypress"],
            "git": ["version control", "github", "gitlab", "collaboration"],
            "sql": ["database", "postgresql", "mysql", "mongodb", "orm"],
            "machine learning": ["python", "tensorflow", "pytorch", "scikit-learn", "pandas"],
        }

        skill_lower = skill.lower()
        for key, related in related_tech_map.items():
            if key in skill_lower or skill_lower in key:
                return related

        return []

    def _generate_skill_recommendations(self, skill_analysis: List[SkillMatch], target_role: str) -> Dict[str, List[str]]:
        """Generate recommendations based on skill analysis."""
        recommendations = []
        learning_resources = []

        missing_skills = [match.skill for match in skill_analysis if match.match_level == "missing"]
        weak_skills = [match.skill for match in skill_analysis if match.match_level == "weak"]

        # Generate specific recommendations
        for skill in missing_skills[:5]:  # Focus on top 5 missing skills
            if "javascript" in skill.lower():
                recommendations.append(f"Learn {skill} fundamentals and practice with small projects")
                learning_resources.append("freeCodeCamp JavaScript curriculum")
                learning_resources.append("MDN Web Docs")
            elif "python" in skill.lower():
                recommendations.append(f"Master {skill} basics and build data processing applications")
                learning_resources.append("Python Crash Course book")
                learning_resources.append("Codecademy Python course")
            elif "react" in skill.lower():
                recommendations.append("Build React applications and learn component patterns")
                learning_resources.append("React Official Documentation")
                learning_resources.append("React for Beginners course")
            elif "docker" in skill.lower():
                recommendations.append(f"Learn containerization with {skill} and Kubernetes basics")
                learning_resources.append("Docker Getting Started guide")
                learning_resources.append("Kubernetes documentation")
            elif "testing" in skill.lower():
                recommendations.append("Implement comprehensive testing strategies for your projects")
                learning_resources.append("Testing JavaScript book")
                learning_resources.append("Jest documentation")
            else:
                recommendations.append(f"Develop proficiency in {skill} through hands-on projects")
                learning_resources.append(f"Search for '{skill} tutorials' on YouTube")
                learning_resources.append(f"Read documentation for {skill}")

        # Add general recommendations
        if len(missing_skills) > 3:
            recommendations.append("Focus on building a portfolio project that demonstrates multiple required skills")
            learning_resources.append("GitHub learning paths")

        if weak_skills:
            recommendations.append(f"Strengthen your knowledge in: {', '.join(weak_skills[:3])}")

        return {
            "recommendations": recommendations[:8],  # Limit to 8 recommendations
            "learning_resources": learning_resources[:6],  # Limit to 6 resources
        }

    async def analyze_skill_gaps(self, request: SkillGapAnalysisRequest) -> SkillGapAnalysisResponse:
        """Analyze skill gaps for a target role."""
        import time

        start_time = time.time()

        try:
            logger.info("📊 SKILL GAP ANALYSIS STARTED")
            logger.info("=" * 60)
            logger.info(f"👤 GitHub Username: {request.github_username}")
            logger.info(f"🎯 Target Role: {request.target_role}")
            logger.info(f"🏢 Industry: {request.industry}")
            logger.info(f"📈 Experience Level: {request.experience_level}")

            # Get GitHub profile data
            logger.info("🔍 STEP 1: FETCHING GITHUB PROFILE")
            logger.info("-" * 50)

            github_data = await self.github_service.analyze_github_profile(username=request.github_username, force_refresh=False)

            if not github_data:
                logger.error(f"❌ Failed to analyze GitHub profile for {request.github_username}")
                raise ValueError(f"Could not analyze GitHub profile for {request.github_username}")

            logger.info("✅ GitHub profile analysis successful")

            # Get skill requirements for the target role
            logger.info("📋 STEP 2: ANALYZING ROLE REQUIREMENTS")
            logger.info("-" * 50)

            role_requirements = self._get_role_skill_requirements(request.target_role or "", request.experience_level or "mid")

            logger.info(f"📋 Role requirements loaded: {len(role_requirements['required'])} required skills")

            # Analyze skill matches
            logger.info("🔍 STEP 3: ANALYZING SKILL MATCHES")
            logger.info("-" * 50)
            skill_analysis = []

            # Analyze required skills
            for skill in role_requirements["required"]:
                match = self._analyze_skill_match(skill, role_requirements["required"], github_data)
                skill_analysis.append(match)

            # Analyze preferred skills (partial weight)
            for skill in role_requirements["preferred"][:5]:  # Top 5 preferred skills
                match = self._analyze_skill_match(skill, role_requirements["required"], github_data)
                match.confidence_score = int(match.confidence_score * 0.8)  # Reduce weight for preferred skills
                skill_analysis.append(match)

            logger.info(f"✅ Analyzed {len(skill_analysis)} skills")

            # Calculate overall match score
            required_matches = [match for match in skill_analysis if match.match_level in ["strong", "moderate"]]
            overall_match_score = int((len(required_matches) / len(role_requirements["required"])) * 100)
            overall_match_score = min(overall_match_score, 100)

            # Generate insights
            logger.info("💡 STEP 4: GENERATING INSIGHTS")
            logger.info("-" * 50)

            # Identify strengths and gaps
            strengths = []
            gaps = []

            for match in skill_analysis:
                if match.match_level == "strong":
                    strengths.append(match.skill)
                elif match.match_level in ["missing", "weak"]:
                    gaps.append(match.skill)

            # Generate recommendations
            recommendations_data = self._generate_skill_recommendations(skill_analysis, request.target_role)

            # Create analysis summary
            analysis_summary = self._create_gap_analysis_summary(overall_match_score, len(strengths), len(gaps), request.target_role)

            logger.info("🎉 SKILL GAP ANALYSIS COMPLETED")
            logger.info("-" * 50)
            logger.info(f"📊 Overall Match Score: {overall_match_score}%")
            logger.info(f"💪 Strengths Identified: {len(strengths)}")
            logger.info(f"🎯 Gaps Identified: {len(gaps)}")
            logger.info("=" * 60)

            return SkillGapAnalysisResponse(
                github_username=request.github_username,
                target_role=request.target_role,
                overall_match_score=overall_match_score,
                skill_analysis=skill_analysis,
                strengths=strengths,
                gaps=gaps,
                recommendations=recommendations_data["recommendations"],
                learning_resources=recommendations_data["learning_resources"],
                analysis_summary=analysis_summary,
                generated_at=datetime.utcnow(),
            )

        except Exception as e:
            logger.error(f"💥 ERROR in skill gap analysis for {request.github_username}: {e}")
            logger.error(f"⏱️  Failed after {time.time() - start_time:.2f} seconds")
            raise

    def _create_gap_analysis_summary(self, match_score: int, strengths_count: int, gaps_count: int, target_role: str) -> str:
        """Create a summary of the skill gap analysis."""
        if match_score >= 80:
            summary = f"Excellent match for {target_role} role! You have strong foundational skills with {strengths_count} key strengths."
        elif match_score >= 60:
            summary = f"Good match for {target_role} role. You have {strengths_count} strengths but {gaps_count} areas for improvement."
        elif match_score >= 40:
            summary = f"Moderate match for {target_role} role. Consider developing {gaps_count} key skills to strengthen your profile."
        else:
            summary = f"Significant gaps for {target_role} role. Focus on building {gaps_count} core skills to become competitive."

        if gaps_count > 0:
            summary += " Prioritize learning the missing skills to improve your overall match score."

        return summary

    def _analyze_contributor_focus(self, contributor_commits: List[Dict[str, Any]], languages: List[str]) -> str:
        """Analyze a contributor's focus area based on their commits and languages."""
        if not contributor_commits:
            return "general"

        # Analyze commit messages for focus areas
        commit_messages = [commit.get("message", "").lower() for commit in contributor_commits]

        focus_scores = {"frontend": 0, "backend": 0, "testing": 0, "devops": 0, "documentation": 0, "design": 0}

        # Keywords for different focus areas
        focus_keywords = {
            "frontend": ["frontend", "ui", "ux", "component", "react", "vue", "angular", "css", "html", "javascript"],
            "backend": ["backend", "api", "server", "database", "sql", "python", "java", "node", "php"],
            "testing": ["test", "spec", "jest", "pytest", "selenium", "cypress", "coverage"],
            "devops": ["docker", "kubernetes", "ci", "cd", "pipeline", "deploy", "aws", "terraform"],
            "documentation": ["readme", "docs", "documentation", "comment", "guide"],
            "design": ["design", "architecture", "structure", "pattern", "system"],
        }

        for message in commit_messages:
            for focus, keywords in focus_keywords.items():
                if any(keyword in message for keyword in keywords):
                    focus_scores[focus] += 1

        # Language-based focus hints
        language_hints = {
            "frontend": ["javascript", "typescript", "html", "css"],
            "backend": ["python", "java", "php", "ruby", "go", "rust"],
            "devops": ["shell", "yaml", "dockerfile"],
        }

        for focus, langs in language_hints.items():
            if any(lang in " ".join(languages).lower() for lang in langs):
                focus_scores[focus] += 2

        # Return the focus with highest score
        if max(focus_scores.values()) > 0:
            return max(focus_scores.items(), key=lambda x: x[1])[0]

        return "general"

    def _extract_key_contributions(self, contributor_commits: List[Dict[str, Any]], max_contributions: int = 3) -> List[str]:
        """Extract key contributions from a contributor's commits."""
        if not contributor_commits:
            return []

        contributions = []

        # Look for significant commits (those with many files changed or important keywords)
        significant_commits = []
        for commit in contributor_commits:
            files_changed = commit.get("files_changed", 0)
            message = commit.get("message", "").lower()

            # Score significance
            significance_score = 0
            significance_score += files_changed * 2  # Files changed
            significance_score += len(message.split()) // 10  # Message length
            if any(word in message for word in ["add", "implement", "create", "build", "feature"]):
                significance_score += 5
            if any(word in message for word in ["fix", "resolve", "correct", "bug"]):
                significance_score += 3

            significant_commits.append((commit, significance_score))

        # Sort by significance and take top contributions
        significant_commits.sort(key=lambda x: x[1], reverse=True)

        for commit, _ in significant_commits[:max_contributions]:
            message = commit.get("message", "").strip()
            if message:
                # Clean up the message for presentation
                if message.startswith("feat: ") or message.startswith("fix: "):
                    message = message.split(": ", 1)[1]
                message = message[0].upper() + message[1:]
                contributions.append(message)

        return contributions

    async def generate_multi_contributor_recommendation(self, request: MultiContributorRequest) -> MultiContributorResponse:
        """Generate a recommendation highlighting multiple contributors to a repository."""
        import time

        start_time = time.time()

        try:
            logger.info("👥 MULTI-CONTRIBUTOR RECOMMENDATION STARTED")
            logger.info("=" * 60)
            logger.info(f"📁 Repository: {request.repository_full_name}")
            logger.info(f"👥 Max Contributors: {request.max_contributors}")
            logger.info(f"📈 Min Contributions: {request.min_contributions}")

            # Get repository contributors
            logger.info("🔍 STEP 1: FETCHING REPOSITORY CONTRIBUTORS")
            logger.info("-" * 50)

            contributors_data = await self.github_service.get_repository_contributors(
                request.repository_full_name, max_contributors=request.max_contributors * 2, force_refresh=False  # Get more to filter
            )

            if not contributors_data:
                logger.error(f"❌ Failed to get contributors for {request.repository_full_name}")
                raise ValueError(f"Could not get contributors for {request.repository_full_name}")

            contributors = contributors_data.get("contributors", [])
            logger.info(f"✅ Found {len(contributors)} total contributors")

            # Filter contributors by minimum contributions
            qualified_contributors = [c for c in contributors if c.get("contributions", 0) >= request.min_contributions][: request.max_contributors]

            if len(qualified_contributors) < 2:
                logger.warning(f"⚠️  Only {len(qualified_contributors)} qualified contributors found")
                # Continue anyway, but note the limitation

            logger.info(f"✅ Analyzing {len(qualified_contributors)} qualified contributors")

            # Analyze each contributor
            logger.info("🔍 STEP 2: ANALYZING INDIVIDUAL CONTRIBUTORS")
            logger.info("-" * 50)

            analyzed_contributors = []

            for i, contributor in enumerate(qualified_contributors):
                username = contributor.get("username")
                logger.info(f"   • Analyzing contributor {i+1}: {username}")

                try:
                    # Get contributor's GitHub profile
                    contributor_profile = await self.github_service.analyze_github_profile(username=username, force_refresh=False)

                    if contributor_profile:
                        # Extract key information
                        user_data = contributor_profile.get("user_data", {})
                        skills = contributor_profile.get("skills", {})
                        languages = contributor_profile.get("languages", [])

                        # Get contributor's commits to this repository
                        # Note: This is a simplified approach - in a real implementation,
                        # you'd want to filter commits by repository
                        commit_analysis = contributor_profile.get("commit_analysis", {})
                        contributor_commits = []
                        if commit_analysis.get("total_commits_analyzed", 0) > 0:
                            # This is approximate - ideally we'd get repo-specific commits
                            contributor_commits = [{"message": f"Contribution to {request.repository_full_name}", "files_changed": contributor.get("contributions", 0)}]

                        # Analyze contributor focus
                        primary_languages = [lang.get("language") for lang in languages[:3]]
                        contribution_focus = self._analyze_contributor_focus(contributor_commits, primary_languages)

                        # Extract key contributions
                        key_contributions = self._extract_key_contributions(contributor_commits)

                        # Get top skills
                        technical_skills = skills.get("technical_skills", [])[:3]
                        frameworks = skills.get("frameworks", [])[:2]
                        top_skills = technical_skills + frameworks

                        contributor_info = ContributorInfo(
                            username=username,
                            full_name=user_data.get("full_name") or user_data.get("name"),
                            contributions=contributor.get("contributions", 0),
                            primary_languages=primary_languages,
                            top_skills=top_skills,
                            contribution_focus=contribution_focus,
                            key_contributions=key_contributions,
                        )

                        analyzed_contributors.append(contributor_info)

                except Exception as e:
                    logger.warning(f"Could not analyze contributor {username}: {e}")
                    # Add basic info for contributor we couldn't analyze fully
                    contributor_info = ContributorInfo(
                        username=username,
                        full_name=contributor.get("full_name") or username,
                        contributions=contributor.get("contributions", 0),
                        primary_languages=[],
                        top_skills=[],
                        contribution_focus="general",
                        key_contributions=[],
                    )
                    analyzed_contributors.append(contributor_info)

            # Generate team insights
            logger.info("💡 STEP 3: GENERATING TEAM INSIGHTS")
            logger.info("-" * 50)

            team_highlights = self._generate_team_highlights(analyzed_contributors, contributors_data)
            collaboration_insights = self._generate_collaboration_insights(analyzed_contributors)
            technical_diversity = self._calculate_technical_diversity(analyzed_contributors)

            # Generate the multi-contributor recommendation
            logger.info("🤖 STEP 4: GENERATING AI RECOMMENDATION")
            logger.info("-" * 50)

            ai_result = await self.ai_service._generate_multi_contributor_recommendation(
                repository_data={"repository_info": {"name": request.repository_full_name.split("/")[-1]}},
                contributors=[c.dict() for c in analyzed_contributors],
                team_highlights=team_highlights,
                collaboration_insights=collaboration_insights,
                technical_diversity=technical_diversity,
                recommendation_type=request.recommendation_type,
                tone=request.tone,
                length=request.length,
                focus_areas=request.focus_areas,
            )

            logger.info("🎉 MULTI-CONTRIBUTOR RECOMMENDATION COMPLETED")
            logger.info("-" * 50)
            logger.info(f"📊 Contributors Analyzed: {len(analyzed_contributors)}")
            logger.info(f"📝 Recommendation Length: {ai_result['word_count']} words")
            logger.info(f"🎯 Confidence Score: {ai_result['confidence_score']}")
            logger.info("=" * 60)

            return MultiContributorResponse(
                repository_name=request.repository_full_name.split("/")[-1],
                repository_full_name=request.repository_full_name,
                total_contributors=len(contributors),
                contributors_analyzed=len(analyzed_contributors),
                contributors=analyzed_contributors,
                recommendation=ai_result["recommendation"],
                team_highlights=team_highlights,
                collaboration_insights=collaboration_insights,
                technical_diversity=technical_diversity,
                word_count=ai_result["word_count"],
                confidence_score=ai_result["confidence_score"],
                generated_at=datetime.utcnow(),
            )

        except Exception as e:
            logger.error(f"💥 ERROR in multi-contributor recommendation for {request.repository_full_name}: {e}")
            logger.error(f"⏱️  Failed after {time.time() - start_time:.2f} seconds")
            raise

    def _generate_team_highlights(self, contributors: List[ContributorInfo], contributors_data: Dict[str, Any]) -> List[str]:
        """Generate highlights about the team as a whole."""
        highlights: List[str] = []

        if not contributors:
            return highlights

        # Total contributions
        total_contributions = sum(c.contributions for c in contributors)
        highlights.append(f"Team of {len(contributors)} contributors with {total_contributions} total contributions")

        # Technical diversity
        all_languages = set()
        for contributor in contributors:
            all_languages.update(contributor.primary_languages)

        if len(all_languages) > 1:
            highlights.append(f"Technically diverse team working with {len(all_languages)} programming languages")

        # Collaboration indicators
        focus_areas = [c.contribution_focus for c in contributors if c.contribution_focus != "general"]
        if len(set(focus_areas)) > 1:
            highlights.append("Well-balanced team with complementary technical expertise")

        # High contributors
        high_contributors = [c for c in contributors if c.contributions > 10]
        if high_contributors:
            highlights.append(f"{len(high_contributors)} highly active contributors driving project success")

        return highlights[:5]  # Limit to top 5 highlights

    def _generate_collaboration_insights(self, contributors: List[ContributorInfo]) -> List[str]:
        """Generate insights about team collaboration."""
        insights: List[str] = []

        if not contributors:
            return insights

        # Focus area distribution
        focus_counts: Dict[str, int] = {}
        for contributor in contributors:
            focus = contributor.contribution_focus
            focus_counts[focus] = focus_counts.get(focus, 0) + 1

        # Identify collaboration patterns
        if len([c for c in contributors if c.contribution_focus == "frontend"]) > 0 and len([c for c in contributors if c.contribution_focus == "backend"]) > 0:
            insights.append("Strong frontend-backend collaboration for full-stack development")

        if len([c for c in contributors if c.contribution_focus == "testing"]) > 0:
            insights.append("Dedicated quality assurance with specialized testing expertise")

        if len([c for c in contributors if c.contribution_focus == "devops"]) > 0:
            insights.append("DevOps expertise ensuring smooth deployment and infrastructure management")

        # Skill diversity
        all_skills = set()
        for contributor in contributors:
            all_skills.update(contributor.top_skills)

        if len(all_skills) > len(contributors) * 2:
            insights.append("High skill diversity enabling comprehensive project coverage")

        return insights[:4]  # Limit to top 4 insights

    def _calculate_technical_diversity(self, contributors: List[ContributorInfo]) -> Dict[str, int]:
        """Calculate technical diversity across the team."""
        language_counts: Dict[str, int] = {}
        skill_counts: Dict[str, int] = {}

        for contributor in contributors:
            # Count languages
            for language in contributor.primary_languages:
                language_counts[language] = language_counts.get(language, 0) + 1

            # Count skills
            for skill in contributor.top_skills:
                skill_counts[skill] = skill_counts.get(skill, 0) + 1

        # Combine into a single diversity metric
        diversity = {}
        diversity.update(language_counts)
        diversity.update(skill_counts)

        return dict(sorted(diversity.items(), key=lambda x: x[1], reverse=True)[:10])

    def _merge_repository_and_contributor_data(
        self,
        repository_data: Dict[str, Any],
        contributor_data: Dict[str, Any],
        contributor_username: str,
    ) -> Dict[str, Any]:
        """Merge repository analysis data with contributor profile data."""
        logger.info(f"🔄 Merging repository and contributor data for {contributor_username}")

        # Start with contributor's profile data as the base
        merged_data = contributor_data.copy()

        # Add repository-specific information
        if repository_data:
            merged_data["repository_info"] = repository_data.get("repository_info", {})
            merged_data["repository_languages"] = repository_data.get("languages", [])
            merged_data["repository_commits"] = repository_data.get("commits", [])
            merged_data["repository_skills"] = repository_data.get("skills", {})
            merged_data["repository_commit_analysis"] = repository_data.get("commit_analysis", {})

            # Update skills to include repository-specific skills
            if "skills" in merged_data and repository_data.get("skills"):
                repo_skills = repository_data["skills"]
                contributor_skills = merged_data["skills"]

                # Merge technical skills
                if repo_skills.get("technical_skills"):
                    contributor_skills["technical_skills"] = list(set(contributor_skills.get("technical_skills", []) + repo_skills["technical_skills"]))

                # Merge frameworks
                if repo_skills.get("frameworks"):
                    contributor_skills["frameworks"] = list(set(contributor_skills.get("frameworks", []) + repo_skills["frameworks"]))

                # Merge tools
                if repo_skills.get("tools"):
                    contributor_skills["tools"] = list(set(contributor_skills.get("tools", []) + repo_skills["tools"]))

                # Merge domains
                if repo_skills.get("domains"):
                    contributor_skills["domains"] = list(set(contributor_skills.get("domains", []) + repo_skills["domains"]))

            # Update commit analysis to focus on repository-specific contributions
            if repository_data.get("commit_analysis") and contributor_data.get("commit_analysis"):
                # Use repository-specific commit analysis if available
                merged_data["commit_analysis"] = repository_data["commit_analysis"]
                merged_data["commit_analysis"]["contributor_focused"] = True
                merged_data["commit_analysis"]["repository_context"] = repository_data.get("repository_info", {}).get("full_name", "")

        # Add metadata about the analysis type
        merged_data["analysis_context_type"] = "repository_contributor"
        merged_data["target_repository"] = repository_data.get("repository_info", {}).get("full_name", "")
        merged_data["contributor_username"] = contributor_username

        logger.info(f"✅ Merged data created with analysis_context_type: {merged_data['analysis_context_type']}")
        return merged_data

    async def create_recommendation_from_option(
        self,
        db: AsyncSession,
        github_username: str,
        selected_option: Dict[str, Any],
        all_options: List[Dict[str, Any]],
        user_id: Optional[int] = None,  # Added user_id
        analysis_context_type: str = "profile",
        repository_url: Optional[str] = None,
        recommendation_type: Optional[str] = None,
        tone: Optional[str] = None,
        length: Optional[str] = None,
    ) -> RecommendationResponse:
        """Create a recommendation from a selected option."""

        import time
        from typing import Optional

        start_time = time.time()

        try:
            logger.info("🔍 STEP 1: GITHUB PROFILE ANALYSIS")
            logger.info("-" * 50)
            github_start = time.time()

            # Determine analysis type and get GitHub data
            github_data: Optional[Dict[str, Any]] = None
            if analysis_context_type == "repo_only" and repository_url:
                logger.info(f"📁 Analyzing repository: {repository_url}")
                # Extract repository name from URL
                if "/" in repository_url:
                    repo_parts = repository_url.split("/")
                    repo_name = repo_parts[-2] + "/" + repo_parts[-1]
                else:
                    repo_name = repository_url

                # Analyze the repository
                repository_data = await self.repository_service.analyze_repository(repository_full_name=repo_name, force_refresh=False)

                # Analyze the specific contributor's profile
                logger.info(f"👤 Analyzing contributor profile: {github_username}")
                contributor_data = await self.github_service.analyze_github_profile(username=github_username, force_refresh=False)

                # Merge repository and contributor data
                if contributor_data and repository_data:
                    github_data = self._merge_repository_and_contributor_data(repository_data, contributor_data, github_username)
                elif contributor_data:
                    github_data = contributor_data
                else:
                    github_data = repository_data
            else:
                logger.info(f"👤 Analyzing profile: {github_username}")
                github_data = await self.github_service.analyze_github_profile(username=github_username, force_refresh=False)

            github_end = time.time()
            logger.info(f"⏱️  GitHub analysis completed in {github_end - github_start:.2f} seconds")

            if not github_data:
                if analysis_context_type == "repo_only":
                    logger.error(f"❌ Failed to analyze GitHub repository: {repository_url}")
                    raise ValueError(f"Could not analyze GitHub repository: {repository_url}")
                else:
                    logger.error(f"❌ Failed to analyze GitHub profile for {github_username}")
                    raise ValueError(f"Could not analyze GitHub profile for {github_username}")

            # Get or create GitHub profile record
            logger.info("💾 STEP 2: DATABASE OPERATIONS")
            logger.info("-" * 50)
            db_start = time.time()

            github_profile = await self._get_or_create_github_profile(db, github_data)
            logger.debug(f"➡️ GitHub Profile ID: {github_profile.id}")

            db_end = time.time()
            logger.info(f"⏱️  Database operations completed in {db_end - db_start:.2f} seconds")
            logger.info(f"✅ GitHub profile record: {'Updated' if github_profile else 'Created'}")

            # Create recommendation record with selected option information
            logger.info("💾 STEP 3: SAVING RECOMMENDATION FROM SELECTED OPTION")
            logger.info("-" * 50)
            save_start = time.time()

            # Extract generation parameters from the selected option
            generation_parameters = {
                "model": selected_option.get("generation_parameters", {}).get("model", "unknown"),
                "temperature": selected_option.get("generation_parameters", {}).get("temperature", 0.7),
                "max_tokens": selected_option.get("generation_parameters", {}).get("max_tokens", 1000),
                "selected_from_options": True,
                "selected_option_id": selected_option.get("id"),
                "selected_option_name": selected_option.get("name"),
                "selected_option_focus": selected_option.get("focus"),
                "analysis_context_type": analysis_context_type,
                "repository_url": repository_url,
                "recommendation_type": recommendation_type or selected_option.get("focus", "professional"),
                "tone": tone or "professional",
                "length": length or "medium",
            }
            logger.debug(f"➡️ Generated Parameters: {generation_parameters}")
            logger.debug(f"➡️ Selected Option Content Length: {len(selected_option.get('content', ''))}")

            recommendation_data = RecommendationCreate(
                github_profile_id=int(github_profile.id),
                title=selected_option.get(
                    "title",
                    f"Professional Recommendation for {github_username}",
                ),
                content=selected_option["content"],
                recommendation_type=recommendation_type or selected_option.get("focus", "professional"),
                tone=tone or "professional",
                length=length or "medium",
                ai_model=generation_parameters["model"],
                generation_prompt=None,  # This comes from the options generation
                generation_parameters=generation_parameters,
                confidence_score=selected_option.get("confidence_score", 0),
                word_count=selected_option.get("word_count", 0),
                selected_option_id=selected_option.get("id"),
                selected_option_name=selected_option.get("name"),
                selected_option_focus=selected_option.get("focus"),
                generated_options=all_options,  # Store all options for reference
            )
            logger.debug(f"➡️ RecommendationCreate data: {recommendation_data.dict()}")

            recommendation = Recommendation(**recommendation_data.dict())
            db.add(recommendation)
            await db.commit()
            await db.refresh(recommendation)
            logger.debug(f"➡️ Recommendation saved to DB with ID: {recommendation.id}")

            save_end = time.time()
            logger.info(f"⏱️  Database save completed in {save_end - save_start:.2f} seconds")
            logger.info(f"✅ Recommendation saved with ID: {recommendation.id}")
            logger.info(f"✅ Selected option: {selected_option.get('name')} (Focus: {selected_option.get('focus')})")

            # Convert to response
            response = RecommendationResponse.from_orm(recommendation)
            response.github_username = github_username

            end_time = time.time()
            total_time = end_time - start_time

            logger.info("🎉 RECOMMENDATION CREATION FROM OPTION SUMMARY")
            logger.info("-" * 50)
            logger.info(f"⏱️  Total processing time: {total_time:.2f} seconds")
            logger.info("📊 Breakdown:")
            logger.info(f"   • GitHub Analysis: {github_end - github_start:.2f}s ({((github_end - github_start)/total_time)*100:.1f}%)")
            logger.info(f"   • Database Ops: {db_end - db_start:.2f}s ({((db_end - db_start)/total_time)*100:.1f}%)")
            logger.info(f"   • Save Record: {save_end - save_start:.2f}s ({((save_end - save_start)/total_time)*100:.1f}%)")

            return response

        except Exception as e:
            logger.error(f"💥 ERROR in recommendation creation from option for {github_username}: {e}")
            logger.error(f"⏱️  Failed after {time.time() - start_time:.2f} seconds")
            await db.rollback()
            raise
