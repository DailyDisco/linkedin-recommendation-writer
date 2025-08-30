"""README Generation Service for creating repository documentation."""

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


class READMEGenerationService:
    """Service for generating README files for repositories."""

    def __init__(self, prompt_service: PromptService) -> None:
        """Initialize README generation service."""
        self.prompt_service = prompt_service
        self.client = None
        if genai and settings.GEMINI_API_KEY:
            self.client = genai.Client(api_key=settings.GEMINI_API_KEY)

    async def generate_repository_readme(
        self,
        repository_data: Dict[str, Any],
        repository_analysis: Dict[str, Any],
        style: str = "comprehensive",
        include_sections: Optional[List[str]] = None,
        target_audience: str = "developers",
    ) -> Dict[str, Any]:
        """Generate a README for a GitHub repository."""
        if not self.client:
            raise ValueError("Gemini AI not configured")

        try:
            # Build the README generation prompt
            readme_prompt = self.prompt_service.build_readme_generation_prompt(
                repository_data=repository_data,
                repository_analysis=repository_analysis,
                style=style,
                include_sections=include_sections,
                target_audience=target_audience,
            )

            # Generate the README content
            config = types.GenerateContentConfig(
                temperature=0.3,  # Lower temperature for more consistent documentation
                max_output_tokens=settings.GEMINI_MAX_TOKENS,
                top_p=0.9,
                top_k=40,
            )

            response = self.client.models.generate_content(model=settings.GEMINI_MODEL, contents=readme_prompt, config=config)
            generated_content = response.candidates[0].content.parts[0].text

            # Extract sections from generated content (basic parsing)
            sections = self._parse_readme_sections(generated_content)

            return {
                "generated_content": generated_content.strip(),
                "sections": sections,
                "word_count": len(generated_content.split()),
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
            raise ValueError(f"Error generating repository README: {e}")

    def _parse_readme_sections(self, content: str) -> Dict[str, str]:
        """Parse README content into sections."""
        sections = {}
        lines = content.split("\n")
        current_section: Optional[str] = None
        current_content: List[str] = []

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
