"""AI Recommendation Service for generating LinkedIn recommendations."""

import logging
from typing import Any, AsyncGenerator, Dict, List, Optional

from app.core.config import settings
from app.core.redis_client import get_cache, set_cache
from app.services.prompt_service import PromptService

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

    async def generate_recommendation_stream(
        self,
        github_data: Dict[str, Any],
        recommendation_type: str = "professional",
        tone: str = "professional",
        length: str = "medium",
        custom_prompt: Optional[str] = None,
        target_role: Optional[str] = None,
        specific_skills: Optional[list] = None,
        exclude_keywords: Optional[list] = None,
        dynamic_params: Optional[Dict[str, Any]] = None,
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
                target_role=target_role,
                specific_skills=specific_skills,
                exclude_keywords=exclude_keywords,
            )

            # Stage 3: Identifying key contributions
            yield {
                "stage": "Identifying key contributions and skills...",
                "progress": 30,
                "status": "processing",
            }

            # Check cache for final result
            cache_key = f"ai_recommendation_v3:{hash(initial_prompt)}"

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

            # Stage 4: Generating options
            yield {
                "stage": "Generating recommendation options...",
                "progress": 50,
                "status": "generating",
            }

            # Generate options with progress updates
            options = []
            base_username = github_data["user_data"]["github_username"]

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
                {
                    "name": "Option 3",
                    "focus": "leadership_growth",
                    "temperature_modifier": 0.15,
                    "custom_instruction": "Highlight leadership potential and growth mindset.",
                },
            ]

            for i, config in enumerate(option_configs, 1):
                progress = 50 + (i * 15)  # 65%, 80%, 95%
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

                option_content = await self._generate_single_option(option_prompt, temp_modifier, length, option_gen_params)

                # Create option object
                option = {
                    "id": i,
                    "name": config["name"],
                    "content": option_content.strip(),
                    "title": self.prompt_service.extract_title(option_content, base_username),
                    "word_count": len(option_content.split()),
                    "focus": config["focus"],
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
        dynamic_tone: Optional[str] = None,
        dynamic_length: Optional[str] = None,
        include_keywords: Optional[List[str]] = None,
        exclude_keywords: Optional[List[str]] = None,
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """Regenerate a recommendation with streaming progress and dynamic refinement parameters."""

        if not self.client:
            raise ValueError("Gemini AI not configured")

        try:
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
                include_keywords=include_keywords,
                exclude_keywords=exclude_keywords,
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
                "title": self.prompt_service.extract_title(refined_content, github_data["user_data"]["github_username"]),
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
        target_role: Optional[str] = None,
        specific_skills: Optional[list] = None,
        exclude_keywords: Optional[list] = None,
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
                target_role=target_role,
                specific_skills=specific_skills,
                exclude_keywords=exclude_keywords,
            )

            if settings.ENVIRONMENT == "development":
                logger.info(f"✅ Prompt built with {len(initial_prompt)} characters")

            # Check cache for final result
            cache_key = f"ai_recommendation_v3:{hash(initial_prompt)}"

            cached_result = await get_cache(cache_key)
            if cached_result and isinstance(cached_result, dict):
                logger.info("Cache hit for AI recommendation")
                return cached_result

            if settings.ENVIRONMENT == "development":
                logger.info("🚀 CACHE MISS: Starting multi-option generation...")

            # Generate 3 different recommendation options with explanations
            options = await self._generate_multiple_options_with_explanations(
                initial_prompt=initial_prompt,
                github_data=github_data,
                recommendation_type=recommendation_type,
                tone=tone,
                length=length,
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

    async def _generate_multiple_options(
        self,
        initial_prompt: str,
        github_data: Dict[str, Any],
        recommendation_type: str,
        tone: str,
        length: str,
    ) -> List[Dict[str, Any]]:
        """Generate 3 different recommendation options."""
        import time

        logger.info("🎭 GENERATING MULTIPLE OPTIONS")
        logger.info("=" * 60)
        pipeline_start = time.time()

        options = []
        base_username = github_data["user_data"]["github_username"]

        # Generate 3 different options with varying approaches
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
            {
                "name": "Option 3",
                "focus": "leadership_growth",
                "temperature_modifier": 0.15,
                "custom_instruction": "Highlight leadership potential and growth mindset.",
            },
        ]

        for i, config in enumerate(option_configs, 1):
            logger.info(f"📝 GENERATING {config['name']}: {config['focus']}")
            logger.info("-" * 40)
            option_start = time.time()

            # Create customized prompt for this option
            option_prompt = self.prompt_service.build_option_prompt(
                initial_prompt,
                str(config["custom_instruction"]),
                str(config["focus"]),
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

            option_content = await self._generate_single_option(option_prompt, temp_modifier, length, option_gen_params)

            option_end = time.time()

            # Create option object
            option = {
                "id": i,
                "name": config["name"],
                "content": option_content.strip(),
                "title": self.prompt_service.extract_title(option_content, base_username),
                "word_count": len(option_content.split()),
                "focus": config["focus"],
            }

            options.append(option)

            logger.info(f"⏱️  {config['name']} completed in {option_end - option_start:.2f} seconds")
            logger.info(f"✅ Generated {option['word_count']} words")
            logger.info(f"   • Preview: {option_content[:100]}...")

        pipeline_end = time.time()
        total_pipeline_time = pipeline_end - pipeline_start

        logger.info("🎉 MULTIPLE OPTIONS GENERATION COMPLETED")
        logger.info("-" * 40)
        logger.info(f"⏱️  Total time: {total_pipeline_time:.2f} seconds")
        logger.info(f"📊 Generated {len(options)} options")
        logger.info("=" * 60)

        return options

    def _generate_option_explanation(self, option_content: str, option_name: str, focus: str, github_data: Dict[str, Any]) -> str:
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
    ) -> List[Dict[str, Any]]:
        """Generate multiple recommendation options with explanations."""
        options = await self._generate_multiple_options(initial_prompt, github_data, recommendation_type, tone, length)

        # Add explanations to each option
        for option in options:
            explanation = self._generate_option_explanation(option["content"], option["name"], option["focus"], github_data)
            option["explanation"] = explanation

        return options

    async def _generate_single_option(self, prompt: str, temperature_modifier: float, length: str = "medium", generation_params: Optional[Dict[str, Any]] = None) -> str:
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
        response = self.client.models.generate_content(model=settings.GEMINI_MODEL, contents=prompt, config=config)

        # Get the raw content
        raw_content = response.candidates[0].content.parts[0].text

        # Apply formatting
        formatted_content = self._format_recommendation_output(raw_content, length, generation_params)

        # Validate the structure
        validation = self._validate_recommendation_structure(formatted_content, generation_params)

        if settings.ENVIRONMENT == "development" and not validation["is_valid"]:
            logger.warning(f"⚠️  Content validation issues: {validation['issues']}")
            if validation["suggestions"]:
                logger.info(f"💡 Suggestions: {validation['suggestions']}")

        return formatted_content

    def _format_recommendation_output(self, content: str, length_guideline: str, generation_params: Optional[Dict[str, Any]] = None) -> str:
        """Format and structure the AI-generated recommendation output."""
        if not content or not content.strip():
            return content

        # Clean up the content
        formatted_content = content.strip()

        # Split into paragraphs and clean up
        paragraphs = [p.strip() for p in formatted_content.split("\n\n") if p.strip()]

        # If we don't have clear paragraphs, try to detect them
        if len(paragraphs) <= 1:
            # Split on double newlines or look for paragraph breaks
            potential_paragraphs = formatted_content.split("\n\n")
            if len(potential_paragraphs) <= 1:
                # Try to split on single newlines or sentence patterns
                sentences = [s.strip() for s in formatted_content.split(".") if s.strip()]
                if len(sentences) > 5:
                    # Group sentences into paragraphs
                    paragraphs = []
                    current_paragraph = []
                    sentences_per_paragraph = max(2, len(sentences) // 3)  # Aim for 3 paragraphs

                    for i, sentence in enumerate(sentences):
                        current_paragraph.append(sentence + ".")
                        if (i + 1) % sentences_per_paragraph == 0 or i == len(sentences) - 1:
                            paragraphs.append(" ".join(current_paragraph))
                            current_paragraph = []
                else:
                    paragraphs = [formatted_content]

        # Ensure proper paragraph count based on length guideline
        target_paragraphs = self._get_target_paragraphs(length_guideline)

        if len(paragraphs) < target_paragraphs:
            # Try to split longer paragraphs
            expanded_paragraphs: List[str] = []
            for para in paragraphs:
                if len(expanded_paragraphs) >= target_paragraphs:
                    expanded_paragraphs.append(para)
                    break

                sentences = [s.strip() for s in para.split(".") if s.strip()]
                if len(sentences) > 3 and len(expanded_paragraphs) < target_paragraphs - 1:
                    # Split this paragraph
                    mid_point = len(sentences) // 2
                    first_half = ". ".join(sentences[:mid_point]) + "."
                    second_half = ". ".join(sentences[mid_point:]) + "."
                    expanded_paragraphs.extend([first_half, second_half])
                else:
                    expanded_paragraphs.append(para + "." if not para.endswith(".") else para)

            paragraphs = expanded_paragraphs

        elif len(paragraphs) > target_paragraphs:
            # Merge shorter paragraphs
            merged_paragraphs: List[str] = []
            i = 0
            while i < len(paragraphs):
                if i + 1 < len(paragraphs) and len(merged_paragraphs) < target_paragraphs - 1:
                    # Merge this paragraph with the next
                    merged = paragraphs[i] + " " + paragraphs[i + 1]
                    merged_paragraphs.append(merged)
                    i += 2
                else:
                    merged_paragraphs.append(paragraphs[i])
                    i += 1

            paragraphs = merged_paragraphs

        # Clean up each paragraph
        cleaned_paragraphs = []
        for para in paragraphs:
            # Remove excessive whitespace
            cleaned = " ".join(para.split())

            # Ensure proper sentence endings
            if cleaned and not cleaned.endswith("."):
                cleaned += "."

            # Capitalize first letter if it's a new sentence
            if cleaned and len(cleaned) > 1:
                cleaned = cleaned[0].upper() + cleaned[1:]

            cleaned_paragraphs.append(cleaned)

        # Join paragraphs with proper spacing
        final_content = "\n\n".join(cleaned_paragraphs)

        # Apply tone-specific formatting
        if generation_params:
            tone = generation_params.get("tone", "professional")
            final_content = self._apply_tone_formatting(final_content, tone)

        return final_content

    def _get_target_paragraphs(self, length_guideline: str) -> int:
        """Get the target number of paragraphs based on length guideline."""
        targets = {"short": 2, "medium": 3, "long": 4}
        return targets.get(length_guideline, 3)

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

    def _validate_recommendation_structure(self, content: str, generation_params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Validate the structure and quality of the formatted recommendation."""
        validation_results: Dict[str, Any] = {"is_valid": True, "issues": [], "suggestions": [], "structure_score": 100}

        paragraphs = [p.strip() for p in content.split("\n\n") if p.strip()]
        word_count = len(content.split())

        # Check paragraph count
        expected_paragraphs = 3  # Default
        if generation_params:
            length = generation_params.get("length", "medium")
            if length == "short":
                expected_paragraphs = 2
            elif length == "long":
                expected_paragraphs = 4

        if len(paragraphs) != expected_paragraphs:
            validation_results["issues"].append(f"Expected {expected_paragraphs} paragraphs, got {len(paragraphs)}")
            validation_results["structure_score"] = int(validation_results["structure_score"]) - 20  # Explicitly cast to int

        # Check word count
        if generation_params:
            length = generation_params.get("length", "medium")
            if length == "short" and word_count > 180:
                validation_results["issues"].append("Content too long for short format")
                validation_results["structure_score"] = int(validation_results["structure_score"]) - 15  # Explicitly cast to int
            elif length == "medium" and (word_count < 120 or word_count > 220):
                validation_results["issues"].append("Word count outside medium range (120-220)")
                validation_results["structure_score"] = int(validation_results["structure_score"]) - 10  # Explicitly cast to int
            elif length == "long" and word_count < 180:
                validation_results["issues"].append("Content too short for long format")
                validation_results["structure_score"] = int(validation_results["structure_score"]) - 15  # Explicitly cast to int

        # Check for incomplete sentences
        sentences = content.split(".")
        incomplete_sentences = [s for s in sentences if s.strip() and len(s.split()) < 3]
        if len(incomplete_sentences) > len(sentences) * 0.2:
            validation_results["issues"].append("Too many incomplete sentences")
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

        if not self.client:
            raise ValueError("Gemini AI not configured")

        try:
            logger.info("🔄 REGENERATING RECOMMENDATION")
            logger.info("=" * 60)

            # Build refinement prompt
            refinement_prompt = self.prompt_service.build_refinement_prompt_for_regeneration(
                original_content=original_content,
                refinement_instructions=refinement_instructions,
                github_data=github_data,
                recommendation_type=recommendation_type,
                tone=tone,
                length=length,
                exclude_keywords=exclude_keywords,
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
                "title": self.prompt_service.extract_title(refined_content, github_data["user_data"]["github_username"]),
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
        response = self.client.models.generate_content(model=settings.GEMINI_MODEL, contents=prompt, config=config)

        # Get the raw content
        raw_content = response.candidates[0].content.parts[0].text

        # Apply formatting
        formatted_content = self._format_recommendation_output(raw_content, length, generation_params)

        # Validate the structure
        validation = self._validate_recommendation_structure(formatted_content, generation_params)

        if settings.ENVIRONMENT == "development" and not validation["is_valid"]:
            logger.warning(f"⚠️  Refined content validation issues: {validation['issues']}")
            if validation["suggestions"]:
                logger.info(f"💡 Suggestions: {validation['suggestions']}")

        return formatted_content
