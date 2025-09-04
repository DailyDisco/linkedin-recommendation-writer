"""AI Prompt Service for building and formatting prompts."""

from typing import Any, Dict, List, Optional


class PromptService:
    """Service for building and formatting AI prompts."""

    def build_prompt(
        self,
        github_data: Dict[str, Any],
        recommendation_type: str = "professional",
        tone: str = "professional",
        length: str = "medium",
        custom_prompt: Optional[str] = None,
        target_role: Optional[str] = None,
        specific_skills: Optional[list] = None,
        exclude_keywords: Optional[list] = None,
        analysis_context_type: str = "profile",
        repository_url: Optional[str] = None,
    ) -> str:
        """Build the AI generation prompt."""

        user_data = github_data.get("user_data", {})
        languages = github_data.get("languages", [])
        skills = github_data.get("skills", {})
        commit_analysis = github_data.get("commit_analysis", {})
        repository_info = github_data.get("repository_info", {})

        # Safely get username: always prioritize the person's GitHub username from user_data
        base_username = user_data.get("github_username")
        if not base_username and repository_info:
            # Only use repository owner as fallback if we don't have user_data
            base_username = repository_info.get("owner", {}).get("login")
        if not base_username:  # Final fallback
            base_username = "the developer"

        # Base prompt structure
        prompt_parts = [
            f"Write a {length} LinkedIn recommendation for {base_username}.",
            f"Make it {tone} and suitable for {recommendation_type} purposes.",
        ]

        if target_role:
            prompt_parts.append(f"Highlight why they'd be great for a {target_role} position.")

        # Add GitHub context based on standardized analysis type
        # Use parameter if provided, otherwise fall back to data
        context_type = analysis_context_type or github_data.get("analysis_context_type", "profile")

        # Flag to track if we've handled context-specific data
        context_handled = False

        # Handle different analysis contexts
        if context_type == "repo_only":
            # Build repository-only prompt and skip all general profile logic
            repo_info = github_data.get("repository_info", {})
            if repo_info:
                prompt_parts.extend(
                    [
                        "\nCRITICAL: ONLY DISCUSS THIS SPECIFIC REPOSITORY - NO OTHER PROJECTS ALLOWED",
                        "",
                        "REPOSITORY DETAILS:",
                        f"- Repository Name: {repo_info.get('name', 'Not provided')}",
                        f"- Description: {repo_info.get('description', 'Not provided')}",
                        f"- Main Language: {repo_info.get('language', 'Not provided')}",
                        f"- Repository URL: {repository_url or 'Not provided'}",
                        "",
                        "STRICT INSTRUCTIONS:",
                        "- ONLY mention work, skills, and contributions from THIS SPECIFIC REPOSITORY",
                        "- DO NOT reference any other projects, repositories, or general GitHub profile",
                        "- DO NOT talk about commits, PRs, or work outside of this repository",
                        "- DO NOT mention their overall coding activity, experience, or background",
                        "- DO NOT reference their starred repositories, organizations, or general profile data",
                        "- DO NOT mention any technologies, frameworks, or languages that are NOT used in THIS repository",
                        "- If you don't have specific information about this repository, be honest about limitations",
                        "- Focus exclusively on what they've done in THIS repository only",
                        "- IGNORE any general guidelines about overall experience or background",
                        "- DO NOT infer or assume technologies based on the person's general profile",
                        "",
                        "WHAT TO INCLUDE (ONLY FROM THIS REPOSITORY):",
                    ]
                )

                # Only include repository-specific data
                repo_languages = github_data.get("repository_languages", [])
                repo_skills = github_data.get("repository_skills", {})
                repo_commit_analysis = github_data.get("repository_commit_analysis", {})

                if repo_languages:
                    top_repo_languages = [lang.get("language", "") for lang in repo_languages[:3]]
                    prompt_parts.append(f"- Languages used in this repository: {', '.join(top_repo_languages)}")
                    prompt_parts.append(f"- IMPORTANT: Only mention these languages: {', '.join(top_repo_languages)}")

                if repo_skills.get("technical_skills"):
                    skills_list = repo_skills["technical_skills"][:8]
                    prompt_parts.append(f"- Technical skills demonstrated in this repository: {', '.join(skills_list)}")
                    prompt_parts.append(f"- IMPORTANT: Only mention these technical skills: {', '.join(skills_list)}")

                if repo_skills.get("frameworks"):
                    frameworks_list = repo_skills["frameworks"][:5]
                    prompt_parts.append(f"- Frameworks/tools used in this repository: {', '.join(frameworks_list)}")
                    prompt_parts.append(f"- IMPORTANT: Only mention these frameworks: {', '.join(frameworks_list)}")
                else:
                    prompt_parts.append("- IMPORTANT: No specific frameworks detected in this repository - do not mention any frameworks")

                # Only include repository-specific commit analysis
                if repo_commit_analysis and repo_commit_analysis.get("total_commits", 0) > 0:
                    prompt_parts.append("")
                    prompt_parts.append("REPOSITORY-SPECIFIC CONTRIBUTIONS:")
                    prompt_parts.append(f"- Number of commits to this repository: {repo_commit_analysis.get('total_commits', 0)}")

                    # Add repository-specific commit patterns if available
                    if repo_commit_analysis.get("patterns"):
                        patterns = repo_commit_analysis["patterns"]
                        if patterns.get("most_active_month"):
                            prompt_parts.append(f"- Most active development period: {patterns['most_active_month']}")

                # Add repository-specific user data if available
                if github_data.get("contributor_info"):
                    contributor = github_data["contributor_info"]
                    prompt_parts.append("")
                    prompt_parts.append("CONTRIBUTOR DETAILS FOR THIS REPOSITORY:")
                    prompt_parts.append(f"- Total contributions to this repository: {contributor.get('contributions', 0)} commits")
                    if contributor.get("full_name"):
                        prompt_parts.append(f"- Contributor: {contributor['full_name']}")

                prompt_parts.append("")
                prompt_parts.append("FINAL WARNING:")
                prompt_parts.append("- DO NOT mention any work outside of this specific repository")
                prompt_parts.append("- If information is limited, focus on what you do know about this repository")
                prompt_parts.append("- Stay focused on THIS repository's work only")

            else:
                prompt_parts.append("\nRepository information is not available for this specific repository.")

            # For repo_only context, skip ALL general profile logic
            # Jump directly to custom prompt and guidelines sections
            context_handled = True

        elif context_type == "repository_contributor":
            # Repository-contributor merged context - balance both
            repo_info = github_data.get("repository_info", {})
            if repo_info:
                prompt_parts.extend(
                    [
                        "\nFOCUS ON THEIR WORK IN THIS CONTEXT:",
                        f"- Project: {repo_info.get('name', 'Not provided')}",
                        f"- What it's about: {repo_info.get('description', 'Not provided')}",
                        f"- Main programming language: {repo_info.get('language', 'Not provided')}",
                        f"- Repository URL: {repository_url or 'Not provided'}",
                        "\nBalance their specific contributions to this repository with relevant aspects of their overall profile.",
                        "Emphasize how their work on this project demonstrates their broader skills and expertise.",
                    ]
                )
            else:
                prompt_parts.append("\nConsider both their specific project contributions and overall professional background.")
        if not context_handled and context_type == "profile":
            # Profile context (default) - only add if we haven't handled context-specific data and it's profile context
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
        # This section handles skills for contexts that haven't been fully handled by the repo_only block above
        if context_type == "profile":
            # Profile-based skills
            if languages:
                top_languages = [lang["language"] for lang in languages[:5]]
                prompt_parts.append(f"- Programming languages they work with: {', '.join(top_languages)}")

            if skills.get("technical_skills"):
                prompt_parts.append(f"- Technical skills: {', '.join(skills['technical_skills'][:10])}")

            if skills.get("frameworks"):
                prompt_parts.append(f"- Frameworks and tools: {', '.join(skills['frameworks'])}")

            if skills.get("domains"):
                prompt_parts.append(f"- Areas they specialize in: {', '.join(skills['domains'])}")

            # Add commit analysis insights with specific examples for profile
            if commit_analysis and commit_analysis.get("total_commits", 0) > 0:
                prompt_parts.append("\nWhat their overall coding work shows:")
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

        elif context_type == "repository_contributor":
            # Repository-contributor context - blend repository and profile data
            repo_languages = github_data.get("languages", [])
            repo_skills = github_data.get("skills", {})
            repo_commit_analysis = github_data.get("commit_analysis", {})

            if repo_languages:
                top_languages = [lang["language"] for lang in repo_languages[:5]]
                prompt_parts.append(f"- Programming languages they work with in this project: {', '.join(top_languages)}")

            if repo_skills.get("technical_skills"):
                prompt_parts.append(f"- Technical skills demonstrated in this project: {', '.join(repo_skills['technical_skills'][:10])}")

            if repo_skills.get("frameworks"):
                prompt_parts.append(f"- Frameworks and tools used in this project: {', '.join(repo_skills['frameworks'])}")

            if repo_skills.get("domains"):
                prompt_parts.append(f"- Areas they specialize in within this project: {', '.join(repo_skills['domains'])}")

            # Add repository-specific commit analysis for repository_contributor
            if repo_commit_analysis and repo_commit_analysis.get("total_commits", 0) > 0:
                prompt_parts.append("\nWhat their contributions to this project show:")
                specific_examples = self._extract_commit_examples(repo_commit_analysis)
                if specific_examples:
                    prompt_parts.append("\nSpecific examples of their work on this project:")
                    for example in specific_examples[:3]:
                        prompt_parts.append(f"- {example}")

                excellence_areas = repo_commit_analysis.get("excellence_areas", {})
                if excellence_areas.get("primary_strength"):
                    primary_strength = excellence_areas["primary_strength"].replace("_", " ").title()
                    prompt_parts.append(f"- Primary strength demonstrated in this project: {primary_strength}")

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

        # Add context-specific restrictions for repo_only
        if context_type == "repo_only":
            prompt_parts.extend(
                [
                    "",
                    "REPO-ONLY SPECIFIC GUIDELINES:",
                    "- ONLY discuss the specific repository mentioned above",
                    "- DO NOT reference any other repositories or projects",
                    "- DO NOT mention general GitHub profile information",
                    "- If you lack specific details about this repository, acknowledge that limitation",
                    "- Stay focused on what the person did in THIS repository only",
                    "- Do not extrapolate or assume work outside of this repository",
                    "- CRITICAL: If no frameworks are listed above, do not mention ANY frameworks",
                    "- CRITICAL: Only mention technologies that are explicitly listed in the repository data above",
                    "- CRITICAL: Do not infer or assume additional technologies based on general knowledge",
                ]
            )

        # Add guidelines based on length
        base_guidelines = [
            "\nGuidelines:",
            "- Write in first person as someone who has worked with this developer",
        ]

        # Add context-specific guidelines
        if context_type == "repo_only":
            base_guidelines.extend(
                [
                    "- Be specific about technical achievements and skills demonstrated in THIS SPECIFIC REPOSITORY",
                    "- Use natural, conversational language, like you're talking to a colleague.",
                    "- Focus on technical competence and collaborative abilities shown in this repository only",
                    "- Provide specific examples and positive anecdotes from their work in THIS repository",
                    "- DO NOT mention any company names, employers, or employment history",
                    "- DO NOT reference work outside of this specific repository",
                    "- Focus on technical skills and collaborative abilities demonstrated in this repository only",
                    "- Separate the recommendation into clear, distinct paragraphs to improve readability.",
                    f"- Target length: {self._get_length_guideline(length)} words",
                    "- Do not include any placeholders or template text",
                    "- Make it sound natural and personal, like a real recommendation",
                ]
            )
        else:
            base_guidelines.extend(
                [
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
            )

        # Add paragraph structure guidelines based on length
        if context_type == "repo_only":
            if length == "short":
                base_guidelines.extend(
                    [
                        "- Structure as 2 paragraphs: introduction with key skills from this repository and a specific example from their work here,",
                        " then a concluding positive anecdote about their contribution to this project.",
                        "- Keep it concise but impactful",
                        "- Focus on 1-2 key strengths demonstrated in this repository with concrete evidence",
                    ]
                )
            elif length == "medium":
                base_guidelines.extend(
                    [
                        "- Structure as 3 paragraphs: introduction to their work on this repository, 2-3 specific technical achievements in this project with examples,",
                        " and a concluding paragraph on personal qualities/collaboration shown in this repository with an anecdote.",
                        "- Provide 2-3 specific examples or achievements from this repository only",
                        "- Balance technical expertise with personal qualities demonstrated in this project",
                    ]
                )
            else:  # long
                base_guidelines.extend(
                    [
                        "- Structure as 4-5 paragraphs: introduction to their role in this repository, detailed technical background with 2-3 achievements in this project,",
                        " specific contributions/problem-solving in this repository, collaboration skills with an anecdote from this project,",
                        " and a strong conclusion about their impact on this repository.",
                        "- Include 3-4 detailed examples from this repository only",
                        "- Show their contributions and growth within this project",
                    ]
                )
        else:
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

        if analysis_context_type in ["repository", "repository_contributor", "repo_only"]:
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
            elif analysis_context_type == "repo_only":
                base_guidelines.insert(
                    3,
                    f"- ONLY focus on skills and technologies demonstrated in {repo_name}",
                )
                base_guidelines.insert(
                    4,
                    f"- DO NOT mention any work outside of {repo_name}",
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

    def build_option_prompt(self, base_prompt: str, custom_instruction: str, focus: str) -> str:
        """Build a customized prompt for a specific option."""
        focus_formatted = focus.replace("_", " ")
        return f"""{base_prompt}

FOR THIS VERSION, FOCUS ON:
{custom_instruction}

Create a recommendation that really highlights their {focus_formatted} skills while keeping it natural and conversational.
"""

    def build_refinement_prompt_for_regeneration(
        self,
        original_content: str,
        refinement_instructions: str,
        github_data: Dict[str, Any],
        recommendation_type: str,
        tone: str,
        length: str,
        analysis_context_type: str = "profile",
        repository_url: Optional[str] = None,
        exclude_keywords: Optional[list] = None,
    ) -> str:
        """Build prompt for regenerating a recommendation."""
        user_data = github_data.get("user_data", {})
        repository_info = github_data.get("repository_info", {})

        username = user_data.get("github_username")
        if not username and repository_info:
            # Only use repository owner as fallback if we don't have user_data
            username = repository_info.get("owner", {}).get("login")
        if not username:
            username = "the developer"

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

    def build_keyword_refinement_prompt(
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

    def build_readme_generation_prompt(
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

        prompt_parts = [
            f"Generate a comprehensive README.md file for the GitHub repository '{repo_name}'.",
            "",
            "REPOSITORY INFORMATION:",
            f"- Name: {repo_name}",
            f"- Description: {description}",
            f"- Primary Language: {repo_info.get('language', 'Unknown')}",
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

    def extract_title(self, content: str, username: str) -> str:
        """Extract or generate a title for the recommendation."""
        # Simple title extraction - could be enhanced
        if content:
            first_sentence = content.split(".")[0]
            if len(first_sentence) < 100:
                return first_sentence.strip()

        return f"Professional Recommendation for {username}"
