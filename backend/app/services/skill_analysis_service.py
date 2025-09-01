"""Skill Analysis Service for analyzing user skills and providing recommendations."""

import logging
from typing import Any, Dict, List

from app.schemas.recommendation import SkillGapAnalysisRequest, SkillGapAnalysisResponse, SkillMatch

logger = logging.getLogger(__name__)


class SkillAnalysisService:
    """Service for analyzing user skills and providing gap analysis."""

    def __init__(self) -> None:
        """Initialize skill analysis service."""
        logger.info("🔧 SkillAnalysisService initialized")

    def get_role_skill_requirements(self, role: str, experience_level: str = "mid") -> Dict[str, Any]:
        """Get skill requirements for common job roles."""
        role_requirements = {
            "frontend_developer": {
                "junior": {
                    "required": ["HTML", "CSS", "JavaScript"],
                    "preferred": ["React", "Vue", "Angular", "Git", "Responsive Design"],
                    "nice_to_have": ["TypeScript", "Webpack", "Testing", "Node.js"],
                },
                "mid": {
                    "required": ["HTML", "CSS", "JavaScript", "React/Vue/Angular", "Git"],
                    "preferred": ["TypeScript", "Testing", "Build Tools", "Performance Optimization"],
                    "nice_to_have": ["GraphQL", "Mobile Development", "Design Systems", "CI/CD"],
                },
                "senior": {
                    "required": ["HTML", "CSS", "JavaScript", "React/Vue/Angular", "TypeScript", "Testing"],
                    "preferred": ["Architecture", "Performance", "Mentoring", "Code Review", "CI/CD"],
                    "nice_to_have": ["Leadership", "System Design", "DevOps", "Product Management"],
                },
            },
            "backend_developer": {
                "junior": {
                    "required": ["Python/Java/Node.js", "SQL", "REST APIs"],
                    "preferred": ["Git", "Testing", "Linux/Unix", "Docker"],
                    "nice_to_have": ["ORM", "Caching", "Security", "Microservices"],
                },
                "mid": {
                    "required": ["Python/Java/Node.js", "SQL", "REST APIs", "Testing", "Git"],
                    "preferred": ["ORM", "Caching", "Security", "Docker", "AWS/GCP/Azure"],
                    "nice_to_have": ["Microservices", "GraphQL", "Message Queues", "Monitoring"],
                },
                "senior": {
                    "required": ["Python/Java/Node.js", "SQL", "REST APIs", "Testing", "Architecture"],
                    "preferred": ["Microservices", "Cloud Platforms", "Security", "Performance", "Mentoring"],
                    "nice_to_have": ["System Design", "DevOps", "Leadership", "Product Strategy"],
                },
            },
            "fullstack_developer": {
                "junior": {
                    "required": ["HTML", "CSS", "JavaScript", "Python/Java/Node.js", "SQL"],
                    "preferred": ["React/Vue", "Git", "REST APIs", "Testing"],
                    "nice_to_have": ["TypeScript", "Docker", "AWS/GCP", "Responsive Design"],
                },
                "mid": {
                    "required": ["HTML", "CSS", "JavaScript", "Python/Java/Node.js", "SQL", "REST APIs"],
                    "preferred": ["React/Vue", "TypeScript", "Testing", "Docker", "AWS/GCP"],
                    "nice_to_have": ["GraphQL", "Microservices", "CI/CD", "Performance Optimization"],
                },
                "senior": {
                    "required": ["HTML", "CSS", "JavaScript", "Python/Java/Node.js", "SQL", "Architecture"],
                    "preferred": ["TypeScript", "Microservices", "Cloud Platforms", "Testing", "Performance"],
                    "nice_to_have": ["Leadership", "System Design", "DevOps", "Product Management"],
                },
            },
            "data_scientist": {
                "junior": {
                    "required": ["Python", "SQL", "Statistics", "Pandas", "NumPy"],
                    "preferred": ["Machine Learning", "Matplotlib", "Jupyter", "Git"],
                    "nice_to_have": ["R", "TensorFlow", "Scikit-learn", "Tableau"],
                },
                "mid": {
                    "required": ["Python", "SQL", "Statistics", "Machine Learning", "Pandas", "NumPy"],
                    "preferred": ["TensorFlow/PyTorch", "Scikit-learn", "Data Visualization", "Big Data"],
                    "nice_to_have": ["Deep Learning", "Spark", "AWS/GCP", "Experimentation"],
                },
                "senior": {
                    "required": ["Python", "SQL", "Statistics", "Machine Learning", "Deep Learning"],
                    "preferred": ["Big Data", "MLOps", "Experimentation", "Leadership", "Strategy"],
                    "nice_to_have": ["System Design", "Product Management", "Research", "Publications"],
                },
            },
            "devops_engineer": {
                "junior": {
                    "required": ["Linux/Unix", "Git", "Docker", "CI/CD"],
                    "preferred": ["AWS/GCP/Azure", "Kubernetes", "Terraform", "Monitoring"],
                    "nice_to_have": ["Python", "Shell Scripting", "Security", "Networking"],
                },
                "mid": {
                    "required": ["Linux/Unix", "Docker", "Kubernetes", "CI/CD", "AWS/GCP/Azure"],
                    "preferred": ["Terraform", "Monitoring", "Security", "Python", "Shell Scripting"],
                    "nice_to_have": ["Service Mesh", "GitOps", "Site Reliability", "Automation"],
                },
                "senior": {
                    "required": ["Linux/Unix", "Docker", "Kubernetes", "CI/CD", "Infrastructure as Code"],
                    "preferred": ["Site Reliability", "Security", "Automation", "Leadership", "Strategy"],
                    "nice_to_have": ["Platform Engineering", "Multi-cloud", "Compliance", "Cost Optimization"],
                },
            },
        }

        # Normalize role name
        normalized_role = role.lower().replace(" ", "_").replace("-", "_")

        # Find matching role or use closest match
        if normalized_role in role_requirements:
            return role_requirements[normalized_role].get(experience_level, role_requirements[normalized_role]["mid"])
        else:
            # Try to find partial matches
            for role_key in role_requirements:
                if role_key in normalized_role or normalized_role in role_key:
                    return role_requirements[role_key].get(experience_level, role_requirements[role_key]["mid"])

            # Default fallback
            return {
                "required": ["Programming", "Git", "Communication"],
                "preferred": ["Testing", "Documentation", "Teamwork"],
                "nice_to_have": ["Leadership", "Problem Solving", "Continuous Learning"],
            }

    def analyze_skill_match(self, user_skill: str, required_skills: List[str], github_data: Dict[str, Any]) -> SkillMatch:
        """Analyze how well a user's skill matches job requirements."""
        # Extract user's skills from the nested skills structure
        skills_data = github_data.get("skills", {})
        user_technical_skills = set(skills_data.get("technical_skills", []))
        user_frameworks = set(skills_data.get("frameworks", []))
        user_tools = set(skills_data.get("tools", []))
        user_domains = set(skills_data.get("domains", []))
        user_dependencies = set(skills_data.get("dependencies_found", []))

        # Combine all user skills for matching
        all_user_skills = user_technical_skills | user_frameworks | user_tools | user_domains | user_dependencies

        # Extract additional data sources
        starred_technologies = github_data.get("starred_technologies", {})
        commit_analysis = github_data.get("commit_analysis", {})

        # Get starred languages and topics
        starred_languages = set(starred_technologies.get("languages", {}).keys())
        starred_topics = set(starred_technologies.get("topics", []))

        # Add starred technologies to skill set
        all_user_skills.update(starred_languages)
        all_user_skills.update(starred_topics)

        # Normalize skills for comparison
        user_skill_lower = user_skill.lower()
        user_skills_lower = {skill.lower() for skill in all_user_skills}

        # Find matches
        evidence = []
        match_score = 0

        # Direct match in skills
        if user_skill_lower in user_skills_lower:
            match_score += 40
            evidence.append("Direct match found in profile")

        # Check starred technologies
        if user_skill_lower in starred_languages:
            match_score += 25
            evidence.append("Interest shown through starred repositories")
        elif user_skill_lower in starred_topics:
            match_score += 20
            evidence.append("Technology interest indicated by repository topics")

        # Partial matches in skills
        for user_skill_name in all_user_skills:
            user_skill_name_lower = user_skill_name.lower()
            if (user_skill_lower in user_skill_name_lower or user_skill_name_lower in user_skill_lower) and user_skill_lower != user_skill_name_lower:
                match_score += 20
                evidence.append(f"Related skill: {user_skill_name}")
                break

        # Check commit analysis for evidence of expertise
        primary_strength = commit_analysis.get("excellence_areas", {}).get("primary_strength", "")
        if primary_strength and (user_skill_lower in primary_strength.lower() or primary_strength.lower() in user_skill_lower):
            match_score += 30
            evidence.append(f"Primary strength based on commit analysis: {primary_strength.replace('_', ' ').title()}")

        # Check commit patterns for relevant skills
        patterns = commit_analysis.get("excellence_areas", {}).get("patterns", {})
        for pattern_name, pattern_data in patterns.items():
            pattern_percentage = pattern_data.get("percentage", 0)
            # If pattern has significant percentage (>15%) and matches skill
            if pattern_percentage > 15 and (user_skill_lower in pattern_name.lower() or pattern_name.lower() in user_skill_lower):
                match_score += min(int(pattern_percentage), 25)  # Cap at 25 points
                evidence.append(f"Strong commit pattern in {pattern_name.replace('_', ' ')} ({pattern_percentage}%)")
                break

        # Check if user has relevant tools/frameworks from commit analysis
        tools_and_features = commit_analysis.get("tools_and_features", {})
        tools_by_category = tools_and_features.get("tools_by_category", {})
        for category, tools in tools_by_category.items():
            for tool in tools:
                if user_skill_lower in tool.lower() or tool.lower() in user_skill_lower:
                    match_score += 20
                    evidence.append(f"Experience with {tool} based on commit history")
                    break

        # Check for related technologies
        related_tech = self.get_related_technologies(user_skill)
        for tech in related_tech:
            if tech.lower() in user_skills_lower:
                match_score += 15
                evidence.append(f"Related technology: {tech}")
            elif tech.lower() in starred_languages:
                match_score += 10
                evidence.append(f"Related technology interest: {tech}")

        # Determine match level
        if match_score >= 40:
            match_level = "strong"
        elif match_score >= 20:
            match_level = "moderate"
        elif match_score >= 5:
            match_level = "weak"
        else:
            match_level = "missing"
            evidence.append("No relevant skills found in profile")

        return SkillMatch(skill=user_skill, match_level=match_level, evidence=evidence)

    def get_related_technologies(self, skill: str) -> List[str]:
        """Get related technologies for a given skill."""
        related_tech_map = {
            "javascript": ["node.js", "express", "react", "vue", "angular"],
            "python": ["django", "flask", "fastapi", "pandas", "numpy", "tensorflow"],
            "java": ["spring", "hibernate", "maven", "gradle"],
            "react": ["javascript", "typescript", "redux", "next.js"],
            "docker": ["kubernetes", "containerization", "devops"],
            "aws": ["cloud", "ec2", "s3", "lambda", "terraform"],
            "testing": ["jest", "pytest", "junit", "selenium", "cypress"],
            "git": ["version control", "github", "gitlab", "collaboration"],
            "sql": ["database", "postgresql", "mysql", "mongodb", "orm"],
            "machine learning": ["python", "tensorflow", "pytorch", "scikit-learn", "pandas"],
        }

        skill_lower = skill.lower()
        for key, related in related_tech_map.items():
            if key in skill_lower or skill_lower in key:
                return related

        return []

    def generate_skill_recommendations(self, skill_analysis: List[SkillMatch], target_role: str) -> Dict[str, List[str]]:
        """Generate recommendations based on skill analysis."""
        recommendations = []
        learning_resources = []

        missing_skills = [match.skill for match in skill_analysis if match.match_level == "missing"]
        weak_skills = [match.skill for match in skill_analysis if match.match_level == "weak"]

        # Generate specific recommendations
        for skill in missing_skills[:5]:  # Focus on top 5 missing skills
            if "javascript" in skill.lower():
                recommendations.append(f"Learn {skill} fundamentals and practice with small projects")
                learning_resources.append("freeCodeCamp JavaScript curriculum")
                learning_resources.append("MDN Web Docs")
            elif "python" in skill.lower():
                recommendations.append(f"Master {skill} basics and build data processing applications")
                learning_resources.append("Python Crash Course book")
                learning_resources.append("Codecademy Python course")
            elif "react" in skill.lower():
                recommendations.append("Build React applications and learn component patterns")
                learning_resources.append("React Official Documentation")
                learning_resources.append("React for Beginners course")
            elif "docker" in skill.lower():
                recommendations.append(f"Learn containerization with {skill} and Kubernetes basics")
                learning_resources.append("Docker Getting Started guide")
                learning_resources.append("Kubernetes documentation")
            elif "testing" in skill.lower():
                recommendations.append("Implement comprehensive testing strategies for your projects")
                learning_resources.append("Testing JavaScript book")
                learning_resources.append("Jest documentation")
            else:
                recommendations.append(f"Develop proficiency in {skill} through hands-on projects")
                learning_resources.append(f"Search for '{skill} tutorials' on YouTube")
                learning_resources.append(f"Read documentation for {skill}")

        # Add general recommendations
        if len(missing_skills) > 3:
            recommendations.append("Focus on building a portfolio project that demonstrates multiple required skills")
            learning_resources.append("GitHub learning paths")

        if weak_skills:
            recommendations.append(f"Strengthen your knowledge in: {', '.join(weak_skills[:3])}")

        return {
            "recommendations": recommendations[:8],  # Limit to 8 recommendations
            "learning_resources": learning_resources[:6],  # Limit to 6 resources
        }

    def create_gap_analysis_summary(self, match_score: int, strengths_count: int, gaps_count: int, target_role: str) -> str:
        """Create a summary of the skill gap analysis."""
        if match_score >= 80:
            summary = f"Excellent match for {target_role} role! You have strong foundational skills with {strengths_count} key strengths."
        elif match_score >= 60:
            summary = f"Good match for {target_role} role. You have {strengths_count} strengths but {gaps_count} areas for improvement."
        elif match_score >= 40:
            summary = f"Moderate match for {target_role} role. Consider developing {gaps_count} key skills to strengthen your profile."
        else:
            summary = f"Significant gaps for {target_role} role. Focus on building {gaps_count} core skills to become competitive."

        if gaps_count > 0:
            summary += " Prioritize learning the missing skills to improve your overall match score."

        return summary

    def analyze_skill_gaps(self, request: SkillGapAnalysisRequest, github_data: Dict[str, Any]) -> SkillGapAnalysisResponse:
        """Analyze skill gaps for a target role."""
        from datetime import datetime

        logger.info("📊 SKILL GAP ANALYSIS STARTED")
        logger.info("=" * 60)
        logger.info(f"👤 GitHub Username: {request.github_username}")
        logger.info(f"🎯 Target Role: {request.target_role}")
        logger.info(f"🏢 Industry: {request.industry}")
        logger.info(f"📈 Experience Level: {request.experience_level}")

        # Get skill requirements for the target role
        logger.info("📋 ANALYZING ROLE REQUIREMENTS")
        logger.info("-" * 50)

        role_requirements = self.get_role_skill_requirements(request.target_role or "", request.experience_level or "mid")

        logger.info(f"📋 Role requirements loaded: {len(role_requirements['required'])} required skills")

        # Analyze skill matches
        logger.info("🔍 ANALYZING SKILL MATCHES")
        logger.info("-" * 50)
        skill_analysis = []

        # Analyze required skills
        for skill in role_requirements["required"]:
            match = self.analyze_skill_match(skill, role_requirements["required"], github_data)
            skill_analysis.append(match)

        # Analyze preferred skills (partial weight)
        for skill in role_requirements["preferred"][:5]:  # Top 5 preferred skills
            match = self.analyze_skill_match(skill, role_requirements["required"], github_data)
            skill_analysis.append(match)

        logger.info(f"✅ Analyzed {len(skill_analysis)} skills")

        # Calculate overall match score
        required_matches = [match for match in skill_analysis if match.match_level in ["strong", "moderate"]]
        overall_match_score = int((len(required_matches) / len(role_requirements["required"])) * 100)
        overall_match_score = min(overall_match_score, 100)

        # Generate insights
        logger.info("💡 GENERATING INSIGHTS")
        logger.info("-" * 50)

        # Identify strengths and gaps
        strengths = []
        gaps = []

        for match in skill_analysis:
            if match.match_level == "strong":
                strengths.append(match.skill)
            elif match.match_level in ["missing", "weak"]:
                gaps.append(match.skill)

        # Generate recommendations
        recommendations_data = self.generate_skill_recommendations(skill_analysis, request.target_role or "")

        # Create analysis summary
        analysis_summary = self.create_gap_analysis_summary(overall_match_score, len(strengths), len(gaps), request.target_role or "")

        logger.info("🎉 SKILL GAP ANALYSIS COMPLETED")
        logger.info("-" * 50)
        logger.info(f"📊 Overall Match Score: {overall_match_score}%")
        logger.info(f"💪 Strengths Identified: {len(strengths)}")
        logger.info(f"🎯 Gaps Identified: {len(gaps)}")
        logger.info("=" * 60)

        return SkillGapAnalysisResponse(
            github_username=request.github_username,
            target_role=request.target_role,
            overall_match_score=overall_match_score,
            skill_analysis=skill_analysis,
            strengths=strengths,
            gaps=gaps,
            recommendations=recommendations_data["recommendations"],
            learning_resources=recommendations_data["learning_resources"],
            analysis_summary=analysis_summary,
            generated_at=datetime.utcnow(),
        )
