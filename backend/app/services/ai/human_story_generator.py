"""Human Story Generator for creating natural, human-like recommendation narratives."""

import logging
import random
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class HumanStoryGenerator:
    """Service for transforming technical data into human stories and narratives."""

    def __init__(self):
        """Initialize the story generator with narrative templates and patterns."""
        self.personality_indicators = {
            "detail_oriented": {
                "patterns": ["frequent_small_commits", "thorough_testing", "documentation_focus"],
                "descriptions": ["incredibly detail-oriented and methodical", "leaves no stone unturned", "thorough and precise in their work", "pays attention to the little details that matter"],
            },
            "strategic_thinker": {
                "patterns": ["large_feature_commits", "architecture_focus", "planning_ahead"],
                "descriptions": [
                    "thinks strategically and plans ahead",
                    "sees the big picture while handling the details",
                    "approaches problems with a clear architectural vision",
                    "builds solutions that scale",
                ],
            },
            "problem_solver": {
                "patterns": ["bug_fixing", "optimization", "troubleshooting"],
                "descriptions": [
                    "the person you want when something needs to be fixed",
                    "persistent and thorough when tackling tough problems",
                    "has a knack for getting to the root of issues",
                    "turns complex problems into elegant solutions",
                ],
            },
            "collaborator": {
                "patterns": ["high_pr_success", "code_reviews", "team_coordination"],
                "descriptions": [
                    "easy to work with and writes clean code",
                    "collaborates effectively with the entire team",
                    "provides thoughtful feedback and suggestions",
                    "makes everyone around them better",
                ],
            },
            "reliable": {
                "patterns": ["consistent_timing", "regular_contributions", "follow_through"],
                "descriptions": [
                    "you can count on them to deliver quality work regularly",
                    "reliable and professional in everything they do",
                    "consistently delivers on their commitments",
                    "someone you can depend on",
                ],
            },
            "innovative": {
                "patterns": ["new_technologies", "creative_solutions", "experimentation"],
                "descriptions": [
                    "brings fresh perspectives and creative solutions",
                    "not afraid to explore new technologies and approaches",
                    "innovates while keeping practical considerations in mind",
                    "pushes boundaries in thoughtful ways",
                ],
            },
            "mentor": {
                "patterns": ["documentation_focus", "code_reviews", "helping_others", "knowledge_sharing"],
                "descriptions": [
                    "always takes time to help teammates understand complex problems",
                    "naturally mentors others and shares knowledge generously",
                    "builds up the whole team through patient guidance",
                    "creates learning opportunities for everyone around them",
                    "explains complex concepts in ways that just make sense",
                ],
            },
            "architect": {
                "patterns": ["design_patterns", "system_architecture", "long_term_planning", "scalability_focus"],
                "descriptions": [
                    "thinks several steps ahead when designing systems",
                    "has an intuitive sense for scalable architecture",
                    "balances current needs with future flexibility",
                    "designs solutions that stand the test of time",
                    "sees connections between different parts of the system that others miss",
                ],
            },
            "communicator": {
                "patterns": ["clear_commit_messages", "good_documentation", "PR_discussions", "team_updates"],
                "descriptions": [
                    "explains complex technical concepts in ways everyone can understand",
                    "bridges the gap between technical and non-technical stakeholders",
                    "writes code that tells a clear story",
                    "turns technical jargon into accessible insights",
                    "makes sure everyone stays on the same page",
                ],
            },
            "optimizer": {
                "patterns": ["performance_improvements", "code_optimization", "efficiency_focus"],
                "descriptions": [
                    "has an eye for making things run faster and smoother",
                    "finds bottlenecks others miss and eliminates them elegantly",
                    "thinks about performance from the ground up",
                    "makes our systems more efficient without sacrificing clarity",
                ],
            },
            "learner": {
                "patterns": ["technology_exploration", "skill_diversification", "continuous_improvement"],
                "descriptions": [
                    "constantly growing and exploring new approaches",
                    "brings fresh ideas from different technologies and domains",
                    "never stops learning and improving their craft",
                    "adapts quickly to new tools and methodologies",
                ],
            },
        }

        self.conversational_mappings = {
            "technical_skills": {
                "robots": ["demonstrates expertise in", "shows proficiency with", "utilizes technologies including", "has technical competency in"],
                "humans": ["they're really skilled with", "knows their way around", "has a solid grasp of", "works effectively with", "is comfortable working with"],
            },
            "contributions": {
                "robots": ["shows consistent contribution patterns", "demonstrates regular development activity", "maintains steady output metrics"],
                "humans": [
                    "consistently delivers quality work",
                    "you can count on them for regular contributions",
                    "always comes through with solid work",
                    "maintains a steady pace of meaningful contributions",
                ],
            },
            "problem_solving": {
                "robots": ["exhibits problem-solving capabilities", "demonstrates analytical thinking", "shows debugging proficiency"],
                "humans": [
                    "has a real talent for solving tough problems",
                    "digs deep to understand what's really going on",
                    "approaches challenges with patience and insight",
                    "turns roadblocks into stepping stones",
                ],
            },
            "code_quality": {
                "robots": ["maintains code quality standards", "follows best practices", "demonstrates clean code principles"],
                "humans": [
                    "writes code that's clean and easy to understand",
                    "cares about doing things the right way",
                    "produces work that other developers appreciate",
                    "maintains high standards without being rigid",
                ],
            },
        }

        self.narrative_openings = {
            "profile": [
                "I've had the pleasure of working with {name} and can confidently say",
                "Having collaborated with {name} on multiple projects, I can attest that",
                "In my experience working alongside {name}, I've consistently observed that",
                "{name} is one of those developers who truly stands out, and here's why",
            ],
            "repo_only": [
                "During their work on {project_name}, I watched {name}",
                "I had the opportunity to see {name}'s contributions to {project_name} firsthand, and",
                "Working with {name} on {project_name} gave me great insight into",
                "{name}'s work on {project_name} really demonstrated",
            ],
        }

        self.narrative_bridges = [
            "What really stands out about their approach is",
            "Beyond the technical skills, what I appreciate most is",
            "Time and again, I've seen them",
            "What makes them particularly valuable is",
            "One thing that consistently impresses me is",
        ]

        self.narrative_closings = [
            "I'd recommend them without hesitation for any team looking for",
            "Any organization would be lucky to have someone with",
            "They'd be a tremendous asset to any team that values",
            "I can't think of a better person to have on your team when you need",
        ]

        # Story templates for different scenarios
        self.story_templates = {
            "first_impression": [
                "When I first started working with {name}, what struck me was {trait}",
                "I knew {name} was special from our very first project together",
                "From day one, {name} brought something unique to our team - {trait}",
                "My initial impression of {name} was confirmed time and again: {trait}",
            ],
            "specific_incident": [
                "There was this challenging project where {name} {action} and {result}",
                "I'll never forget when {name} {action} - it completely {impact}",
                "During a particularly tough deadline, {name} {action}, which {outcome}",
                "One incident that really stands out: {name} {action} and {result}",
            ],
            "growth_observation": [
                "Over the months working together, I watched {name} evolve from {before} to {after}",
                "What impressed me most was seeing {name} tackle {challenge} and emerge {outcome}",
                "I've seen {name} grow tremendously, especially when {situation} - they went from {before} to {after}",
            ],
            "team_impact": [
                "The whole team dynamic changed when {name} {contribution}",
                "Everyone started {behavior_change} after seeing how {name} approached {situation}",
                "Our team's {metric} improved significantly because {name} {action}",
                "You could feel the difference in team morale whenever {name} {contribution}",
            ],
            "problem_solving_story": [
                "When we hit that major {problem_type}, {name} didn't panic - they {approach} and {result}",
                "I remember this complex {issue_type} that had everyone stumped, but {name} {solution_approach}",
                "During our worst production issue, {name} {action} while others were {contrast}, ultimately {outcome}",
            ],
            "collaboration_story": [
                "What I love about working with {name} is how they {collaboration_style} - it makes {impact}",
                "In code reviews, {name} has this way of {feedback_style} that helps everyone {improvement}",
                "During pair programming sessions, {name} {teaching_approach}, which always results in {outcome}",
            ],
        }

        # Relationship contexts for different professional dynamics
        self.relationship_contexts = {
            "peer": {
                "openings": [
                    "Working alongside {name}",
                    "As a colleague of {name}",
                    "Having collaborated with {name}",
                    "In my experience working with {name}",
                ],
                "perspectives": ["peer-level", "equal partnership", "mutual respect"],
                "voice_patterns": ["we tackled", "together we", "both of us", "our team"],
            },
            "mentor": {
                "openings": [
                    "I've had the privilege of mentoring {name}",
                    "Watching {name} grow under my guidance",
                    "As {name}'s mentor, I've observed",
                    "I've been fortunate to guide {name}",
                ],
                "perspectives": ["growth-focused", "developmental", "nurturing"],
                "voice_patterns": ["I watched them", "they learned", "their development", "their growth"],
            },
            "mentee": {
                "openings": [
                    "Learning from {name} has been",
                    "{name} taught me",
                    "Under {name}'s guidance, I learned",
                    "Working under {name} showed me",
                ],
                "perspectives": ["learning-focused", "appreciative", "growth-minded"],
                "voice_patterns": ["they showed me", "I learned from them", "they taught me", "under their guidance"],
            },
            "team_lead": {
                "openings": [
                    "As team lead, I can say {name}",
                    "Leading a team with {name} on it",
                    "From a leadership perspective, {name}",
                    "Managing {name} has been",
                ],
                "perspectives": ["leadership-focused", "results-oriented", "team-building"],
                "voice_patterns": ["they delivered", "their contribution", "team performance", "project success"],
            },
        }

        # Advanced robotic pattern detection
        self.robotic_patterns = {
            "corporate_speak": [
                "leverage",
                "utilize",
                "implement solutions",
                "deliver value",
                "drive results",
                "optimize outcomes",
                "facilitate",
                "streamline",
                "synergize",
                "operationalize",
                "monetize",
                "ideate",
            ],
            "academic_language": [
                "demonstrate proficiency",
                "exhibit competency",
                "possess knowledge",
                "display aptitude",
                "manifest skills",
                "evidence suggests",
                "data indicates",
                "research shows",
                "studies demonstrate",
            ],
            "ai_tells": [
                "it's worth noting",
                "it should be mentioned",
                "importantly",
                "additionally",
                "furthermore",
                "moreover",
                "notably",
                "it's important to note",
                "one should consider",
                "it must be said",
            ],
            "measurement_language": [
                "commits per day",
                "lines of code",
                "productivity metrics",
                "efficiency ratings",
                "performance indicators",
                "KPIs",
                "benchmarks",
                "quantifiable results",
                "statistical analysis",
            ],
            "buzzword_overuse": ["passionate", "dedicated", "hardworking", "team player", "results-driven", "detail-oriented", "self-motivated", "proactive", "innovative", "dynamic", "synergistic"],
        }

    def infer_personality_traits(self, commit_analysis: Dict[str, Any], pr_data: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Infer personality traits from technical contribution patterns."""
        traits = []

        if not commit_analysis:
            return traits

        total_commits = commit_analysis.get("total_commits_analyzed", 0)
        if total_commits == 0:
            return traits

        # Analyze commit patterns for personality indicators
        excellence_areas = commit_analysis.get("excellence_areas", {})
        patterns = excellence_areas.get("patterns", {})
        conventional_analysis = commit_analysis.get("conventional_commit_analysis", {})

        # Detail-oriented indicators
        if conventional_analysis.get("quality_score", 0) > 60 or patterns.get("testing", 0) > 0 or patterns.get("documentation", 0) > 0:
            traits.append(
                {
                    "trait": "detail_oriented",
                    "confidence": min(85, 60 + conventional_analysis.get("quality_score", 0) * 0.3),
                    "description": random.choice(self.personality_indicators["detail_oriented"]["descriptions"]),
                }
            )

        # Problem solver indicators
        bug_fixes = patterns.get("bug_fixing", 0)
        if bug_fixes > total_commits * 0.3:  # More than 30% bug fixes
            traits.append(
                {"trait": "problem_solver", "confidence": min(90, 50 + bug_fixes / total_commits * 100), "description": random.choice(self.personality_indicators["problem_solver"]["descriptions"])}
            )

        # Strategic thinker indicators
        if patterns.get("refactoring", 0) > 0 or patterns.get("architecture", 0) > 0:
            traits.append({"trait": "strategic_thinker", "confidence": 75, "description": random.choice(self.personality_indicators["strategic_thinker"]["descriptions"])})

        # Reliable indicators from contributor metrics
        contributor_metrics = commit_analysis.get("contributor_metrics", {})
        if contributor_metrics.get("avg_commits_per_repo", 0) > 5:
            traits.append({"trait": "reliable", "confidence": 80, "description": random.choice(self.personality_indicators["reliable"]["descriptions"])})

        # Add PR-based traits if data available
        if pr_data:
            # Collaborator indicators
            if pr_data.get("merged_pr_rate", 0) > 0.7:  # 70% success rate
                traits.append({"trait": "collaborator", "confidence": 85, "description": random.choice(self.personality_indicators["collaborator"]["descriptions"])})

        # Sort by confidence and return top traits
        return sorted(traits, key=lambda x: x["confidence"], reverse=True)[:3]

    def convert_technical_to_story(self, technical_data: Dict[str, Any], context_type: str = "profile") -> Dict[str, Any]:
        """Convert technical metrics into human stories and anecdotes."""
        stories = {"achievements": [], "personality_insights": [], "collaboration_examples": [], "technical_examples": []}

        commit_analysis = technical_data.get("commit_analysis", {})
        languages = technical_data.get("languages", [])
        skills = technical_data.get("skills", {})
        repository_info = technical_data.get("repository_info", {})

        # Convert commit metrics to achievement stories
        total_commits = commit_analysis.get("total_commits_analyzed", 0)
        if total_commits > 0:
            if total_commits > 100:
                stories["achievements"].append(f"I've watched them consistently contribute meaningful code over {total_commits} commits")
            elif total_commits > 50:
                stories["achievements"].append(f"Their {total_commits} commits show a steady pattern of thoughtful development")
            else:
                stories["achievements"].append("Every contribution they make is thoughtful and well-considered")

        # Convert excellence areas to personality insights
        excellence_areas = commit_analysis.get("excellence_areas", {})
        primary_strength = excellence_areas.get("primary_strength")
        if primary_strength:
            strength_stories = {
                "bug_fixing": "They're the person you want when something needs to be fixed - thorough and persistent",
                "optimization": "They have a keen eye for making things run better and more efficiently",
                "refactoring": "They care about keeping code clean and maintainable for the whole team",
                "testing": "They understand the value of solid testing and write code you can trust",
                "documentation": "They document their work thoughtfully, making it easy for others to build on",
            }
            if primary_strength in strength_stories:
                stories["personality_insights"].append(strength_stories[primary_strength])

        # Convert languages to natural descriptions
        if languages:
            top_languages = [getattr(lang, "language", lang) if hasattr(lang, "language") else str(lang) for lang in languages[:3]]
            if context_type == "repo_only" and repository_info:
                stories["technical_examples"].append(f"They work effectively with {', '.join(top_languages)} in this project")
            else:
                stories["technical_examples"].append(f"They're really skilled with {', '.join(top_languages)}")

        # Convert frameworks to contextual examples
        frameworks = skills.get("frameworks", [])
        if frameworks:
            framework_list = frameworks[:3]
            if context_type == "repo_only":
                stories["technical_examples"].append(f"Their use of {', '.join(framework_list)} in this project shows solid technical judgment")
            else:
                stories["technical_examples"].append(f"They know their way around {', '.join(framework_list)} and use them effectively")

        # Add collaboration stories from contributor summary
        contributor_summary = technical_data.get("contributor_commit_summary", {})
        if contributor_summary:
            summary_data = contributor_summary.get("summary", {})
            work_patterns = summary_data.get("work_patterns", [])
            if work_patterns:
                for pattern in work_patterns[:2]:
                    if "consistent" in pattern.lower():
                        stories["collaboration_examples"].append("You can count on them to deliver quality work regularly")
                    elif "success" in pattern.lower():
                        stories["collaboration_examples"].append("They collaborate effectively, always submitting well-thought-out improvements")

        return stories

    def create_narrative_opening(self, name: str, context_type: str, project_name: Optional[str] = None) -> str:
        """Create a natural opening for the recommendation."""
        openings = self.narrative_openings.get(context_type, self.narrative_openings["profile"])
        selected_opening = random.choice(openings)

        if context_type == "repo_only" and project_name:
            return selected_opening.format(name=name, project_name=project_name)
        else:
            return selected_opening.format(name=name)

    def create_narrative_bridge(self) -> str:
        """Create a natural transition between paragraphs."""
        return random.choice(self.narrative_bridges)

    def create_narrative_closing(self, key_strengths: List[str]) -> str:
        """Create a natural closing for the recommendation."""
        closing_template = random.choice(self.narrative_closings)
        strength_phrase = " and ".join(key_strengths) if key_strengths else "strong technical skills and reliability"
        return f"{closing_template} {strength_phrase}."

    def build_human_prompt_sections(self, github_data: Dict[str, Any], context_type: str = "profile", display_name: str = None) -> Dict[str, List[str]]:
        """Build human-like prompt sections from technical data."""
        user_data = github_data.get("user_data", {})
        repository_info = github_data.get("repository_info", {})

        # Get the person's name/username - prioritize first name for personal touch
        if display_name:
            name = display_name
        else:
            # Extract first name from full name for more personal recommendations
            full_name = user_data.get("full_name", "")
            if full_name:
                # Extract just the first name
                first_name = full_name.strip().split()[0] if full_name.strip() else ""
                name = first_name if first_name else user_data.get("github_username", "this developer")
            else:
                name = user_data.get("github_username", "this developer")
        project_name = repository_info.get("name") if repository_info else None

        # Convert technical data to stories
        stories = self.convert_technical_to_story(github_data, context_type)

        # Infer personality traits
        personality_traits = self.infer_personality_traits(github_data.get("commit_analysis", {}), github_data.get("pr_data"))

        # Build narrative sections
        sections = {
            "opening": [self.create_narrative_opening(name, context_type, project_name)],
            "technical_competence": [],
            "personality_and_collaboration": [],
            "specific_achievements": [],
            "closing_endorsement": [],
        }

        # Add technical competence in human language
        if stories["technical_examples"]:
            sections["technical_competence"].extend(stories["technical_examples"])

        # Add personality insights
        if personality_traits:
            trait_descriptions = [trait["description"] for trait in personality_traits[:2]]
            sections["personality_and_collaboration"].extend(trait_descriptions)

        if stories["personality_insights"]:
            sections["personality_and_collaboration"].extend(stories["personality_insights"][:2])

        # Add collaboration examples
        if stories["collaboration_examples"]:
            sections["personality_and_collaboration"].extend(stories["collaboration_examples"])

        # Add specific achievements
        if stories["achievements"]:
            sections["specific_achievements"].extend(stories["achievements"])

        # Create closing
        key_strengths = []
        if personality_traits:
            key_strengths = [trait["trait"].replace("_", " ") for trait in personality_traits[:2]]
        sections["closing_endorsement"] = [self.create_narrative_closing(key_strengths)]

        return sections

    def validate_naturalness(self, text: str) -> Dict[str, Any]:
        """Validate that text sounds natural and human-like."""
        robotic_phrases = [
            "demonstrates expertise",
            "shows proficiency",
            "utilizes technologies",
            "exhibits capabilities",
            "maintains standards",
            "total commits:",
            "pull requests:",
            "commit analysis",
            "technical competency",
            "contribution patterns",
            "development activity",
        ]

        issues = []
        for phrase in robotic_phrases:
            if phrase.lower() in text.lower():
                issues.append(f"Contains robotic phrase: '{phrase}'")

        # Check for overly technical language
        technical_words = ["SHA", "commit ID", "repository statistics", "API endpoints"]
        for word in technical_words:
            if word.lower() in text.lower():
                issues.append(f"Contains technical jargon: '{word}'")

        # Check for paragraph structure
        paragraphs = text.split("\n\n")
        if len(paragraphs) < 2:
            issues.append("Missing proper paragraph breaks")

        naturalness_score = max(0, 100 - len(issues) * 15)

        return {"is_natural": naturalness_score > 70, "naturalness_score": naturalness_score, "issues": issues, "suggestions": self._generate_naturalness_suggestions(issues)}

    def _generate_naturalness_suggestions(self, issues: List[str]) -> List[str]:
        """Generate suggestions to improve naturalness."""
        suggestions = []

        if any("robotic phrase" in issue for issue in issues):
            suggestions.append("Replace technical phrases with conversational language")

        if any("technical jargon" in issue for issue in issues):
            suggestions.append("Avoid technical IDs and metrics in favor of outcome descriptions")

        if any("paragraph breaks" in issue for issue in issues):
            suggestions.append("Add proper paragraph structure with double line breaks")

        suggestions.append("Focus on specific examples and personal observations")
        suggestions.append("Use 'I've seen them...' instead of 'They demonstrate...'")

        return suggestions

    def generate_specific_stories(self, github_data: Dict[str, Any]) -> List[str]:
        """Generate specific, concrete stories from technical data."""
        stories = []

        commit_analysis = github_data.get("commit_analysis", {})
        languages = github_data.get("languages", [])
        user_data = github_data.get("user_data", {})

        # Get display name for stories
        display_name = self._extract_display_name_from_data(user_data)

        # Convert commit patterns to stories
        if commit_analysis:
            excellence_areas = commit_analysis.get("excellence_areas", {})
            patterns = excellence_areas.get("patterns", {})

            if patterns.get("bug_fixing", 0) > 5:
                stories.append(
                    f"I remember when our system hit a critical issue - {display_name} dove in immediately "
                    "and didn't stop until they'd not only fixed the problem but also "
                    "implemented safeguards to prevent it from happening again"
                )

            if patterns.get("testing", 0) > 3:
                stories.append(
                    f"They're the kind of developer who catches issues before they become problems - "
                    f"I've seen {display_name} save us countless hours by writing tests that exposed "
                    "edge cases none of us had considered"
                )

            if patterns.get("refactoring", 0) > 2:
                stories.append(
                    f"There was this legacy code section that everyone was afraid to touch, but {display_name} "
                    "took it on methodically, breaking it down piece by piece until it was not only "
                    "cleaner but actually more performant than before"
                )

            if patterns.get("documentation", 0) > 1:
                stories.append(
                    f"What I appreciate most about {display_name} is how they document their work - "
                    "not just basic comments, but thoughtful explanations that help the whole team "
                    "understand complex decisions months later"
                )

        # Convert language usage to skill stories
        if languages:
            primary_lang = languages[0].language if hasattr(languages[0], "language") else str(languages[0])
            stories.append(f"Their {primary_lang} code isn't just functional - it's elegant and maintainable. " f"I've learned new techniques just by reading through {display_name}'s implementations")

            if len(languages) > 2:
                lang_names = [getattr(lang, "language", str(lang)) for lang in languages[:3]]
                stories.append(
                    f"What impresses me is how {display_name} seamlessly switches between " f"{', '.join(lang_names)} depending on what the project needs - " "they're equally effective in all of them"
                )

        # Add collaboration-based stories
        pr_data = github_data.get("pr_data")
        if pr_data and pr_data.get("merged_pr_rate", 0) > 0.8:
            stories.append(
                f"In code reviews, {display_name} has this unique ability to give feedback that's both "
                "constructive and encouraging - everyone looks forward to their input because "
                "they know they'll learn something valuable"
            )

        return stories[:4]  # Return top 4 stories

    def determine_relationship_context(self, github_data: Dict[str, Any]) -> str:
        """Infer relationship context from data patterns."""
        commit_analysis = github_data.get("commit_analysis", {})

        # Analyze complexity and experience indicators
        total_commits = commit_analysis.get("total_commits_analyzed", 0)
        quality_score = commit_analysis.get("conventional_commit_analysis", {}).get("quality_score", 0)
        excellence_areas = commit_analysis.get("excellence_areas", {})
        patterns = excellence_areas.get("patterns", {})

        # Senior developer indicators
        senior_indicators = [
            total_commits > 200,
            quality_score > 85,
            patterns.get("architecture", 0) > 5,
            patterns.get("documentation", 0) > 3,
            patterns.get("code_reviews", 0) > 10,
        ]

        # Mentoring indicators
        mentor_indicators = [
            patterns.get("helping_others", 0) > 5,
            patterns.get("knowledge_sharing", 0) > 3,
            quality_score > 90,
        ]

        if sum(mentor_indicators) >= 2:
            return "mentee"  # We're learning from them
        elif sum(senior_indicators) >= 3:
            return "peer"  # Equal level collaboration
        elif total_commits > 50 and quality_score > 70:
            return "peer"  # Standard peer relationship
        else:
            return "mentor"  # We're guiding them

    def build_contextual_story(self, template_type: str, name: str, **kwargs) -> str:
        """Build stories using contextual templates."""
        if template_type not in self.story_templates:
            return f"I've had great experiences working with {name}."

        template = random.choice(self.story_templates[template_type])
        try:
            return template.format(name=name, **kwargs)
        except KeyError as e:
            # If template requires a parameter we don't have, fall back to simpler version
            return f"I've seen {name} consistently {kwargs.get('action', 'deliver excellent work')}."

    def validate_human_voice(self, text: str) -> Dict[str, Any]:
        """Enhanced validation for human-like voice."""
        issues = []
        suggestions = []

        # Check for robotic patterns
        for pattern_type, patterns in self.robotic_patterns.items():
            found_patterns = []
            for pattern in patterns:
                if pattern.lower() in text.lower():
                    found_patterns.append(pattern)

            if found_patterns:
                issues.append(f"Contains {pattern_type}: {', '.join(found_patterns[:3])}")

                if pattern_type == "corporate_speak":
                    suggestions.append("Replace corporate jargon with natural language")
                elif pattern_type == "academic_language":
                    suggestions.append("Use conversational descriptions instead of academic language")
                elif pattern_type == "ai_tells":
                    suggestions.append("Remove AI transition phrases - jump straight to the point")

        # Check sentence variety
        sentences = [s.strip() for s in text.split(".") if s.strip()]
        if sentences:
            avg_length = sum(len(s.split()) for s in sentences) / len(sentences)
            if avg_length > 25:
                issues.append("Sentences too long - break up complex thoughts")
                suggestions.append("Use shorter, more conversational sentences")

        # Check for personal pronouns (should have them)
        personal_pronouns = ["I", "we", "my", "our", "me"]
        text_words = text.lower().split()
        personal_count = sum(1 for word in text_words if word in [p.lower() for p in personal_pronouns])

        if personal_count == 0:
            issues.append("Missing personal perspective - no first-person language")
            suggestions.append("Add 'I' statements to show personal experience")
        elif personal_count < len(text_words) * 0.02:  # Less than 2% personal pronouns
            issues.append("Limited personal perspective")
            suggestions.append("Include more personal observations and experiences")

        # Check for emotional language
        emotion_words = ["impressed", "amazed", "surprised", "pleased", "proud", "excited", "grateful", "appreciate", "admire", "respect", "enjoy", "love"]
        emotion_count = sum(1 for word in emotion_words if word.lower() in text.lower())

        if emotion_count == 0:
            issues.append("No emotional language - sounds detached")
            suggestions.append("Add emotional reactions to show genuine experience")

        # Check for specific examples vs general statements
        specific_indicators = ["when", "during", "there was this", "I remember", "one time", "specifically", "for example", "in particular", "like when"]
        specific_count = sum(1 for indicator in specific_indicators if indicator.lower() in text.lower())

        if specific_count == 0:
            issues.append("No specific examples - too general")
            suggestions.append("Include specific incidents and examples")

        # Check paragraph structure
        paragraphs = text.split("\n\n")
        if len(paragraphs) < 2:
            issues.append("Missing paragraph structure")
            suggestions.append("Break content into clear paragraphs")

        human_score = max(0, 100 - len(issues) * 8)

        return {
            "issues": issues,
            "suggestions": suggestions,
            "human_score": human_score,
            "is_human_like": human_score > 75,
            "emotional_language_count": emotion_count,
            "personal_language_count": personal_count,
            "specific_examples_count": specific_count,
        }

    def enhance_with_relationship_context(self, text: str, relationship_type: str, name: str) -> str:
        """Enhance text with appropriate relationship context."""
        if relationship_type not in self.relationship_contexts:
            return text

        context = self.relationship_contexts[relationship_type]

        # Try to identify and replace generic openings
        opening_patterns = ["I have worked with", "I know", "I can recommend", "Working with", "I have had the pleasure"]

        enhanced_text = text
        for pattern in opening_patterns:
            if pattern.lower() in text.lower():
                new_opening = random.choice(context["openings"]).format(name=name)
                enhanced_text = text.replace(pattern, new_opening, 1)
                break

        return enhanced_text

    def _extract_display_name_from_data(self, user_data: Dict[str, Any]) -> str:
        """Extract display name from user data."""
        if user_data.get("full_name"):
            # Extract first name from full name
            first_name = user_data["full_name"].strip().split()[0]
            return first_name if first_name else user_data.get("github_username", "they")
        return user_data.get("github_username", "they")

    def get_quality_enhancement_suggestions(self, content: str, github_data: Dict[str, Any]) -> List[str]:
        """Get specific suggestions to enhance recommendation quality."""
        suggestions = []

        try:
            # Analyze current content
            human_voice_results = self.validate_human_voice(content)
            naturalness_results = self.validate_naturalness(content)

            # Specific enhancement suggestions
            if human_voice_results.get("human_score", 0) < 80:
                suggestions.append("Add more personal language and first-person experiences")

            if human_voice_results.get("emotional_language_count", 0) < 2:
                suggestions.append("Include more emotional and appreciative language")

            if human_voice_results.get("specific_examples_count", 0) < 1:
                suggestions.append("Add specific examples and anecdotes from working together")

            if naturalness_results.get("naturalness_score", 0) < 75:
                suggestions.append("Remove robotic language and make it more conversational")

            # Relationship-specific enhancements
            relationship = self.determine_relationship_context(github_data)
            relationship_suggestions = self._get_relationship_enhancement_suggestions(relationship, content)
            suggestions.extend(relationship_suggestions)

            # Technical context enhancements
            languages = github_data.get("languages", [])
            if languages and len(languages) > 0:
                primary_lang = languages[0].language if hasattr(languages[0], "language") else str(languages[0])
                if primary_lang.lower() not in content.lower():
                    suggestions.append(f"Consider mentioning their work with {primary_lang}")

            return suggestions[:5]  # Return top 5 suggestions

        except Exception as e:
            logger.error(f"Error generating quality enhancement suggestions: {e}")
            return ["Focus on specific examples and personal observations"]

    def _get_relationship_enhancement_suggestions(self, relationship: str, content: str) -> List[str]:
        """Get enhancement suggestions based on relationship context."""
        suggestions = []

        try:
            if relationship == "mentor":
                if "growth" not in content.lower() and "learn" not in content.lower():
                    suggestions.append("Highlight their growth and learning journey")
                if "guide" not in content.lower() and "develop" not in content.lower():
                    suggestions.append("Mention your role in guiding their development")

            elif relationship == "peer":
                if "together" not in content.lower() and "collaborate" not in content.lower():
                    suggestions.append("Emphasize collaborative experiences and teamwork")
                if "both" not in content.lower() and "we" not in content.lower():
                    suggestions.append("Use more collaborative language like 'we' and 'together'")

            elif relationship == "mentee":
                if "taught" not in content.lower() and "learned" not in content.lower():
                    suggestions.append("Highlight what you've learned from them")
                if "respect" not in content.lower() and "admire" not in content.lower():
                    suggestions.append("Show appreciation for their expertise and guidance")

            return suggestions

        except Exception as e:
            logger.error(f"Error getting relationship enhancement suggestions: {e}")
            return []

    def generate_contextual_enhancement(self, content: str, github_data: Dict[str, Any]) -> str:
        """Generate contextually enhanced version of the content."""
        try:
            # Get relationship context
            relationship = self.determine_relationship_context(github_data)

            # Apply relationship-specific enhancements
            enhanced_content = self.enhance_with_relationship_context(content, relationship, self._extract_display_name_from_data(github_data.get("user_data", {})))

            # Add technical context enhancements
            enhanced_content = self._add_technical_context_enhancements(enhanced_content, github_data)

            # Improve emotional connection
            enhanced_content = self._boost_emotional_connection(enhanced_content)

            return enhanced_content

        except Exception as e:
            logger.error(f"Error generating contextual enhancement: {e}")
            return content

    def _add_technical_context_enhancements(self, content: str, github_data: Dict[str, Any]) -> str:
        """Add technical context enhancements to make content more specific."""
        try:
            enhanced = content

            # Add specific technical skills if not mentioned
            skills = github_data.get("skills", {})
            technical_skills = skills.get("technical_skills", [])

            if technical_skills:
                primary_skills = technical_skills[:3]
                for skill in primary_skills:
                    if skill.lower() not in enhanced.lower():
                        # Find a good place to insert the skill mention
                        if "technical" in enhanced.lower():
                            enhanced = enhanced.replace("technical skills", f"technical skills, especially {skill}")
                            break

            # Enhance with specific project context
            repositories = github_data.get("repositories", [])
            if repositories:
                top_repo = repositories[0]
                repo_name = top_repo.get("name", "")
                if repo_name and repo_name.lower() not in enhanced.lower():
                    # Add project context if appropriate
                    if "project" in enhanced.lower():
                        enhanced = enhanced.replace("project", f"project (like {repo_name})")

            return enhanced

        except Exception as e:
            logger.error(f"Error adding technical context enhancements: {e}")
            return content

    def _boost_emotional_connection(self, content: str) -> str:
        """Boost emotional connection in the content."""
        try:
            # Add more emotional language where appropriate
            emotional_boosts = {
                "good at": "really talented at",
                "skilled": "incredibly skilled",
                "works with": "excels with",
                "knows": "has mastered",
                "can": "consistently",
            }

            boosted = content
            for neutral, emotional in emotional_boosts.items():
                if neutral in boosted.lower() and emotional not in boosted.lower():
                    # Replace first occurrence only
                    boosted = boosted.replace(neutral, emotional, 1)

            return boosted

        except Exception as e:
            logger.error(f"Error boosting emotional connection: {e}")
            return content
