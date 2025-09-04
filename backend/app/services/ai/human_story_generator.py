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
