"""Multi-Contributor Service for generating team recommendations."""

from typing import Any, Dict, List, Optional

from app.core.config import settings
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


class MultiContributorService:
    """Service for generating recommendations highlighting multiple contributors to a repository."""

    def __init__(self, prompt_service: PromptService) -> None:
        """Initialize multi-contributor service."""
        self.prompt_service = prompt_service
        self.client = None
        if genai and settings.GEMINI_API_KEY:
            self.client = genai.Client(api_key=settings.GEMINI_API_KEY)

    async def generate_multi_contributor_recommendation(
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
        if not self.client:
            raise ValueError("Gemini AI not configured")

        try:
            # Build the multi-contributor prompt
            prompt = self.prompt_service.build_multi_contributor_prompt(
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
            config = types.GenerateContentConfig(
                temperature=0.4,  # Slightly higher for collaborative content
                max_output_tokens=settings.GEMINI_MAX_TOKENS,
                top_p=0.9,
                top_k=40,
            )

            response = self.client.models.generate_content(model=settings.GEMINI_MODEL, contents=prompt, config=config)
            generated_content = response.candidates[0].content.parts[0].text

            # Apply formatting
            formatted_content = self._format_multi_contributor_content(generated_content, length, {"tone": tone, "length": length})

            return {
                "recommendation": formatted_content.strip(),
                "word_count": len(formatted_content.split()),
                "confidence_score": 85,  # Placeholder - will be calculated by ConfidenceScorerService
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
            raise ValueError(f"Error generating multi-contributor recommendation: {e}")

    def _format_multi_contributor_content(self, content: str, length: str, generation_params: Optional[Dict[str, Any]] = None) -> str:
        """Format multi-contributor content to maintain consistency."""
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
                    sentences_per_paragraph = max(2, len(sentences) // 4)  # Aim for more paragraphs in team recommendations

                    for i, sentence in enumerate(sentences):
                        current_paragraph.append(sentence + ".")
                        if (i + 1) % sentences_per_paragraph == 0 or i == len(sentences) - 1:
                            paragraphs.append(" ".join(current_paragraph))
                            current_paragraph = []
                else:
                    paragraphs = [formatted_content]

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

        # Apply tone-specific formatting if generation_params provided
        if generation_params:
            tone = generation_params.get("tone", "professional")
            final_content = self._apply_tone_formatting(final_content, tone)

        return final_content

    def _apply_tone_formatting(self, content: str, tone: str) -> str:
        """Apply tone-specific formatting to the content."""
        if tone == "professional":
            # Ensure professional language and structure
            return content
        elif tone == "casual":
            # For casual tone, might want to adjust formality slightly
            return content
        else:
            return content

    def _validate_multi_contributor_structure(self, content: str, contributors: List[Dict[str, Any]], generation_params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Validate the structure and quality of multi-contributor recommendations."""
        validation_results: Dict[str, Any] = {"is_valid": True, "issues": [], "suggestions": [], "structure_score": 100}

        paragraphs = [p.strip() for p in content.split("\n\n") if p.strip()]
        word_count = len(content.split())

        # Check paragraph count (team recommendations should have more paragraphs)
        expected_paragraphs = 4  # Default for team recommendations
        if generation_params:
            length = generation_params.get("length", "medium")
            if length == "short":
                expected_paragraphs = 3
            elif length == "long":
                expected_paragraphs = 5

        if len(paragraphs) != expected_paragraphs:
            validation_results["issues"].append(f"Expected {expected_paragraphs} paragraphs for team recommendation, got {len(paragraphs)}")
            validation_results["structure_score"] = int(validation_results["structure_score"]) - 15

        # Check word count
        if generation_params:
            length = generation_params.get("length", "medium")
            if length == "short" and word_count > 220:
                validation_results["issues"].append("Content too long for short format")
                validation_results["structure_score"] = int(validation_results["structure_score"]) - 15
            elif length == "medium" and (word_count < 150 or word_count > 250):
                validation_results["issues"].append("Word count outside medium range (150-250)")
                validation_results["structure_score"] = int(validation_results["structure_score"]) - 10
            elif length == "long" and word_count < 200:
                validation_results["issues"].append("Content too short for long format")
                validation_results["structure_score"] = int(validation_results["structure_score"]) - 15

        # Check for team/collaboration language
        content_lower = content.lower()
        team_words = ["team", "collaboration", "together", "collaborative", "group", "collectively", "contributors"]
        team_mentions = sum(1 for word in team_words if word in content_lower)

        if team_mentions < 2:
            validation_results["issues"].append("Team recommendation should mention collaboration/teamwork more prominently")
            validation_results["structure_score"] = int(validation_results["structure_score"]) - 20

        # Check for contributor mentions
        mentioned_contributors = 0
        for contributor in contributors[:5]:  # Check top 5 contributors
            username = contributor.get("username", "").lower()
            full_name = contributor.get("full_name", "").lower() if contributor.get("full_name") else ""
            if username in content_lower or full_name in content_lower:
                mentioned_contributors += 1

        if mentioned_contributors < 2:
            validation_results["suggestions"].append("Consider mentioning more team members by name")
            validation_results["structure_score"] = int(validation_results["structure_score"]) - 10

        # Check paragraph lengths
        for i, para in enumerate(paragraphs):
            para_words = len(para.split())
            if para_words < 25:
                validation_results["suggestions"].append(f"Paragraph {i+1} is quite short ({para_words} words)")
            elif para_words > 180:
                validation_results["suggestions"].append(f"Paragraph {i+1} is very long ({para_words} words)")

        validation_results["structure_score"] = max(0, int(validation_results["structure_score"]))
        return validation_results
