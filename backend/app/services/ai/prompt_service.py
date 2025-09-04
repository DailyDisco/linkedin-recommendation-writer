"""AI Prompt Service for building and formatting prompts with natural human storytelling."""

import logging
from typing import Any, Dict, List, Optional

from app.services.ai.human_story_generator import HumanStoryGenerator

logger = logging.getLogger(__name__)


class PromptService:
    """Service for building and formatting AI prompts with natural human storytelling."""

    def __init__(self):
        """Initialize prompt service with human story generator."""
        self.story_generator = HumanStoryGenerator()

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
        focus_keywords: Optional[List[str]] = None,
        focus_weights: Optional[Dict[str, float]] = None,
        analysis_context_type: str = "profile",
        repository_url: Optional[str] = None,
        display_name: Optional[str] = None,  # New parameter
    ) -> str:
        """Build the AI generation prompt."""

        user_data = github_data.get("user_data", {})
        languages = github_data.get("languages", [])
        skills = github_data.get("skills", {})
        commit_analysis = github_data.get("commit_analysis", {})
        repository_info = github_data.get("repository_info", {})

        # Determine the reference name for the person
        if display_name:  # Prioritize display_name if provided
            person_reference = display_name
        else:
            # Use the enhanced display name extraction method
            person_reference = self._extract_display_name(user_data)

            # Fallback to repository owner if we still don't have a good name
            if person_reference == "the developer" and repository_info:
                repo_owner = repository_info.get("owner", {}).get("login")
                if repo_owner:
                    extracted_name = self._extract_name_from_username(repo_owner)
                    person_reference = extracted_name if extracted_name else repo_owner

        # Build human narrative sections using story generator
        narrative_sections = self.story_generator.build_human_prompt_sections(github_data, analysis_context_type, display_name=person_reference)

        # Base prompt structure with storytelling approach
        prompt_parts = [
            narrative_sections["opening"][0].format(name=person_reference),  # Use opening from story generator
            f"Make it {tone} and suitable for {recommendation_type} purposes.",
            "",
            f"CRITICAL: Use '{person_reference}' as the person's name throughout the entire recommendation.",
            f"NEVER use placeholders like '[Colleague's Name]', '[Name]', or '[Person]' - always use '{person_reference}'.",
            f"Write the recommendation as if you know {person_reference} personally and have worked with them directly.",
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
            # ULTRA-STRICT: Build repository-only prompt with ZERO profile data access
            # CRITICAL: NO access to general profile data - only repository-specific data allowed
            logger.info("🔒 PROMPT SERVICE: REPO_ONLY mode - validating data isolation")
            logger.info(f"🔍 PROMPT SERVICE: Received github_data keys: {list(github_data.keys())}")
            if "user_data" in github_data:
                logger.info(f"🔍 PROMPT SERVICE: user_data: {github_data['user_data']}")
                # Validate that user_data only contains username
                user_data = github_data["user_data"]
                allowed_fields = {"github_username", "login"}
                for field in user_data:
                    if field not in allowed_fields and user_data[field]:
                        logger.warning(f"⚠️ PROMPT SERVICE: Unexpected user_data field '{field}' with value: {user_data[field]}")
            if "repo_contributor_stats" in github_data:
                logger.info(f"🔍 PROMPT SERVICE: repo_contributor_stats: {github_data['repo_contributor_stats']}")
            if "repository_info" in github_data:
                logger.info(f"🔍 PROMPT SERVICE: repository_info: {github_data['repository_info']}")
            if "languages" in github_data:
                logger.info(f"🔍 PROMPT SERVICE: languages count: {len(github_data['languages'])}")
            if "skills" in github_data:
                logger.info(f"🔍 PROMPT SERVICE: skills keys: {list(github_data['skills'].keys())}")

            # Log forbidden profile data fields that should NOT be present
            # Note: full_name is allowed as it's essential for personalized recommendations
            forbidden_fields = ["bio", "company", "location", "email", "followers", "following", "public_repos", "avatar_url", "organizations", "starred_repositories"]
            for field in forbidden_fields:
                if field in github_data.get("user_data", {}):
                    logger.error(f"🚨 CRITICAL: Forbidden profile field '{field}' found in repo_only data!")
                elif field in github_data:
                    logger.error(f"🚨 CRITICAL: Forbidden profile section '{field}' found in repo_only data!")

            # VALIDATION: Ensure no profile data is present in the data structure
            if self._contains_profile_data(github_data):
                logger.error("🚨 CRITICAL: Profile data detected in repo_only context - ABORTING")
                raise ValueError("Profile data contamination detected in repo_only context")

            # ADDITIONAL VALIDATION: Check final prompt for profile data leaks
            final_prompt = "\n".join(prompt_parts)
            prompt_validation = self._validate_prompt_for_profile_data(final_prompt)
            if not prompt_validation["is_valid"]:
                logger.error("🚨 CRITICAL: Profile data detected in final prompt - ABORTING")
                for issue in prompt_validation["issues"]:
                    logger.error(f"   • {issue}")
                raise ValueError(f"Profile data contamination detected in repo_only prompt: {prompt_validation['issues']}")

            # Use ONLY repository-specific data - NO general user profile access
            user_data = github_data.get("user_data", {})  # Basic identifying info only (username only)
            languages = github_data.get("languages", [])  # Repository-specific languages only
            skills = github_data.get("skills", {})  # Repository-specific skills only
            commit_analysis = github_data.get("commit_analysis", {})  # Repository-specific commits only

            repo_info = github_data.get("repository_info", {})
            repo_contributor_stats = github_data.get("repo_contributor_stats", {})

            logger.info(f"🔍 PROMPT SERVICE: Using repo_info: {repo_info.get('name', 'N/A') if repo_info else 'N/A'}")
            logger.info(f"🔍 PROMPT SERVICE: Using username: {user_data.get('github_username', 'N/A')}")

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
                        "- CRITICAL: Do not mention any personal details such as bio, company, or location unless directly relevant to contributions in this specific repository.",
                        "- CRITICAL: Do not reference the user's overall follower count or public repository count outside of this project.",
                        "- CRITICAL: Do not mention any starred repositories, organizations, or general profile information.",
                        "- CRITICAL: DO NOT infer or mention any technologies, languages, or frameworks (e.g., Go, Python, machine learning) that are NOT explicitly listed in the 'WHAT TO INCLUDE (ONLY FROM THIS REPOSITORY)' section above.",
                        "This includes their 'curiosity' or 'interest' in such unlisted technologies.",
                        "",
                        "WHAT TO INCLUDE (ONLY FROM THIS REPOSITORY):",
                    ]
                )

                # Use the explicitly filtered data sources (already set above)
                repo_languages = languages  # Already filtered to repository-specific
                repo_skills = skills  # Already filtered to repository-specific
                repo_commit_analysis = commit_analysis  # Already filtered to repository-specific

                if repo_languages:
                    top_repo_languages = [getattr(lang, "language", "") for lang in repo_languages[:3]]
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

                # Add human story elements from contributor summary
                contributor_summary = github_data.get("contributor_commit_summary", {})
                if contributor_summary and contributor_summary.get("total_commits", 0) > 0:
                    logger.info("🔍 PROMPT SERVICE: Adding human story elements from contributor summary")
                    prompt_parts.append("")
                    prompt_parts.append("PERSONAL OBSERVATIONS ABOUT THEIR WORK:")

                    # Convert technical data to human stories
                    stories = self.story_generator.convert_technical_to_story(github_data, context_type)
                    personality_traits = self.story_generator.infer_personality_traits(github_data.get("commit_analysis", {}))

                    # Add personality insights
                    if personality_traits:
                        for trait in personality_traits[:2]:
                            prompt_parts.append(f"- {trait['description']}")

                    # Add collaboration examples
                    if stories["collaboration_examples"]:
                        for example in stories["collaboration_examples"][:2]:
                            prompt_parts.append(f"- {example}")

                    # Extract summary data
                    summary_data = contributor_summary.get("summary", {})
                    technical_focus = summary_data.get("technical_focus", [])

                    # Add work patterns
                    work_patterns = summary_data.get("work_patterns", [])
                    if work_patterns:
                        prompt_parts.append(f"- Work patterns: {', '.join(work_patterns[:2])}")

                    # Add collaboration patterns
                    collaboration_patterns = summary_data.get("collaboration_patterns", [])
                    if collaboration_patterns:
                        prompt_parts.append(f"- Collaboration approach: {', '.join(collaboration_patterns[:2])}")

                    logger.info(f"✅ Added contributor summary: {contributor_summary.get('total_commits', 0)} commits, {len(technical_focus)} focus areas")

                # Legacy contributor stats (if no commit summary available)
                elif repo_contributor_stats:
                    logger.info("🔍 PROMPT SERVICE: Adding legacy repo_contributor_stats to prompt")
                    prompt_parts.append("")
                    prompt_parts.append("CONTRIBUTOR DETAILS:")
                    prompt_parts.append(f"- Total contributions: {repo_contributor_stats.get('contributions_to_repo', 0)} commits")
                    prompt_parts.append(f"- Contributor: {repo_contributor_stats.get('username', 'Unknown')}")
                    logger.info(
                        f"🔍 PROMPT SERVICE: Added legacy contributor stats: username={repo_contributor_stats.get('username')}, contributions={repo_contributor_stats.get('contributions_to_repo', 0)}"
                    )

                prompt_parts.append("")
                prompt_parts.append("STORYTELLING GUIDELINES:")
                prompt_parts.append("- Write as someone who has genuinely worked with this person")
                prompt_parts.append("- Use phrases like 'I've seen them...', 'They have a knack for...', 'What I appreciate most is...'")
                prompt_parts.append("- Focus on personal observations and specific examples from their work")
                prompt_parts.append("- Emphasize their character traits and working style, not just technical skills")
                prompt_parts.append("- Tell a story about their contributions, don't list technical metrics")
                prompt_parts.append("- Make it sound like a genuine colleague endorsement")
                prompt_parts.append("- NEVER mention commit numbers, PR counts, or technical IDs")
                prompt_parts.append("- Transform technical achievements into workplace stories")
                prompt_parts.append("- Focus on outcomes and impact, not process metrics")

                # LOG THE COMPLETE PROMPT FOR DEBUGGING
                final_prompt = "\n".join(prompt_parts)
                logger.info("🔍 PROMPT SERVICE: FINAL PROMPT PREVIEW (first 500 chars):")
                logger.info(f"🔍 PROMPT SERVICE: {final_prompt[:500]}...")
                logger.info(f"🔍 PROMPT SERVICE: Total prompt length: {len(final_prompt)} characters")

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
            # Only include full name if display_name is not provided (to avoid duplication)
            if user_data.get("full_name") and not display_name:
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

        # Add human-friendly technical context for profile mode
        if context_type == "profile":
            prompt_parts.append("")
            prompt_parts.append("NATURAL OBSERVATIONS ABOUT THEIR TECHNICAL ABILITIES:")

            # Use story generator for natural technical descriptions
            stories = self.story_generator.convert_technical_to_story(github_data, context_type)
            if stories["technical_examples"]:
                for example in stories["technical_examples"][:3]:
                    prompt_parts.append(f"- {example}")

            # Add personality and collaboration insights
            if stories["personality_insights"]:
                prompt_parts.append("")
                prompt_parts.append("PERSONAL QUALITIES I'VE NOTICED:")
                for insight in stories["personality_insights"][:2]:
                    prompt_parts.append(f"- {insight}")

            # Add natural commit analysis insights for profile
            if commit_analysis and commit_analysis.get("total_commits", 0) > 0:
                prompt_parts.append("\nWHAT I'VE OBSERVED FROM THEIR OVERALL WORK:")

                # Use story generator to create natural examples
                stories = self.story_generator.convert_technical_to_story(github_data, context_type)
                personality_traits = self.story_generator.infer_personality_traits(commit_analysis)

                # Add achievements as natural observations
                if stories["achievements"]:
                    for achievement in stories["achievements"][:2]:
                        prompt_parts.append(f"- {achievement}")

                # Add personality insights
                if personality_traits:
                    for trait in personality_traits[:2]:
                        prompt_parts.append(f"- {trait['description']}")

                # Add collaboration examples
                if stories["collaboration_examples"]:
                    for example in stories["collaboration_examples"][:1]:
                        prompt_parts.append(f"- {example}")

        elif context_type == "repository_contributor":
            # Repository-contributor context - blend repository and profile data
            repo_languages = github_data.get("languages", [])
            repo_skills = github_data.get("skills", {})
            repo_commit_analysis = github_data.get("commit_analysis", {})

            if repo_languages:
                top_languages = [getattr(lang, "language", "") for lang in repo_languages[:5]]
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

        # Add focus keywords with weights for enhanced customization
        if focus_keywords:
            focus_parts = ["\nFOCUS AREAS TO EMPHASIZE:"]
            for keyword in focus_keywords:
                weight = focus_weights.get(keyword, 1.0) if focus_weights else 1.0
                weight_text = ""
                if weight > 1.5:
                    weight_text = " (HIGH PRIORITY - dedicate significant attention to this)"
                elif weight > 1.2:
                    weight_text = " (MODERATE PRIORITY - give extra emphasis to this)"
                elif weight < 0.8:
                    weight_text = " (OPTIONAL - mention if relevant but not required)"

                focus_parts.append(f"- {keyword}{weight_text}")
            prompt_parts.extend(focus_parts)

        # Add keywords to exclude with strict enforcement
        if exclude_keywords:
            prompt_parts.extend(
                [
                    "\nSTRICT EXCLUSION REQUIREMENTS:",
                    f"- ABSOLUTELY DO NOT mention any of these terms: {', '.join(exclude_keywords)}",
                    "- If any of these terms appear in your knowledge, rephrase completely to avoid them",
                    "- Even subtle references or synonyms of these terms are prohibited",
                    "- If the topic would naturally involve these terms, find alternative ways to express the same concepts",
                ]
            )

        # Add custom prompt if provided
        if custom_prompt:
            prompt_parts.append(f"\nAdditional information to include: {custom_prompt}")

        # Add context-specific storytelling guidelines
        if context_type == "repo_only":
            prompt_parts.extend(
                [
                    "",
                    "HUMAN STORYTELLING APPROACH:",
                    "- Write as if you worked alongside them on this specific project",
                    "- Use personal observations: 'I watched them...', 'They consistently...'",
                    "- Turn technical achievements into workplace stories",
                    "- Focus on character traits revealed through their work",
                    "- Describe the impact of their contributions, not the process",
                    "- Make it feel like a genuine colleague endorsement",
                    "- Avoid any technical jargon, metrics, or commit references",
                    "- Tell stories about what they accomplished, not how they coded",
                    "- Emphasize their reliability, problem-solving, and collaboration",
                ]
            )

        # Add natural formatting and storytelling guidelines
        base_guidelines = [
            "\nNATURAL RECOMMENDATION WRITING INSTRUCTIONS:",
            "- Write as a colleague who genuinely knows and respects this person",
            "- Use conversational, warm language with personal observations",
            "- **MANDATORY**: Structure with clear paragraph breaks using DOUBLE NEWLINES",
            "- **FORMAT REQUIREMENT**: Each paragraph MUST be separated by exactly TWO newline characters (\\n\\n)",
            "- **PARAGRAPH STRUCTURE**: Create 3-4 distinct paragraphs telling a cohesive story",
            "- **STORYTELLING FLOW**: Opening impression → Specific examples → Character qualities → Strong endorsement",
            "- **NATURAL LANGUAGE**: Use 'I've seen...', 'They consistently...', 'What impresses me...' style phrasing",
            "- **AVOID**: Technical metrics, commit counts, PR numbers, or any robotic language",
            "- **FOCUS**: Personal qualities, work impact, and genuine professional admiration",
        ]

        # Add context-specific natural writing guidelines
        if context_type == "repo_only":
            base_guidelines.extend(
                [
                    "- Write about specific project work with genuine enthusiasm and respect",
                    "- Use storytelling: 'During their work on this project, I noticed...'",
                    "- Transform technical skills into character observations",
                    "- Share personal anecdotes about their working style and reliability",
                    "- Describe the positive impact they had on the project outcome",
                    "- Highlight their problem-solving mindset and collaborative spirit",
                    "- Make every sentence sound like something a real colleague would say",
                    "- **HUMAN TONE**: Write with warmth, respect, and genuine professional admiration",
                    "- **STORY STRUCTURE**: Opening connection → Specific examples → Character traits → Strong endorsement",
                    "- **NATURAL PHRASING**: 'I've had the pleasure...', 'What stands out...', 'They consistently...'",
                    "- **PARAGRAPH COUNT**: Create exactly 3 compelling paragraphs",
                    f"- Target length: {self._get_length_guideline(length)} words",
                    "- Write as if recommending a valued colleague to a friend",
                ]
            )
        else:
            base_guidelines.extend(
                [
                    "- Write with genuine professional admiration and personal connection",
                    "- Share specific stories and examples from your working relationship",
                    "- Focus on character qualities revealed through their technical work",
                    "- Describe the positive impact they've had on projects and teams",
                    "- DO NOT mention company names, employers, or employment history",
                    "- Transform technical skills into personal qualities and work style",
                    "- **AUTHENTIC VOICE**: Write as someone who truly values this person's contributions",
                    "- **PERSONAL TOUCH**: Use phrases like 'I've always admired...', 'Time and again...'",
                    "- **STORY-DRIVEN**: Each paragraph should tell part of their professional story",
                    "- **WARM TONE**: Professional but personal, like recommending a respected friend",
                    "- **PARAGRAPH COUNT**: Create exactly 3 engaging paragraphs",
                    f"- Target length: {self._get_length_guideline(length)} words",
                    "- Write as if you genuinely want to help them succeed",
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

    def build_option_prompt(self, base_prompt: str, custom_instruction: str, focus: str, focus_keywords: Optional[List[str]] = None, focus_weights: Optional[Dict[str, float]] = None) -> str:
        """Build a customized prompt for a specific option with enhanced focus control."""
        focus_formatted = focus.replace("_", " ")

        # Build focus enhancement section
        focus_enhancement = f"""
FOR THIS VERSION, FOCUS ON:
{custom_instruction}

Create a recommendation that really highlights their {focus_formatted} skills while keeping it natural and conversational."""

        # Add specific keyword focus if provided
        if focus_keywords:
            focus_enhancement += "\n\nADDITIONAL FOCUS AREAS:"
            for keyword in focus_keywords:
                weight = focus_weights.get(keyword, 1.0) if focus_weights else 1.0
                priority_text = ""
                if weight > 1.5:
                    priority_text = " - PRIORITY: Dedicate significant attention"
                elif weight > 1.2:
                    priority_text = " - PRIORITY: Give extra emphasis"
                focus_enhancement += f"\n- {keyword}{priority_text}"

        return f"{base_prompt}{focus_enhancement}"

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
        display_name: Optional[str] = None,
    ) -> str:
        """Build prompt for regenerating a recommendation."""
        user_data = github_data.get("user_data", {})

        # Use display_name if provided, otherwise extract it for consistent naming
        if display_name is None:
            display_name = self._extract_display_name(user_data)

        person_reference = display_name

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
- Person: {person_reference}
- Type: {recommendation_type}
- Tone: {tone}
- Target Length: {target_length} words{exclude_section}

**CRITICAL FORMATTING REQUIREMENTS:**
- **MANDATORY**: Structure your response with clear paragraph breaks using DOUBLE NEWLINES
- **FORMAT REQUIREMENT**: Each paragraph MUST be separated by exactly TWO newline characters (\\n\\n)
- **PARAGRAPH STRUCTURE**: Create 3 distinct paragraphs, each containing 2-4 complete sentences
- **DO NOT** create single-line breaks within paragraphs - only double newlines between paragraphs
- **OUTPUT FORMAT**: Paragraph1 text here.\\n\\nParagraph2 text here.\\n\\nParagraph3 text here.
- **VERIFICATION**: Ensure there are exactly 2 blank lines between each paragraph block

Please rewrite the recommendation with these changes while keeping it:
1. Authentic and real-sounding
2. The right tone and length
3. Focused on their technical and teamwork skills
4. Natural and conversational
5. Properly formatted with paragraph breaks as specified above

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

    def extract_title(self, content: str, username: str, first_name: Optional[str] = None, display_name: Optional[str] = None) -> str:
        """Extract or generate a title for the recommendation using first name when possible."""
        # Simple title extraction - could be enhanced
        if content:
            first_sentence = content.split(".")[0]
            if len(first_sentence) < 100:
                return first_sentence.strip()

        # Prioritize display_name, then first_name, then try to extract name from username
        if display_name:
            person_name = display_name
        elif first_name:
            person_name = first_name
        else:
            # Try to extract a better name from username
            extracted_name = self._extract_name_from_username(username)
            person_name = extracted_name if extracted_name else username

        return f"Professional Recommendation for {person_name}"

    def _contains_profile_data(self, data: Dict[str, Any]) -> bool:
        """Check if data contains general profile information that should be excluded in repo_only mode."""
        # Define profile data fields that should NEVER appear in repo_only context
        # Note: full_name is allowed as it's essential for personalized recommendations
        profile_indicators = [
            "bio",
            "company",
            "location",
            "email",
            "blog",
            "followers",
            "following",
            "public_repos",
            "public_gists",
            "starred_repositories",
            "organizations",
            "starred_technologies",
            "repositories",
            "name",  # Keep this since we use full_name instead
            "avatar_url",
        ]

        # Check user_data section
        user_data = data.get("user_data", {})
        for field in profile_indicators:
            if field in user_data:
                logger.debug(f"🚨 PROFILE DATA DETECTED: Found '{field}' in user_data for repo_only context with value: {user_data[field]}")
                return True

        # Check for contributor_info (old structure that might contain profile data)
        if data.get("contributor_info"):
            contributor_info = data["contributor_info"]
            for field in ["full_name", "email", "bio", "company", "location", "avatar_url"]:
                if field in contributor_info:
                    logger.debug(f"🚨 PROFILE DATA DETECTED: Found '{field}' in contributor_info for repo_only context with value: {contributor_info[field]}")
                    return True

        # Check for other potential profile data sections
        profile_sections = ["organizations", "starred_technologies", "starred_repositories"]
        for section in profile_sections:
            if data.get(section):
                logger.debug(f"🚨 PROFILE DATA DETECTED: Found '{section}' section in repo_only context with value: {data[section]}")
                return True

        return False

    def _validate_prompt_for_profile_data(self, prompt: str) -> Dict[str, Any]:
        """Validate that the final prompt doesn't contain profile data (but allows profile keywords in instructions)."""
        validation_result = {"is_valid": True, "issues": [], "warnings": []}

        prompt_lower = prompt.lower()

        # Profile data keywords that should never appear in repo_only prompts
        # Note: 'linkedin' is excluded because it's part of legitimate "LinkedIn recommendation" context
        profile_keywords = [
            "bio",
            "company",
            "location",
            "email",
            "blog",
            "followers",
            "following",
            "public repos",
            "public_repos",
            "starred",
            "organizations",
            "orgs",
            "full name",
            "full_name",
            "avatar",
            "hireable",
            "website",
            "twitter",
        ]

        # Distinguish between main content and instructions
        content_start = prompt_lower.find("strict instructions:")
        if content_start == -1:
            content_start = len(prompt)  # If no instructions section, check whole prompt

        main_content = prompt[:content_start]  # Only check the part before instructions
        instruction_content = prompt[content_start:]  # The instructions/warnings part

        found_in_content = []
        found_in_instructions = []

        # Check profile keywords
        for keyword in profile_keywords:
            if keyword in main_content.lower():
                found_in_content.append(keyword)
            elif keyword in instruction_content.lower():
                found_in_instructions.append(keyword)

        # Profile keywords in main content are BAD (actual profile data)
        if found_in_content:
            validation_result["is_valid"] = False
            for keyword in found_in_content:
                # Get context around the keyword in main content
                keyword_index = main_content.lower().find(keyword)
                start = max(0, keyword_index - 50)
                end = min(len(main_content), keyword_index + len(keyword) + 50)
                context = main_content[start:end].replace("\n", " ").strip()
                logger.debug(f"🚨 PROMPT VALIDATION: Found profile data '{keyword}' in main content: '{context}'")
                validation_result["issues"].append(f"Profile data '{keyword}' found in main content: '...{context}...'")

        # Profile keywords in instructions are OK (they're warnings to prevent AI from using profile data)
        if found_in_instructions:
            for keyword in found_in_instructions:
                logger.debug(f"✅ PROMPT VALIDATION: Profile keyword '{keyword}' found in instructions (OK)")
            validation_result["warnings"].extend([f"Profile keyword '{keyword}' found in instructions (OK - this prevents AI from using profile data)" for keyword in found_in_instructions])

        # Check for specific patterns that indicate profile data in main content only
        import re

        profile_patterns = [
            r"\d+\s+followers",  # "123 followers"
            r"\d+\s+following",  # "456 following"
            r"\d+\s+public\s+repos",  # "78 public repos"
            r"@[\w.-]+\s",  # Email-like patterns
        ]

        for pattern in profile_patterns:
            matches = re.findall(pattern, main_content, re.IGNORECASE)
            if matches:
                validation_result["is_valid"] = False
                logger.debug(f"🚨 PROMPT VALIDATION: Found profile pattern '{pattern}' in main content: {matches[:3]}...")
                validation_result["issues"].append(f"Profile pattern '{pattern}' found in main content: {matches[:3]}...")

        # Check for common profile section headers in main content
        profile_headers = ["about me", "contact", "personal info", "background", "experience", "education", "social media"]

        for header in profile_headers:
            if header in main_content.lower():
                logger.debug(f"⚠️ PROMPT VALIDATION: Potential profile header '{header}' found in main content")
                validation_result["warnings"].append(f"Potential profile header '{header}' found in main content")

        return validation_result

    def _extract_first_name(self, full_name: str) -> str:
        """Extract first name from full name with enhanced parsing."""
        if not full_name:
            return ""

        # Clean and normalize the full name
        full_name = full_name.strip()
        if not full_name:
            return ""

        # Handle common patterns and edge cases
        import re

        # Remove common prefixes and suffixes
        prefixes = ["mr", "mrs", "ms", "dr", "prof", "professor"]
        suffixes = ["jr", "sr", "ii", "iii", "iv", "v", "phd", "md"]

        # Split into parts
        parts = full_name.lower().split()
        cleaned_parts = []

        for part in parts:
            # Remove punctuation
            clean_part = re.sub(r"[^\w]", "", part)
            if clean_part and clean_part not in prefixes and clean_part not in suffixes:
                cleaned_parts.append(clean_part)

        if not cleaned_parts:
            return ""

        # Return the first meaningful part, properly capitalized
        first_name = cleaned_parts[0]

        # Handle special cases like hyphenated names (take first part)
        if "-" in first_name:
            first_name = first_name.split("-")[0]

        # Capitalize properly
        return first_name.capitalize()

    def _extract_display_name(self, user_data: Dict[str, Any]) -> str:
        """Extract the best display name for the user from available data."""
        # Priority: full_name first name > username-derived name > username > fallback

        full_name = user_data.get("full_name", "")
        if full_name:
            first_name = self._extract_first_name(full_name)
            if first_name:
                return first_name

        # Fallback to username as-is (don't try to extract name from username)
        username = user_data.get("github_username", "")
        if username:
            return username

        return "the developer"

    def _extract_name_from_username(self, username: str) -> str:
        """Extract a likely first name from username patterns with enhanced detection."""
        if not username:
            return ""

        import re

        # Extended common name patterns
        name_patterns = {
            "john": "John",
            "jane": "Jane",
            "mike": "Mike",
            "michael": "Michael",
            "chris": "Chris",
            "christopher": "Christopher",
            "alex": "Alex",
            "alexander": "Alexander",
            "david": "David",
            "dave": "Dave",
            "sarah": "Sarah",
            "sara": "Sara",
            "james": "James",
            "jim": "Jim",
            "robert": "Robert",
            "rob": "Rob",
            "bob": "Bob",
            "william": "William",
            "will": "Will",
            "bill": "Bill",
            "elizabeth": "Elizabeth",
            "liz": "Liz",
            "beth": "Beth",
            "richard": "Richard",
            "rick": "Rick",
            "dick": "Dick",
            "jennifer": "Jennifer",
            "jen": "Jen",
            "jenny": "Jenny",
            "daniel": "Daniel",
            "dan": "Dan",
            "matthew": "Matthew",
            "matt": "Matt",
            "anthony": "Anthony",
            "tony": "Tony",
            "mark": "Mark",
            "steven": "Steven",
            "steve": "Steve",
            "paul": "Paul",
            "andrew": "Andrew",
            "andy": "Andy",
            "joshua": "Joshua",
            "josh": "Josh",
            "kenneth": "Kenneth",
            "ken": "Ken",
            "kevin": "Kevin",
            "brian": "Brian",
            "george": "George",
            "edward": "Edward",
            "ed": "Ed",
            "eddie": "Eddie",
            "ronald": "Ronald",
            "ron": "Ron",
            "timothy": "Timothy",
            "tim": "Tim",
            "jason": "Jason",
            "jeffrey": "Jeffrey",
            "jeff": "Jeff",
            "ryan": "Ryan",
            "jacob": "Jacob",
            "jake": "Jake",
            "gary": "Gary",
            "nicholas": "Nicholas",
            "nick": "Nick",
            "eric": "Eric",
            "jonathan": "Jonathan",
            "stephen": "Stephen",
            "larry": "Larry",
            "justin": "Justin",
            "scott": "Scott",
            "brandon": "Brandon",
            "benjamin": "Benjamin",
            "ben": "Ben",
            "samuel": "Samuel",
            "sam": "Sam",
            "gregory": "Gregory",
            "greg": "Greg",
            "patrick": "Patrick",
            "pat": "Pat",
            "frank": "Frank",
            "raymond": "Raymond",
            "ray": "Ray",
            "jack": "Jack",
            "dennis": "Dennis",
            "jerry": "Jerry",
            "tyler": "Tyler",
            "aaron": "Aaron",
            "jose": "Jose",
            "henry": "Henry",
            "adam": "Adam",
            "douglas": "Douglas",
            "doug": "Doug",
            "nathan": "Nathan",
            "nate": "Nate",
            "peter": "Peter",
            "pete": "Pete",
            "zachary": "Zachary",
            "zach": "Zach",
            "kyle": "Kyle",
            "noah": "Noah",
            "alan": "Alan",
            "ethan": "Ethan",
            "thomas": "Thomas",
            "tom": "Tom",
            "tommy": "Tommy",
            "joe": "Joe",
            "joseph": "Joseph",
        }

        username_lower = username.lower()

        # Direct match
        if username_lower in name_patterns:
            return name_patterns[username_lower]

        # Check if username starts with a known name
        for pattern, name in name_patterns.items():
            if username_lower.startswith(pattern):
                return name

        # Try to extract from camelCase or PascalCase patterns
        # e.g., JohnSmith123 -> John, camelCaseUser -> camel
        camel_match = re.match(r"^([A-Z][a-z]+)", username)
        if camel_match:
            potential_name = camel_match.group(1).lower()
            if potential_name in name_patterns:
                return name_patterns[potential_name]
            elif len(potential_name) >= 3:
                return potential_name.capitalize()

        # Handle underscores and hyphens (take first part)
        # e.g., john_doe -> john, mary-jane -> mary
        separator_parts = re.split(r"[_\-]", username_lower)
        if len(separator_parts) > 1 and separator_parts[0]:
            first_part = separator_parts[0]
            if first_part in name_patterns:
                return name_patterns[first_part]
            elif len(first_part) >= 3:
                return first_part.capitalize()

        # Clean username and try to extract meaningful first part
        # Remove numbers and special characters
        clean_username = re.sub(r"[0-9_\-\.\@\+]+", "", username)

        if len(clean_username) >= 3:
            # Check if it's a recognizable name pattern
            clean_lower = clean_username.lower()
            if clean_lower in name_patterns:
                return name_patterns[clean_lower]

            # Try first 3-8 characters as potential name
            for length in range(min(8, len(clean_username)), 2, -1):
                potential = clean_lower[:length]
                if potential in name_patterns:
                    return name_patterns[potential]

            # Last resort: capitalize the first part if it looks name-like
            if clean_username.isalpha() and 3 <= len(clean_username) <= 12:
                return clean_username.capitalize()

        return ""
