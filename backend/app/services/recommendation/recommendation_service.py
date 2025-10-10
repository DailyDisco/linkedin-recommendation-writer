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
    RecommendationCreate,
    RecommendationOptionsResponse,
    RecommendationResponse,
    RecommendationVersionDetail,
    RecommendationVersionHistoryResponse,
    RecommendationVersionInfo,
    VersionComparisonResponse,
)
from app.services.ai.ai_service_new import AIService
from app.services.github.github_commit_service import GitHubCommitService
from app.services.github.github_repository_service import GitHubRepositoryService
from app.services.github.github_user_service import GitHubUserService
from app.services.recommendation.recommendation_engine_service import RecommendationEngineService

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
        self.recommendation_engine_service = RecommendationEngineService(self.ai_service)

    async def create_recommendation(
        self,
        db: AsyncSession,
        github_username: str,
        user_id: Optional[int] = None,  # Added user_id
        recommendation_type: str = "professional",
        tone: str = "professional",
        length: str = "medium",
        custom_prompt: Optional[str] = None,
        shared_work_context: Optional[str] = None,
        target_role: Optional[str] = None,
        specific_skills: Optional[List[str]] = None,
        include_keywords: Optional[List[str]] = None,
        exclude_keywords: Optional[List[str]] = None,
        analysis_context_type: str = "profile",
        repository_url: Optional[str] = None,
        force_refresh: bool = False,
    ) -> RecommendationResponse:
        """Create a new recommendation."""

        logger.info("🔍 DEBUG: create_recommendation called with:")
        logger.info(f"   • github_username: {github_username}")
        logger.info(f"   • analysis_context_type: {analysis_context_type}")
        logger.info(f"   • repository_url: {repository_url}")
        logger.info(f"   • force_refresh: {force_refresh}")

        # Log parameter validation for repo_only mode
        if analysis_context_type == "repo_only":
            logger.info("🎯 REPO_ONLY MODE DETECTED")
            if not repository_url:
                logger.warning("⚠️  REPO_ONLY mode but no repository_url provided!")
            else:
                logger.info(f"✅ REPO_ONLY: Will analyze repository: {repository_url}")
        elif analysis_context_type == "repository_contributor":
            logger.info("👥 REPOSITORY CONTRIBUTOR MODE DETECTED")
        else:
            logger.info("👤 PROFILE MODE (default)")

        import time

        start_time = time.time()

        try:
            logger.info("🔍 STEP 1: GITHUB DATA ANALYSIS")
            logger.info("-" * 50)
            logger.info(f"   • Analysis Context: {analysis_context_type}")
            logger.info(f"   • Repository URL: {repository_url or 'N/A'}")
            github_start = time.time()

            # Conditionally fetch GitHub data based on analysis context
            if analysis_context_type == "repo_only" and repository_url:
                logger.info("📦 Analyzing specific repository...")
                # Extract owner/repo from URL
                repo_path = repository_url.replace("https://github.com/", "").split("?")[0]
                if "/" in repo_path:
                    owner, repo = repo_path.split("/", 1)
                    github_data = await self.repository_service.analyze_repository(f"{owner}/{repo}", force_refresh=False)

                    if github_data:
                        # For repo_only, we need to create a minimal profile structure
                        # Merge repository data with basic contributor info
                        contributor_data = await self.github_service.analyze_github_profile(username=github_username, force_refresh=False)
                        if contributor_data:
                            github_data = self._merge_repository_and_contributor_data(github_data, contributor_data, github_username, analysis_context_type)
                        else:
                            logger.warning(f"Could not fetch contributor data for {github_username}, using repository data only")

                else:
                    raise ValueError(f"Invalid repository URL format: {repository_url}")

            elif analysis_context_type == "repository_contributor" and repository_url:
                logger.info("👥 Analyzing repository with contributor context...")
                # Get full profile data but emphasize repository context
                github_data = await self.github_service.analyze_github_profile(username=github_username, force_refresh=False)

                if github_data and repository_url:
                    # Extract owner/repo from URL and get repository-specific data
                    repo_path = repository_url.replace("https://github.com/", "").split("?")[0]
                    if "/" in repo_path:
                        owner, repo = repo_path.split("/", 1)
                        repo_data = await self.repository_service.analyze_repository(f"{owner}/{repo}", force_refresh=False)
                        if repo_data:
                            github_data = self._merge_repository_and_contributor_data(repo_data, github_data, github_username, analysis_context_type)

            else:
                logger.info("👤 Analyzing full GitHub profile...")
                # Default: analyze full profile
                github_data = await self.github_service.analyze_github_profile(username=github_username, force_refresh=False)

            github_end = time.time()
            logger.info(f"⏱️  GitHub analysis completed in {github_end - github_start:.2f} seconds")

            if not github_data:
                context_desc = "repository" if analysis_context_type == "repo_only" else "GitHub profile"
                logger.error(f"❌ Failed to analyze {context_desc} for {github_username}")
                raise ValueError(f"Could not analyze {context_desc} for {github_username}")

            logger.info("✅ GitHub analysis successful:")
            logger.info(f"   • Analysis Type: {analysis_context_type}")
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

            ai_result = await self.recommendation_engine_service.generate_recommendation(
                github_data=github_data,
                recommendation_type=recommendation_type,
                tone=tone,
                length=length,
                custom_prompt=custom_prompt,
                shared_work_context=shared_work_context,
                target_role=target_role,
                specific_skills=specific_skills,
                exclude_keywords=exclude_keywords,
                analysis_context_type=analysis_context_type,
                repository_url=repository_url,
                force_refresh=force_refresh,
            )

            ai_end = time.time()
            logger.info(f"⏱️  AI generation completed in {ai_end - ai_start:.2f} seconds")
            logger.info("✅ AI recommendation generated:")
            logger.info(f"   • Content length: {len(ai_result['content'])} characters")
            logger.info(f"   • Word count: {ai_result['word_count']}")

            # Create recommendation record
            logger.info("💾 STEP 4: SAVING RECOMMENDATION")
            logger.info("-" * 50)
            save_start = time.time()

            recommendation_data = self.recommendation_engine_service.create_recommendation_data(
                ai_result=ai_result,
                github_profile_id=github_profile.id,  # type: ignore
                recommendation_type=recommendation_type,
                tone=tone,
                length=length,
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

        logger.info("🔍 DEBUG: create_recommendation_options called with:")
        logger.info(f"   • github_username: {github_username}")
        logger.info(f"   • analysis_context_type: {analysis_context_type}")
        logger.info(f"   • repository_url: {repository_url}")

        import time

        start_time = time.time()

        try:
            logger.info("🎭 STEP 1: GITHUB DATA ANALYSIS")
            logger.info("-" * 50)
            logger.info(f"   • Analysis Context: {analysis_context_type}")
            logger.info(f"   • Repository URL: {repository_url or 'N/A'}")
            github_start = time.time()

            # Conditionally fetch GitHub data based on analysis context
            logger.info("🔍 DEBUG: Checking repo_only condition in create_recommendation_options:")
            logger.info(f"   • analysis_context_type: '{analysis_context_type}'")
            logger.info(f"   • repository_url: '{repository_url}'")
            logger.info(f"   • condition check: {analysis_context_type == 'repo_only' and repository_url is not None}")

            if analysis_context_type == "repo_only" and repository_url:
                logger.info("📦 Analyzing specific repository...")
                # Extract owner/repo from URL
                repo_path = repository_url.replace("https://github.com/", "").split("?")[0]
                if "/" in repo_path:
                    owner, repo = repo_path.split("/", 1)
                    github_data = await self.repository_service.analyze_repository(f"{owner}/{repo}", force_refresh=False)

                    if github_data:
                        # For repo_only, we need to create a minimal profile structure
                        # Merge repository data with basic contributor info
                        contributor_data = await self.github_service.analyze_github_profile(username=github_username, force_refresh=False)
                        if contributor_data:
                            github_data = self._merge_repository_and_contributor_data(github_data, contributor_data, github_username, analysis_context_type)
                        else:
                            logger.warning(f"Could not fetch contributor data for {github_username}, using repository data only")

                else:
                    raise ValueError(f"Invalid repository URL format: {repository_url}")

            elif analysis_context_type == "repository_contributor" and repository_url:
                logger.info("👥 Analyzing repository with contributor context...")
                # Get full profile data but emphasize repository context
                github_data = await self.github_service.analyze_github_profile(username=github_username, force_refresh=False)

                if github_data and repository_url:
                    # Extract owner/repo from URL and get repository-specific data
                    repo_path = repository_url.replace("https://github.com/", "").split("?")[0]
                    if "/" in repo_path:
                        owner, repo = repo_path.split("/", 1)
                        repo_data = await self.repository_service.analyze_repository(f"{owner}/{repo}", force_refresh=False)
                        if repo_data:
                            github_data = self._merge_repository_and_contributor_data(repo_data, github_data, github_username, analysis_context_type)

            else:
                logger.info("👤 Analyzing full GitHub profile...")
                # Default: analyze full profile
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

            # For repo_only context, we don't need to store/retrieve profile data from database
            # since we're only using repository-specific data
            if analysis_context_type == "repo_only":
                logger.info("🔒 REPO_ONLY: Skipping database profile operations - using repository-only data")
                github_profile = None
            else:
                github_profile = await self._get_or_create_github_profile(db, github_data)

            db_end = time.time()
            logger.info(f"⏱️  Database operations completed in {db_end - db_start:.2f} seconds")
            if analysis_context_type != "repo_only":
                logger.info(f"✅ GitHub profile record: {'Updated' if github_profile else 'Created'}")
            else:
                logger.info("✅ REPO_ONLY: Database operations skipped")

            # Generate AI recommendation options
            logger.info("🤖 STEP 3: AI RECOMMENDATION OPTIONS GENERATION")
            logger.info("-" * 50)
            ai_start = time.time()

            response = await self.recommendation_engine_service.generate_recommendation_options(
                github_data=github_data,
                base_recommendation_type=recommendation_type,
                base_tone=tone,
                base_length=length,
                target_role=target_role,
                specific_skills=specific_skills,
            )

            ai_end = time.time()
            logger.info(f"⏱️  AI generation completed in {ai_end - ai_start:.2f} seconds")
            logger.info("✅ AI recommendation options generated:")
            logger.info(f"   • Options: {len(response.options)}")

            end_time = time.time()
            total_time = end_time - start_time

            logger.info("🎉 RECOMMENDATION OPTIONS CREATION SUMMARY")
            logger.info("-" * 50)
            logger.info(f"⏱️  Total processing time: {total_time:.2f} seconds")
            logger.info("📊 Breakdown:")
            logger.info(f"   • GitHub Analysis: {github_end - github_start:.2f}s ({((github_end - github_start)/total_time)*100:.1f}%)")
            logger.info(f"   • Database Ops: {db_end - db_start:.2f}s ({((db_end - db_start)/total_time)*100:.1f}%)")
            logger.info(f"   • AI Generation: {ai_end - ai_start:.2f}s ({((ai_end - ai_start)/total_time)*100:.1f}%)")

            # Return both the options response and the filtered GitHub data for streaming
            return {"options_response": response, "github_data": github_data}

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
        shared_work_context: Optional[str] = None,
        analysis_context_type: str = "profile",
        repository_url: Optional[str] = None,
        force_refresh: bool = False,
        display_name: Optional[str] = None,
    ) -> RecommendationResponse:
        """Regenerate a recommendation with refinement instructions."""

        import time

        start_time = time.time()

        try:
            logger.info("🔄 STEP 1: GITHUB DATA ANALYSIS")
            logger.info("-" * 50)
            logger.info(f"   • Analysis Context: {analysis_context_type}")
            logger.info(f"   • Repository URL: {repository_url or 'N/A'}")
            github_start = time.time()

            # Conditionally fetch GitHub data based on analysis context (same logic as create_recommendation)
            if analysis_context_type == "repo_only" and repository_url:
                logger.info("📦 Analyzing specific repository...")
                # Extract owner/repo from URL
                repo_path = repository_url.replace("https://github.com/", "").split("?")[0]
                if "/" in repo_path:
                    owner, repo = repo_path.split("/", 1)
                    github_data = await self.repository_service.analyze_repository(f"{owner}/{repo}", force_refresh=False)

                    if github_data:
                        # For repo_only, we need to create a minimal profile structure
                        # Merge repository data with basic contributor info
                        contributor_data = await self.github_service.analyze_github_profile(username=github_username, force_refresh=False)
                        if contributor_data:
                            github_data = self._merge_repository_and_contributor_data(github_data, contributor_data, github_username, analysis_context_type)
                        else:
                            logger.warning(f"Could not fetch contributor data for {github_username}, using repository data only")

                else:
                    raise ValueError(f"Invalid repository URL format: {repository_url}")

            elif analysis_context_type == "repository_contributor" and repository_url:
                logger.info("👥 Analyzing repository with contributor context...")
                # Get full profile data but emphasize repository context
                github_data = await self.github_service.analyze_github_profile(username=github_username, force_refresh=False)

                if github_data and repository_url:
                    # Extract owner/repo from URL and get repository-specific data
                    repo_path = repository_url.replace("https://github.com/", "").split("?")[0]
                    if "/" in repo_path:
                        owner, repo = repo_path.split("/", 1)
                        repo_data = await self.repository_service.analyze_repository(f"{owner}/{repo}", force_refresh=False)
                        if repo_data:
                            github_data = self._merge_repository_and_contributor_data(repo_data, github_data, github_username, analysis_context_type)

            else:
                logger.info("👤 Analyzing full GitHub profile...")
                # Default: analyze full profile
                github_data = await self.github_service.analyze_github_profile(username=github_username, force_refresh=False)

            github_end = time.time()
            logger.info(f"⏱️  GitHub analysis completed in {github_end - github_start:.2f} seconds")

            if not github_data:
                context_desc = "repository" if analysis_context_type == "repo_only" else "GitHub profile"
                logger.error(f"❌ Failed to analyze {context_desc} for {github_username}")
                raise ValueError(f"Could not analyze {context_desc} for {github_username}")
            logger.debug(f"➡️ GitHub data used for recommendation regeneration: {github_data}")  # Log github_data

            # Extract display name for consistent naming (prioritizes first name)
            if display_name is None and github_data.get("user_data"):
                from app.services.ai.prompt_service import PromptService

                prompt_service = PromptService()
                display_name = prompt_service._extract_display_name(github_data["user_data"])

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

            ai_result = await self.recommendation_engine_service.regenerate_recommendation(
                original_content=original_content,
                refinement_instructions=refinement_instructions,
                github_data=github_data,
                recommendation_type=recommendation_type,
                tone=tone,
                length=length,
                shared_work_context=shared_work_context,
                analysis_context_type=analysis_context_type,
                repository_url=repository_url,
                force_refresh=force_refresh,
                display_name=display_name,
            )

            ai_end = time.time()
            logger.info(f"⏱️  AI regeneration completed in {ai_end - ai_start:.2f} seconds")
            logger.info("✅ AI recommendation regenerated:")
            logger.info(f"   • Content length: {len(ai_result['content'])} characters")
            logger.info(f"   • Word count: {ai_result['word_count']}")

            # Create recommendation record
            logger.info("💾 STEP 4: SAVING RECOMMENDATION")
            logger.info("-" * 50)
            save_start = time.time()

            # For repo_only mode, github_profile is None, so we use a placeholder ID
            github_profile_id = github_profile.id if github_profile else None

            recommendation_data = self.recommendation_engine_service.create_recommendation_data(
                ai_result=ai_result,
                github_profile_id=github_profile_id,
                recommendation_type=recommendation_type,
                tone=tone,
                length=length,
            )
            # Override the generation prompt with refinement instructions
            recommendation_data.generation_prompt = refinement_instructions

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

            end_time = time.time()
            total_time = end_time - start_time

            logger.info("🎉 README GENERATION COMPLETED")
            logger.info("-" * 50)
            logger.info(f"⏱️  Total processing time: {total_time:.2f} seconds")
            logger.info("📊 Final Results:")
            logger.info(f"   • Repository: {repository_full_name}")
            logger.info(f"   • Style: {style}")

            logger.info("=" * 60)

            return {
                "repository_name": repository_data.get("repository_info", {}).get("name", ""),
                "repository_full_name": repository_full_name,
                "generated_content": ai_result["generated_content"],
                "sections": ai_result["sections"],
                "word_count": ai_result["word_count"],
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
            "documentation": ["docs", "documentation", "comment", "guide"],
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

    def _merge_repository_and_contributor_data(
        self,
        repository_data: Dict[str, Any],
        contributor_data: Dict[str, Any],
        contributor_username: str,
        analysis_context_type: str = "repository_contributor",
    ) -> Dict[str, Any]:
        """Merge repository analysis data with contributor profile data."""
        logger.info(f"🔄 Merging repository and contributor data for {contributor_username} with context: {analysis_context_type}")

        if analysis_context_type == "repo_only":
            # For repo_only context, we want ONLY repository-specific data
            # Filter out general user profile information to prevent data leakage
            logger.info("🎯 REPO_ONLY MODE: Filtering out general user data")
            logger.info(f"🔍 REPO_ONLY: Input contributor_data keys: {list(contributor_data.keys())}")
            if "user_data" in contributor_data:
                logger.info(f"🔍 REPO_ONLY: contributor user_data keys: {list(contributor_data['user_data'].keys())}")
            logger.info(f"🔍 REPO_ONLY: Input repository_data keys: {list(repository_data.keys())}")
            if "repository_info" in repository_data:
                logger.info(f"🔍 REPO_ONLY: repository_info: {repository_data['repository_info']}")

            # Start with MINIMAL contributor data - include essential identity info for repo_only
            logger.info("🔍 REPO_ONLY: Creating MINIMAL contributor data (essential identity + username)")
            user_data_source = contributor_data.get("user_data", {})
            filtered_contributor_data = {
                "user_data": {
                    "github_username": user_data_source.get("github_username") or contributor_username,
                    "login": user_data_source.get("login") or contributor_username,
                    # Include essential identity information for natural recommendations
                    "full_name": user_data_source.get("full_name"),  # Real name is essential for personal recommendations
                    # EXCLUDE: bio, company, location, followers, etc. (general profile info)
                    # EXCLUDE: avatar_url, profile_url (not needed for text recommendations)
                }
            }
            logger.info(f"🔍 REPO_ONLY: MINIMAL user_data: {filtered_contributor_data['user_data']}")

            merged_data = filtered_contributor_data.copy()

            # Add repository-specific information with explicit overrides
            if repository_data:
                merged_data["repository_info"] = repository_data.get("repository_info", {})
                merged_data["repository_languages"] = repository_data.get("languages", [])
                merged_data["repository_commits"] = repository_data.get("commits", [])
                merged_data["repository_skills"] = repository_data.get("skills", {})
                merged_data["repository_commit_analysis"] = repository_data.get("commit_analysis", {})

                # CRITICAL: For repo_only, use ONLY repository-specific data
                # Do NOT merge with general contributor skills - this prevents data leakage
                merged_data["languages"] = repository_data.get("languages", [])
                merged_data["skills"] = repository_data.get("skills", {})
                merged_data["commit_analysis"] = repository_data.get("commit_analysis", {})

            # Add metadata about the analysis type
            merged_data["analysis_context_type"] = "repo_only"
            merged_data["target_repository"] = repository_data.get("repository_info", {}).get("full_name", "")
            merged_data["contributor_username"] = contributor_username

            logger.info("✅ REPO_ONLY: Filtered merged data created - general profile data excluded")
            logger.info(f"🔍 REPO_ONLY: Final merged_data keys: {list(merged_data.keys())}")
            if "user_data" in merged_data:
                logger.info(f"🔍 REPO_ONLY: Final user_data: {merged_data['user_data']}")
            if "repo_contributor_stats" in merged_data:
                logger.info(f"🔍 REPO_ONLY: repo_contributor_stats: {merged_data['repo_contributor_stats']}")

            # CRITICAL DEBUG: Log the complete merged data structure to see what gets passed to AI
            logger.info("🔍 REPO_ONLY: ======= COMPLETE MERGED DATA STRUCTURE =======")
            for key, value in merged_data.items():
                if key == "user_data":
                    logger.info(f"🔍 REPO_ONLY: user_data = {value}")
                elif key == "repo_contributor_stats":
                    logger.info(f"🔍 REPO_ONLY: repo_contributor_stats = {value}")
                elif key in ["languages", "skills", "commit_analysis", "repository_info"]:
                    logger.info(f"🔍 REPO_ONLY: {key} = {type(value)} (length: {len(value) if hasattr(value, '__len__') else 'N/A'})")
                else:
                    logger.info(f"🔍 REPO_ONLY: {key} = {value}")
            logger.info("🔍 REPO_ONLY: ===============================================")

            # VALIDATION: Ensure no profile data leaked through
            logger.info("🔍 REPO_ONLY: Running final validation...")
            validation_result = self._validate_repo_only_data_isolation(merged_data)
            if not validation_result["is_valid"]:
                logger.error("🚨 CRITICAL: Profile data contamination detected in repo_only data!")
                for issue in validation_result["issues"]:
                    logger.error(f"   • {issue}")
                raise ValueError(f"Profile data contamination in repo_only context: {validation_result['issues']}")
            else:
                logger.info("✅ REPO_ONLY: Validation PASSED - no profile data contamination")

            # FINAL DEBUG: Log what will be sent to AI
            logger.info("🎯 REPO_ONLY: FINAL DATA SENT TO AI:")
            logger.info(f"   • Username: {merged_data.get('user_data', {}).get('github_username', 'N/A')}")
            logger.info(f"   • Repository: {merged_data.get('repository_info', {}).get('full_name', 'N/A')}")
            logger.info(f"   • Languages: {len(merged_data.get('languages', []))} languages")
            logger.info(f"   • Skills: {len(merged_data.get('skills', {}).get('technical_skills', []))} technical skills")
            logger.info(f"   • Commits: {merged_data.get('commit_analysis', {}).get('total_commits', 0)} total commits")
            logger.info("🎯 REPO_ONLY: Data isolation complete - sending to AI")

            if validation_result["warnings"]:
                logger.warning("⚠️ REPO_ONLY: Validation warnings:")
                for warning in validation_result["warnings"]:
                    logger.warning(f"   • {warning}")

            logger.info("🎉 REPO_ONLY: Data isolation complete and validated")
            return merged_data

        else:
            # Original logic for repository_contributor and other contexts
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
            merged_data["analysis_context_type"] = analysis_context_type
            merged_data["target_repository"] = repository_data.get("repository_info", {}).get("full_name", "")
            merged_data["contributor_username"] = contributor_username

            logger.info(f"✅ Merged data created with analysis_context_type: {merged_data['analysis_context_type']}")
            return merged_data

    async def _get_or_create_github_profile_data(
        self,
        db: AsyncSession,
        github_username: str,
        analysis_context_type: str = "profile",
        repository_url: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        logger.info("🔍 DEBUG: _get_or_create_github_profile_data called with:")
        logger.info(f"   • username: {github_username}")
        logger.info(f"   • analysis_context_type: {analysis_context_type}")
        logger.info(f"   • repository_url: {repository_url}")
        """Get or create GitHub profile data with conditional analysis based on context."""

        # Conditionally fetch GitHub data based on analysis context
        logger.info(f"🔍 DEBUG: About to check repo_only condition: analysis_context_type='{analysis_context_type}', repository_url='{repository_url}'")
        if analysis_context_type == "repo_only" and repository_url:
            logger.info("📦 Analyzing specific repository for repo_only context...")
            # Extract owner/repo from URL
            repo_path = repository_url.replace("https://github.com/", "").split("?")[0]
            if "/" in repo_path:
                owner, repo = repo_path.split("/", 1)

                # Get repository data
                logger.info(f"🔍 DEBUG: Calling repository_service.analyze_repository for {owner}/{repo}")
                # CRITICAL: Pass target_username for repo_only context to ensure commit filtering
                repository_data = await self.repository_service.analyze_repository(
                    f"{owner}/{repo}",
                    force_refresh=False,
                    analysis_context_type=analysis_context_type,
                    repository_url=repository_url,
                    target_username=github_username if analysis_context_type == "repo_only" else None,
                )
                logger.info(f"🔍 DEBUG: Repository data returned keys: {list(repository_data.keys()) if repository_data else 'None'}")
                if repository_data:
                    logger.info("🔍 DEBUG: Repository data structure sample:")
                    for key in ["repository_info", "languages", "skills", "commits", "commit_analysis"]:
                        if key in repository_data:
                            value = repository_data[key]
                            if isinstance(value, (list, dict)):
                                logger.info(f"   • {key}: {type(value)} (length: {len(value)})")
                            else:
                                logger.info(f"   • {key}: {value}")

                if repository_data:
                    # Filter repository commits to only include the contributor's commits
                    filtered_commits = []
                    if repository_data.get("commits"):
                        filtered_commits = [
                            commit
                            for commit in repository_data["commits"]
                            if commit.get("author", {}).get("login", "").lower() == github_username.lower()
                            or commit.get("commit", {}).get("author", {}).get("name", "").lower() == github_username.lower()
                        ]

                    # Generate contributor commit summary for better recommendations
                    try:
                        logger.info(f"📝 Generating contributor commit summary for {github_username} in {repo_path}")
                        commit_service = GitHubCommitService()
                        contributor_summary = await commit_service.generate_contributor_commit_summary(github_username, repo_path, max_commits=50)
                        repository_data["contributor_commit_summary"] = contributor_summary
                        logger.info(f"✅ Generated commit summary: {contributor_summary.get('total_commits', 0)} commits, {contributor_summary.get('total_prs', 0)} PRs")
                    except Exception as e:
                        logger.warning(f"⚠️ Failed to generate contributor commit summary: {e}")
                        repository_data["contributor_commit_summary"] = None

                    # Get minimal contributor info (only basic profile, no extensive data)
                    logger.info(f"🔍 DEBUG: Calling _get_minimal_contributor_info for {github_username}")
                    contributor_info = await self._get_minimal_contributor_info(github_username, analysis_context_type)
                    logger.info(f"🔍 DEBUG: Contributor info returned keys: {list(contributor_info.keys()) if contributor_info else 'None'}")
                    if contributor_info and "user_data" in contributor_info:
                        logger.info(f"🔍 DEBUG: Contributor user_data keys: {list(contributor_info['user_data'].keys())}")

                    # Construct ULTRA-STRICTLY FILTERED github_data for repository-only context
                    # ABSOLUTELY NO general profile data allowed - ONLY repository-specific data
                    logger.info("🔒 REPO_ONLY: Constructing ultra-filtered data structure - NO profile data allowed")

                    github_data: Dict[str, Any] = {
                        "user_data": {
                            "github_username": github_username,
                            "login": github_username,
                            # CRITICAL: NO profile data - full_name, bio, company, location, etc. are ALL excluded
                        },
                        # EXPLICITLY EXCLUDE all general profile data:
                        # EXCLUDE: "repositories" (list of all user's repos)
                        # EXCLUDE: "languages" (general user languages)
                        # EXCLUDE: "skills" (general user skills)
                        # EXCLUDE: "commit_analysis" (general user commit analysis)
                        # EXCLUDE: "commits" (all user's commits)
                        # EXCLUDE: "starred_technologies"
                        # EXCLUDE: "organizations"
                        # EXCLUDE: "bio", "company", "location", "followers", "following", "public_repos"
                        # ONLY include repository-specific data:
                        "repository_info": repository_data.get("repository_info", {}),
                        "languages": repository_data.get("languages", []),  # Repository-specific languages only
                        "skills": repository_data.get("skills", {}),  # Repository-specific skills only
                        "commits": filtered_commits,  # Only contributor's commits to this repo
                        "commit_analysis": repository_data.get("commit_analysis", {}),  # Repository-specific analysis only
                        # CRITICAL: NO contributor_info with profile data - only essential repo contribution info
                        "repo_contributor_stats": {
                            "username": github_username,
                            "contributions_to_repo": len(filtered_commits),  # Only count commits to this specific repo
                        },
                        "analyzed_at": datetime.utcnow().isoformat(),
                        "analysis_context_type": "repo_only",
                        "repository_url": repository_url,
                        "ai_focus_instruction": (
                            f"Focus ONLY on {github_username}'s contributions to "
                            f"{repository_data.get('repository_info', {}).get('full_name', '')} repository. "
                            "Do not mention or reference any other repositories, projects, or general profile information."
                        ),
                    }

                    logger.info(f"✅ Constructed focused repo_only data for {github_username} in {repository_data.get('repository_info', {}).get('full_name', '')}")
                    logger.info(f"   • Filtered to {len(filtered_commits)} contributor commits")
                    return github_data
                else:
                    logger.error(f"❌ Failed to analyze repository {repository_url} for repo_only context.")
                    raise ValueError(f"Could not analyze repository: {repository_url}")
            else:
                raise ValueError(f"Invalid repository URL format: {repository_url}")

        else:
            logger.info("🔍 DEBUG: NOT taking repo_only path. Falling through to other analysis types.")
            logger.info(f"   • analysis_context_type: {analysis_context_type}")
            logger.info(f"   • repository_url: {repository_url}")

        if analysis_context_type == "repository_contributor" and repository_url:
            logger.info("👥 Analyzing repository with contributor context...")
            # Get full profile data but emphasize repository context
            github_data = await self.github_service.analyze_github_profile(username=github_username, force_refresh=False, analysis_context_type=analysis_context_type, repository_url=repository_url)

            if github_data and repository_url:
                # Extract owner/repo from URL and get repository-specific data
                repo_path = repository_url.replace("https://github.com/", "").split("?")[0]
                if "/" in repo_path:
                    owner, repo = repo_path.split("/", 1)
                    repo_data = await self.repository_service.analyze_repository(f"{owner}/{repo}", force_refresh=False, analysis_context_type=analysis_context_type, repository_url=repository_url)
                    if repo_data:
                        github_data = self._merge_repository_and_contributor_data(repo_data, github_data, github_username)

        else:
            logger.info("👤 Analyzing full GitHub profile...")
            # Default: analyze full profile
            github_data = await self.github_service.analyze_github_profile(username=github_username, force_refresh=False, analysis_context_type=analysis_context_type, repository_url=repository_url)

        return github_data

    async def _get_minimal_contributor_info(self, username: str, context_type: str = "profile") -> Dict[str, Any]:
        """Get minimal contributor information without extensive profile analysis.

        For repo_only context, we want to minimize profile data exposure.
        """
        try:
            # For repo_only context, use a much more restrictive approach
            if context_type == "repo_only":
                logger.info("🔒 REPO_ONLY: Using ultra-minimal contributor info to prevent profile data leakage")
                # Only fetch the absolute minimum needed - no profile data
                return {
                    "github_username": username,
                    "login": username,
                    # Explicitly exclude: full_name, avatar_url, github_id, bio, company, location, etc.
                    # We only need the username for identification in repo_only mode
                }

            # For other contexts, use the existing logic
            user_data = await self.github_service._get_user_data(username)
            if user_data:
                return {
                    "full_name": user_data.get("name", ""),
                    "avatar_url": user_data.get("avatar_url", ""),
                    "github_id": user_data.get("id", ""),
                }
        except Exception as e:
            logger.warning(f"Could not fetch minimal contributor info for {username}: {e}")

        # Return minimal fallback - just the username
        return {"github_username": username, "login": username}

    def _validate_repo_only_data_isolation(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate that repo_only data contains no general profile information."""
        validation_result = {"is_valid": True, "issues": [], "warnings": []}

        # Define profile data fields that should NEVER appear in repo_only context
        # Note: full_name is allowed as it's essential for personalized recommendations
        forbidden_profile_fields = [
            "bio",
            "company",
            "location",
            "email",
            "blog",
            "followers",
            "following",
            "public_repos",
            "public_gists",
            "starred_repositories",
            "organizations",
            "starred_technologies",
            "repositories",
            "name",  # Keeping this since we use full_name instead
            "avatar_url",
        ]

        # Check user_data section for profile data
        user_data = data.get("user_data", {})
        for field in forbidden_profile_fields:
            if field in user_data and user_data[field]:
                validation_result["is_valid"] = False
                validation_result["issues"].append(f"Profile field '{field}' found in user_data")

        # Check for contributor_info (old structure that might contain profile data)
        if data.get("contributor_info"):
            contributor_info = data["contributor_info"]
            for field in ["full_name", "email", "bio", "company", "location", "avatar_url"]:
                if field in contributor_info and contributor_info[field]:
                    validation_result["is_valid"] = False
                    validation_result["issues"].append(f"Profile field '{field}' found in contributor_info")

        # Check for profile data sections that should be excluded
        profile_sections = ["organizations", "starred_technologies", "starred_repositories"]
        for section in profile_sections:
            if data.get(section):
                validation_result["is_valid"] = False
                validation_result["issues"].append(f"Profile section '{section}' found in data")

        # Check user_data for non-empty profile fields (excluding allowed fields)
        allowed_user_fields = {"github_username", "login", "full_name"}  # Allow full_name for personalized recommendations
        for field, value in user_data.items():
            if field not in allowed_user_fields and value:
                # Allow empty strings but not actual data
                if isinstance(value, str) and value.strip():
                    validation_result["warnings"].append(f"Unexpected data in user_data['{field}']: '{value[:50]}...'")
                elif not isinstance(value, str):
                    validation_result["warnings"].append(f"Unexpected non-string data in user_data['{field}']: {type(value)}")

        # Ensure required repository data is present
        required_repo_fields = ["repository_info", "languages", "skills", "commit_analysis"]
        for field in required_repo_fields:
            if not data.get(field):
                validation_result["warnings"].append(f"Missing required repository field: '{field}'")

        # Validate analysis_context_type
        if data.get("analysis_context_type") != "repo_only":
            validation_result["is_valid"] = False
            validation_result["issues"].append("analysis_context_type is not 'repo_only'")

        return validation_result

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

        start_time = time.time()

        try:
            logger.info("🔍 STEP 1: GITHUB DATA ANALYSIS")
            logger.info("-" * 50)
            logger.info(f"   • Analysis Context: {analysis_context_type}")
            logger.info(f"   • Repository URL: {repository_url or 'N/A'}")
            github_start = time.time()

            # Conditionally fetch GitHub data based on analysis context
            if analysis_context_type == "repo_only" and repository_url:
                logger.info("📦 Analyzing specific repository...")
                # Extract owner/repo from URL
                repo_path = repository_url.replace("https://github.com/", "").split("?")[0]
                if "/" in repo_path:
                    owner, repo = repo_path.split("/", 1)
                    github_data = await self.repository_service.analyze_repository(f"{owner}/{repo}", force_refresh=False)

                    if github_data:
                        # For repo_only, we need to create a minimal profile structure
                        # Merge repository data with basic contributor info
                        contributor_data = await self.github_service.analyze_github_profile(username=github_username, force_refresh=False)
                        if contributor_data:
                            github_data = self._merge_repository_and_contributor_data(github_data, contributor_data, github_username, analysis_context_type)
                        else:
                            logger.warning(f"Could not fetch contributor data for {github_username}, using repository data only")

                else:
                    raise ValueError(f"Invalid repository URL format: {repository_url}")

            elif analysis_context_type == "repository_contributor" and repository_url:
                logger.info("👥 Analyzing repository with contributor context...")
                # Get full profile data but emphasize repository context
                github_data = await self.github_service.analyze_github_profile(username=github_username, force_refresh=False)

                if github_data and repository_url:
                    # Extract owner/repo from URL and get repository-specific data
                    repo_path = repository_url.replace("https://github.com/", "").split("?")[0]
                    if "/" in repo_path:
                        owner, repo = repo_path.split("/", 1)
                        repo_data = await self.repository_service.analyze_repository(f"{owner}/{repo}", force_refresh=False)
                        if repo_data:
                            github_data = self._merge_repository_and_contributor_data(repo_data, github_data, github_username, analysis_context_type)

            else:
                logger.info("👤 Analyzing full GitHub profile...")
                # Default: analyze full profile
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
