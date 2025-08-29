"""Confidence Scorer Service for calculating quality scores for AI-generated content."""

from typing import Any, Dict, List, Optional


class ConfidenceScorerService:
    """Service for calculating confidence scores for AI-generated content."""

    def calculate_confidence_score(self, github_data: Dict[str, Any], generated_content: str, prompt: Optional[str] = None, generation_params: Optional[Dict[str, Any]] = None) -> int:
        """Calculate dynamic confidence score based on multiple quality factors."""
        score = 0.0
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
            commits_score = min(commit_analysis["total_commits_analyzed"] / 10, 10)  # Up to 10 points
            score += commits_score

        # Conventional commit analysis (professional development practices)
        conventional_analysis = commit_analysis.get("conventional_commit_analysis", {})
        if conventional_analysis.get("stats", {}).get("conventional_commits", 0) > 0:
            score += 5  # Bonus for conventional commits

        return min(int(score), max_score)

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

    def _score_prompt_alignment(self, prompt: str, generated_content: str, generation_params: Dict[str, Any]) -> float:
        """Score how well the generated content aligns with the prompt requirements."""
        score = 0.0
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

    def calculate_readme_confidence_score(self, content: str, repository_data: Dict[str, Any], repository_analysis: Dict[str, Any]) -> int:
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

    def calculate_multi_contributor_confidence_score(self, content: str, contributors: List[Dict[str, Any]], team_highlights: List[str]) -> int:
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

    def validate_keyword_compliance(self, content: str, include_keywords: Optional[List[str]] = None, exclude_keywords: Optional[List[str]] = None) -> Dict[str, Any]:
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

    def generate_refinement_summary(self, validation: Dict[str, Any]) -> str:
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
