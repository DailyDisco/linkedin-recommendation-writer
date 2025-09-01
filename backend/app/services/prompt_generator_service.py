"""AI Prompt Generator Service for handling prompt assistant features."""

import logging
from typing import Any, Dict, List

from app.core.config import get_settings
from app.schemas.recommendation import (
    ChatAssistantResponse,
    PromptSuggestionsResponse,
)

logger = logging.getLogger(__name__)
settings = get_settings()


class GitHubProfileMinimalSchema:
    """Minimal schema for GitHub profile data needed for prompt generation."""

    def __init__(self, github_data: Dict[str, Any]):
        self.username = github_data.get("user_data", {}).get("github_username", "")
        self.bio = github_data.get("user_data", {}).get("bio", "")
        self.full_name = github_data.get("user_data", {}).get("full_name", "")
        self.company = github_data.get("user_data", {}).get("company", "")
        self.location = github_data.get("user_data", {}).get("location", "")
        self.public_repos = github_data.get("user_data", {}).get("public_repos", 0)
        self.followers = github_data.get("user_data", {}).get("followers", 0)
        self.following = github_data.get("user_data", {}).get("following", 0)
        self.languages = [lang.get("language", "") for lang in github_data.get("languages", [])][:5]  # Top 5 languages
        self.skills = github_data.get("skills", {}).get("technical_skills", [])[:10]  # Top 10 skills
        self.repositories = [repo.get("name", "") for repo in github_data.get("repositories", [])][:5]  # Top 5 repos
        self.commit_analysis = github_data.get("commit_analysis", {})


class PromptGeneratorService:
    """Service for generating AI-powered prompts and handling responses for the prompt assistant."""

    def __init__(self):
        """Initialize the prompt generator service."""
        try:
            import google.generativeai as genai

            genai.configure(api_key=settings.GEMINI_API_KEY)
            self.client = genai.GenerativeModel(settings.GEMINI_MODEL)
            self.generation_config = {
                "temperature": settings.GEMINI_TEMPERATURE,
                "top_p": 0.9,
                "top_k": 40,
                "max_output_tokens": settings.GEMINI_MAX_TOKENS,
            }
        except ImportError:
            logger.warning("Google Generative AI not available")
            self.client = None

    async def get_initial_prompt_suggestions(
        self,
        github_data: Dict[str, Any],
        recommendation_type: str,
        tone: str,
        length: str,
    ) -> PromptSuggestionsResponse:
        """Generate initial prompt suggestions based on GitHub profile data."""
        if not self.client:
            logger.warning("AI client not available, returning empty suggestions")
            return PromptSuggestionsResponse()

        try:
            # Convert github_data to minimal schema
            profile = GitHubProfileMinimalSchema(github_data)

            # Build the prompt
            prompt = self._build_initial_suggestions_prompt(profile, recommendation_type, tone, length)

            # Generate response
            response = await self.client.generate_content_async(prompt, generation_config=self.generation_config)

            # Parse the response
            return self._parse_initial_suggestions_response(response.text)

        except Exception as e:
            logger.error(f"Error generating initial prompt suggestions: {e}")
            return PromptSuggestionsResponse()

    def _build_initial_suggestions_prompt(
        self,
        profile: GitHubProfileMinimalSchema,
        recommendation_type: str,
        tone: str,
        length: str,
    ) -> str:
        """Build the prompt for generating initial suggestions."""
        return f"""
You are a LinkedIn recommendation writing assistant. Based on this GitHub profile data, suggest helpful examples for filling out a recommendation form.

PROFILE INFORMATION:
- Username: {profile.username}
- Full Name: {profile.full_name or 'Not provided'}
- Bio: {profile.bio or 'Not provided'}
- Company: {profile.company or 'Not provided'}
- Location: {profile.location or 'Not provided'}
- Public Repositories: {profile.public_repos}
- Followers: {profile.followers}
- Programming Languages: {', '.join(profile.languages) if profile.languages else 'None specified'}
- Technical Skills: {', '.join(profile.skills) if profile.skills else 'None specified'}
- Notable Repositories: {', '.join(profile.repositories) if profile.repositories else 'None specified'}

RECOMMENDATION SETTINGS:
- Type: {recommendation_type}
- Tone: {tone}
- Length: {length}

Please provide 3-5 relevant suggestions for each of these form fields:
1. Working Relationship: Suggest descriptions of how someone might have worked with this person
2. Specific Skills: Suggest key skills to highlight from their profile
3. Notable Achievements: Suggest achievements or contributions based on their GitHub activity

Format your response as JSON with this structure:
{{
    "working_relationship": ["suggestion 1", "suggestion 2", "suggestion 3"],
    "specific_skills": ["skill 1", "skill 2", "skill 3"],
    "notable_achievements": ["achievement 1", "achievement 2", "achievement 3"]
}}

Make suggestions that are:
- Realistic based on the GitHub profile
- Professional and appropriate for LinkedIn
- Varied to give the user options
- Concise and actionable
"""

    def _parse_initial_suggestions_response(self, ai_response: str) -> PromptSuggestionsResponse:
        """Parse the AI response into structured suggestions."""
        try:
            import json

            # Clean the response to extract JSON
            cleaned_response = ai_response.strip()
            if cleaned_response.startswith("```json"):
                cleaned_response = cleaned_response[7:]
            if cleaned_response.endswith("```"):
                cleaned_response = cleaned_response[:-3]
            cleaned_response = cleaned_response.strip()

            # Parse JSON
            data = json.loads(cleaned_response)

            return PromptSuggestionsResponse(
                suggested_working_relationship=data.get("working_relationship", []),
                suggested_specific_skills=data.get("specific_skills", []),
                suggested_notable_achievements=data.get("notable_achievements", []),
            )

        except Exception as e:
            logger.error(f"Error parsing AI response: {e}")
            return PromptSuggestionsResponse()

    async def get_autocomplete_suggestions(
        self,
        github_data: Dict[str, Any],
        field_name: str,
        current_input: str,
    ) -> List[str]:
        """Generate auto-completion suggestions for form fields."""
        if not self.client:
            logger.warning("AI client not available, returning empty suggestions")
            return []

        if not current_input.strip():
            return []

        try:
            # Convert github_data to minimal schema
            profile = GitHubProfileMinimalSchema(github_data)

            # Build the prompt
            prompt = self._build_autocomplete_prompt(profile, field_name, current_input)

            # Generate response
            response = await self.client.generate_content_async(prompt, generation_config=self.generation_config)

            # Parse the response
            return self._parse_autocomplete_response(response.text)

        except Exception as e:
            logger.error(f"Error generating autocomplete suggestions: {e}")
            return []

    def _build_autocomplete_prompt(
        self,
        profile: GitHubProfileMinimalSchema,
        field_name: str,
        current_input: str,
    ) -> str:
        """Build the prompt for auto-completion suggestions."""
        field_context = {
            "specific_skills": "technical skills, programming languages, frameworks, or tools",
            "notable_achievements": "project accomplishments, contributions, or professional achievements",
        }

        return f"""
You are helping with auto-completion for a LinkedIn recommendation form.

PROFILE INFORMATION:
- Username: {profile.username}
- Technical Skills: {', '.join(profile.skills) if profile.skills else 'None specified'}
- Programming Languages: {', '.join(profile.languages) if profile.languages else 'None specified'}
- Notable Repositories: {', '.join(profile.repositories) if profile.repositories else 'None specified'}

USER IS TYPING IN: {field_name.upper().replace('_', ' ')}
Current input: "{current_input}"

Please suggest 3-5 relevant completions for {field_context[field_name]} based on:
1. The user's current input
2. The GitHub profile data above
3. Common {field_name.replace('_', ' ')} in this field

Return only a JSON array of suggestions, like:
["suggestion 1", "suggestion 2", "suggestion 3"]

Make suggestions:
- Relevant to the current input
- Based on the GitHub profile when possible
- Professional and appropriate
- Concise (max 50 characters each)
"""

    def _parse_autocomplete_response(self, ai_response: str) -> List[str]:
        """Parse the AI response into a list of suggestions."""
        try:
            import json

            # Clean the response to extract JSON
            cleaned_response = ai_response.strip()
            if cleaned_response.startswith("```json"):
                cleaned_response = cleaned_response[7:]
            if cleaned_response.endswith("```"):
                cleaned_response = cleaned_response[:-3]
            cleaned_response = cleaned_response.strip()

            # Parse JSON
            suggestions = json.loads(cleaned_response)

            # Ensure it's a list and filter out invalid suggestions
            if isinstance(suggestions, list):
                return [str(s).strip() for s in suggestions if str(s).strip()][:5]  # Max 5 suggestions
            else:
                return []

        except Exception as e:
            logger.error(f"Error parsing autocomplete response: {e}")
            return []

    async def chat_with_assistant(
        self,
        github_data: Dict[str, Any],
        conversation_history: List[Dict[str, str]],
        user_message: str,
        current_form_data: Dict[str, Any],
    ) -> ChatAssistantResponse:
        """Handle conversational AI assistance for the recommendation form."""
        if not self.client:
            logger.warning("AI client not available, returning generic response")
            return ChatAssistantResponse(ai_reply="I'm sorry, but the AI assistant is currently unavailable. Please try again later.")

        try:
            # Convert github_data to minimal schema
            profile = GitHubProfileMinimalSchema(github_data)

            # Build the prompt
            prompt = self._build_chat_prompt(profile, conversation_history, user_message, current_form_data)

            # Generate response
            response = await self.client.generate_content_async(prompt, generation_config=self.generation_config)

            # Parse the response
            return self._parse_chat_response(response.text)

        except Exception as e:
            logger.error(f"Error in chat assistant: {e}")
            return ChatAssistantResponse(ai_reply="I encountered an error while processing your request. Please try again.")

    def _build_chat_prompt(
        self,
        profile: GitHubProfileMinimalSchema,
        conversation_history: List[Dict[str, str]],
        user_message: str,
        current_form_data: Dict[str, Any],
    ) -> str:
        """Build the prompt for the chat assistant."""
        # Format conversation history
        history_text = ""
        if conversation_history:
            for msg in conversation_history[-5:]:  # Last 5 messages for context
                role = msg.get("role", "unknown")
                content = msg.get("content", "")
                history_text += f"{role.title()}: {content}\n"

        # Format current form data
        form_data_text = ""
        for key, value in current_form_data.items():
            if value and str(value).strip():
                form_data_text += f"- {key}: {value}\n"

        return f"""
You are a helpful LinkedIn recommendation writing assistant. Help users fill out their recommendation forms effectively.

PROFILE INFORMATION:
- Username: {profile.username}
- Full Name: {profile.full_name or 'Not provided'}
- Technical Skills: {', '.join(profile.skills) if profile.skills else 'None specified'}
- Programming Languages: {', '.join(profile.languages) if profile.languages else 'None specified'}
- Notable Repositories: {', '.join(profile.repositories) if profile.repositories else 'None specified'}

CURRENT FORM DATA:
{form_data_text.strip()}

CONVERSATION HISTORY:
{history_text.strip()}

USER'S CURRENT MESSAGE: {user_message}

Please provide a helpful, concise response. If appropriate, you can suggest specific updates to form fields.

Format your response as JSON:
{{
    "ai_reply": "Your helpful response here",
    "suggested_form_updates": {{
        "field_name": "suggested_value"
    }} or null if no suggestions
}}

Guidelines:
- Be encouraging and professional
- Provide specific, actionable advice
- Base suggestions on the GitHub profile data when possible
- Keep responses concise but helpful
- Only suggest form updates if they directly address the user's question
"""

    def _parse_chat_response(self, ai_response: str) -> ChatAssistantResponse:
        """Parse the AI response for the chat assistant."""
        try:
            import json

            # Clean the response to extract JSON
            cleaned_response = ai_response.strip()
            if cleaned_response.startswith("```json"):
                cleaned_response = cleaned_response[7:]
            if cleaned_response.endswith("```"):
                cleaned_response = cleaned_response[:-3]
            cleaned_response = cleaned_response.strip()

            # Parse JSON
            data = json.loads(cleaned_response)

            return ChatAssistantResponse(ai_reply=data.get("ai_reply", "I'm sorry, I couldn't process your request properly."), suggested_form_updates=data.get("suggested_form_updates"))

        except Exception as e:
            logger.error(f"Error parsing chat response: {e}")
            return ChatAssistantResponse(ai_reply="I'm sorry, I encountered an issue processing your message. Please try rephrasing your question.")
