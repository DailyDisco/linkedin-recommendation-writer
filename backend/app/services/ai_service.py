"""AI service for generating recommendations using Google Gemini."""

import logging
from typing import Any, Dict, List, Optional

try:
    import google.generativeai as genai
except ImportError:
    genai = None  # type: ignore

from app.core.config import settings
from app.core.redis_client import get_cache, set_cache

logger = logging.getLogger(__name__)


class AIService:
    """Service for generating AI-powered recommendations."""

    def __init__(self):
        """Initialize AI service."""
        self.model = None
        if genai and settings.GEMINI_API_KEY:
            genai.configure(api_key=settings.GEMINI_API_KEY)
            self.model = genai.GenerativeModel(settings.GEMINI_MODEL)
            self.generation_config = genai.types.GenerationConfig(
                temperature=settings.GEMINI_TEMPERATURE,
                max_output_tokens=settings.GEMINI_MAX_TOKENS,
                top_p=0.9,
                top_k=40,
            )

    async def generate_recommendation(
        self,
        github_data: Dict[str, Any],
        recommendation_type: str = "professional",
        tone: str = "professional",
        length: str = "medium",
        custom_prompt: Optional[str] = None,
        target_role: Optional[str] = None,
        specific_skills: Optional[list] = None,
    ) -> Dict[str, Any]:
        """Generate a LinkedIn recommendation using AI."""

        if not self.model:
            raise ValueError("Gemini AI not configured")

        try:
            if settings.ENVIRONMENT == "development":
                logger.info("🧠 AI SERVICE: Building initial prompt...")

            # Build the initial prompt
            initial_prompt = self._build_prompt(
                github_data=github_data,
                recommendation_type=recommendation_type,
                tone=tone,
                length=length,
                custom_prompt=custom_prompt,
                target_role=target_role,
                specific_skills=specific_skills,
            )

            if settings.ENVIRONMENT == "development":
                logger.info(f"✅ Prompt built with {len(initial_prompt)} characters")

            # Check cache for final result
            cache_key = f"ai_recommendation_v3:{hash(initial_prompt)}"

            cached_result = await get_cache(cache_key)
            if cached_result:
                logger.info("Cache hit for AI recommendation")
                return cached_result

            if settings.ENVIRONMENT == "development":
                logger.info("🚀 CACHE MISS: Starting multi-option generation...")

            # Generate 3 different recommendation options
            options = await self._generate_multiple_options(
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
                "generation_prompt": (
                    initial_prompt[:500] + "..."
                    if len(initial_prompt) > 500
                    else initial_prompt
                ),
            }

            # Cache for 24 hours
            await set_cache(cache_key, result, ttl=86400)

            return result

        except Exception as e:
            logger.error(f"Error generating AI recommendation: {e}")
            raise

    def _build_prompt(
        self,
        github_data: Dict[str, Any],
        recommendation_type: str,
        tone: str,
        length: str,
        custom_prompt: Optional[str] = None,
        target_role: Optional[str] = None,
        specific_skills: Optional[list] = None,
    ) -> str:
        """Build the AI generation prompt."""

        user_data = github_data["user_data"]
        repositories = github_data["repositories"]
        languages = github_data["languages"]
        skills = github_data["skills"]
        commit_analysis = github_data.get("commit_analysis", {})

        # Base prompt structure
        prompt_parts = [
            f"Write a {length} LinkedIn recommendation for {user_data['github_username']}.",
            f"Make it {tone} and suitable for {recommendation_type} purposes.",
        ]

        if target_role:
            prompt_parts.append(
                f"Highlight why they'd be great for a {target_role} position."
            )

        # Add GitHub context based on analysis type
        if github_data.get("repository_info"):
            # Repository-specific context
            repo_info = github_data["repository_info"]
            prompt_parts.extend(
                [
                    "\nHere's what I know about their work:",
                    f"- Project: {repo_info.get('name', 'Not provided')}",
                    f"- What it's about: {repo_info.get('description', 'Not provided')}",
                    f"- Main programming language: {repo_info.get('language', 'Not provided')}",
                ]
            )
        else:
            # Profile context
            prompt_parts.extend(
                [
                    "\nHere's what I know about them:",
                    f"- Name: {user_data.get('full_name', 'Not provided')}",
                    f"- Bio: {user_data.get('bio', 'Not provided')}",
                ]
            )

        # Add technical skills based on data source
        if github_data.get("repository_info"):
            # Repository-specific skills
            repo_languages = github_data.get("languages", [])
            repo_skills = github_data.get("skills", {})

            if repo_languages:
                top_languages = [lang["language"] for lang in repo_languages[:5]]
                prompt_parts.append(
                    f"- Programming languages they work with: {', '.join(top_languages)}"
                )

            if repo_skills.get("technical_skills"):
                prompt_parts.append(
                    f"- Technical skills: {', '.join(repo_skills['technical_skills'][:10])}"
                )

            if repo_skills.get("frameworks"):
                prompt_parts.append(
                    f"- Frameworks and tools: {', '.join(repo_skills['frameworks'])}"
                )

            if repo_skills.get("domains"):
                prompt_parts.append(
                    f"- Areas they specialize in: {', '.join(repo_skills['domains'])}"
                )
        else:
            # Profile-based skills
            if languages:
                top_languages = [lang["language"] for lang in languages[:5]]
                prompt_parts.append(
                    f"- Programming languages they work with: {', '.join(top_languages)}"
                )

            if skills["technical_skills"]:
                prompt_parts.append(
                    f"- Technical skills: {', '.join(skills['technical_skills'][:10])}"
                )

            if skills["frameworks"]:
                prompt_parts.append(
                    f"- Frameworks and tools: {', '.join(skills['frameworks'])}"
                )

            if skills["domains"]:
                prompt_parts.append(
                    f"- Areas they specialize in: {', '.join(skills['domains'])}"
                )

        # Add commit analysis insights based on analysis type
        if commit_analysis and commit_analysis.get("total_commits_analyzed", 0) > 0:
            if github_data.get("repository_info"):
                # Repository-specific insights
                prompt_parts.append("\nWhat their coding work shows:")

                if commit_analysis.get("repository_focused"):
                    excellence_areas = commit_analysis.get("excellence_areas", {})
                    if excellence_areas.get("primary_strength"):
                        primary_strength = excellence_areas["primary_strength"]
                        prompt_parts.append(
                            f"- What they're really good at: {primary_strength}"
                        )

                    patterns = excellence_areas.get("patterns", {})
                    if patterns:
                        top_patterns = list(patterns.keys())[:2]
                        pattern_str = ", ".join(
                            [p.replace("_", " ").title() for p in top_patterns]
                        )
                        prompt_parts.append(
                            f"- How they approach development: {pattern_str}"
                        )

                    tech_contributions = commit_analysis.get(
                        "technical_contributions", {}
                    )
                    if tech_contributions:
                        top_contributions = list(tech_contributions.keys())[:2]
                        contrib_str = ", ".join(top_contributions)
                        prompt_parts.append(
                            f"- Technical areas they focus on: {contrib_str}"
                        )
            else:
                # Profile-based insights
                prompt_parts.append("\nWhat their overall coding work shows:")

                excellence_areas = commit_analysis.get("excellence_areas", {})
                if excellence_areas.get("primary_strength"):
                    primary_strength = (
                        excellence_areas["primary_strength"].replace("_", " ").title()
                    )
                    prompt_parts.append(
                        f"- What they're really good at: {primary_strength}"
                    )

                patterns = excellence_areas.get("patterns", {})
                if patterns:
                    top_patterns = list(patterns.keys())[:3]
                    pattern_str = ", ".join(
                        [p.replace("_", " ").title() for p in top_patterns]
                    )
                    prompt_parts.append(
                        f"- How they approach development: {pattern_str}"
                    )

                tech_contributions = commit_analysis.get("technical_contributions", {})
                if tech_contributions:
                    top_contributions = sorted(
                        tech_contributions.items(), key=lambda x: x[1], reverse=True
                    )[:2]
                    contrib_str = ", ".join(
                        [
                            contrib[0].replace("_", " ").title()
                            for contrib in top_contributions
                        ]
                    )
                    prompt_parts.append(
                        f"- Technical areas they focus on: {contrib_str}"
                    )

        # Add specific skills if requested
        if specific_skills:
            prompt_parts.append(
                f"\nMake sure to highlight these skills: {', '.join(specific_skills)}"
            )

        # Add custom prompt if provided
        if custom_prompt:
            prompt_parts.append(f"\nAdditional information to include: {custom_prompt}")

        # Add guidelines based on length
        base_guidelines = [
            "\nGuidelines:",
            "- Write in first person as someone who has worked with this developer",
            "- Be specific about technical achievements and skills",
            "- Use natural, conversational language like you're talking to a colleague",
            "- Focus on both technical competence and collaborative abilities",
            "- DO NOT mention any company names, employers, or employment history",
            "- Focus on technical skills and collaborative abilities only",
            f"- Target length: {self._get_length_guideline(length)} words",
            "- Do not include any placeholders or template text",
            "- Make it sound natural and personal, like a real recommendation",
        ]

        # Add paragraph structure guidelines based on length
        if length == "short":
            base_guidelines.extend(
                [
                    "- Structure as 2 paragraphs: introduction with key skills, then specific example",
                    "- Keep it concise but impactful",
                    "- Focus on 1-2 key strengths",
                ]
            )
        elif length == "medium":
            base_guidelines.extend(
                [
                    "- Structure as 3 paragraphs: introduction, technical skills with examples, personal qualities",
                    "- Provide 2-3 specific examples or achievements",
                    "- Balance technical expertise with personal qualities",
                ]
            )
        else:  # long
            base_guidelines.extend(
                [
                    "- Structure as 4-5 paragraphs: introduction, technical background, specific achievements, collaboration skills, conclusion",
                    "- Include 3-4 detailed examples",
                    "- Show development journey and growth",
                ]
            )

        if github_data.get("repository_info"):
            # Repository-specific guidelines
            repo_info = github_data["repository_info"]
            repo_name = repo_info.get("name", "the repository")
            base_guidelines.insert(
                3, f"- Focus on skills and technologies they showed in {repo_name}"
            )
            base_guidelines.insert(
                4, "- Mention the project when it helps explain their contributions"
            )

        prompt_parts.extend(base_guidelines)

        return "\n".join(prompt_parts)

    def _get_length_guideline(self, length: str) -> str:
        """Get word count guideline for different lengths."""
        length_map = {"short": "100-150", "medium": "150-200", "long": "200-300"}
        return length_map.get(length, "150-200")

    def _extract_title(self, content: str, username: str) -> str:
        """Extract or generate a title for the recommendation."""
        # Simple title extraction - could be enhanced
        if content:
            first_sentence = content.split(".")[0]
            if len(first_sentence) < 100:
                return first_sentence.strip()

        return f"Professional Recommendation for {username}"

    def _calculate_confidence_score(
        self, github_data: Dict[str, Any], generated_content: str
    ) -> int:
        """Calculate dynamic confidence score based on data quality and content."""
        score: float = 0.0
        max_score = 100

        # Data completeness score (40 points max)
        data_score = self._score_data_completeness(github_data)
        score += data_score * 0.4

        # Content quality score (30 points max)
        content_score = self._score_content_quality(generated_content)
        score += content_score * 0.3

        # Commit analysis availability (20 points max)
        commit_analysis = github_data.get("commit_analysis", {})
        if commit_analysis.get("total_commits_analyzed", 0) > 0:
            commit_score = min(
                commit_analysis["total_commits_analyzed"] / 150 * 100, 100
            )
            score += commit_score * 0.2

        # Multi-stage refinement bonus (10 points max)
        score += 10  # Always add this since we're using multi-stage

        return min(int(score), max_score)

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
            option_prompt = self._build_option_prompt(
                initial_prompt, str(config["custom_instruction"]), str(config["focus"])
            )

            # Generate the option
            temp_modifier = config.get("temperature_modifier", 0.7)
            temp_modifier = (
                float(temp_modifier)
                if isinstance(temp_modifier, (int, float, str))
                else 0.7
            )

            option_content = await self._generate_single_option(
                option_prompt, temp_modifier
            )

            option_end = time.time()

            # Create option object
            option = {
                "id": i,
                "name": config["name"],
                "content": option_content.strip(),
                "title": self._extract_title(option_content, base_username),
                "word_count": len(option_content.split()),
                "focus": config["focus"],
                "confidence_score": self._calculate_confidence_score(
                    github_data, option_content
                ),
            }

            options.append(option)

            logger.info(
                f"⏱️  {config['name']} completed in {option_end - option_start:.2f} seconds"
            )
            logger.info(
                f"✅ Generated {option['word_count']} words, confidence: {option['confidence_score']}"
            )
            logger.info(f"   • Preview: {option_content[:100]}...")

        pipeline_end = time.time()
        total_pipeline_time = pipeline_end - pipeline_start

        logger.info("🎉 MULTIPLE OPTIONS GENERATION COMPLETED")
        logger.info("-" * 40)
        logger.info(f"⏱️  Total time: {total_pipeline_time:.2f} seconds")
        logger.info(f"📊 Generated {len(options)} options")
        logger.info("=" * 60)

        return options

    def _build_option_prompt(
        self, base_prompt: str, custom_instruction: str, focus: str
    ) -> str:
        """Build a customized prompt for a specific option."""
        return f"""{base_prompt}

FOR THIS VERSION, FOCUS ON:
{custom_instruction}

Create a recommendation that really highlights their {focus.replace('_', ' ')} skills while keeping it natural and conversational.
"""

    async def _generate_single_option(
        self, prompt: str, temperature_modifier: float
    ) -> str:
        """Generate a single recommendation option."""
        # Adjust temperature for variety
        config = genai.types.GenerationConfig(
            temperature=min(settings.GEMINI_TEMPERATURE + temperature_modifier, 2.0),
            max_output_tokens=settings.GEMINI_MAX_TOKENS,
            top_p=0.9,
            top_k=40,
        )
        response = self.model.generate_content(prompt, generation_config=config)
        return response.text

    async def regenerate_recommendation(
        self,
        original_content: str,
        refinement_instructions: str,
        github_data: Dict[str, Any],
        recommendation_type: str = "professional",
        tone: str = "professional",
        length: str = "medium",
    ) -> Dict[str, Any]:
        """Regenerate a recommendation with refinement instructions."""

        if not self.model:
            raise ValueError("Gemini AI not configured")

        try:
            logger.info("🔄 REGENERATING RECOMMENDATION")
            logger.info("=" * 60)

            # Build refinement prompt
            refinement_prompt = self._build_refinement_prompt_for_regeneration(
                original_content=original_content,
                refinement_instructions=refinement_instructions,
                github_data=github_data,
                recommendation_type=recommendation_type,
                tone=tone,
                length=length,
            )

            # Generate refined recommendation
            refined_content = await self._generate_refined_regeneration(
                refinement_prompt
            )

            # Return refined result
            result = {
                "content": refined_content.strip(),
                "title": self._extract_title(
                    refined_content, github_data["user_data"]["github_username"]
                ),
                "word_count": len(refined_content.split()),
                "confidence_score": self._calculate_confidence_score(
                    github_data, refined_content
                ),
                "generation_parameters": {
                    "model": settings.GEMINI_MODEL,
                    "temperature": settings.GEMINI_TEMPERATURE,
                    "max_tokens": settings.GEMINI_MAX_TOKENS,
                    "recommendation_type": recommendation_type,
                    "tone": tone,
                    "length": length,
                    "regeneration": True,
                },
            }

            logger.info("✅ RECOMMENDATION REGENERATED SUCCESSFULLY")
            logger.info("=" * 60)

            return result

        except Exception as e:
            logger.error(f"Error regenerating recommendation: {e}")
            raise

    def _build_refinement_prompt_for_regeneration(
        self,
        original_content: str,
        refinement_instructions: str,
        github_data: Dict[str, Any],
        recommendation_type: str,
        tone: str,
        length: str,
    ) -> str:
        """Build prompt for regenerating a recommendation."""
        username = github_data["user_data"]["github_username"]
        target_length = self._get_length_guideline(length)

        return f"""
I have this LinkedIn recommendation that needs some changes:

ORIGINAL RECOMMENDATION:
{original_content}

WHAT TO CHANGE:
{refinement_instructions}

DETAILS:
- Person: {username}
- Type: {recommendation_type}
- Tone: {tone}
- Target Length: {target_length} words

Please rewrite the recommendation with these changes while keeping it:
1. Authentic and real-sounding
2. The right tone and length
3. Focused on their technical and teamwork skills
4. Natural and conversational

Just give me the updated recommendation text, nothing else.
"""

    async def _generate_refined_regeneration(self, prompt: str) -> str:
        """Generate refined recommendation for regeneration."""
        config = genai.types.GenerationConfig(
            temperature=settings.GEMINI_TEMPERATURE
            + 0.1,  # Slightly higher for refinement
            max_output_tokens=settings.GEMINI_MAX_TOKENS,
            top_p=0.9,
            top_k=40,
        )
        response = self.model.generate_content(prompt, generation_config=config)
        return response.text

    def _score_data_completeness(self, github_data: Dict[str, Any]) -> int:
        """Score the completeness of GitHub data (0-100)."""
        score = 0
        user_data = github_data.get("user_data", {})

        # Basic profile completeness
        if user_data.get("bio"):
            score += 15
        if user_data.get("public_repos", 0) > 0:
            score += 20
        if user_data.get("followers", 0) > 0:
            score += 10

        # Repository data
        repositories = github_data.get("repositories", [])
        if repositories:
            score += 20
        if len(repositories) >= 5:
            score += 10

        # Language diversity
        languages = github_data.get("languages", [])
        if len(languages) >= 3:
            score += 15

        # Skills analysis
        skills = github_data.get("skills", {})
        if skills.get("technical_skills"):
            score += 10

        return min(score, 100)

    def _score_content_quality(self, content: str) -> int:
        """Score the quality of generated content (0-100)."""
        score = 0
        word_count = len(content.split())

        # Length appropriateness
        if 100 <= word_count <= 400:
            score += 30
        elif 50 <= word_count <= 500:
            score += 20
        else:
            score += 10

        # Content structure indicators
        sentences = content.split(".")
        if len(sentences) >= 3:
            score += 20  # Has multiple sentences

        # Professional language indicators
        professional_words = [
            "technical",
            "skilled",
            "expertise",
            "development",
            "project",
            "team",
        ]
        if any(word in content.lower() for word in professional_words):
            score += 25

        # Specificity indicators
        specific_indicators = ["github", "repository", "commit", "code", "programming"]
        if any(indicator in content.lower() for indicator in specific_indicators):
            score += 25

        return min(score, 100)
