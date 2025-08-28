"""Service for managing recommendations."""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.github_profile import GitHubProfile
from app.models.recommendation import Recommendation
from app.schemas.recommendation import (
    RecommendationCreate,
    RecommendationOptionsResponse,
    RecommendationResponse,
)
from app.services.ai_service import AIService
from app.services.github_service import GitHubService

logger = logging.getLogger(__name__)


def parse_datetime(dt):
    if isinstance(dt, str):
        return datetime.fromisoformat(dt)
    return dt


class RecommendationService:
    """Service for managing recommendations."""

    def __init__(self):
        """Initialize recommendation service."""
        self.github_service = GitHubService()
        self.ai_service = AIService()

    async def create_recommendation(
        self,
        db: AsyncSession,
        github_username: str,
        recommendation_type: str = "professional",
        tone: str = "professional",
        length: str = "medium",
        custom_prompt: Optional[str] = None,
        target_role: Optional[str] = None,
        specific_skills: Optional[List[str]] = None,
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
                github_profile_id=int(github_profile.id),
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
        recommendation_type: Optional[str] = None,
        limit: int = 10,
        offset: int = 0,
    ) -> List[RecommendationResponse]:
        """Get recommendations with optional filtering."""

        query = select(Recommendation).join(GitHubProfile)

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

    async def get_recommendation_by_id(self, db: AsyncSession, recommendation_id: int) -> Optional[RecommendationResponse]:
        """Get a specific recommendation by ID."""

        query = select(Recommendation).where(Recommendation.id == recommendation_id)
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
        if github_data.get("analysis_type") == "repository_contributor":
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
        recommendation_type: str = "professional",
        tone: str = "professional",
        length: str = "medium",
        custom_prompt: Optional[str] = None,
        target_role: Optional[str] = None,
        specific_skills: Optional[List[str]] = None,
        analysis_type: str = "profile",
        repository_url: Optional[str] = None,
    ) -> RecommendationOptionsResponse:
        """Create multiple recommendation options."""

        import time

        start_time = time.time()

        try:
            logger.info("🎭 STEP 1: GITHUB ANALYSIS")
            logger.info("-" * 50)
            github_start = time.time()

            # Determine analysis type and get GitHub data
            if analysis_type == "repo_only" and repository_url:
                logger.info(f"📁 Analyzing repository: {repository_url}")
                # Extract repository name from URL
                if "/" in repository_url:
                    repo_parts = repository_url.split("/")
                    repo_name = repo_parts[-2] + "/" + repo_parts[-1]
                else:
                    repo_name = repository_url

                # Analyze the repository
                repository_data = await self.github_service.analyze_repository(repository_full_name=repo_name, force_refresh=False)

                # Analyze the specific contributor's profile
                logger.info(f"👤 Analyzing contributor profile: {github_username}")
                contributor_data = await self.github_service.analyze_github_profile(username=github_username, force_refresh=False)

                # Merge repository and contributor data
                github_data = self._merge_repository_and_contributor_data(repository_data, contributor_data, github_username)
            else:
                logger.info(f"👤 Analyzing profile: {github_username}")
                github_data = await self.github_service.analyze_github_profile(username=github_username, force_refresh=False)

            github_end = time.time()
            logger.info(f"⏱️  GitHub analysis completed in {github_end - github_start:.2f} seconds")

            if not github_data:
                if analysis_type == "repo_only":
                    logger.error(f"❌ Failed to analyze GitHub repository: {repository_url}")
                    raise ValueError(f"Could not analyze GitHub repository: {repository_url}")
                else:
                    logger.error(f"❌ Failed to analyze GitHub profile for {github_username}")
                    raise ValueError(f"Could not analyze GitHub profile for {github_username}")

            if analysis_type == "repo_only":
                logger.info("✅ Repository analysis successful:")
                logger.info(f"   • Repository: {github_data.get('repository_info', {}).get('name', 'N/A')}")
                logger.info(f"   • Language: {github_data.get('repository_info', {}).get('language', 'N/A')}")
                logger.info(f"   • Commits analyzed: {len(github_data.get('commits', []))}")
            else:
                logger.info("✅ Profile analysis successful:")
                logger.info(f"   • Repositories: {len(github_data.get('repositories', []))}")
                logger.info(f"   • Languages: {len(github_data.get('languages', []))}")
                logger.info(f"   • Commits analyzed: {github_data.get('commit_analysis', {}).get('total_commits_analyzed', 0)}")

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
                    contributor_skills["technical_skills"] = list(
                        set(contributor_skills.get("technical_skills", []) + repo_skills["technical_skills"])
                    )

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
        merged_data["analysis_type"] = "repository_contributor"
        merged_data["target_repository"] = repository_data.get("repository_info", {}).get("full_name", "")
        merged_data["contributor_username"] = contributor_username

        logger.info(f"✅ Merged data created with analysis_type: {merged_data['analysis_type']}")
        return merged_data

    async def create_recommendation_from_option(
        self,
        db: AsyncSession,
        github_username: str,
        selected_option: Dict[str, Any],
        all_options: List[Dict[str, Any]],
        analysis_type: str = "profile",
        repository_url: Optional[str] = None,
    ) -> RecommendationResponse:
        """Create a recommendation from a selected option."""

        import time

        start_time = time.time()

        try:
            logger.info("🔍 STEP 1: GITHUB PROFILE ANALYSIS")
            logger.info("-" * 50)
            github_start = time.time()

            # Determine analysis type and get GitHub data
            if analysis_type == "repo_only" and repository_url:
                logger.info(f"📁 Analyzing repository: {repository_url}")
                # Extract repository name from URL
                if "/" in repository_url:
                    repo_parts = repository_url.split("/")
                    repo_name = repo_parts[-2] + "/" + repo_parts[-1]
                else:
                    repo_name = repository_url

                # Analyze the repository
                repository_data = await self.github_service.analyze_repository(repository_full_name=repo_name, force_refresh=False)

                # Analyze the specific contributor's profile
                logger.info(f"👤 Analyzing contributor profile: {github_username}")
                contributor_data = await self.github_service.analyze_github_profile(username=github_username, force_refresh=False)

                # Merge repository and contributor data
                github_data = self._merge_repository_and_contributor_data(repository_data, contributor_data, github_username)
            else:
                logger.info(f"👤 Analyzing profile: {github_username}")
                github_data = await self.github_service.analyze_github_profile(username=github_username, force_refresh=False)

            github_end = time.time()
            logger.info(f"⏱️  GitHub analysis completed in {github_end - github_start:.2f} seconds")

            if not github_data:
                if analysis_type == "repo_only":
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
                "analysis_type": analysis_type,
                "repository_url": repository_url,
            }

            recommendation_data = RecommendationCreate(
                github_profile_id=int(github_profile.id),
                title=selected_option.get(
                    "title",
                    f"Professional Recommendation for {github_username}",
                ),
                content=selected_option["content"],
                recommendation_type=generation_parameters.get("recommendation_type", "professional"),
                tone=generation_parameters.get("tone", "professional"),
                length=generation_parameters.get("length", "medium"),
                ai_model=generation_parameters["model"],
                generation_prompt=None,  # This comes from the options generation
                generation_parameters=generation_parameters,
                confidence_score=selected_option.get("confidence_score", 0),
                word_count=selected_option.get("word_count", 0),
                selected_option_id=selected_option.get("id"),
                selected_option_name=selected_option.get("name"),
                selected_option_focus=selected_option.get("focus"),
                generated_options=[option for option in all_options],  # Store all options for reference
            )

            recommendation = Recommendation(**recommendation_data.dict())
            db.add(recommendation)
            await db.commit()
            await db.refresh(recommendation)

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
