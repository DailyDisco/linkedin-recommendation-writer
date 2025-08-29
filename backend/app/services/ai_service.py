"""AI service for generating recommendations using Google Gemini."""

import logging
from typing import Any, Dict, List, Optional, TypedDict

from app.core.config import settings
from app.core.redis_client import get_cache, set_cache

# Handle optional Google Generative AI import
try:
    import google.generativeai as genai

    genai_available = True
except ImportError:
    genai = None  # type: ignore
    genai_available = False

logger = logging.getLogger(__name__)


class RecommendationValidationResult(TypedDict):
    is_valid: bool
    issues: List[str]
    suggestions: List[str]
    structure_score: int


class AIService:
    """Service for generating AI-powered recommendations."""

    def __init__(self) -> None:
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
        exclude_keywords: Optional[list] = None,
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
        """Build the AI generation prompt."""

        user_data = github_data["user_data"]
        # repositories = ...  # Removed unused variable
        languages = github_data["languages"]
        skills = github_data["skills"]
        commit_analysis = github_data.get("commit_analysis", {})

        # Base prompt structure
        prompt_parts = [
            f"Write a {length} LinkedIn recommendation for {user_data['github_username']}.",
            f"Make it {tone} and suitable for {recommendation_type} purposes.",
        ]

        if target_role:
            prompt_parts.append(f"Highlight why they'd be great for a {target_role} position.")

        # Add GitHub context based on standardized analysis type
        analysis_context_type = github_data.get("analysis_context_type", "profile")

        if analysis_context_type == "repository":
            # Repository-specific context
            repo_info = github_data["repository_info"]
            prompt_parts.extend(
                [
                    "\nHere's what I know about this repository:",
                    f"- Project: {repo_info.get('name', 'Not provided')}",
                    f"- What it's about: {repo_info.get('description', 'Not provided')}",
                    f"- Main programming language: {repo_info.get('language', 'Not provided')}",
                ]
            )
        elif analysis_context_type == "repository_contributor":
            # Repository-contributor merged context
            repo_info = github_data["repository_info"]
            prompt_parts.extend(
                [
                    "\nHere's what I know about their work on this project:",
                    f"- Project: {repo_info.get('name', 'Not provided')}",
                    f"- What it's about: {repo_info.get('description', 'Not provided')}",
                    f"- Main programming language: {repo_info.get('language', 'Not provided')}",
                ]
            )
        else:
            # Profile context (default)
            prompt_parts.append("\nHere's what I know about them:")
            if user_data.get("full_name"):
                prompt_parts.append(f"- Name: {user_data['full_name']}")

            # Add starred repositories insights (shows interests and learning focus)
            starred_tech = user_data.get("starred_technologies", {})
            if starred_tech and starred_tech.get("total_starred", 0) > 0:
                prompt_parts.append("\nWhat they've shown interest in:")
                top_languages = list(starred_tech.get("languages", {}).keys())[:3]
                if top_languages:
                    prompt_parts.append(f"- Technologies they follow: {', '.join(top_languages)}")

                tech_focus = list(starred_tech.get("technology_focus", {}).keys())[:2]
                if tech_focus:
                    prompt_parts.append(f"- Areas they seem interested in: {', '.join(tech_focus)}")

                interest_score = starred_tech.get("interest_score", 0)
                if interest_score > 70:
                    prompt_parts.append("- Shows strong curiosity and keeps up with technology trends")

            # Add organizations (shows professional network and community involvement)
            organizations = user_data.get("organizations", [])
            if organizations:
                org_names = [org.get("name") or org.get("login") for org in organizations[:3]]
                if org_names:
                    prompt_parts.append(f"- Active in organizations: {', '.join(org_names)}")
                    prompt_parts.append("- Demonstrates community involvement and collaboration skills")

        # Add technical skills based on standardized analysis context
        if analysis_context_type in ["repository", "repository_contributor"]:
            # Repository-specific skills
            repo_languages = github_data.get("languages", [])
            repo_skills = github_data.get("skills", {})

            if repo_languages:
                top_languages = [lang["language"] for lang in repo_languages[:5]]
                prompt_parts.append(f"- Programming languages they work with: {', '.join(top_languages)}")

            if repo_skills.get("technical_skills"):
                prompt_parts.append(f"- Technical skills: {', '.join(repo_skills['technical_skills'][:10])}")

            if repo_skills.get("frameworks"):
                prompt_parts.append(f"- Frameworks and tools: {', '.join(repo_skills['frameworks'])}")

            if repo_skills.get("domains"):
                prompt_parts.append(f"- Areas they specialize in: {', '.join(repo_skills['domains'])}")
        else:
            # Profile-based skills
            if languages:
                top_languages = [lang["language"] for lang in languages[:5]]
                prompt_parts.append(f"- Programming languages they work with: {', '.join(top_languages)}")

            if skills["technical_skills"]:
                prompt_parts.append(f"- Technical skills: {', '.join(skills['technical_skills'][:10])}")

            if skills["frameworks"]:
                prompt_parts.append(f"- Frameworks and tools: {', '.join(skills['frameworks'])}")

            if skills["domains"]:
                prompt_parts.append(f"- Areas they specialize in: {', '.join(skills['domains'])}")

        # Add commit analysis insights with specific examples
        if commit_analysis and commit_analysis.get("total_commits_analyzed", 0) > 0:
            if analysis_context_type == "repository":
                # Repository-specific insights
                prompt_parts.append("\nWhat the repository's commit history shows:")
            elif analysis_context_type == "repository_contributor":
                # Repository-contributor insights
                prompt_parts.append("\nWhat their contributions to this project show:")
            else:
                # Profile-based insights
                prompt_parts.append("\nWhat their overall coding work shows:")

            # Inject specific commit examples for evidence-based writing
            if analysis_context_type != "repository":  # Don't inject examples for pure repository analysis
                specific_examples = self._extract_commit_examples(commit_analysis)
                if specific_examples:
                    prompt_parts.append("\nSpecific examples of their work:")
                    for example in specific_examples[:3]:  # Limit to 3 examples
                        prompt_parts.append(f"- {example}")

            excellence_areas = commit_analysis.get("excellence_areas", {})
            if excellence_areas.get("primary_strength"):
                primary_strength = excellence_areas["primary_strength"].replace("_", " ").title()
                prompt_parts.append(f"- Primary strength: {primary_strength}")

            # Add conventional commit insights
            conventional_analysis = commit_analysis.get("conventional_commit_analysis", {})
            if conventional_analysis and conventional_analysis.get("quality_score", 0) > 60:
                prompt_parts.append("- Uses professional commit message standards (conventional commits)")
                prompt_parts.append("- Demonstrates attention to code quality and documentation")

            patterns = excellence_areas.get("patterns", {})
            if patterns:
                top_patterns = list(patterns.keys())[:2]
                pattern_str = ", ".join([p.replace("_", " ").title() for p in top_patterns])
                prompt_parts.append(f"- How they approach development: {pattern_str}")

            tech_contributions = commit_analysis.get("technical_contributions", {})
            if tech_contributions:
                top_contributions = sorted(
                    tech_contributions.items(),
                    key=lambda x: x[1],
                    reverse=True,
                )[:2]
                contrib_str = ", ".join([contrib[0].replace("_", " ").title() for contrib in top_contributions])
                prompt_parts.append(f"- Technical areas they focus on: {contrib_str}")
        else:
            # Profile-based insights
            prompt_parts.append("\nWhat their overall coding work shows:")

            excellence_areas = commit_analysis.get("excellence_areas", {})
            if excellence_areas.get("primary_strength"):
                primary_strength = excellence_areas["primary_strength"].replace("_", " ").title()
                prompt_parts.append(f"- What they're really good at: {primary_strength}")

            patterns = excellence_areas.get("patterns", {})
            if patterns:
                top_patterns = list(patterns.keys())[:3]
                pattern_str = ", ".join([p.replace("_", " ").title() for p in top_patterns])
                prompt_parts.append(f"- How they approach development: {pattern_str}")

            tech_contributions = commit_analysis.get("technical_contributions", {})
            if tech_contributions:
                top_contributions = sorted(
                    tech_contributions.items(),
                    key=lambda x: x[1],
                    reverse=True,
                )[:2]
                contrib_str = ", ".join([contrib[0].replace("_", " ").title() for contrib in top_contributions])
                prompt_parts.append(f"- Technical areas they focus on: {contrib_str}")

        # Add specific skills if requested
        if specific_skills:
            prompt_parts.append(f"\nMake sure to highlight these skills: {', '.join(specific_skills)}")

        # Add keywords to exclude if provided
        if exclude_keywords:
            prompt_parts.append(f"\nIMPORTANT: Do NOT mention any of these terms or concepts: {', '.join(exclude_keywords)}")
            prompt_parts.append("- If any of these terms would naturally appear, rephrase to avoid them entirely")

        # Add custom prompt if provided
        if custom_prompt:
            prompt_parts.append(f"\nAdditional information to include: {custom_prompt}")

        # Add guidelines based on length
        base_guidelines = [
            "\nGuidelines:",
            "- Write in first person as someone who has worked with this developer",
            "- Be specific about technical achievements and skills",
            "- Use natural, conversational language, like you're talking to a colleague.",
            "- Focus on both technical competence and collaborative abilities, providing specific examples and positive anecdotes from their work.",
            "- DO NOT mention any company names, employers, or employment history",
            "- Focus on technical skills and collaborative abilities only",
            "- Separate the recommendation into clear, distinct paragraphs to improve readability.",
            f"- Target length: {self._get_length_guideline(length)} words",
            "- Do not include any placeholders or template text",
            "- Make it sound natural and personal, like a real recommendation",
        ]

        # Add paragraph structure guidelines based on length
        if length == "short":
            base_guidelines.extend(
                [
                    "- Structure as 2 paragraphs: introduction with key skills and a specific example,",
                    " then a concluding positive anecdote.",
                    "- Keep it concise but impactful",
                    "- Focus on 1-2 key strengths with concrete evidence",
                ]
            )
        elif length == "medium":
            base_guidelines.extend(
                [
                    "- Structure as 3 paragraphs: introduction, 2-3 specific technical achievements with examples,",
                    " and a concluding paragraph on personal qualities/collaboration with an anecdote.",
                    "- Provide 2-3 specific examples or achievements",
                    "- Balance technical expertise with personal qualities",
                ]
            )
        else:  # long
            base_guidelines.extend(
                [
                    "- Structure as 4-5 paragraphs: introduction, detailed technical background with 2-3 achievements,",
                    " specific project contributions/problem-solving, collaboration skills with an anecdote,",
                    " and a strong conclusion.",
                    "- Include 3-4 detailed examples",
                    "- Show development journey and growth",
                ]
            )

        if analysis_context_type in ["repository", "repository_contributor"]:
            # Repository-specific guidelines
            repo_info = github_data["repository_info"]
            repo_name = repo_info.get("name", "the repository")
            if analysis_context_type == "repository":
                base_guidelines.insert(
                    3,
                    f"- Focus on the skills and technologies demonstrated in {repo_name}",
                )
                base_guidelines.insert(
                    4,
                    "- Highlight the project's technical achievements and impact",
                )
            else:  # repository_contributor
                base_guidelines.insert(
                    3,
                    f"- Focus on skills and technologies they showed in {repo_name}",
                )
                base_guidelines.insert(
                    4,
                    "- Mention the project when it helps explain their contributions",
                )

        prompt_parts.extend(base_guidelines)

        return "\n".join(prompt_parts)

    def _get_length_guideline(self, length: str) -> str:
        """Get word count guideline for different lengths."""
        length_map = {
            "short": "100-150",
            "medium": "150-200",
            "long": "200-300",
        }
        return length_map.get(length, "150-200")

    def _extract_title(self, content: str, username: str) -> str:
        """Extract or generate a title for the recommendation."""
        # Simple title extraction - could be enhanced
        if content:
            first_sentence = content.split(".")[0]
            if len(first_sentence) < 100:
                return first_sentence.strip()

        return f"Professional Recommendation for {username}"

    def _calculate_confidence_score(self, github_data: Dict[str, Any], generated_content: str, prompt: Optional[str] = None, generation_params: Optional[Dict[str, Any]] = None) -> int:
        """Calculate dynamic confidence score based on multiple quality factors."""
        score: float = 0.0
        max_score = 100

        # Data completeness score (25 points max)
        data_score = self._score_data_completeness(github_data)
        score += data_score * 0.25

        # Content quality score (20 points max)
        content_score = self._score_content_quality(generated_content)
        score += content_score * 0.2

        # Prompt alignment score (20 points max) - NEW
        if prompt:
            alignment_score = self._score_prompt_alignment(prompt, generated_content, generation_params or {})
            score += alignment_score * 0.2

        # Readability & tone check (15 points max) - NEW
        readability_score = self._score_readability_and_tone(generated_content, generation_params or {})
        score += readability_score * 0.15

        # Uniqueness & specificity score (10 points max) - NEW
        uniqueness_score = self._score_uniqueness_and_specificity(generated_content, github_data)
        score += uniqueness_score * 0.1

        # Commit analysis availability (5 points max)
        commit_analysis = github_data.get("commit_analysis", {})
        if commit_analysis.get("total_commits_analyzed", 0) > 0:
            commit_score = min(commit_analysis["total_commits_analyzed"] / 150 * 100, 100)
            score += commit_score * 0.05

        # Conventional commit quality bonus (5 points max) - NEW
        conventional_analysis = commit_analysis.get("conventional_commit_analysis", {})
        if conventional_analysis.get("quality_score", 0) > 0:
            conv_bonus = min(conventional_analysis["quality_score"] / 20, 5)  # Scale to 5 points max
            score += conv_bonus

        return min(int(score), max_score)

    def _score_prompt_alignment(self, prompt: str, generated_content: str, generation_params: Dict[str, Any]) -> float:
        """Score how well the generated content aligns with the prompt requirements."""
        score: float = 0.0
        content_lower = generated_content.lower()

        # Extract key requirements from prompt
        key_requirements = []

        # Check for username presence
        if "github_username" in generation_params:
            username = generation_params["github_username"].lower()
            if username in content_lower:
                key_requirements.append("username_present")
                score += 20

        # Check for recommendation type alignment
        rec_type = generation_params.get("recommendation_type", "professional")
        if rec_type == "professional":
            # Should contain professional language
            prof_indicators = ["professional", "excellent", "skilled", "expertise", "recommend"]
            prof_matches = sum(1 for indicator in prof_indicators if indicator in content_lower)
            if prof_matches >= 2:
                key_requirements.append("professional_tone")
                score += 15

        # Check for tone alignment
        tone = generation_params.get("tone", "professional")
        if tone == "professional" and "would recommend" in content_lower:
            key_requirements.append("tone_alignment")
            score += 15

        # Check for length appropriateness
        length = generation_params.get("length", "medium")
        word_count = len(generated_content.split())
        length_ranges = {"short": (100, 150), "medium": (150, 200), "long": (200, 300)}

        if length in length_ranges:
            min_words, max_words = length_ranges[length]
            if min_words <= word_count <= max_words:
                key_requirements.append("length_appropriate")
                score += 15

        # Check for specific skills mention if provided
        specific_skills = generation_params.get("specific_skills", [])
        if specific_skills:
            skills_mentioned = sum(1 for skill in specific_skills if skill.lower() in content_lower)
            if skills_mentioned > 0:
                key_requirements.append("specific_skills_mentioned")
                skill_score = min((skills_mentioned / len(specific_skills)) * 20, 20)
                score += skill_score

        # Check for excluded keywords (negative scoring)
        exclude_keywords = generation_params.get("exclude_keywords", [])
        if exclude_keywords:
            excluded_found = sum(1 for keyword in exclude_keywords if keyword.lower() in content_lower)
            if excluded_found == 0:
                key_requirements.append("exclusions_respected")
                score += 15
            else:
                # Penalty for including excluded terms
                score -= excluded_found * 10

        return max(0, min(score, 100))  # Ensure score is between 0-100

    def _score_readability_and_tone(self, content: str, generation_params: Dict[str, Any]) -> int:
        """Score readability and tone appropriateness."""
        score = 0

        # Basic readability metrics
        sentences = [s.strip() for s in content.split(".") if s.strip()]
        words = content.split()
        word_count = len(words)

        # Sentence length analysis (ideal: 15-25 words per sentence)
        if sentences:
            avg_sentence_length = word_count / len(sentences)
            if 15 <= avg_sentence_length <= 25:
                score += 25  # Optimal sentence length
            elif 10 <= avg_sentence_length <= 30:
                score += 15  # Acceptable range
            else:
                score += 5  # Too short or long

        # Paragraph structure (should have multiple paragraphs)
        paragraphs = [p.strip() for p in content.split("\n\n") if p.strip()]
        if len(paragraphs) >= 3:
            score += 20  # Good paragraph structure
        elif len(paragraphs) >= 2:
            score += 10  # Acceptable structure
        else:
            score += 5  # Could be improved

        # Tone analysis
        tone = generation_params.get("tone", "professional")
        content_lower = content.lower()

        if tone == "professional":
            # Check for professional indicators
            prof_words = ["professional", "excellent", "skilled", "team", "recommend", "experience"]
            prof_count = sum(1 for word in prof_words if word in content_lower)
            if prof_count >= 3:
                score += 25
            elif prof_count >= 1:
                score += 15

            # Check for unprofessional language (negative indicators)
            informal_words = ["awesome", "amazing", "super", "totally", "really", "just"]
            informal_count = sum(1 for word in informal_words if word in content_lower)
            if informal_count == 0:
                score += 15  # No informal language
            else:
                score -= informal_count * 5  # Penalty for informal language

        # Natural language flow (check for repeated words)
        unique_words = set(words)
        repetition_ratio = len(unique_words) / max(len(words), 1)
        if repetition_ratio > 0.7:
            score += 15  # Good vocabulary diversity
        elif repetition_ratio > 0.5:
            score += 10  # Acceptable diversity

        return max(0, min(score, 100))

    def _score_uniqueness_and_specificity(self, content: str, github_data: Dict[str, Any]) -> int:
        """Score how unique and specific the content is."""
        score = 0
        content_lower = content.lower()

        # Generic phrase penalty (negative scoring)
        generic_phrases = [
            "i had the pleasure",
            "it is my pleasure",
            "i am pleased to recommend",
            "i highly recommend",
            "excellent professional",
            "great team player",
            "hard working",
            "dedicated professional",
            "valuable asset",
            "strong technical skills",
        ]

        generic_matches = sum(1 for phrase in generic_phrases if phrase in content_lower)
        if generic_matches == 0:
            score += 30  # No generic phrases - very good
        elif generic_matches <= 2:
            score += 20  # Few generic phrases
        elif generic_matches <= 4:
            score += 10  # Some generic phrases
        else:
            score += 5  # Many generic phrases

        # GitHub-specific references (positive scoring)
        github_specific_score = 0

        # Check for repository references
        repositories = github_data.get("repositories", [])
        repo_names = [repo.get("name", "").lower() for repo in repositories[:5]]  # Top 5 repos
        repo_mentions = sum(1 for repo_name in repo_names if repo_name in content_lower)
        if repo_mentions > 0:
            github_specific_score += min(repo_mentions * 10, 20)

        # Check for language references
        languages = github_data.get("languages", [])
        language_names = [lang.get("language", "").lower() for lang in languages[:5]]
        lang_mentions = sum(1 for lang in language_names if lang in content_lower)
        if lang_mentions > 0:
            github_specific_score += min(lang_mentions * 8, 15)

        # Check for technology/framework references
        skills = github_data.get("skills", {})
        technical_skills = skills.get("technical_skills", [])
        frameworks = skills.get("frameworks", [])

        tech_mentions = 0
        for tech in technical_skills[:10]:  # Top 10 skills
            if tech.lower() in content_lower:
                tech_mentions += 1

        for framework in frameworks[:5]:  # Top 5 frameworks
            if framework.lower() in content_lower:
                tech_mentions += 2  # Frameworks are more specific

        if tech_mentions > 0:
            github_specific_score += min(tech_mentions * 5, 25)

        # Bonus for conventional commit references
        commit_analysis = github_data.get("commit_analysis", {})
        conventional_analysis = commit_analysis.get("conventional_commit_analysis", {})
        if conventional_analysis.get("quality_score", 0) > 60:
            if "professional" in content_lower or "standards" in content_lower or "commit" in content_lower:
                github_specific_score += 10

        # Add GitHub-specific score
        score += min(github_specific_score, 40)

        return max(0, min(score, 100))

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

    def _validate_recommendation_structure(self, content: str, generation_params: Optional[Dict[str, Any]] = None) -> RecommendationValidationResult:
        """Validate the structure and quality of the formatted recommendation."""
        validation_results: RecommendationValidationResult = {"is_valid": True, "issues": [], "suggestions": [], "structure_score": 100}

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
            # Prepare generation parameters for confidence scoring
            generation_params = {
                "github_username": base_username,
                "recommendation_type": recommendation_type,
                "tone": tone,
                "length": length,
                "focus": config["focus"],
            }

            option = {
                "id": i,
                "name": config["name"],
                "content": option_content.strip(),
                "title": self._extract_title(option_content, base_username),
                "word_count": len(option_content.split()),
                "focus": config["focus"],
                "confidence_score": self._calculate_confidence_score(github_data, option_content, initial_prompt, generation_params),
            }

            options.append(option)

            logger.info(f"⏱️  {config['name']} completed in {option_end - option_start:.2f} seconds")
            logger.info(f"✅ Generated {option['word_count']} words, confidence: {option['confidence_score']}")
            logger.info(f"   • Preview: {option_content[:100]}...")

        pipeline_end = time.time()
        total_pipeline_time = pipeline_end - pipeline_start

        logger.info("🎉 MULTIPLE OPTIONS GENERATION COMPLETED")
        logger.info("-" * 40)
        logger.info(f"⏱️  Total time: {total_pipeline_time:.2f} seconds")
        logger.info(f"📊 Generated {len(options)} options")
        logger.info("=" * 60)

        return options

    def _extract_commit_examples(self, commit_analysis: Dict[str, Any]) -> List[str]:
        """Extract specific, concrete examples from commit analysis for evidence-based writing."""
        examples = []

        # Get high-impact commits
        impact_analysis = commit_analysis.get("impact_analysis", {})
        high_impact_commits = impact_analysis.get("high_impact_commits", [])

        for commit_data in high_impact_commits[:3]:  # Limit to top 3
            commit = commit_data.get("commit", {})
            impact_data = commit_data.get("impact_analysis", {})

            message = commit.get("message", "").strip()
            if not message:
                continue

            # Clean up the commit message for presentation
            # Remove conventional commit prefixes if present
            clean_message = message
            if ": " in message:
                parts = message.split(": ", 1)
                if len(parts) == 2 and len(parts[0]) <= 20:  # Likely a conventional commit
                    clean_message = parts[1]

            # Capitalize first letter
            if clean_message:
                clean_message = clean_message[0].upper() + clean_message[1:]

            # Add context about impact if available
            impact_level = impact_data.get("impact_level", "")
            conventional_info = impact_data.get("conventional_info", {})

            example = clean_message
            if conventional_info.get("is_conventional"):
                commit_type = conventional_info.get("type", "")
                if commit_type == "feat":
                    example = f"Implemented {clean_message.lower()}"
                elif commit_type == "fix":
                    example = f"Resolved {clean_message.lower()}"
                elif commit_type == "refactor":
                    example = f"Refactored {clean_message.lower()}"
                elif commit_type == "perf":
                    example = f"Optimized {clean_message.lower()}"

            # Add impact context
            if impact_level == "high":
                example += " (significant improvement)"
            elif impact_level == "moderate":
                example += " (notable enhancement)"

            examples.append(example)

        # If we don't have enough high-impact examples, add some from conventional commits
        if len(examples) < 3:
            conventional_commits = commit_analysis.get("conventional_commit_analysis", {}).get("conventional_commits", [])
            for conv_commit_data in conventional_commits[:3]:
                if len(examples) >= 3:
                    break

                commit = conv_commit_data.get("commit", {})
                message = commit.get("message", "").strip()

                # Skip if we already have this message
                if any(example.startswith(message[:30]) for example in examples):
                    continue

                clean_message = message
                if ": " in message:
                    parts = message.split(": ", 1)
                    if len(parts) == 2:
                        clean_message = parts[1]

                if clean_message:
                    clean_message = clean_message[0].upper() + clean_message[1:]
                    examples.append(clean_message)

        return examples

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

    def _build_option_prompt(self, base_prompt: str, custom_instruction: str, focus: str) -> str:
        """Build a customized prompt for a specific option."""
        focus_formatted = focus.replace("_", " ")
        return f"""{base_prompt}

FOR THIS VERSION, FOCUS ON:
{custom_instruction}

Create a recommendation that really highlights their {focus_formatted} skills while keeping it natural and conversational.
"""

    async def _generate_single_option(self, prompt: str, temperature_modifier: float, length: str = "medium", generation_params: Optional[Dict[str, Any]] = None) -> str:
        """Generate a single recommendation option with formatting."""
        if not self.model or not genai_available:
            raise ValueError("AI model not initialized")

        # Adjust temperature for variety
        config = genai.types.GenerationConfig(
            temperature=min(settings.GEMINI_TEMPERATURE + temperature_modifier, 2.0),
            max_output_tokens=settings.GEMINI_MAX_TOKENS,
            top_p=0.9,
            top_k=40,
        )
        response = self.model.generate_content(prompt, generation_config=config)

        # Get the raw content
        raw_content = str(response.text)

        # Apply formatting
        formatted_content = self._format_recommendation_output(raw_content, length, generation_params)

        # Validate the structure
        validation = self._validate_recommendation_structure(formatted_content, generation_params)

        if settings.ENVIRONMENT == "development" and not validation["is_valid"]:
            logger.warning(f"⚠️  Content validation issues: {validation['issues']}")
            if validation["suggestions"]:
                logger.info(f"💡 Suggestions: {validation['suggestions']}")

        return formatted_content

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
                "title": self._extract_title(
                    refined_content,
                    github_data["user_data"]["github_username"],
                ),
                "word_count": len(refined_content.split()),
                "confidence_score": self._calculate_confidence_score(github_data, refined_content, refinement_prompt, regeneration_params),
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
        exclude_keywords: Optional[list] = None,
    ) -> str:
        """Build prompt for regenerating a recommendation."""
        username = github_data["user_data"]["github_username"]
        target_length = self._get_length_guideline(length)

        exclude_section = ""
        if exclude_keywords:
            exclude_section = f"""
EXCLUDE THESE TERMS:
Do NOT mention any of these terms or concepts: {', '.join(exclude_keywords)}
If any of these terms would naturally appear, rephrase to avoid them entirely.
"""

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
- Target Length: {target_length} words{exclude_section}

Please rewrite the recommendation with these changes while keeping it:
1. Authentic and real-sounding
2. The right tone and length
3. Focused on their technical and teamwork skills
4. Natural and conversational

Just give me the updated recommendation text, nothing else.
"""

    async def _generate_refined_regeneration(self, prompt: str, length: str = "medium", generation_params: Optional[Dict[str, Any]] = None) -> str:
        """Generate refined recommendation for regeneration with formatting."""
        if not self.model or not genai_available:
            raise ValueError("AI model not initialized")

        config = genai.types.GenerationConfig(
            temperature=settings.GEMINI_TEMPERATURE + 0.1,  # Slightly higher for refinement
            max_output_tokens=settings.GEMINI_MAX_TOKENS,
            top_p=0.9,
            top_k=40,
        )
        response = self.model.generate_content(prompt, generation_config=config)

        # Get the raw content
        raw_content = str(response.text)

        # Apply formatting
        formatted_content = self._format_recommendation_output(raw_content, length, generation_params)

        # Validate the structure
        validation = self._validate_recommendation_structure(formatted_content, generation_params)

        if settings.ENVIRONMENT == "development" and not validation["is_valid"]:
            logger.warning(f"⚠️  Refined content validation issues: {validation['issues']}")
            if validation["suggestions"]:
                logger.info(f"💡 Suggestions: {validation['suggestions']}")

        return formatted_content

    def _build_keyword_refinement_prompt(
        self,
        original_content: str,
        include_keywords: Optional[List[str]] = None,
        exclude_keywords: Optional[List[str]] = None,
        refinement_instructions: Optional[str] = None,
        github_data: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Build a prompt for keyword-based refinement of recommendations."""
        prompt_parts = [
            "I need you to refine this LinkedIn recommendation while carefully managing specific keywords and phrases.",
            "",
            "ORIGINAL RECOMMENDATION:",
            original_content,
            "",
        ]

        if include_keywords:
            prompt_parts.extend(
                [
                    "MANDATORY INCLUSIONS - These keywords/phrases MUST be included in the refined recommendation:",
                    ", ".join(f'"{kw}"' for kw in include_keywords),
                    "",
                    "IMPORTANT: Ensure these terms are naturally integrated into the recommendation.",
                    "",
                ]
            )

        if exclude_keywords:
            prompt_parts.extend(
                [
                    "MANDATORY EXCLUSIONS - These keywords/phrases MUST NOT appear in the refined recommendation:",
                    ", ".join(f'"{kw}"' for kw in exclude_keywords),
                    "",
                    "IMPORTANT: Completely avoid these terms. If they appear in the original, rephrase to eliminate them.",
                    "",
                ]
            )

        if refinement_instructions:
            prompt_parts.extend(
                [
                    "ADDITIONAL REFINEMENT INSTRUCTIONS:",
                    refinement_instructions,
                    "",
                ]
            )

        # Add context about the person's background if available
        if github_data:
            context_parts = []
            user_data = github_data.get("user_data", {})

            if user_data.get("full_name"):
                context_parts.append(f"Person's name: {user_data['full_name']}")

            # Add technical context
            skills = github_data.get("skills", {})
            technical_skills = skills.get("technical_skills", [])[:5]  # Top 5 skills
            if technical_skills:
                context_parts.append(f"Key technical skills: {', '.join(technical_skills)}")

            frameworks = skills.get("frameworks", [])[:3]  # Top 3 frameworks
            if frameworks:
                context_parts.append(f"Frameworks/tools: {', '.join(frameworks)}")

            if context_parts:
                prompt_parts.extend(
                    [
                        "CONTEXT ABOUT THE PERSON:",
                        "\n".join(f"- {part}" for part in context_parts),
                        "",
                    ]
                )

        prompt_parts.extend(
            [
                "REFINEMENT REQUIREMENTS:",
                "1. Maintain the same professional tone and structure",
                "2. Keep approximately the same length",
                "3. Preserve all factual information about the person's background",
                "4. Ensure the recommendation flows naturally",
                "5. Make sure all mandatory inclusions are present and naturally integrated",
                "6. Ensure all mandatory exclusions are completely absent",
                "",
                "Please provide the refined recommendation text only, without any explanations or metadata.",
            ]
        )

        return "\n".join(prompt_parts)

    def _validate_keyword_compliance(
        self,
        content: str,
        include_keywords: Optional[List[str]] = None,
        exclude_keywords: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Validate that the refined content complies with keyword requirements."""
        content_lower = content.lower()
        validation_results: Dict[str, Any] = {
            "include_compliance": [],
            "exclude_compliance": [],
            "issues": [],
        }

        # Check included keywords
        if include_keywords:
            for keyword in include_keywords:
                if keyword.lower() in content_lower:
                    validation_results["include_compliance"].append(keyword)
                else:
                    validation_results["issues"].append(f"Missing required keyword: '{keyword}'")

        # Check excluded keywords
        if exclude_keywords:
            for keyword in exclude_keywords:
                if keyword.lower() in content_lower:
                    validation_results["issues"].append(f"Found excluded keyword: '{keyword}'")
                else:
                    validation_results["exclude_compliance"].append(keyword)

        return validation_results

    async def refine_recommendation_with_keywords(
        self,
        original_content: str,
        refinement_instructions: str,
        github_data: Dict[str, Any],
        recommendation_type: str,
        tone: str,
        length: str,
        exclude_keywords: Optional[List[str]] = None,
        regeneration_params: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Refine a generated recommendation based on keywords and regeneration parameters."""
        if not self.model:
            raise ValueError("Gemini AI not configured")

        if regeneration_params is None:
            regeneration_params = {}

        try:
            # Build the refinement prompt
            refinement_prompt = self._build_refinement_prompt_for_regeneration(
                original_content=original_content,
                refinement_instructions=refinement_instructions,
                github_data=github_data,
                recommendation_type=recommendation_type,
                tone=tone,
                length=length,
                exclude_keywords=exclude_keywords,
            )

            # Generate refined recommendation
            config = genai.types.GenerationConfig(
                temperature=settings.GEMINI_TEMPERATURE + 0.05,  # Slightly higher for refinement
                max_output_tokens=settings.GEMINI_MAX_TOKENS,
                top_p=0.9,
                top_k=40,
            )

            response = self.model.generate_content(refinement_prompt, generation_config=config)
            refined_content = str(response.text)

            # Apply formatting
            formatted_content = self._format_recommendation_output(refined_content, length, {"tone": tone, "length": length})

            # Validate keyword compliance
            validation = self._validate_keyword_compliance(formatted_content, exclude_keywords=exclude_keywords)

            # Generate refinement summary
            refinement_summary = self._generate_refinement_summary(validation)

            # Calculate confidence score for refined content
            # Ensure 'regeneration' is always set in params for confidence score calculation
            regeneration_params["regeneration"] = True

            confidence_score = self._calculate_confidence_score(github_data, formatted_content, refinement_prompt, regeneration_params)

            return {
                "refined_content": formatted_content.strip(),
                "refined_title": self._extract_title(formatted_content, github_data["user_data"]["github_username"]),
                "word_count": len(formatted_content.split()),
                "confidence_score": confidence_score,
                "exclude_keywords_avoided": validation["exclude_compliance"],
                "refinement_summary": refinement_summary,
                "validation_issues": validation["issues"],
                "generation_parameters": regeneration_params,
            }

        except Exception as e:
            logger.error(f"Error refining recommendation with keywords: {e}")
            raise

    def _generate_refinement_summary(self, validation: Dict[str, Any]) -> str:
        """Generate a summary of the refinement process."""
        summary_parts = []

        # Success metrics
        if validation["include_compliance"]:
            summary_parts.append(f"Successfully included {len(validation['include_compliance'])} required keywords")

        if validation["exclude_compliance"]:
            summary_parts.append(f"Successfully avoided {len(validation['exclude_compliance'])} excluded keywords")

        # Issues
        if validation["issues"]:
            summary_parts.append(f"Note: {len(validation['issues'])} compliance issues identified")

        if not summary_parts:
            summary_parts.append("Refinement completed with full keyword compliance")

        return ". ".join(summary_parts) + "."

    def _build_readme_generation_prompt(
        self,
        repository_data: Dict[str, Any],
        repository_analysis: Dict[str, Any],
        style: str = "comprehensive",
        include_sections: Optional[List[str]] = None,
        target_audience: str = "developers",
    ) -> str:
        """Build a prompt for README generation."""
        repo_info = repository_data.get("repository_info", {})
        repo_name = repo_info.get("name", "Project")
        description = repo_info.get("description", "")
        language = repo_info.get("language", "Unknown")

        prompt_parts = [
            f"Generate a comprehensive README.md file for the GitHub repository '{repo_name}'.",
            "",
            "REPOSITORY INFORMATION:",
            f"- Name: {repo_name}",
            f"- Description: {description}",
            f"- Primary Language: {language}",
            f"- Stars: {repo_info.get('stars', 0)}",
            f"- Forks: {repo_info.get('forks', 0)}",
            "",
        ]

        # Add repository analysis insights
        if repository_analysis.get("existing_readme"):
            prompt_parts.extend(
                [
                    "NOTE: This repository already has a README. Generate an improved, more comprehensive version.",
                    "",
                ]
            )

        # Add technical context
        languages = repository_data.get("languages", [])
        if languages:
            top_langs = [lang.get("language") for lang in languages[:3]]
            prompt_parts.append(f"- Technologies: {', '.join(top_langs)}")

        skills = repository_data.get("skills", {})
        frameworks = skills.get("frameworks", [])
        if frameworks:
            prompt_parts.append(f"- Frameworks/Libraries: {', '.join(frameworks[:5])}")

        # Add repository structure insights
        main_files = repository_analysis.get("main_files", [])
        if main_files:
            prompt_parts.append(f"- Main Files: {', '.join(main_files[:5])}")

        source_dirs = repository_analysis.get("source_directories", [])
        if source_dirs:
            prompt_parts.append(f"- Source Directories: {', '.join(source_dirs)}")

        # Add feature insights
        key_features = repository_analysis.get("key_features", [])
        if key_features:
            prompt_parts.extend(
                [
                    "",
                    "KEY FEATURES:",
                ]
                + [f"- {feature}" for feature in key_features[:5]]
            )

        # Add infrastructure insights
        infra_parts = []
        if repository_analysis.get("has_tests"):
            infra_parts.append("Testing framework configured")
        if repository_analysis.get("has_ci_cd"):
            infra_parts.append("CI/CD pipeline configured")
        if repository_analysis.get("has_docker"):
            infra_parts.append("Docker containerization")
        if repository_analysis.get("license_info"):
            license_name = repository_analysis["license_info"].get("name", "Unknown")
            infra_parts.append(f"Licensed under {license_name}")

        if infra_parts:
            prompt_parts.extend(
                [
                    "",
                    "INFRASTRUCTURE:",
                ]
                + [f"- {item}" for item in infra_parts]
            )

        # Style and audience guidance
        prompt_parts.extend(
            [
                "",
                "GENERATION REQUIREMENTS:",
            ]
        )

        if style == "comprehensive":
            prompt_parts.extend(
                [
                    "- Create a complete, professional README with all standard sections",
                    "- Include detailed setup and usage instructions",
                    "- Add comprehensive API documentation if applicable",
                    "- Include contribution guidelines and development information",
                ]
            )
        elif style == "minimal":
            prompt_parts.extend(
                [
                    "- Create a concise README with essential information only",
                    "- Focus on core functionality and basic setup",
                    "- Keep it brief but informative",
                ]
            )
        elif style == "technical":
            prompt_parts.extend(
                [
                    "- Focus on technical details and implementation",
                    "- Include detailed API documentation and architecture information",
                    "- Emphasize technical specifications and requirements",
                    "- Include development and deployment technical details",
                ]
            )

        if target_audience == "developers":
            prompt_parts.append("- Tailor content for developers and technical users")
        elif target_audience == "users":
            prompt_parts.append("- Tailor content for end-users with simpler language")
        else:
            prompt_parts.append("- Balance technical and user-friendly content")

        # Custom sections
        if include_sections:
            prompt_parts.extend(
                [
                    "",
                    f"REQUIRED SECTIONS TO INCLUDE: {', '.join(include_sections)}",
                ]
            )

        # Standard sections to include
        standard_sections = [
            "Project Title and Description",
            "Installation Instructions",
            "Usage Examples",
            "API Documentation (if applicable)",
            "Contributing Guidelines",
            "License Information",
        ]

        if style == "comprehensive":
            standard_sections.extend(
                [
                    "Features",
                    "Requirements",
                    "Configuration",
                    "Testing",
                    "Deployment",
                    "Support",
                ]
            )

        prompt_parts.extend(
            [
                "",
                "STANDARD SECTIONS TO INCLUDE:",
            ]
            + [f"- {section}" for section in standard_sections]
        )

        prompt_parts.extend(
            [
                "",
                "FORMATTING REQUIREMENTS:",
                "- Use proper Markdown formatting with headers, code blocks, and links",
                "- Include badges for language, license, build status if applicable",
                "- Use clear, descriptive section headers",
                "- Format code examples with proper syntax highlighting",
                "- Include table of contents for longer READMEs",
                "",
                "IMPORTANT NOTES:",
                "- Make the content engaging and professional",
                "- Ensure all technical information is accurate based on the repository analysis",
                "- Use active voice and clear, concise language",
                "- Include placeholders for information that can't be determined from the analysis",
                "- Generate the complete README content ready for use",
            ]
        )

        return "\n".join(prompt_parts)

    def _generate_readme_content(
        self,
        repository_data: Dict[str, Any],
        repository_analysis: Dict[str, Any],
        style: str = "comprehensive",
        include_sections: Optional[List[str]] = None,
        target_audience: str = "developers",
    ) -> Dict[str, Any]:
        """Generate README content for a repository."""
        if not self.model:
            raise ValueError("Gemini AI not configured")

        try:
            # Build the README generation prompt
            readme_prompt = self._build_readme_generation_prompt(
                repository_data=repository_data,
                repository_analysis=repository_analysis,
                style=style,
                include_sections=include_sections,
                target_audience=target_audience,
            )

            # Generate the README content
            config = genai.types.GenerationConfig(
                temperature=0.3,  # Lower temperature for more consistent documentation
                max_output_tokens=settings.GEMINI_MAX_TOKENS,
                top_p=0.9,
                top_k=40,
            )

            response = self.model.generate_content(readme_prompt, generation_config=config)
            generated_content = str(response.text)

            # Extract sections from generated content (basic parsing)
            sections = self._parse_readme_sections(generated_content)

            # Calculate confidence score based on content quality
            confidence_score = self._calculate_readme_confidence_score(generated_content, repository_data, repository_analysis)

            return {
                "generated_content": generated_content.strip(),
                "sections": sections,
                "word_count": len(generated_content.split()),
                "confidence_score": confidence_score,
                "generation_parameters": {
                    "model": settings.GEMINI_MODEL,
                    "style": style,
                    "target_audience": target_audience,
                    "include_sections": include_sections or [],
                    "temperature": 0.3,
                },
                "analysis_summary": self._generate_readme_analysis_summary(repository_analysis),
            }

        except Exception as e:
            logger.error(f"Error generating README content: {e}")
            raise

    def _parse_readme_sections(self, content: str) -> Dict[str, str]:
        """Parse README content into sections."""
        sections = {}
        lines = content.split("\n")
        current_section: Optional[str] = None  # Added type annotation
        current_content: List[str] = []  # Added type annotation

        for line in lines:
            if line.startswith("#"):
                # Save previous section
                if current_section and current_content:
                    sections[current_section] = "\n".join(current_content).strip()

                # Start new section
                current_section = line.lstrip("#").strip()
                current_content = []
            elif current_section:
                current_content.append(line)

        # Save final section
        if current_section and current_content:
            sections[current_section] = "\n".join(current_content).strip()

        return sections

    def _calculate_readme_confidence_score(self, content: str, repository_data: Dict[str, Any], repository_analysis: Dict[str, Any]) -> int:
        """Calculate confidence score for generated README."""
        score = 50  # Base score

        # Content length and structure
        word_count = len(content.split())
        if word_count > 300:
            score += 20  # Good length
        elif word_count > 150:
            score += 10

        # Check for key repository information inclusion
        repo_info = repository_data.get("repository_info", {})
        repo_name = repo_info.get("name", "").lower()
        description = repo_info.get("description", "").lower()

        content_lower = content.lower()

        if repo_name and repo_name in content_lower:
            score += 10

        if description and any(word in content_lower for word in description.split()[:3]):
            score += 10

        # Check for technical information
        languages = repository_data.get("languages", [])
        if languages and any(lang.get("language", "").lower() in content_lower for lang in languages[:2]):
            score += 10

        # Check for infrastructure mentions
        infra_score = 0
        if repository_analysis.get("has_tests") and "test" in content_lower:
            infra_score += 5
        if repository_analysis.get("has_ci_cd") and any(term in content_lower for term in ["ci", "cd", "pipeline"]):
            infra_score += 5
        if repository_analysis.get("has_docker") and "docker" in content_lower:
            infra_score += 5
        score += infra_score

        # Check for proper markdown formatting
        if any(header in content for header in ["## ", "### ", "```"]):
            score += 10

        return min(score, 100)

    def _generate_readme_analysis_summary(self, repository_analysis: Dict[str, Any]) -> str:
        """Generate a summary of the repository analysis used for README generation."""
        summary_parts = []

        if repository_analysis.get("existing_readme"):
            summary_parts.append("Repository has existing README")

        main_files = repository_analysis.get("main_files", [])
        if main_files:
            summary_parts.append(f"Found {len(main_files)} main source files")

        if repository_analysis.get("has_tests"):
            summary_parts.append("Testing framework detected")

        if repository_analysis.get("has_ci_cd"):
            summary_parts.append("CI/CD pipeline configured")

        if repository_analysis.get("has_docker"):
            summary_parts.append("Docker configuration found")

        license_info = repository_analysis.get("license_info")
        if license_info:
            summary_parts.append(f"Licensed under {license_info.get('name', 'Unknown')}")

        if not summary_parts:
            summary_parts.append("Basic repository structure analyzed")

        return ". ".join(summary_parts) + "."

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
        """Generate a recommendation highlighting multiple contributors to a repository."""
        if not self.model:
            raise ValueError("Gemini AI not configured")

        try:
            # Build the multi-contributor prompt
            prompt = self._build_multi_contributor_prompt(
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

            # Generate the recommendation
            config = genai.types.GenerationConfig(
                temperature=0.4,  # Slightly higher for collaborative content
                max_output_tokens=settings.GEMINI_MAX_TOKENS,
                top_p=0.9,
                top_k=40,
            )

            response = self.model.generate_content(prompt, generation_config=config)
            generated_content = str(response.text)

            # Apply formatting
            formatted_content = self._format_recommendation_output(generated_content, length, {"tone": tone, "length": length})

            # Calculate confidence score
            confidence_score = self._calculate_multi_contributor_confidence_score(formatted_content, contributors, team_highlights)

            return {
                "recommendation": formatted_content.strip(),
                "word_count": len(formatted_content.split()),
                "confidence_score": confidence_score,
                "generation_parameters": {
                    "model": settings.GEMINI_MODEL,
                    "contributors_count": len(contributors),
                    "recommendation_type": recommendation_type,
                    "tone": tone,
                    "length": length,
                    "focus_areas": focus_areas or [],
                },
            }

        except Exception as e:
            logger.error(f"Error generating multi-contributor recommendation: {e}")
            raise

    def _build_multi_contributor_prompt(
        self,
        repository_data: Dict[str, Any],
        contributors: List[Dict[str, Any]],
        team_highlights: List[str],
        collaboration_insights: List[str],
        technical_diversity: Dict[str, int],
        recommendation_type: str,
        tone: str,
        length: str,
        focus_areas: Optional[List[str]] = None,
    ) -> str:
        """Build a prompt for multi-contributor recommendation generation."""
        repo_info = repository_data.get("repository_info", {})
        repo_name = repo_info.get("name", "Project")

        prompt_parts = [
            f"Generate a {length} LinkedIn recommendation highlighting the collaborative work of a development team on the '{repo_name}' project.",
            "",
            f"Make it {tone} and suitable for {recommendation_type} purposes.",
            "",
            "TEAM OVERVIEW:",
        ]

        # Add team highlights
        if team_highlights:
            prompt_parts.extend([f"- {highlight}" for highlight in team_highlights])

        prompt_parts.append("")

        # Add collaboration insights
        if collaboration_insights:
            prompt_parts.append("COLLABORATION STRENGTHS:")
            prompt_parts.extend([f"- {insight}" for insight in collaboration_insights])

        prompt_parts.append("")

        # Add technical diversity
        if technical_diversity:
            prompt_parts.append("TECHNICAL EXPERTISE:")
            for tech, count in list(technical_diversity.items())[:8]:
                if count > 1:
                    prompt_parts.append(f"- {tech} (used by {count} team members)")
                else:
                    prompt_parts.append(f"- {tech}")

        prompt_parts.append("")

        # Add individual contributor information
        prompt_parts.append("TEAM MEMBERS:")
        for i, contributor in enumerate(contributors, 1):
            username = contributor.get("username", f"Contributor {i}")
            full_name = contributor.get("full_name", username)
            contributions = contributor.get("contributions", 0)
            focus = contributor.get("contribution_focus", "general")
            languages = contributor.get("primary_languages", [])
            skills = contributor.get("top_skills", [])
            key_contributions = contributor.get("key_contributions", [])

            contributor_info = [
                f"{i}. {full_name} ({username})",
                f"   - Contributions: {contributions}",
                f"   - Focus Area: {focus}",
            ]

            if languages:
                contributor_info.append(f"   - Languages: {', '.join(languages)}")

            if skills:
                contributor_info.append(f"   - Key Skills: {', '.join(skills)}")

            if key_contributions:
                contributor_info.append(f"   - Key Contributions: {', '.join(key_contributions[:2])}")

            prompt_parts.extend(contributor_info)
            prompt_parts.append("")

        # Add focus areas if specified
        if focus_areas:
            prompt_parts.extend(
                [
                    "",
                    f"SPECIAL FOCUS AREAS TO EMPHASIZE: {', '.join(focus_areas)}",
                    "",
                ]
            )

        # Add generation guidelines
        prompt_parts.extend(
            [
                "RECOMMENDATION GUIDELINES:",
                "- Write in first person as someone who has worked with this entire team",
                "- Highlight how the team's collaboration and diverse skills contributed to project success",
                "- Emphasize both individual contributions and team synergy",
                "- Focus on technical achievements, problem-solving, and collaboration",
                "- Use natural, conversational language like you're talking to a colleague",
                "- Balance recognition of individual excellence with team accomplishments",
                "- Include specific examples of collaborative achievements when possible",
                "- DO NOT mention any company names, employers, or employment history",
                "- Focus only on technical skills and collaborative abilities",
                "",
                f"Target length: {self._get_length_guideline(length)} words",
                "",
                "Structure the recommendation with:",
                "- Introduction highlighting team composition and collaboration",
                "- Specific examples of technical achievements and problem-solving",
                "- Emphasis on how diverse skills contributed to project success",
                "- Conclusion reinforcing the team's collaborative excellence",
                "",
                "Generate the complete recommendation text ready for use.",
            ]
        )

        return "\n".join(prompt_parts)

    def _calculate_multi_contributor_confidence_score(self, content: str, contributors: List[Dict[str, Any]], team_highlights: List[str]) -> int:
        """Calculate confidence score for multi-contributor recommendations."""
        score = 60  # Base score for collaborative content

        content_lower = content.lower()

        # Check if contributors are mentioned
        mentioned_contributors = 0
        for contributor in contributors:
            username = contributor.get("username", "").lower()
            full_name = contributor.get("full_name", "").lower() if contributor.get("full_name") else ""
            if username in content_lower or full_name in content_lower:
                mentioned_contributors += 1

        if mentioned_contributors > 0:
            score += min(mentioned_contributors * 5, 20)

        # Check for team/collaboration language
        team_words = ["team", "collaboration", "together", "collaborative", "group", "collectively"]
        team_mentions = sum(1 for word in team_words if word in content_lower)
        if team_mentions > 0:
            score += min(team_mentions * 5, 15)

        # Check for technical diversity mentions
        technical_words = ["diverse", "diversity", "variety", "complementary", "skills", "expertise"]
        technical_mentions = sum(1 for word in technical_words if word in content_lower)
        if technical_mentions > 0:
            score += min(technical_mentions * 3, 10)

        # Length and structure bonus
        word_count = len(content.split())
        if word_count > 200:
            score += 10
        elif word_count > 150:
            score += 5

        return min(score, 100)

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

        # Enhanced data sources (new)
        user_data_enhanced = user_data

        # Starred repositories (shows interests)
        starred_repos = user_data_enhanced.get("starred_repositories", [])
        if starred_repos:
            score += min(len(starred_repos) * 2, 10)  # Up to 10 points

        # Organizations (shows community involvement)
        organizations = user_data_enhanced.get("organizations", [])
        if organizations:
            score += min(len(organizations) * 3, 10)  # Up to 10 points

        # Dependencies found (shows deep technical analysis)
        skills_enhanced = skills
        dependencies_found = skills_enhanced.get("dependencies_found", [])
        if dependencies_found:
            score += min(len(dependencies_found) * 1, 10)  # Up to 10 points

        # Commit analysis depth
        commit_analysis = github_data.get("commit_analysis", {})
        if commit_analysis.get("total_commits_analyzed", 0) > 0:
            commits_score = min(commit_analysis["total_commits_analyzed"] / 10, 10)  # Up to 10 points
            score += commits_score

        # Conventional commit analysis (professional development practices)
        conventional_analysis = commit_analysis.get("conventional_commit_analysis", {})
        if conventional_analysis.get("stats", {}).get("conventional_commits", 0) > 0:
            score += 5  # Bonus for conventional commits

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
        specific_indicators = [
            "github",
            "repository",
            "commit",
            "code",
            "programming",
        ]
        if any(indicator in content.lower() for indicator in specific_indicators):
            score += 25

        return min(score, 100)

    async def generate_repository_readme(
        self,
        repository_data: Dict[str, Any],
        repository_analysis: Dict[str, Any],
        style: str = "comprehensive",
        include_sections: Optional[List[str]] = None,
        target_audience: str = "developers",
    ) -> Dict[str, Any]:
        """Generate a README for a GitHub repository."""
        if not self.model:
            raise ValueError("Gemini AI not configured")

        try:
            # Build the README generation prompt
            readme_prompt = self._build_readme_generation_prompt(
                repository_data=repository_data,
                repository_analysis=repository_analysis,
                style=style,
                include_sections=include_sections,
                target_audience=target_audience,
            )

            # Generate the README content
            config = genai.types.GenerationConfig(
                temperature=0.3,  # Lower temperature for more consistent documentation
                max_output_tokens=settings.GEMINI_MAX_TOKENS,
                top_p=0.9,
                top_k=40,
            )

            response = self.model.generate_content(readme_prompt, generation_config=config)
            generated_content = str(response.text)

            # Extract sections from generated content (basic parsing)
            sections = self._parse_readme_sections(generated_content)

            # Calculate confidence score based on content quality
            confidence_score = self._calculate_readme_confidence_score(generated_content, repository_data, repository_analysis)

            return {
                "generated_content": generated_content.strip(),
                "sections": sections,
                "word_count": len(generated_content.split()),
                "confidence_score": confidence_score,
                "generation_parameters": {
                    "model": settings.GEMINI_MODEL,
                    "style": style,
                    "target_audience": target_audience,
                    "include_sections": include_sections or [],
                    "temperature": 0.3,
                },
                "analysis_summary": self._generate_readme_analysis_summary(repository_analysis),
            }

        except Exception as e:
            logger.error(f"Error generating repository README: {e}")
            raise
