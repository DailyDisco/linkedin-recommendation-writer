"""AI Recommendation Service for generating LinkedIn recommendations."""

import logging
import re
from typing import Any, AsyncGenerator, Dict, List, Optional

from app.core.config import settings
from app.core.redis_client import get_cache, set_cache
from app.services.ai.human_story_generator import HumanStoryGenerator
from app.services.ai.prompt_service import PromptService

# Handle optional Google Generative AI import
try:
    import google.genai as genai
    from google.genai import types

    genai_available = True
except ImportError:
    genai = None  # type: ignore
    types = None  # type: ignore
    genai_available = False

logger = logging.getLogger(__name__)


class AIRecommendationService:
    """Service for generating AI-powered recommendations."""

    def __init__(self, prompt_service: PromptService) -> None:
        """Initialize recommendation service."""
        self.prompt_service = prompt_service
        self.story_generator = HumanStoryGenerator()
        self.client = None
        if genai and settings.GEMINI_API_KEY:
            # Create client with API key
            self.client = genai.Client(api_key=settings.GEMINI_API_KEY)
            self.generation_config = types.GenerateContentConfig(
                temperature=settings.GEMINI_TEMPERATURE,
                max_output_tokens=settings.GEMINI_MAX_TOKENS,
                top_p=0.9,
                top_k=40,
            )
        self.rate_limit_requests_per_minute = 15
        self.request_timestamps = []

    async def generate_recommendation_stream(
        self,
        github_data: Dict[str, Any],
        recommendation_type: str = "professional",
        tone: str = "professional",
        length: str = "medium",
        custom_prompt: Optional[str] = None,
        shared_work_context: Optional[str] = None,
        target_role: Optional[str] = None,
        specific_skills: Optional[list] = None,
        exclude_keywords: Optional[list] = None,
        focus_keywords: Optional[List[str]] = None,
        focus_weights: Optional[Dict[str, float]] = None,
        dynamic_params: Optional[Dict[str, Any]] = None,
        analysis_context_type: str = "profile",
        repository_url: Optional[str] = None,
        force_refresh: bool = False,
        display_name: Optional[str] = None,
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """Generate a LinkedIn recommendation with streaming progress updates."""

        if not self.client:
            raise ValueError("Gemini AI not configured")

        try:
            # Stage 1: Initializing
            yield {
                "stage": "Initializing AI service...",
                "progress": 5,
                "status": "preparing",
            }

            # Stage 2: Building prompt
            yield {
                "stage": "Analyzing GitHub profile data...",
                "progress": 15,
                "status": "analyzing",
            }

            # Build the initial prompt
            initial_prompt = self.prompt_service.build_prompt(
                github_data=github_data,
                recommendation_type=recommendation_type,
                tone=tone,
                length=length,
                custom_prompt=custom_prompt,
                shared_work_context=shared_work_context,
                target_role=target_role,
                specific_skills=specific_skills,
                exclude_keywords=exclude_keywords,
                focus_keywords=focus_keywords,
                focus_weights=focus_weights,
                analysis_context_type=analysis_context_type,
                repository_url=repository_url,
                display_name=display_name,
            )

            # Stage 3: Identifying key contributions
            yield {
                "stage": "Identifying key contributions and skills...",
                "progress": 30,
                "status": "processing",
            }

            # Check cache for final result - include analysis context in cache key
            # CRITICAL: Separate cache keys for different contexts to prevent data contamination
            if analysis_context_type == "repo_only":
                # Use separate cache namespace for repo_only to ensure complete isolation
                if repository_url:
                    repo_path = repository_url.replace("https://github.com/", "").split("?")[0]
                    cache_key = f"ai_recommendation_repo_only:{hash(initial_prompt)}:{repo_path}"
                else:
                    cache_key = f"ai_recommendation_repo_only:{hash(initial_prompt)}"
                logger.info(f"🔒 Using isolated cache key for repo_only context: {cache_key}")
            else:
                # Original caching logic for other contexts
                context_suffix = ""
                if analysis_context_type != "profile":
                    context_suffix = f":{analysis_context_type}"
                    if repository_url:
                        repo_path = repository_url.replace("https://github.com/", "").split("?")[0]
                        context_suffix += f":{repo_path}"

                cache_key = f"ai_recommendation_v3:{hash(initial_prompt)}{context_suffix}"

            # Skip cache if force_refresh is requested
            if not force_refresh:
                cached_result = await get_cache(cache_key)
                if cached_result and isinstance(cached_result, dict):
                    logger.info("Cache hit for AI recommendation")
                    yield {
                        "stage": "Generating recommendation options...",
                        "progress": 70,
                        "status": "generating",
                    }
                    # Return cached result with final progress
                    yield {
                        "stage": "Recommendation ready!",
                        "progress": 100,
                        "status": "complete",
                        "result": cached_result,
                    }
                    return
            else:
                logger.info("Force refresh requested - skipping cache")

            # Stage 4: Generating options
            yield {
                "stage": "Generating recommendation options...",
                "progress": 50,
                "status": "generating",
            }

            # Generate options with progress updates
            options = []
            base_username = github_data["user_data"]["github_username"]

            # Extract display name for consistent naming (prioritizes first name)
            if display_name is None:
                display_name = self.prompt_service._extract_display_name(github_data["user_data"])

            option_configs = [
                {
                    "name": "Option 1",
                    "focus": "technical_expertise",
                    "temperature_modifier": 0.1,
                    "custom_instruction": "Focus on technical skills and problem-solving abilities.",
                },
                {
                    "name": "Option 2",
                    "focus": "collaboration",
                    "temperature_modifier": 0.2,
                    "custom_instruction": "Emphasize teamwork and collaborative abilities.",
                },
            ]

            for i, config in enumerate(option_configs, 1):
                progress = 50 + (i * 20)  # 70%, 90%
                yield {
                    "stage": f"Drafting {config['name']}...",
                    "progress": progress,
                    "status": "generating",
                }

                # Create customized prompt for this option
                option_prompt = self.prompt_service.build_option_prompt(
                    initial_prompt,
                    str(config["custom_instruction"]),
                    str(config["focus"]),
                    focus_keywords,
                    focus_weights,
                )

                # Generate the option
                temp_modifier = config.get("temperature_modifier", 0.7)
                temp_modifier = float(temp_modifier) if isinstance(temp_modifier, (int, float, str)) else 0.7

                option_gen_params = {
                    "github_username": base_username,
                    "recommendation_type": recommendation_type,
                    "tone": tone,
                    "length": length,
                    "focus": config["focus"],
                }

                option_content, validation_results = await self._generate_single_option(option_prompt, temp_modifier, length, option_gen_params, github_data)

                # Create option object
                option = {
                    "id": i,
                    "name": config["name"],
                    "content": option_content.strip(),
                    "title": self.prompt_service.extract_title(option_content, base_username, None, display_name),
                    "word_count": len(option_content.split()),
                    "focus": config["focus"],
                    "validation_results": validation_results,
                }

                options.append(option)

            # Stage 5: Finalizing
            yield {
                "stage": "Finalizing recommendation options...",
                "progress": 95,
                "status": "finalizing",
            }

            # Process and format the response
            result = {
                "options": options,
                "generation_parameters": {
                    "model": settings.GEMINI_MODEL,
                    "temperature": settings.GEMINI_TEMPERATURE,
                    "max_tokens": settings.GEMINI_MAX_TOKENS,
                    "recommendation_type": recommendation_type,
                    "tone": tone,
                    "length": length,
                    "multiple_options": True,
                },
                "generation_prompt": (initial_prompt[:500] + "..." if len(initial_prompt) > 500 else initial_prompt),
            }

            # Cache for 24 hours
            await set_cache(cache_key, result, ttl=86400)

            # Stage 6: Complete
            yield {
                "stage": "Recommendation ready!",
                "progress": 100,
                "status": "complete",
                "result": result,
            }

        except Exception as e:
            logger.error(f"Error in streaming recommendation generation: {e}")
            yield {
                "stage": f"Error: {str(e)}",
                "progress": 0,
                "status": "error",
                "error": str(e),
            }
            raise

    async def regenerate_recommendation_stream(
        self,
        original_content: str,
        refinement_instructions: str,
        github_data: Dict[str, Any],
        recommendation_type: str = "professional",
        tone: str = "professional",
        length: str = "medium",
        analysis_context_type: str = "profile",
        repository_url: Optional[str] = None,
        dynamic_tone: Optional[str] = None,
        dynamic_length: Optional[str] = None,
        include_keywords: Optional[List[str]] = None,
        exclude_keywords: Optional[List[str]] = None,
        display_name: Optional[str] = None,
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """Regenerate a recommendation with streaming progress and dynamic refinement parameters."""

        if not self.client:
            raise ValueError("Gemini AI not configured")

        try:
            # Extract display name for consistent naming (prioritizes first name)
            if display_name is None:
                display_name = self.prompt_service._extract_display_name(github_data["user_data"])

            # Stage 1: Initializing
            yield {
                "stage": "Preparing refinement...",
                "progress": 10,
                "status": "preparing",
            }

            # Stage 2: Analyzing original content
            yield {
                "stage": "Analyzing original recommendation...",
                "progress": 25,
                "status": "analyzing",
            }

            # Use dynamic parameters if provided, otherwise fall back to defaults
            final_tone = dynamic_tone or tone
            final_length = dynamic_length or length

            # Stage 3: Building refinement prompt
            yield {
                "stage": "Building refinement prompt...",
                "progress": 40,
                "status": "processing",
            }

            # Build refinement prompt with dynamic parameters
            refinement_prompt = self.prompt_service.build_refinement_prompt_for_regeneration(
                original_content=original_content,
                refinement_instructions=refinement_instructions,
                github_data=github_data,
                recommendation_type=recommendation_type,
                tone=final_tone,
                length=final_length,
                analysis_context_type=analysis_context_type,
                repository_url=repository_url,
                exclude_keywords=exclude_keywords,
                display_name=display_name,
            )

            # Create regeneration parameters
            regeneration_params: Dict[str, Any] = {
                "recommendation_type": recommendation_type,
                "tone": final_tone,
                "length": final_length,
                "include_keywords": include_keywords or [],
                "exclude_keywords": exclude_keywords or [],
                "refinement_instructions": refinement_instructions,
            }

            # Stage 4: Generating refined content
            yield {
                "stage": "Generating refined recommendation...",
                "progress": 70,
                "status": "generating",
            }

            # Generate refined recommendation
            refined_content = await self._generate_refined_regeneration(refinement_prompt, final_length, regeneration_params)

            # Stage 5: Finalizing
            yield {
                "stage": "Finalizing refined recommendation...",
                "progress": 90,
                "status": "finalizing",
            }

            # Return refined result
            result = {
                "content": refined_content.strip(),
                "title": self.prompt_service.extract_title(refined_content, github_data["user_data"]["github_username"], None, display_name),
                "word_count": len(refined_content.split()),
                "generation_parameters": regeneration_params,
            }

            # Stage 6: Complete
            yield {
                "stage": "Refined recommendation ready!",
                "progress": 100,
                "status": "complete",
                "result": result,
            }

        except Exception as e:
            logger.error(f"Error in streaming recommendation regeneration: {e}")
            yield {
                "stage": f"Error: {str(e)}",
                "progress": 0,
                "status": "error",
                "error": str(e),
            }
            raise

    async def generate_recommendation(
        self,
        github_data: Dict[str, Any],
        recommendation_type: str = "professional",
        tone: str = "professional",
        length: str = "medium",
        custom_prompt: Optional[str] = None,
        shared_work_context: Optional[str] = None,
        target_role: Optional[str] = None,
        specific_skills: Optional[list] = None,
        exclude_keywords: Optional[list] = None,
        focus_keywords: Optional[List[str]] = None,
        focus_weights: Optional[Dict[str, float]] = None,
        analysis_context_type: str = "profile",
        repository_url: Optional[str] = None,
        force_refresh: bool = False,
        display_name: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Generate a LinkedIn recommendation using AI."""

        if not self.client:
            raise ValueError("Gemini AI not configured")

        try:
            if settings.ENVIRONMENT == "development":
                logger.info("🧠 RECOMMENDATION SERVICE: Building initial prompt...")

            # Build the initial prompt
            initial_prompt = self.prompt_service.build_prompt(
                github_data=github_data,
                recommendation_type=recommendation_type,
                tone=tone,
                length=length,
                custom_prompt=custom_prompt,
                shared_work_context=shared_work_context,
                target_role=target_role,
                specific_skills=specific_skills,
                exclude_keywords=exclude_keywords,
                focus_keywords=focus_keywords,
                focus_weights=focus_weights,
                analysis_context_type=analysis_context_type,
                repository_url=repository_url,
                display_name=display_name,
            )

            if settings.ENVIRONMENT == "development":
                logger.info(f"✅ Prompt built with {len(initial_prompt)} characters")

            # Check cache for final result - include analysis context in cache key
            # CRITICAL: Separate cache keys for different contexts to prevent data contamination
            if analysis_context_type == "repo_only":
                # Use separate cache namespace for repo_only to ensure complete isolation
                if repository_url:
                    repo_path = repository_url.replace("https://github.com/", "").split("?")[0]
                    cache_key = f"ai_recommendation_repo_only:{hash(initial_prompt)}:{repo_path}"
                else:
                    cache_key = f"ai_recommendation_repo_only:{hash(initial_prompt)}"
                logger.info(f"🔒 Using isolated cache key for repo_only context: {cache_key}")
            else:
                # Original caching logic for other contexts
                context_suffix = ""
                if analysis_context_type != "profile":
                    context_suffix = f":{analysis_context_type}"
                    if repository_url:
                        repo_path = repository_url.replace("https://github.com/", "").split("?")[0]
                        context_suffix += f":{repo_path}"

                cache_key = f"ai_recommendation_v3:{hash(initial_prompt)}{context_suffix}"

            # Skip cache if force_refresh is requested
            if not force_refresh:
                cached_result = await get_cache(cache_key)
                if cached_result and isinstance(cached_result, dict):
                    logger.info("Cache hit for AI recommendation")
                    return cached_result

            if settings.ENVIRONMENT == "development":
                if force_refresh:
                    logger.info("🔄 FORCE REFRESH: Bypassing cache for fresh generation...")
                else:
                    logger.info("🚀 CACHE MISS: Starting multi-option generation...")

            # Generate 2 different recommendation options with explanations
            options = await self._generate_multiple_options_with_explanations(
                initial_prompt=initial_prompt,
                github_data=github_data,
                recommendation_type=recommendation_type,
                tone=tone,
                length=length,
                focus_keywords=focus_keywords,
                focus_weights=focus_weights,
                display_name=display_name,
            )

            # Process and format the response
            result = {
                "options": options,
                "generation_parameters": {
                    "model": settings.GEMINI_MODEL,
                    "temperature": settings.GEMINI_TEMPERATURE,
                    "max_tokens": settings.GEMINI_MAX_TOKENS,
                    "recommendation_type": recommendation_type,
                    "tone": tone,
                    "length": length,
                    "multiple_options": True,
                },
                "generation_prompt": (initial_prompt[:500] + "..." if len(initial_prompt) > 500 else initial_prompt),
            }

            # Cache for 24 hours
            await set_cache(cache_key, result, ttl=86400)

            return result

        except Exception as e:
            logger.error(f"Error generating AI recommendation: {e}")
            raise

    async def generate_recommendation_with_quality_gate(
        self,
        github_data: Dict[str, Any],
        recommendation_type: str = "professional",
        tone: str = "professional",
        length: str = "medium",
        custom_prompt: Optional[str] = None,
        shared_work_context: Optional[str] = None,
        target_role: Optional[str] = None,
        specific_skills: Optional[list] = None,
        exclude_keywords: Optional[list] = None,
        focus_keywords: Optional[List[str]] = None,
        focus_weights: Optional[Dict[str, float]] = None,
        analysis_context_type: str = "profile",
        repository_url: Optional[str] = None,
        force_refresh: bool = False,
        display_name: Optional[str] = None,
        min_quality_score: int = 65,
        max_retries: int = 3,
    ) -> Dict[str, Any]:
        """Generate a recommendation with quality gate - automatically retries if quality is too low.

        Args:
            min_quality_score: Minimum acceptable quality score (0-100). Default 65.
            max_retries: Maximum number of generation attempts. Default 3.
            Other args: Same as generate_recommendation.

        Returns:
            Best quality recommendation result, with quality_gate_metadata added.
        """
        if not self.client:
            raise ValueError("Gemini AI not configured")

        best_result = None
        best_score = 0
        attempts_log = []

        for attempt in range(1, max_retries + 1):
            logger.info(f"🎯 QUALITY GATE: Attempt {attempt}/{max_retries}")

            # Adjust parameters based on retry attempt
            adjusted_temperature_boost = (attempt - 1) * 0.1  # Increase creativity on retries

            try:
                # Generate recommendation
                result = await self.generate_recommendation(
                    github_data=github_data,
                    recommendation_type=recommendation_type,
                    tone=tone,
                    length=length,
                    custom_prompt=custom_prompt,
                    shared_work_context=shared_work_context,
                    target_role=target_role,
                    specific_skills=specific_skills,
                    exclude_keywords=exclude_keywords,
                    focus_keywords=focus_keywords,
                    focus_weights=focus_weights,
                    analysis_context_type=analysis_context_type,
                    repository_url=repository_url,
                    force_refresh=True if attempt > 1 else force_refresh,  # Force fresh on retries
                    display_name=display_name,
                )

                # Calculate average quality score across options
                options = result.get("options", [])
                if not options:
                    logger.warning(f"⚠️ Attempt {attempt}: No options generated")
                    attempts_log.append({"attempt": attempt, "score": 0, "reason": "no_options"})
                    continue

                # Get best option quality
                option_scores = []
                for option in options:
                    validation = option.get("validation_results", {})
                    score = validation.get("overall_quality_score", 50)
                    option_scores.append(score)

                avg_score = sum(option_scores) / len(option_scores)
                max_option_score = max(option_scores)

                logger.info(f"📊 Attempt {attempt} quality: avg={avg_score:.1f}, max={max_option_score:.1f}")
                attempts_log.append({
                    "attempt": attempt,
                    "avg_score": avg_score,
                    "max_score": max_option_score,
                    "option_scores": option_scores,
                })

                # Track best result
                if max_option_score > best_score:
                    best_score = max_option_score
                    best_result = result

                # Check if quality meets threshold
                if max_option_score >= min_quality_score:
                    logger.info(f"✅ QUALITY GATE PASSED: Score {max_option_score:.1f} >= {min_quality_score}")
                    break
                else:
                    logger.info(f"⚠️ Quality {max_option_score:.1f} < {min_quality_score}, retrying...")

                    # Add more specific instructions for retry
                    if attempt < max_retries:
                        if not specific_skills:
                            specific_skills = []
                        # Extract top skills to emphasize on retry
                        skills_data = github_data.get("skills", {})
                        top_skills = skills_data.get("technical_skills", [])[:3]
                        specific_skills = list(set(specific_skills + top_skills))

            except Exception as e:
                logger.error(f"❌ Attempt {attempt} failed: {e}")
                attempts_log.append({"attempt": attempt, "error": str(e)})
                if attempt == max_retries:
                    raise

        # Return best result with metadata
        if best_result:
            best_result["quality_gate_metadata"] = {
                "attempts": len(attempts_log),
                "final_score": best_score,
                "min_threshold": min_quality_score,
                "passed": best_score >= min_quality_score,
                "attempts_log": attempts_log,
            }
            logger.info(f"🏁 QUALITY GATE COMPLETE: Best score {best_score:.1f} after {len(attempts_log)} attempts")
            return best_result

        raise ValueError("Failed to generate recommendation after all attempts")

    async def _generate_multiple_options(
        self,
        initial_prompt: str,
        github_data: Dict[str, Any],
        recommendation_type: str,
        tone: str,
        length: str,
        focus_keywords: Optional[List[str]] = None,
        focus_weights: Optional[Dict[str, float]] = None,
        display_name: Optional[str] = None,
        parallel: bool = True,
    ) -> List[Dict[str, Any]]:
        """Generate 2 different recommendation options.

        Args:
            parallel: If True, generate options concurrently for faster response.
                     Default True. Set False if hitting rate limits.
        """
        import asyncio
        import time

        logger.info("🎭 GENERATING MULTIPLE OPTIONS")
        logger.info(f"⚡ Mode: {'PARALLEL' if parallel else 'SEQUENTIAL'}")
        logger.info("=" * 60)
        pipeline_start = time.time()

        base_username = github_data["user_data"]["github_username"]

        # Extract display name for consistent naming (prioritizes first name)
        if display_name is None:
            display_name = self.prompt_service._extract_display_name(github_data["user_data"])

        # Generate 2 different options with varying approaches
        option_configs = self._get_dynamic_option_configs(github_data)

        if parallel:
            # PARALLEL GENERATION - Generate all options concurrently
            options = await self._generate_options_parallel(
                initial_prompt=initial_prompt,
                option_configs=option_configs,
                base_username=base_username,
                recommendation_type=recommendation_type,
                tone=tone,
                length=length,
                focus_keywords=focus_keywords,
                focus_weights=focus_weights,
                display_name=display_name,
                github_data=github_data,
            )
        else:
            # SEQUENTIAL GENERATION - Generate options one by one (original behavior)
            options = await self._generate_options_sequential(
                initial_prompt=initial_prompt,
                option_configs=option_configs,
                base_username=base_username,
                recommendation_type=recommendation_type,
                tone=tone,
                length=length,
                focus_keywords=focus_keywords,
                focus_weights=focus_weights,
                display_name=display_name,
                github_data=github_data,
            )

        pipeline_end = time.time()
        total_pipeline_time = pipeline_end - pipeline_start

        logger.info("🎉 MULTIPLE OPTIONS GENERATION COMPLETED")
        logger.info(f"⏱️  Total time: {total_pipeline_time:.2f} seconds")
        if parallel and len(options) > 1:
            logger.info(f"⚡ Parallel speedup: ~{len(options)}x faster than sequential")

        return options

    async def _generate_options_parallel(
        self,
        initial_prompt: str,
        option_configs: List[Dict[str, Any]],
        base_username: str,
        recommendation_type: str,
        tone: str,
        length: str,
        focus_keywords: Optional[List[str]],
        focus_weights: Optional[Dict[str, float]],
        display_name: str,
        github_data: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        """Generate options in parallel using asyncio.gather for faster response."""
        import asyncio

        logger.info(f"🚀 Starting parallel generation of {len(option_configs)} options")

        # Prepare all generation tasks
        async def generate_single_option_task(config: Dict[str, Any], index: int) -> Dict[str, Any]:
            """Task wrapper for single option generation."""
            try:
                # Create customized prompt for this option
                option_prompt = self.prompt_service.build_option_prompt(
                    initial_prompt,
                    str(config["custom_instruction"]),
                    str(config["focus"]),
                    focus_keywords,
                    focus_weights,
                )

                # Generate the option
                temp_modifier = config.get("temperature_modifier", 0.7)
                temp_modifier = float(temp_modifier) if isinstance(temp_modifier, (int, float, str)) else 0.7

                # Prepare generation parameters for formatting and validation
                option_gen_params = {
                    "github_username": base_username,
                    "recommendation_type": recommendation_type,
                    "tone": tone,
                    "length": length,
                    "focus": config["focus"],
                }

                option_content, validation_results = await self._generate_single_option(
                    option_prompt, temp_modifier, length, option_gen_params, github_data
                )

                # Create option object
                return {
                    "id": index,
                    "name": config["name"],
                    "content": option_content.strip(),
                    "title": self.prompt_service.extract_title(option_content, base_username, None, display_name),
                    "word_count": len(option_content.split()),
                    "focus": config["focus"],
                    "validation_results": validation_results,
                    "success": True,
                }
            except Exception as e:
                logger.error(f"❌ Error generating {config['name']}: {e}")
                return {
                    "id": index,
                    "name": config["name"],
                    "content": "",
                    "error": str(e),
                    "success": False,
                }

        # Create tasks for all options
        tasks = [
            generate_single_option_task(config, i + 1)
            for i, config in enumerate(option_configs)
        ]

        # Execute all tasks concurrently
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Process results
        options = []
        for result in results:
            if isinstance(result, Exception):
                logger.error(f"❌ Task exception: {result}")
                continue
            if isinstance(result, dict) and result.get("success"):
                options.append(result)
                logger.info(f"✅ {result['name']}: {result['word_count']} words generated")

        return options

    async def _generate_options_sequential(
        self,
        initial_prompt: str,
        option_configs: List[Dict[str, Any]],
        base_username: str,
        recommendation_type: str,
        tone: str,
        length: str,
        focus_keywords: Optional[List[str]],
        focus_weights: Optional[Dict[str, float]],
        display_name: str,
        github_data: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        """Generate options sequentially (original behavior, useful if rate-limited)."""
        import time

        options = []

        for i, config in enumerate(option_configs, 1):
            logger.info(f"📝 GENERATING {config['name']}: {config['focus']}")
            logger.info("-" * 40)
            option_start = time.time()

            # Create customized prompt for this option
            option_prompt = self.prompt_service.build_option_prompt(
                initial_prompt,
                str(config["custom_instruction"]),
                str(config["focus"]),
                focus_keywords,
                focus_weights,
            )

            # Generate the option
            temp_modifier = config.get("temperature_modifier", 0.7)
            temp_modifier = float(temp_modifier) if isinstance(temp_modifier, (int, float, str)) else 0.7

            # Prepare generation parameters for formatting and validation
            option_gen_params = {
                "github_username": base_username,
                "recommendation_type": recommendation_type,
                "tone": tone,
                "length": length,
                "focus": config["focus"],
            }

            option_content, validation_results = await self._generate_single_option(
                option_prompt, temp_modifier, length, option_gen_params, github_data
            )

            option_end = time.time()

            # Create option object
            option = {
                "id": i,
                "name": config["name"],
                "content": option_content.strip(),
                "title": self.prompt_service.extract_title(option_content, base_username, None, display_name),
                "word_count": len(option_content.split()),
                "focus": config["focus"],
                "validation_results": validation_results,
            }

            options.append(option)

            logger.info(f"⏱️  {config['name']} completed in {option_end - option_start:.2f} seconds")
            logger.info(f"✅ Generated {option['word_count']} words")
            logger.info(f"   • Preview: {option_content[:100]}...")

        return options

    async def _generate_multiple_options_legacy(
        self,
        initial_prompt: str,
        github_data: Dict[str, Any],
        recommendation_type: str,
        tone: str,
        length: str,
        focus_keywords: Optional[List[str]] = None,
        focus_weights: Optional[Dict[str, float]] = None,
        display_name: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Legacy sequential generation - kept for backwards compatibility."""
        return await self._generate_multiple_options(
            initial_prompt=initial_prompt,
            github_data=github_data,
            recommendation_type=recommendation_type,
            tone=tone,
            length=length,
            focus_keywords=focus_keywords,
            focus_weights=focus_weights,
            display_name=display_name,
            parallel=False,
        )

    def _log_generation_complete(self, options: List[Dict[str, Any]], total_time: float) -> None:
        """Log completion of multiple options generation."""
        logger.info("🎉 MULTIPLE OPTIONS GENERATION COMPLETED")
        logger.info("-" * 40)
        logger.info(f"⏱️  Total time: {total_time:.2f} seconds")
        logger.info(f"📊 Generated {len(options)} options")
        logger.info("=" * 60)

    def _get_dynamic_option_configs(self, github_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate dynamic recommendation options based on inferred personality traits."""
        trait_to_instruction = {
            "detail_oriented": "Focus on their methodical and detail-oriented approach, highlighting precision and thoroughness.",
            "strategic_thinker": "Emphasize their ability to see the big picture and design scalable solutions.",
            "problem_solver": "Highlight their skill in debugging and solving complex technical challenges.",
            "collaborator": "Focus on their teamwork, communication, and ability to work effectively with others.",
            "reliable": "Showcase their consistency, dependability, and the quality of their contributions.",
            "innovative": "Highlight their creativity and use of new technologies to solve problems.",
            "technical_expertise": "Focus on technical skills and problem-solving abilities.",
        }

        inferred_traits = self.story_generator.infer_personality_traits(github_data.get("commit_analysis", {}), github_data.get("pr_data"))

        unique_traits = []
        for trait_info in inferred_traits:
            if trait_info["trait"] not in unique_traits:
                unique_traits.append(trait_info["trait"])

        focuses = unique_traits[:2]

        # Fallback logic
        if not focuses:
            focuses = ["technical_expertise", "collaboration"]
        elif len(focuses) == 1:
            if focuses[0] == "collaboration":
                focuses.insert(0, "technical_expertise")
            else:
                focuses.append("collaboration")

        option_configs = []
        for i, focus in enumerate(focuses, 1):
            instruction = trait_to_instruction.get(focus, f"Emphasize their {focus.replace('_', ' ')}.")
            option_configs.append(
                {
                    "name": f"Option {i}",
                    "focus": focus,
                    "temperature_modifier": 0.1 * i,
                    "custom_instruction": instruction,
                }
            )

        return option_configs

    def _generate_option_explanation(self, option_content: str, option_name: str, focus: str, github_data: Dict[str, Any], display_name: Optional[str] = None) -> str:
        """Generate a concise explanation for why to choose this recommendation option."""
        try:
            # Analyze the option content to understand its key characteristics
            content_lower = option_content.lower()
            word_count = len(option_content.split())

            # Identify key themes and strengths
            themes = []

            # Technical focus indicators
            if any(word in content_lower for word in ["technical", "skills", "expertise", "programming", "development"]):
                themes.append("technical expertise")

            # Collaboration focus indicators
            if any(word in content_lower for word in ["team", "collaboration", "communication", "working", "together"]):
                themes.append("team collaboration")

            # Leadership focus indicators
            if any(word in content_lower for word in ["leadership", "growth", "learning", "development", "potential"]):
                themes.append("leadership and growth")

            # Impact/achievement focus indicators
            if any(word in content_lower for word in ["impact", "achievement", "success", "accomplished", "delivered"]):
                themes.append("impact and achievements")

            # Length-based characteristics
            length_desc = "concise" if word_count < 150 else "balanced" if word_count < 200 else "comprehensive"

            # Generate explanation based on focus and themes
            if focus == "technical_expertise":
                explanation = (
                    "This option emphasizes technical skills and problem-solving abilities, " f"making it ideal for technical roles. It's {length_desc} and focuses on their technical capabilities."
                )
            elif focus == "collaboration":
                explanation = (
                    "This option highlights teamwork and collaborative abilities, "
                    f"perfect for roles requiring strong interpersonal skills. It's {length_desc} with a focus on relationship-building."
                )
            elif focus == "leadership_growth":
                explanation = "This option showcases leadership potential and growth mindset, " f"suitable for senior positions. It's {length_desc} and emphasizes their development trajectory."
            else:
                themes_str = ", ".join(themes) if themes else "balanced approach"
                explanation = f"This option provides a {themes_str}, making it suitable for general professional recommendations. " f"It's {length_desc} and offers a well-rounded perspective."

            return explanation

        except Exception as e:
            logger.debug(f"Error generating option explanation: {e}")
            return f"This {option_name.lower()} provides a unique perspective on their professional background " "and is suitable for various professional contexts."

    async def _generate_multiple_options_with_explanations(
        self,
        initial_prompt: str,
        github_data: Dict[str, Any],
        recommendation_type: str,
        tone: str,
        length: str,
        focus_keywords: Optional[List[str]] = None,
        focus_weights: Optional[Dict[str, float]] = None,
        display_name: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Generate multiple recommendation options with explanations."""
        options = await self._generate_multiple_options(initial_prompt, github_data, recommendation_type, tone, length, focus_keywords, focus_weights, display_name)

        # Add explanations to each option
        for option in options:
            explanation = self._generate_option_explanation(option["content"], option["name"], option["focus"], github_data, display_name)
            option["explanation"] = explanation

        return options

    async def _generate_single_option(
        self, prompt: str, temperature_modifier: float, length: str = "medium", generation_params: Optional[Dict[str, Any]] = None, github_data: Optional[Dict[str, Any]] = None
    ) -> tuple[str, Optional[Dict[str, Any]]]:
        """Generate a single recommendation option with formatting."""
        if not self.client or not genai_available:
            raise ValueError("AI client not initialized")

        # Adjust temperature for variety
        config = types.GenerateContentConfig(
            temperature=min(settings.GEMINI_TEMPERATURE + temperature_modifier, 2.0),
            max_output_tokens=settings.GEMINI_MAX_TOKENS,
            top_p=0.9,
            top_k=40,
        )
        try:
            response = self.client.models.generate_content(model=settings.GEMINI_MODEL, contents=prompt, config=config)
        except Exception as e:
            if "429" in str(e) or "RESOURCE_EXHAUSTED" in str(e):
                # Extract retry delay from error
                import re

                match = re.search(r"retryDelay.*?(\d+)s", str(e))
                retry_seconds = int(match.group(1)) if match else 60

                raise Exception(
                    {
                        "type": "rate_limit_exceeded",
                        "message": f"API rate limit reached. Please wait {retry_seconds} seconds.",
                        "retry_after": retry_seconds,
                        "suggestions": ["Wait and try again", "Consider upgrading to Gemini Pro for higher limits", "Use fewer options to reduce API calls"],
                    }
                )
            raise e

        # Get the raw content
        raw_content = response.candidates[0].content.parts[0].text

        # Debug: Log raw AI output to see what we're working with
        logger.info(f"🔍 RAW AI OUTPUT (length: {len(raw_content)} chars):")
        logger.info(f"🔍 First 300 chars: {raw_content[:300]}...")
        double_newlines = "\n\n" in raw_content
        logger.info(f"🔍 Contains double newlines: {double_newlines}")
        logger.info(f"🔍 Number of sentences (estimated): {len(raw_content.split('.'))}")

        # Apply formatting
        formatted_content = self._format_recommendation_output(raw_content, length, generation_params)

        # Validate naturalness using story generator
        try:
            naturalness_validation = self.story_generator.validate_naturalness(formatted_content)
        except Exception as e:
            logger.error(f"Error in naturalness validation: {e}")
            naturalness_validation = {"is_natural": True, "naturalness_score": 85, "issues": [f"Naturalness validation error: {str(e)}"], "suggestions": ["Review naturalness validation logic"]}

        # Validate the structure
        validation = self._validate_recommendation_structure(formatted_content, generation_params)

        # Enhanced validation with semantic alignment and generic content detection
        if generation_params and github_data is not None:
            # Get github_data from generation_params or assume it's passed through
            semantic_validation = self._validate_semantic_alignment(formatted_content, github_data, generation_params)
            generic_validation = self._detect_generic_content(formatted_content)

            # Combine validation results including naturalness
            combined_validation = {
                "structure_valid": validation["is_valid"],
                "semantically_aligned": semantic_validation["is_aligned"],
                "not_too_generic": not generic_validation["is_too_generic"],
                "is_natural": naturalness_validation.get("is_natural", True),
                "naturalness_score": naturalness_validation.get("naturalness_score", 85),
                "overall_quality_score": min(
                    validation.get("structure_score", 100),
                    semantic_validation.get("alignment_score", 100),
                    max(0, 100 - generic_validation.get("generic_score", 0)),
                    naturalness_validation.get("naturalness_score", 85),
                ),
                "issues": validation["issues"] + semantic_validation["issues"] + generic_validation["issues"] + naturalness_validation.get("issues", []),
                "suggestions": validation["suggestions"] + semantic_validation["suggestions"] + generic_validation["suggestions"] + naturalness_validation.get("suggestions", []),
                "semantic_coverage": semantic_validation.get("data_coverage", {}),
                "generic_indicators": {
                    "buzzwords": generic_validation.get("buzzwords_detected", []),
                    "generic_phrases": generic_validation.get("generic_phrases_detected", []),
                    "vague_descriptors": generic_validation.get("vague_descriptors_detected", []),
                },
                "naturalness_indicators": {
                    "robotic_phrases": [issue for issue in naturalness_validation.get("issues", []) if "robotic phrase" in issue],
                    "technical_jargon": [issue for issue in naturalness_validation.get("issues", []) if "technical jargon" in issue],
                },
            }

            if settings.ENVIRONMENT == "development":
                if not combined_validation["structure_valid"]:
                    logger.warning(f"⚠️  Structure validation issues: {validation['issues']}")
                if not combined_validation["semantically_aligned"]:
                    logger.warning(f"⚠️  Semantic alignment issues: {semantic_validation['issues']}")
                if combined_validation["not_too_generic"] is False:
                    logger.warning(f"⚠️  Generic content detected: {generic_validation['issues']}")
                if not combined_validation["is_natural"]:
                    logger.warning(f"⚠️  Naturalness issues detected: {naturalness_validation['issues']}")
                if combined_validation["suggestions"]:
                    logger.info(f"💡 Quality improvement suggestions: {combined_validation['suggestions'][:3]}")

                logger.info(f"📊 Overall quality score: {combined_validation['overall_quality_score']}/100")

            return formatted_content, combined_validation

        # Legacy validation for backward compatibility with naturalness validation
        legacy_validation = {
            "structure_valid": validation["is_valid"],
            "is_natural": naturalness_validation["is_natural"],
            "naturalness_score": naturalness_validation["naturalness_score"],
            "overall_quality_score": min(validation.get("structure_score", 100), naturalness_validation["naturalness_score"]),
            "issues": validation["issues"] + naturalness_validation["issues"],
            "suggestions": validation["suggestions"] + naturalness_validation["suggestions"],
        }

        if settings.ENVIRONMENT == "development":
            if not validation["is_valid"]:
                logger.warning(f"⚠️  Content validation issues: {validation['issues']}")
            if not naturalness_validation["is_natural"]:
                logger.warning(f"⚠️  Naturalness issues detected: {naturalness_validation['issues']}")
            if legacy_validation["suggestions"]:
                logger.info(f"💡 Suggestions: {legacy_validation['suggestions'][:3]}")

        return formatted_content, legacy_validation

    def _format_recommendation_output(self, content: str, length_guideline: str, generation_params: Optional[Dict[str, Any]] = None) -> str:
        """Format and structure the AI-generated recommendation output."""
        if not content or not content.strip():
            return content

        logger.debug(f"Formatting started for content (first 100 chars): {content[:100]}...")

        # 1. Remove Markdown for bold and italics
        # Regex to find **text**, __text__, *text*, _text_ and replace with just text
        cleaned_content = re.sub(r"\*\*(.*?)\*\*|__(.*?)__|\*(.*?)\*|_(.*?)_", r"\1\2\3\4", content)
        logger.debug(f"After markdown removal (first 100 chars): {cleaned_content[:100]}...")

        # Clean up the content (remove excessive whitespace and strip leading/trailing)
        formatted_content = cleaned_content.strip()

        # 2. Initial splitting into paragraphs
        # Try splitting by double newlines first for explicit breaks
        paragraphs = [p.strip() for p in formatted_content.split("\n\n") if p.strip()]
        logger.debug(f"After initial split (found {len(paragraphs)} paragraphs): {paragraphs[:2]}...")

        # If few paragraphs, try to split by sentences to form more natural paragraphs
        if len(paragraphs) <= 1:
            sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+", formatted_content) if s.strip()]

            if len(sentences) > 2:  # Only re-paragraph if there are enough sentences
                paragraphs = []
                current_paragraph_sentences = []

                # Determine target sentences per paragraph based on overall length and target paragraphs
                target_paragraphs = self._get_target_paragraphs(length_guideline)
                sentences_per_paragraph = max(2, len(sentences) // target_paragraphs)

                for i, sentence in enumerate(sentences):
                    current_paragraph_sentences.append(sentence)
                    if len(current_paragraph_sentences) >= sentences_per_paragraph and (len(paragraphs) < target_paragraphs - 1 or i == len(sentences) - 1):
                        paragraphs.append(" ".join(current_paragraph_sentences))
                        current_paragraph_sentences = []

                # Add any remaining sentences as the last paragraph
                if current_paragraph_sentences:
                    paragraphs.append(" ".join(current_paragraph_sentences))
            else:
                paragraphs = [formatted_content]  # Fallback if not enough sentences for splitting
            logger.debug(f"After sentence-based re-paragraphing (found {len(paragraphs)} paragraphs): {paragraphs[:2]}...")

        # 3. Ensure proper paragraph count based on length guideline
        target_paragraphs = self._get_target_paragraphs(length_guideline)

        # Dynamic adjustment of paragraphs
        # If we have too few, try to split longer ones
        while len(paragraphs) < target_paragraphs and any(len(p.split()) > 70 for p in paragraphs):
            new_paragraphs = []
            made_split = False
            for para in paragraphs:
                if len(para.split()) > 70 and len(new_paragraphs) < target_paragraphs - 1:  # Prevent endless splitting
                    sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+", para) if s.strip()]
                    if len(sentences) > 2:
                        mid_point = len(sentences) // 2
                        new_paragraphs.append(" ".join(sentences[:mid_point]))
                        new_paragraphs.append(" ".join(sentences[mid_point:]))
                        made_split = True
                    else:
                        new_paragraphs.append(para)
                else:
                    new_paragraphs.append(para)
            if not made_split or len(new_paragraphs) == len(paragraphs):  # No more paragraphs were split or no split was made
                break
            paragraphs = new_paragraphs
            logger.debug(f"After dynamic splitting (now {len(paragraphs)} paragraphs): {paragraphs[:2]}...")

        # If we have too many, try to merge shorter ones
        while len(paragraphs) > target_paragraphs and any(len(p.split()) < 40 for p in paragraphs):
            merged_paragraphs = []
            made_merge = False
            i = 0
            while i < len(paragraphs):
                if i + 1 < len(paragraphs) and len(paragraphs[i].split()) + len(paragraphs[i + 1].split()) < 100 and len(merged_paragraphs) < target_paragraphs - 1:
                    merged_paragraphs.append(paragraphs[i] + " " + paragraphs[i + 1])
                    made_merge = True
                    i += 2
                else:
                    merged_paragraphs.append(paragraphs[i])
                    i += 1
            if not made_merge or len(merged_paragraphs) == len(paragraphs):  # No more paragraphs were merged or no merge was made
                break
            paragraphs = merged_paragraphs
            logger.debug(f"After dynamic merging (now {len(paragraphs)} paragraphs): {paragraphs[:2]}...")

        # Final cleaning and joining
        cleaned_paragraphs = []
        for para in paragraphs:
            # Replace single newlines within a paragraph with a space, then remove excessive whitespace
            cleaned = " ".join(para.replace("\n", " ").split())
            if cleaned and not cleaned.endswith((".", "!", "?")):  # Ensure proper sentence endings
                cleaned += "."
            if cleaned and len(cleaned) > 1:  # Capitalize first letter
                cleaned = cleaned[0].upper() + cleaned[1:]
            cleaned_paragraphs.append(cleaned)

        # Explicitly join with double newlines
        final_content = "\n\n".join(cleaned_paragraphs)
        logger.debug(f"Final content before tone formatting (first 100 chars): {final_content[:100]}...")

        # Apply tone-specific formatting (existing logic)
        if generation_params:
            tone = generation_params.get("tone", "professional")
            final_content = self._apply_tone_formatting(final_content, tone)
            logger.debug(f"Final content after tone formatting (first 100 chars): {final_content[:100]}...")

        return final_content

    def _get_target_paragraphs(self, length_guideline: str) -> int:
        """Get the target number of paragraphs based on length guideline."""
        targets = {"short": 1, "medium": 2, "long": 3}
        return targets.get(length_guideline, 2)

    def _apply_tone_formatting(self, content: str, tone: str) -> str:
        """Apply tone-specific formatting to the content."""
        if tone == "professional":
            # Ensure professional language and structure
            # Could add checks for overly casual language here
            return content
        elif tone == "casual":
            # For casual tone, might want to adjust formality slightly
            return content
        else:
            return content

    def _validate_semantic_alignment(self, content: str, github_data: Dict[str, Any], generation_params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Validate that the generated content semantically aligns with the input GitHub data."""
        validation_results = {"is_aligned": True, "alignment_score": 100, "issues": [], "suggestions": [], "data_coverage": {}}

        content_lower = content.lower()

        # Extract key data points from github_data
        user_data = github_data.get("user_data", {})
        username = user_data.get("github_username", "").lower()
        skills = github_data.get("skills", {})
        technical_skills = [skill.lower() for skill in skills.get("technical_skills", [])]
        frameworks = [fw.lower() for fw in skills.get("frameworks", [])]
        languages = github_data.get("languages", [])
        languages_lower = [lang.language.lower() for lang in languages if lang.language]

        # Check for username presence (should be mentioned)
        if username and username not in content_lower:
            validation_results["issues"].append(f"Username '{username}' not mentioned in recommendation")
            validation_results["alignment_score"] -= 20

        # Check for technical skills coverage
        mentioned_skills = []
        for skill in technical_skills[:5]:  # Check top 5 skills
            if skill in content_lower:
                mentioned_skills.append(skill)

        skill_coverage = len(mentioned_skills) / max(len(technical_skills[:5]), 1)
        validation_results["data_coverage"]["technical_skills"] = {"mentioned": mentioned_skills, "coverage_ratio": skill_coverage, "total_available": len(technical_skills[:5])}

        if skill_coverage < 0.4 and technical_skills:  # Less than 40% coverage
            validation_results["issues"].append(f"Low technical skills coverage: only {len(mentioned_skills)}/{len(technical_skills[:5])} skills mentioned")
            validation_results["alignment_score"] -= 15

        # Check for programming languages
        mentioned_languages = []
        for lang in languages_lower[:3]:  # Check top 3 languages
            if lang in content_lower:
                mentioned_languages.append(lang)

        language_coverage = len(mentioned_languages) / max(len(languages_lower[:3]), 1)
        validation_results["data_coverage"]["languages"] = {"mentioned": mentioned_languages, "coverage_ratio": language_coverage, "total_available": len(languages_lower[:3])}

        # Check for frameworks
        mentioned_frameworks = []
        for framework in frameworks[:3]:  # Check top 3 frameworks
            if framework in content_lower:
                mentioned_frameworks.append(framework)

        framework_coverage = len(mentioned_frameworks) / max(len(frameworks[:3]), 1)
        validation_results["data_coverage"]["frameworks"] = {"mentioned": mentioned_frameworks, "coverage_ratio": framework_coverage, "total_available": len(frameworks[:3])}

        # Check for high-impact contributions if available
        high_impact = github_data.get("high_impact_contributions", {})
        notable_contributions = high_impact.get("notable_contributions", [])
        if notable_contributions:
            contribution_mentioned = any(contrib.get("repository", "").lower() in content_lower for contrib in notable_contributions)
            if not contribution_mentioned:
                validation_results["issues"].append("No mention of notable high-impact contributions")
                validation_results["alignment_score"] -= 10

        # Overall alignment assessment
        total_coverage = (skill_coverage + language_coverage + framework_coverage) / 3
        if total_coverage < 0.3:
            validation_results["is_aligned"] = False
            validation_results["issues"].append("Overall data coverage is very low - recommendation may be too generic")
            validation_results["suggestions"].append("Consider mentioning more specific technical skills and technologies from the profile")

        validation_results["alignment_score"] = max(0, validation_results["alignment_score"])

        return validation_results

    def _detect_generic_content(self, content: str) -> Dict[str, Any]:
        """Detect generic, cliché, or overly common phrases in the recommendation.

        Enhanced detection includes:
        - Buzzwords and clichés
        - LinkedIn platitudes
        - Vague descriptors
        - Specificity requirements (technology mentions, examples, outcomes)
        - Structural quality checks
        """
        generic_indicators = {
            "buzzwords": [
                "passionate",
                "dedicated",
                "hardworking",
                "team player",
                "quick learner",
                "detail-oriented",
                "problem solver",
                "innovative",
                "creative",
                "proactive",
                "results-driven",
                "customer-focused",
                "self-motivated",
                "excellent communication",
                "dynamic",
                "synergistic",
                "motivated",
                "enthusiastic",
                "driven",
                "committed",
            ],
            "generic_phrases": [
                "worked on various projects",
                "contributed to the team",
                "helped improve",
                "was responsible for",
                "played a key role",
                "worked closely with",
                "gained experience in",
                "developed skills in",
                "learned to use",
                "has a strong background",
                "brings a wealth of experience",
                "demonstrated ability to",
                "proven track record",
                "exceeded expectations",
                "went above and beyond",
                "takes initiative",
                "adds value",
            ],
            "vague_descriptors": [
                "good at",
                "skilled in",
                "experienced with",
                "knowledge of",
                "understanding of",
                "familiar with",
                "comfortable with",
                "proficient in",
                "competent in",
                "capable of",
            ],
            "linkedin_platitudes": [
                "pleasure to work with",
                "asset to any team",
                "would be an asset",
                "highly recommend",
                "would not hesitate to recommend",
                "without hesitation",
                "any team would be lucky",
                "lucky to have",
                "pleasure of working",
                "honor to work with",
                "privilege to work",
                "strongly recommend",
                "wholeheartedly recommend",
                "cannot recommend enough",
                "one of the best",
                "among the best",
                "top performer",
                "star performer",
                "outstanding individual",
                "exceptional talent",
            ],
            "ai_tells": [
                "it's worth noting",
                "importantly",
                "furthermore",
                "moreover",
                "additionally",
                "in conclusion",
                "to summarize",
                "it should be mentioned",
                "notably",
                "indeed",
                "certainly",
                "undoubtedly",
                "without a doubt",
                "needless to say",
            ],
        }

        content_lower = content.lower()
        detected_issues = []

        # Count buzzwords
        buzzword_count = 0
        found_buzzwords = []
        for buzzword in generic_indicators["buzzwords"]:
            if buzzword in content_lower:
                buzzword_count += 1
                found_buzzwords.append(buzzword)

        # Count generic phrases
        generic_phrase_count = 0
        found_generic_phrases = []
        for phrase in generic_indicators["generic_phrases"]:
            if phrase in content_lower:
                generic_phrase_count += 1
                found_generic_phrases.append(phrase)

        # Count vague descriptors
        vague_descriptor_count = 0
        found_vague_descriptors = []
        for descriptor in generic_indicators["vague_descriptors"]:
            if descriptor in content_lower:
                vague_descriptor_count += 1
                found_vague_descriptors.append(descriptor)

        # Count LinkedIn platitudes (heavily penalized)
        platitude_count = 0
        found_platitudes = []
        for platitude in generic_indicators["linkedin_platitudes"]:
            if platitude in content_lower:
                platitude_count += 1
                found_platitudes.append(platitude)

        # Count AI tells
        ai_tell_count = 0
        found_ai_tells = []
        for tell in generic_indicators["ai_tells"]:
            if tell in content_lower:
                ai_tell_count += 1
                found_ai_tells.append(tell)

        # SPECIFICITY REQUIREMENTS CHECK
        specificity_score = 100
        specificity_issues = []

        # Check for technology/skill mentions (at least 1 specific tech)
        tech_indicators = [
            "python", "javascript", "typescript", "java", "go", "rust", "c++", "c#",
            "react", "vue", "angular", "node", "django", "flask", "fastapi", "spring",
            "docker", "kubernetes", "aws", "gcp", "azure", "postgresql", "mongodb",
            "redis", "graphql", "rest", "api", "microservices", "machine learning",
            "tensorflow", "pytorch", "sql", "nosql", "ci/cd", "git", "linux",
        ]
        has_tech = any(tech in content_lower for tech in tech_indicators)
        if not has_tech:
            specificity_score -= 15
            specificity_issues.append("No specific technology mentioned")

        # Check for specific examples/incidents
        example_indicators = [
            "when", "during", "there was", "i remember", "one time", "specifically",
            "for example", "in particular", "instance", "situation", "project",
            "incident", "challenge", "problem we faced", "deadline",
        ]
        has_example = sum(1 for ind in example_indicators if ind in content_lower) >= 2
        if not has_example:
            specificity_score -= 20
            specificity_issues.append("No specific examples or incidents mentioned")

        # Check for outcome/impact statements
        outcome_indicators = [
            "resulted in", "led to", "improved", "reduced", "increased", "saved",
            "achieved", "delivered", "completed", "launched", "shipped", "fixed",
            "solved", "built", "created", "implemented", "automated", "streamlined",
            "within an hour", "in record time", "ahead of schedule", "under budget",
        ]
        has_outcome = any(ind in content_lower for ind in outcome_indicators)
        if not has_outcome:
            specificity_score -= 15
            specificity_issues.append("No specific outcomes or impact mentioned")

        # Check for first-person perspective (personal voice)
        first_person = ["i worked", "i saw", "i observed", "i watched", "i noticed",
                       "impressed me", "what i", "my experience", "i've seen",
                       "i remember", "i learned", "we worked", "our team"]
        has_personal_voice = sum(1 for fp in first_person if fp in content_lower) >= 2
        if not has_personal_voice:
            specificity_score -= 10
            specificity_issues.append("Lacks personal voice/first-person perspective")

        # Calculate generic score (higher = more generic)
        base_generic_score = (
            buzzword_count * 5 +
            generic_phrase_count * 7 +
            vague_descriptor_count * 4 +
            platitude_count * 10 +  # Heavy penalty for platitudes
            ai_tell_count * 8       # Heavy penalty for AI tells
        )
        generic_score = min(100, base_generic_score)

        # Combine with specificity (lack of specificity adds to generic score)
        specificity_penalty = max(0, 100 - specificity_score) * 0.5
        final_generic_score = min(100, generic_score + specificity_penalty)

        # Assess severity
        if buzzword_count > 3:
            detected_issues.append(f"High buzzword usage ({buzzword_count} detected) - makes content less authentic")
        if generic_phrase_count > 2:
            detected_issues.append(f"Multiple generic phrases ({generic_phrase_count} detected) - lacks specificity")
        if platitude_count > 1:
            detected_issues.append(f"LinkedIn platitudes detected ({platitude_count}) - sounds template-like")
        if ai_tell_count > 0:
            detected_issues.append(f"AI-style phrases detected ({ai_tell_count}) - sounds robotic")
        if final_generic_score > 60:
            detected_issues.append("Content appears highly generic and could benefit from more specific examples")

        # Add specificity issues
        detected_issues.extend(specificity_issues)

        return {
            "generic_score": final_generic_score,
            "issues": detected_issues,
            "buzzwords_detected": found_buzzwords,
            "generic_phrases_detected": found_generic_phrases,
            "vague_descriptors_detected": found_vague_descriptors,
            "linkedin_platitudes_detected": found_platitudes,
            "ai_tells_detected": found_ai_tells,
            "specificity_score": specificity_score,
            "specificity_issues": specificity_issues,
            "is_too_generic": final_generic_score > 40,
            "suggestions": (
                ["Replace buzzwords with specific examples and achievements", "Include concrete project names and technical details", "Focus on measurable outcomes rather than general descriptors"]
                if generic_score > 30
                else []
            ),
        }

    def _validate_recommendation_structure(self, content: str, generation_params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Validate the structure and quality of the formatted recommendation."""
        validation_results: Dict[str, Any] = {"is_valid": True, "issues": [], "suggestions": [], "structure_score": 100}

        paragraphs = [p.strip() for p in content.split("\n\n") if p.strip()]
        word_count = len(content.split())

        # Check paragraph count
        expected_paragraphs = 2  # Default (medium)
        if generation_params:
            length = generation_params.get("length", "medium")
            if length == "short":
                expected_paragraphs = 1
            elif length == "medium":
                expected_paragraphs = 2
            elif length == "long":
                expected_paragraphs = 3

        if len(paragraphs) != expected_paragraphs:
            validation_results["issues"].append(f"Expected {expected_paragraphs} paragraphs, got {len(paragraphs)}")
            validation_results["structure_score"] = int(validation_results["structure_score"]) - 20  # Explicitly cast to int

        # Check word count
        if generation_params:
            length = generation_params.get("length", "medium")
            if length == "short" and (word_count < 80 or word_count > 120):
                validation_results["issues"].append("Word count outside short range (80-120)")
                validation_results["structure_score"] = int(validation_results["structure_score"]) - 15  # Explicitly cast to int
            elif length == "medium" and (word_count < 120 or word_count > 180):
                validation_results["issues"].append("Word count outside medium range (120-180)")
                validation_results["structure_score"] = int(validation_results["structure_score"]) - 10  # Explicitly cast to int
            elif length == "long" and (word_count < 180 or word_count > 250):
                validation_results["issues"].append("Word count outside long range (180-250)")
                validation_results["structure_score"] = int(validation_results["structure_score"]) - 15  # Explicitly cast to int

        # Check for incomplete sentences (using regex to split more robustly)
        sentences = re.split(r"(?<=[.!?])\s+", content)
        incomplete_sentences = [s for s in sentences if s.strip() and len(s.split()) < 3]
        if len(incomplete_sentences) > len(sentences) * 0.2 and len(sentences) > 5:  # Only flag if many sentences and a significant percentage are short
            validation_results["issues"].append(f"Too many incomplete or very short sentences ({len(incomplete_sentences)} out of {len(sentences)})")
            validation_results["structure_score"] = int(validation_results["structure_score"]) - 10  # Explicitly cast to int

        # Check paragraph lengths
        for i, para in enumerate(paragraphs):
            para_words = len(para.split())
            if para_words < 20:
                validation_results["suggestions"].append(f"Paragraph {i+1} is quite short ({para_words} words)")
            elif para_words > 150:
                validation_results["suggestions"].append(f"Paragraph {i+1} is very long ({para_words} words)")

        validation_results["structure_score"] = max(0, int(validation_results["structure_score"]))  # Explicitly cast to int
        return validation_results

    def calculate_confidence_score(
        self,
        github_data: Dict[str, Any],
        recommendation: str,
        validation_results: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Calculate confidence score for a generated recommendation.

        This provides transparency about recommendation quality by scoring:
        - Data richness: How much GitHub data was available
        - Evidence strength: How well the recommendation uses actual data
        - Specificity: How specific and unique the recommendation is
        - Natural voice: How human-like the writing sounds

        Returns:
            Dict with overall score (0-100), breakdown by category, and limitations.
        """
        scores = {}
        limitations = []

        # 1. DATA RICHNESS SCORE (0-100)
        data_richness = self._score_data_richness(github_data)
        scores["data_richness"] = data_richness["score"]
        limitations.extend(data_richness.get("limitations", []))

        # 2. EVIDENCE STRENGTH SCORE (0-100)
        evidence_strength = self._score_evidence_in_text(recommendation, github_data)
        scores["evidence_strength"] = evidence_strength["score"]

        # 3. SPECIFICITY SCORE (0-100)
        specificity = self._score_specificity(recommendation)
        scores["specificity"] = specificity["score"]

        # 4. NATURAL VOICE SCORE (0-100)
        naturalness = self._score_naturalness(recommendation)
        scores["natural_voice"] = naturalness["score"]

        # Calculate weighted overall score
        weights = {
            "data_richness": 0.25,
            "evidence_strength": 0.30,
            "specificity": 0.25,
            "natural_voice": 0.20,
        }

        overall = sum(scores[key] * weights[key] for key in weights)

        # Determine confidence level
        if overall >= 80:
            confidence_level = "high"
            confidence_message = "High confidence - recommendation is well-supported by data"
        elif overall >= 60:
            confidence_level = "medium"
            confidence_message = "Medium confidence - recommendation has good foundation but could be stronger"
        elif overall >= 40:
            confidence_level = "low"
            confidence_message = "Low confidence - limited data or evidence available"
        else:
            confidence_level = "very_low"
            confidence_message = "Very low confidence - recommendation may be too generic"

        return {
            "overall_score": round(overall, 1),
            "confidence_level": confidence_level,
            "confidence_message": confidence_message,
            "breakdown": {
                "data_richness": {
                    "score": scores["data_richness"],
                    "description": "How much GitHub data was available to inform the recommendation",
                },
                "evidence_strength": {
                    "score": scores["evidence_strength"],
                    "description": "How well the recommendation uses actual data points from the profile",
                },
                "specificity": {
                    "score": scores["specificity"],
                    "description": "How specific and unique the recommendation is vs generic praise",
                },
                "natural_voice": {
                    "score": scores["natural_voice"],
                    "description": "How natural and human-like the writing sounds",
                },
            },
            "limitations": limitations,
            "suggestions": self._generate_confidence_suggestions(scores, limitations),
        }

    def _score_data_richness(self, github_data: Dict[str, Any]) -> Dict[str, Any]:
        """Score how rich the available GitHub data is."""
        score = 0
        max_score = 100
        limitations = []

        # Check user data (20 points)
        user_data = github_data.get("user_data", {})
        if user_data.get("full_name"):
            score += 5
        if user_data.get("bio"):
            score += 10
        else:
            limitations.append("No bio available - personality signals limited")
        if user_data.get("company"):
            score += 5

        # Check repositories (25 points)
        repositories = github_data.get("repositories", [])
        if len(repositories) >= 5:
            score += 25
        elif len(repositories) >= 3:
            score += 15
        elif len(repositories) >= 1:
            score += 10
        else:
            limitations.append("No repositories found - technical skills cannot be verified")

        # Check languages (15 points)
        languages = github_data.get("languages", [])
        if len(languages) >= 3:
            score += 15
        elif len(languages) >= 1:
            score += 10
        else:
            limitations.append("No language data - tech stack unknown")

        # Check commit analysis (25 points)
        commit_analysis = github_data.get("commit_analysis", {})
        total_commits = commit_analysis.get("total_commits_analyzed", 0)
        if total_commits >= 50:
            score += 25
        elif total_commits >= 20:
            score += 15
        elif total_commits >= 5:
            score += 10
        else:
            limitations.append("Limited commit history - contribution patterns unclear")

        # Check skills (15 points)
        skills = github_data.get("skills", {})
        technical_skills = skills.get("technical_skills", [])
        if len(technical_skills) >= 5:
            score += 15
        elif len(technical_skills) >= 2:
            score += 10
        elif len(technical_skills) >= 1:
            score += 5
        else:
            limitations.append("No specific skills detected")

        return {
            "score": min(score, max_score),
            "limitations": limitations,
        }

    def _score_evidence_in_text(
        self,
        recommendation: str,
        github_data: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Score how well the recommendation uses actual data."""
        score = 0
        recommendation_lower = recommendation.lower()

        # Check for language mentions (25 points)
        languages = github_data.get("languages", [])
        language_names = [
            lang.get("language", lang) if isinstance(lang, dict) else str(lang)
            for lang in languages[:5]
        ]
        languages_mentioned = sum(1 for lang in language_names if lang.lower() in recommendation_lower)
        score += min(25, languages_mentioned * 10)

        # Check for framework/tool mentions (25 points)
        skills = github_data.get("skills", {})
        frameworks = skills.get("frameworks", [])
        tools = skills.get("tools", [])
        all_tools = frameworks + tools
        tools_mentioned = sum(1 for tool in all_tools[:10] if tool.lower() in recommendation_lower)
        score += min(25, tools_mentioned * 8)

        # Check for contribution pattern mentions (25 points)
        commit_analysis = github_data.get("commit_analysis", {})
        excellence = commit_analysis.get("excellence_areas", {})
        primary_strength = excellence.get("primary_strength", "")

        strength_keywords = {
            "bug_fixing": ["fix", "debug", "troubleshoot", "resolve"],
            "optimization": ["optimize", "performance", "efficient"],
            "refactoring": ["refactor", "clean", "maintain"],
            "testing": ["test", "quality", "reliable"],
            "documentation": ["document", "clear", "explain"],
        }

        if primary_strength and primary_strength in strength_keywords:
            if any(kw in recommendation_lower for kw in strength_keywords[primary_strength]):
                score += 25
            else:
                score += 10  # Partial credit

        # Check for user name usage (25 points)
        user_data = github_data.get("user_data", {})
        username = user_data.get("github_username", "")
        full_name = user_data.get("full_name", "")
        first_name = full_name.split()[0] if full_name else ""

        if first_name and first_name.lower() in recommendation_lower:
            score += 25
        elif username and username.lower() in recommendation_lower:
            score += 15

        return {"score": min(score, 100)}

    def _score_specificity(self, recommendation: str) -> Dict[str, Any]:
        """Score how specific vs generic the recommendation is."""
        score = 100
        recommendation_lower = recommendation.lower()

        # Penalize generic buzzwords
        buzzwords = [
            "passionate", "dedicated", "hardworking", "team player",
            "innovative", "creative", "proactive", "results-driven",
        ]
        buzzword_count = sum(1 for bw in buzzwords if bw in recommendation_lower)
        score -= buzzword_count * 5

        # Penalize generic phrases
        generic_phrases = [
            "asset to any team", "highly recommend", "pleasure to work with",
            "without hesitation", "would be lucky",
        ]
        generic_count = sum(1 for phrase in generic_phrases if phrase in recommendation_lower)
        score -= generic_count * 10

        # Reward specific indicators
        specific_indicators = [
            "when", "during", "specifically", "for example", "i remember",
            "one time", "project", "deadline", "challenge",
        ]
        specific_count = sum(1 for ind in specific_indicators if ind in recommendation_lower)
        score += min(20, specific_count * 5)

        # Reward outcome mentions
        outcome_words = [
            "resulted", "improved", "reduced", "saved", "achieved",
            "delivered", "fixed", "solved", "built", "launched",
        ]
        outcome_count = sum(1 for word in outcome_words if word in recommendation_lower)
        score += min(15, outcome_count * 5)

        return {"score": max(0, min(100, score))}

    def _score_naturalness(self, recommendation: str) -> Dict[str, Any]:
        """Score how natural and human-like the writing is."""
        score = 100
        recommendation_lower = recommendation.lower()

        # Penalize AI tells
        ai_tells = [
            "it's worth noting", "importantly", "furthermore", "moreover",
            "additionally", "in conclusion", "notably", "indeed",
        ]
        ai_tell_count = sum(1 for tell in ai_tells if tell in recommendation_lower)
        score -= ai_tell_count * 10

        # Reward first-person voice
        first_person = ["i ", "i've", "my ", "we ", "our "]
        first_person_count = sum(1 for fp in first_person if fp in recommendation_lower)
        score += min(15, first_person_count * 3)

        # Check sentence variety (penalize if all similar length)
        sentences = [s.strip() for s in recommendation.split(".") if s.strip()]
        if len(sentences) >= 3:
            lengths = [len(s.split()) for s in sentences]
            avg_len = sum(lengths) / len(lengths)
            variance = sum((l - avg_len) ** 2 for l in lengths) / len(lengths)
            if variance > 20:  # Good variety
                score += 10
            elif variance < 5:  # Too uniform
                score -= 10

        # Reward emotional language
        emotion_words = [
            "impressed", "amazed", "appreciate", "admire", "respect",
            "enjoy", "love", "proud", "grateful", "pleasure",
        ]
        emotion_count = sum(1 for word in emotion_words if word in recommendation_lower)
        score += min(10, emotion_count * 3)

        return {"score": max(0, min(100, score))}

    def _generate_confidence_suggestions(
        self,
        scores: Dict[str, int],
        limitations: List[str],
    ) -> List[str]:
        """Generate suggestions to improve confidence."""
        suggestions = []

        if scores.get("data_richness", 0) < 60:
            suggestions.append("Consider requesting additional context about shared work experience")

        if scores.get("evidence_strength", 0) < 60:
            suggestions.append("Try regenerating with specific skills or projects highlighted")

        if scores.get("specificity", 0) < 60:
            suggestions.append("Request more specific examples using keyword refinement")

        if scores.get("natural_voice", 0) < 60:
            suggestions.append("Consider adjusting tone to 'casual' or 'friendly' for more natural output")

        if limitations:
            suggestions.append(f"Note: {len(limitations)} data limitation(s) may affect accuracy")

        return suggestions[:3]  # Return top 3 suggestions

    async def regenerate_recommendation(
        self,
        original_content: str,
        refinement_instructions: str,
        github_data: Dict[str, Any],
        recommendation_type: str = "professional",
        tone: str = "professional",
        length: str = "medium",
        exclude_keywords: Optional[list] = None,
        analysis_context_type: str = "profile",
        repository_url: Optional[str] = None,
        force_refresh: bool = False,
        display_name: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Regenerate a recommendation with refinement instructions."""

        if not self.client:
            raise ValueError("Gemini AI not configured")

        try:
            logger.info("🔄 REGENERATING RECOMMENDATION")
            logger.info("=" * 60)

            # Extract display name for consistent naming (prioritizes first name)
            if display_name is None:
                display_name = self.prompt_service._extract_display_name(github_data["user_data"])

            # Build refinement prompt
            refinement_prompt = self.prompt_service.build_refinement_prompt_for_regeneration(
                original_content=original_content,
                refinement_instructions=refinement_instructions,
                github_data=github_data,
                recommendation_type=recommendation_type,
                tone=tone,
                length=length,
                exclude_keywords=exclude_keywords,
                display_name=display_name,
            )

            # Create regeneration parameters
            regeneration_params: Dict[str, Any] = {
                "recommendation_type": recommendation_type,
                "tone": tone,
                "length": length,
                "exclude_keywords": exclude_keywords or [],
                "refinement_instructions": refinement_instructions,
            }

            # Generate refined recommendation with formatting
            refined_content = await self._generate_refined_regeneration(refinement_prompt, length, regeneration_params)

            # Update regeneration_params for confidence scoring
            if regeneration_params is None:
                regeneration_params = {}
            regeneration_params["regeneration"] = True

            # Return refined result
            result = {
                "content": refined_content.strip(),
                "title": self.prompt_service.extract_title(refined_content, github_data["user_data"]["github_username"], None, display_name),
                "word_count": len(refined_content.split()),
                "generation_parameters": regeneration_params,
            }

            logger.info("✅ RECOMMENDATION REGENERATED SUCCESSFULLY")
            logger.info("=" * 60)

            return result

        except Exception as e:
            logger.error(f"Error regenerating recommendation: {e}")
            raise

    async def _generate_refined_regeneration(self, prompt: str, length: str = "medium", generation_params: Optional[Dict[str, Any]] = None) -> str:
        """Generate refined recommendation for regeneration with formatting."""
        if not self.client or not genai_available:
            raise ValueError("AI client not initialized")

        config = types.GenerateContentConfig(
            temperature=settings.GEMINI_TEMPERATURE + 0.1,  # Slightly higher for refinement
            max_output_tokens=settings.GEMINI_MAX_TOKENS,
            top_p=0.9,
            top_k=40,
        )
        try:
            response = self.client.models.generate_content(model=settings.GEMINI_MODEL, contents=prompt, config=config)
        except Exception as e:
            if "429" in str(e) or "RESOURCE_EXHAUSTED" in str(e):
                # Extract retry delay from error
                import re

                match = re.search(r"retryDelay.*?(\d+)s", str(e))
                retry_seconds = int(match.group(1)) if match else 60

                raise Exception(
                    {
                        "type": "rate_limit_exceeded",
                        "message": f"API rate limit reached. Please wait {retry_seconds} seconds.",
                        "retry_after": retry_seconds,
                        "suggestions": ["Wait and try again", "Consider upgrading to Gemini Pro for higher limits", "Use fewer options to reduce API calls"],
                    }
                )
            raise e

        # Get the raw content
        raw_content = response.candidates[0].content.parts[0].text

        # Debug: Log raw AI output to see what we're working with
        logger.info(f"🔄 RAW REGENERATION AI OUTPUT (length: {len(raw_content)} chars):")
        logger.info(f"🔄 First 300 chars: {raw_content[:300]}...")
        double_newlines = "\n\n" in raw_content
        logger.info(f"🔄 Contains double newlines: {double_newlines}")
        logger.info(f"🔄 Number of sentences (estimated): {len(raw_content.split('.'))}")

        # Apply formatting
        formatted_content = self._format_recommendation_output(raw_content, length, generation_params)

        # Validate the structure
        validation = self._validate_recommendation_structure(formatted_content, generation_params)

        if settings.ENVIRONMENT == "development" and not validation["is_valid"]:
            logger.warning(f"⚠️  Refined content validation issues: {validation['issues']}")
            if validation["suggestions"]:
                logger.info(f"💡 Suggestions: {validation['suggestions']}")

        return formatted_content

    def can_make_requests(self, num_requests: int) -> bool:
        """Check if we can make multiple requests without hitting rate limits."""
        import time

        now = time.time()
        # Remove timestamps older than 1 minute
        self.request_timestamps = [ts for ts in self.request_timestamps if now - ts < 60]
        return len(self.request_timestamps) + num_requests <= self.rate_limit_requests_per_minute

    def record_requests(self, num_requests: int):
        """Record multiple requests."""
        import time

        now = time.time()
        for _ in range(num_requests):
            self.request_timestamps.append(now)
