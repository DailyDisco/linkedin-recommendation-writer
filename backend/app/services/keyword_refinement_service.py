"""Keyword Refinement Service for refining recommendations with specific keywords."""

import logging
from typing import Any, Dict, List, Optional

from app.core.config import settings
from app.services.prompt_service import PromptService

logger = logging.getLogger(__name__)

# Handle optional Google Generative AI import
try:
    import google.genai as genai
    from google.genai import types

    genai_available = True
except ImportError:
    genai = None  # type: ignore
    types = None  # type: ignore
    genai_available = False


class KeywordRefinementService:
    """Service for refining recommendations with keyword-based modifications."""

    def __init__(self, prompt_service: PromptService) -> None:
        """Initialize keyword refinement service."""
        self.prompt_service = prompt_service
        self.client = None
        if genai and settings.GEMINI_API_KEY:
            self.client = genai.Client(api_key=settings.GEMINI_API_KEY)

    async def refine_recommendation_with_keywords(
        self,
        original_content: str,
        refinement_instructions: str,
        github_data: Dict[str, Any],
        recommendation_type: str,
        tone: str,
        length: str,
        include_keywords: Optional[List[str]] = None,
        exclude_keywords: Optional[List[str]] = None,
        regeneration_params: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Refine a generated recommendation based on keywords and regeneration parameters."""
        if not self.client:
            raise ValueError("Gemini AI not configured")

        if regeneration_params is None:
            regeneration_params = {}

        try:
            # Build the refinement prompt
            refinement_prompt = self.prompt_service.build_keyword_refinement_prompt(
                original_content=original_content,
                include_keywords=include_keywords,  # Pass include keywords
                exclude_keywords=exclude_keywords,
                refinement_instructions=refinement_instructions,
                github_data=github_data,
            )

            # Generate refined recommendation
            config = types.GenerateContentConfig(
                temperature=settings.GEMINI_TEMPERATURE + 0.05,  # Slightly higher for refinement
                max_output_tokens=settings.GEMINI_MAX_TOKENS,
                top_p=0.9,
                top_k=40,
            )

            response = self.client.models.generate_content(model=settings.GEMINI_MODEL, contents=refinement_prompt, config=config)
            refined_content = response.candidates[0].content.parts[0].text

            # Apply formatting
            formatted_content = self._format_refined_content(refined_content, length, {"tone": tone, "length": length})

            # Validate keyword compliance
            validation = self._validate_keyword_compliance(formatted_content, include_keywords=include_keywords, exclude_keywords=exclude_keywords)

            # Generate refinement summary
            refinement_summary = self._generate_refinement_summary(validation)

            # Calculate confidence score for refined content
            # Ensure 'regeneration' is always set in params for confidence score calculation
            regeneration_params["regeneration"] = True

            return {
                "refined_content": formatted_content.strip(),
                "refined_title": self.prompt_service.extract_title(formatted_content, github_data["user_data"]["github_username"]),
                "word_count": len(formatted_content.split()),
                "confidence_score": 85,  # Placeholder - will be calculated by ConfidenceScorerService
                "include_keywords_used": validation["include_compliance"],
                "exclude_keywords_avoided": validation["exclude_compliance"],
                "refinement_summary": refinement_summary,
                "validation_issues": validation["issues"],
                "generation_parameters": regeneration_params,
            }

        except Exception as e:
            raise ValueError(f"Error refining recommendation with keywords: {e}")

    def _format_refined_content(self, content: str, length: str, generation_params: Optional[Dict[str, Any]] = None) -> str:
        """Format refined content to maintain consistency."""
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

    def _validate_keyword_compliance(self, content: str, include_keywords: Optional[List[str]] = None, exclude_keywords: Optional[List[str]] = None) -> Dict[str, Any]:
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
