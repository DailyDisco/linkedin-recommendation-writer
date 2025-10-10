import asyncio
import logging
import re
from collections import Counter
from datetime import datetime
from typing import Any, Dict, List, Optional, TypedDict

from github import Github

from app.core.config import settings

logger = logging.getLogger(__name__)


class ConventionalStats(TypedDict):
    total_commits: int
    conventional_commits: int
    breaking_changes: int
    types: Dict[str, int]
    scopes: Dict[str, int]
    categories: Dict[str, int]
    conventional_percentage: float
    top_types: Dict[str, int]
    top_categories: Dict[str, int]
    top_scopes: Dict[str, int]


class GitHubCommitService:
    """Service for fetching and analyzing GitHub commit data."""

    MAX_CONCURRENT_REQUESTS = 3  # Limit concurrent GitHub API requests
    REPOSITORY_BATCH_SIZE = 5  # Process repositories in batches
    MAX_COMMITS_PER_REPO = 30  # Max commits per repository for better distribution
    COMMIT_ANALYSIS_CACHE_TTL = 14400  # 4 hours cache for expensive operations

    def __init__(self) -> None:
        """Initialize GitHub commit service."""
        self.github_client = None
        if settings.GITHUB_TOKEN:
            logger.info("🔧 Initializing GitHub client with token for commit service")
            self.github_client = Github(settings.GITHUB_TOKEN)
        else:
            logger.warning("⚠️  GitHub token not configured - GitHub API calls will fail in commit service")

    async def analyze_contributor_commits(
        self,
        username: str,
        repositories: List[Dict[str, Any]],
        max_commits: int = 150,
    ) -> Dict[str, Any]:
        """Analyze up to 150 commits specifically from this contributor across all accessible repositories using async batch processing."""
        try:
            if not self.github_client:
                return self._empty_commit_analysis()

            logger.info(f"🎯 COMMIT ANALYSIS: Targeting {max_commits} commits from contributor: {username}")

            # Create semaphore to limit concurrent GitHub API requests (avoid rate limiting)
            semaphore = asyncio.Semaphore(self.MAX_CONCURRENT_REQUESTS)

            # Split repositories into batches for processing
            repo_batches = [repositories[i : i + self.REPOSITORY_BATCH_SIZE] for i in range(0, len(repositories), self.REPOSITORY_BATCH_SIZE)]

            all_commits = []
            commits_collected = 0

            # For contributor-focused analysis, we want to maximize commits from this specific user
            # Calculate optimal commits per repo, but prioritize repositories with more activity
            optimal_commits_per_repo = self._calculate_contributor_optimal_commits_per_repo(len(repositories), max_commits)

            logger.info(f"📝 Fetching commits specifically from contributor '{username}' across {len(repositories)} repositories")
            logger.info(f"🎯 Target: {max_commits} commits total from this contributor")
            logger.info(f"📊 Strategy: Up to {optimal_commits_per_repo} commits per repository")
            logger.info(f"⚡ Processing in {len(repo_batches)} batches with {self.MAX_CONCURRENT_REQUESTS} concurrent requests")

            # Process repository batches concurrently
            for batch_idx, repo_batch in enumerate(repo_batches):
                if commits_collected >= max_commits:
                    break

                logger.info(f"🔄 Processing batch {batch_idx + 1}/{len(repo_batches)} with {len(repo_batch)} repositories")
                logger.info(f"📊 Current progress: {commits_collected}/{max_commits} commits collected from {username}")

                # Create tasks for concurrent fetching within batch
                batch_tasks = []
                for repo_data in repo_batch:
                    if commits_collected >= max_commits:
                        break

                    # Calculate commits for this repo (prioritize getting commits from this contributor)
                    remaining_commits = max_commits - commits_collected
                    commits_per_repo = min(optimal_commits_per_repo, remaining_commits)

                    # Enhanced task for contributor-specific commit fetching
                    task = self._fetch_contributor_commits_async(semaphore, username, repo_data, commits_per_repo)
                    batch_tasks.append(task)

                # Execute batch concurrently
                batch_results = await asyncio.gather(*batch_tasks, return_exceptions=True)

                # Process results
                for result in batch_results:
                    if isinstance(result, Exception):
                        logger.warning(f"Error in batch task: {result}")
                        continue

                    if isinstance(result, list) and result:
                        commits_to_add = min(len(result), max_commits - commits_collected)
                        all_commits.extend(result[:commits_to_add])
                        commits_collected += commits_to_add

                        if commits_collected >= max_commits:
                            break

                logger.info(f"✅ Batch {batch_idx + 1} completed. Progress: {commits_collected}/{max_commits} commits from {username}")

                # Break if we've collected enough commits
                if commits_collected >= max_commits:
                    logger.info(f"🎯 TARGET REACHED: Collected {max_commits} commits from {username}")
                    break

            logger.info("🎉 COMMIT COLLECTION COMPLETED")
            logger.info(f"📊 Final results: {len(all_commits)} commits analyzed from contributor '{username}'")

            if len(all_commits) < max_commits:
                logger.info(f"ℹ️  Note: Only {len(all_commits)} commits available (target was {max_commits})")

            # Analyze the collected commits with contributor focus
            return self._perform_commit_analysis(all_commits)

        except Exception as e:
            logger.error(f"Error analyzing commits for {username}: {e}")
            return self._empty_commit_analysis()

    async def _fetch_repo_commits_async(
        self,
        semaphore: asyncio.Semaphore,
        username: str,
        repo_data: Dict[str, Any],
        max_commits_per_repo: int,
    ) -> List[Dict[str, Any]]:
        """Fetch commits from a single repository asynchronously with rate limiting."""
        async with semaphore:
            try:
                # Run GitHub API calls in thread pool to avoid blocking
                loop = asyncio.get_event_loop()
                repo_commits = await loop.run_in_executor(
                    None,
                    self._fetch_repo_commits_sync,
                    username,
                    repo_data,
                    max_commits_per_repo,
                )
                return repo_commits

            except Exception as e:
                logger.warning(f"Error fetching commits from {repo_data['name']}: {e}")
                return []

    async def _fetch_contributor_commits_async(
        self,
        semaphore: asyncio.Semaphore,
        contributor_username: str,
        repo_data: Dict[str, Any],
        max_commits_per_repo: int,
    ) -> List[Dict[str, Any]]:
        """Fetch commits specifically from a contributor across any repository they have access to."""
        async with semaphore:
            try:
                # Run GitHub API calls in thread pool to avoid blocking
                loop = asyncio.get_event_loop()
                repo_commits = await loop.run_in_executor(
                    None,
                    self._fetch_contributor_commits_sync,
                    contributor_username,
                    repo_data,
                    max_commits_per_repo,
                )
                return repo_commits

            except Exception as e:
                logger.warning(f"Error fetching commits from contributor {contributor_username} in {repo_data['name']}: {e}")
                return []

    def _fetch_repo_commits_sync(
        self,
        username: str,
        repo_data: Dict[str, Any],
        max_commits_per_repo: int,
    ) -> List[Dict[str, Any]]:
        """Synchronous helper to fetch commits from a repository (runs in thread pool)."""
        if not self.github_client:
            logger.error("GitHub client not initialized")
            return []

        try:
            user = self.github_client.get_user(username)
            repo = self.github_client.get_repo(f"{username}/{repo_data['name']}")
            commits = repo.get_commits(author=user)

            repo_commits = []
            commits_collected = 0

            for commit in commits:
                if commits_collected >= max_commits_per_repo:
                    break

                try:
                    commit_data = {
                        "message": commit.commit.message,
                        "date": (commit.commit.author.date.isoformat() if commit.commit.author.date else None),
                        "repository": repo_data["name"],
                        "sha": commit.sha,
                        "files_changed": (len(list(commit.files)) if hasattr(commit, "files") else 0),
                    }
                    repo_commits.append(commit_data)
                    commits_collected += 1

                except Exception as e:
                    logger.debug(f"Error processing commit {commit.sha}: {e}")
                    continue

            logger.debug(f"Fetched {len(repo_commits)} commits from {repo_data['name']}")
            return repo_commits

        except Exception as e:
            logger.warning(f"Error in sync fetch for {repo_data['name']}: {e}")
            return []

    def _fetch_contributor_commits_sync(
        self,
        contributor_username: str,
        repo_data: Dict[str, Any],
        max_commits_per_repo: int,
    ) -> List[Dict[str, Any]]:
        """Synchronous helper to fetch commits from a specific contributor in any repository."""
        if not self.github_client:
            logger.error("GitHub client not initialized")
            return []

        try:
            # Get the contributor as a user object
            contributor = self.github_client.get_user(contributor_username)

            # Try to access the repository - it might be owned by the contributor or someone else
            repo = None

            # First, try to access as contributor's own repo
            try:
                repo = self.github_client.get_repo(f"{contributor_username}/{repo_data['name']}")
                logger.debug(f"✅ Accessing {repo_data['name']} as {contributor_username}'s own repository")
            except Exception:
                # If that fails, try to access it via the full name if available
                try:
                    if "full_name" in repo_data:
                        repo = self.github_client.get_repo(repo_data["full_name"])
                        logger.debug(f"✅ Accessing {repo_data['full_name']} as contributed repository")
                    elif "url" in repo_data and "/repos/" in repo_data["url"]:
                        # Extract full name from URL
                        repo_full_name = repo_data["url"].split("/repos/")[-1].split("/")[0:2]
                        if len(repo_full_name) == 2:
                            full_repo_name = f"{repo_full_name[0]}/{repo_full_name[1]}"
                            repo = self.github_client.get_repo(full_repo_name)
                            logger.debug(f"✅ Accessing {full_repo_name} via URL extraction")
                except Exception as e2:
                    logger.debug(f"❌ Could not access repository {repo_data['name']}: {e2}")
                    return []

            if not repo:
                logger.debug(f"❌ Could not access repository {repo_data['name']}")
                return []

            # Get commits specifically from this contributor
            commits = repo.get_commits(author=contributor)

            repo_commits = []
            commits_collected = 0

            logger.debug(f"🔍 Scanning {repo_data['name']} for commits from {contributor_username}")

            for commit in commits:
                if commits_collected >= max_commits_per_repo:
                    break

                try:
                    commit_data = {
                        "message": commit.commit.message,
                        "date": (commit.commit.author.date.isoformat() if commit.commit.author.date else None),
                        "repository": repo_data["name"],
                        "repository_full_name": repo.full_name,
                        "sha": commit.sha,
                        "files_changed": (len(list(commit.files)) if hasattr(commit, "files") else 0),
                        "contributor": contributor_username,
                    }
                    repo_commits.append(commit_data)
                    commits_collected += 1

                except Exception as e:
                    logger.debug(f"Error processing commit {commit.sha}: {e}")
                    continue

            if repo_commits:
                logger.debug(f"✅ Found {len(repo_commits)} commits from {contributor_username} in {repo_data['name']}")
            else:
                logger.debug(f"ℹ️  No commits found from {contributor_username} in {repo_data['name']}")

            return repo_commits

        except Exception as e:
            logger.warning(f"Error fetching contributor commits from {repo_data['name']}: {e}")
            return []

    def _calculate_optimal_commits_per_repo(self, total_repos: int, max_commits: int) -> int:
        """Calculate optimal commits per repository for better distribution."""
        if total_repos == 0:
            return self.MAX_COMMITS_PER_REPO

        # Calculate ideal distribution
        ideal_per_repo = max_commits // total_repos

        # Ensure minimum commits per repo but respect maximum
        optimal = max(5, min(ideal_per_repo, self.MAX_COMMITS_PER_REPO))

        # If we have very few repos, increase commits per repo
        if total_repos <= 3:
            optimal = min(50, max_commits // max(1, total_repos))

        return optimal

    def _calculate_contributor_optimal_commits_per_repo(self, total_repos: int, max_commits: int) -> int:
        """Calculate optimal commits per repository specifically for contributor analysis."""
        if total_repos == 0:
            return self.MAX_COMMITS_PER_REPO

        # For contributor-focused analysis, we want to be more aggressive in collecting commits
        # since we're specifically targeting this person's contributions

        # Calculate ideal distribution
        ideal_per_repo = max_commits // total_repos

        # For contributor analysis, we want a higher minimum to ensure we capture their work
        # Even from repositories where they might have fewer commits
        min_commits_per_repo = 10  # Higher minimum for contributor analysis
        optimal = max(
            min_commits_per_repo,
            min(ideal_per_repo, self.MAX_COMMITS_PER_REPO),
        )

        # If we have very few repos, we can afford to get more commits per repo
        if total_repos <= 2:
            optimal = min(75, max_commits // max(1, total_repos))  # Higher for few repos
        elif total_repos <= 5:
            optimal = min(50, max_commits // max(1, total_repos))  # Moderate for few repos

        return optimal

    def _parse_conventional_commit(self, commit_message: str) -> Dict[str, Any]:
        """Parse a commit message for conventional commit format and extract structured information."""
        # Conventional commit pattern: type(scope): description
        conventional_pattern = r"^(?P<type>\w+)(?:\((?P<scope>[^\)]+)\))?: (?P<description>.+)$"

        # Breaking change pattern
        breaking_pattern = r"BREAKING CHANGE: (.+)$"

        # Common conventional commit types and their meanings
        commit_types = {
            "feat": {"category": "feature_development", "description": "New feature"},
            "fix": {"category": "bug_fixing", "description": "Bug fix"},
            "docs": {"category": "documentation", "description": "Documentation"},
            "style": {"category": "code_quality", "description": "Code style changes"},
            "refactor": {"category": "refactoring", "description": "Code refactoring"},
            "test": {"category": "testing", "description": "Testing"},
            "chore": {"category": "maintenance", "description": "Maintenance"},
            "perf": {"category": "optimization", "description": "Performance improvement"},
            "ci": {"category": "ci_cd", "description": "CI/CD changes"},
            "build": {"category": "build", "description": "Build system changes"},
            "revert": {"category": "maintenance", "description": "Revert changes"},
        }

        result = {
            "is_conventional": False,
            "type": None,
            "scope": None,
            "description": commit_message.strip(),
            "category": "other",
            "is_breaking_change": False,
            "breaking_description": None,
            "impact_level": "minor",  # minor, moderate, major
        }

        # Check for conventional commit format
        match = re.match(conventional_pattern, commit_message.strip(), re.IGNORECASE)
        if match:
            result["is_conventional"] = True
            result["type"] = match.group("type").lower()
            result["scope"] = match.group("scope").lower() if match.group("scope") else None
            result["description"] = match.group("description").strip()

            # Map to category
            if result["type"]:
                assert isinstance(result["type"], str)
                if result["type"] in commit_types:
                    result["category"] = commit_types[result["type"]]["category"]

            # Determine impact level based on type
            if result["type"] in ["feat", "perf"]:
                result["impact_level"] = "moderate"
            elif result["type"] in ["fix", "refactor"]:
                result["impact_level"] = "minor"
            elif result["type"] in ["revert"]:
                result["impact_level"] = "major"

        # Check for breaking changes
        breaking_match = re.search(breaking_pattern, commit_message, re.IGNORECASE | re.MULTILINE)
        if breaking_match:
            result["is_breaking_change"] = True
            result["breaking_description"] = breaking_match.group(1).strip()
            result["impact_level"] = "major"

        return result

    def _analyze_commit_impact(self, commit_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze the impact and significance of a single commit."""
        message = commit_data.get("message", "")
        files_changed = commit_data.get("files_changed", 0)

        # Parse conventional commit
        conventional_info = self._parse_conventional_commit(message)

        # Calculate impact score based on multiple factors
        impact_score = 0

        # Conventional commit bonus
        if conventional_info["is_conventional"]:
            impact_score += 20

        # Breaking change bonus
        if conventional_info["is_breaking_change"]:
            impact_score += 30

        # Files changed impact
        if files_changed > 0:
            if files_changed <= 3:
                impact_score += 10
            elif files_changed <= 10:
                impact_score += 20
            elif files_changed <= 20:
                impact_score += 30
            else:
                impact_score += 40

        # Message length and detail
        message_words = len(message.split())
        if message_words > 50:
            impact_score += 15
        elif message_words > 20:
            impact_score += 10
        elif message_words > 10:
            impact_score += 5

        # Keywords that indicate significance
        significant_keywords = [
            "breaking",
            "major",
            "critical",
            "security",
            "performance",
            "optimization",
            "architecture",
            "design",
            "api",
            "database",
        ]
        message_lower = message.lower()
        keyword_count = sum(1 for keyword in significant_keywords if keyword in message_lower)
        impact_score += keyword_count * 5

        # Determine impact level
        if impact_score >= 70:
            impact_level = "high"
        elif impact_score >= 40:
            impact_level = "moderate"
        elif impact_score >= 20:
            impact_level = "low"
        else:
            impact_level = "minimal"

        return {
            "impact_score": impact_score,
            "impact_level": impact_level,
            "conventional_info": conventional_info,
            "files_changed": files_changed,
            "message_quality": "high" if message_words > 20 else "medium" if message_words > 10 else "low",
        }

    def _analyze_conventional_commits(self, commits: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze conventional commit patterns across all commits."""
        conventional_commits: List[Dict[str, Any]] = []
        conventional_stats: ConventionalStats = {
            "total_commits": len(commits),
            "conventional_commits": 0,
            "breaking_changes": 0,
            "types": {},
            "scopes": {},
            "categories": {},
            "conventional_percentage": 0.0,  # Initialize with default value
            "top_types": {},
            "top_categories": {},
            "top_scopes": {},
        }

        for commit in commits:
            message = commit.get("message", "")
            conventional_info = self._parse_conventional_commit(message)

            if conventional_info["is_conventional"]:
                conventional_commits.append(
                    {
                        "commit": commit,
                        "conventional_info": conventional_info,
                    }
                )

                conventional_stats["conventional_commits"] += 1

                # Track commit types
                commit_type = conventional_info["type"]
                conventional_stats["types"][commit_type] = conventional_stats["types"].get(commit_type, 0) + 1

                # Track scopes
                if conventional_info["scope"]:
                    scope = conventional_info["scope"]
                    conventional_stats["scopes"][scope] = conventional_stats["scopes"].get(scope, 0) + 1

                # Track categories
                category = conventional_info["category"]
                conventional_stats["categories"][category] = conventional_stats["categories"].get(category, 0) + 1

                # Track breaking changes
                if conventional_info["is_breaking_change"]:
                    conventional_stats["breaking_changes"] += 1

        # Calculate percentages
        conventional_stats["conventional_percentage"] = (
            round((conventional_stats["conventional_commits"] / conventional_stats["total_commits"]) * 100, 1) if conventional_stats["total_commits"] > 0 else 0
        )

        # Sort types and categories by frequency
        conventional_stats["top_types"] = dict(sorted(conventional_stats["types"].items(), key=lambda x: x[1], reverse=True)[:5])
        conventional_stats["top_categories"] = dict(sorted(conventional_stats["categories"].items(), key=lambda x: x[1], reverse=True)[:5])
        conventional_stats["top_scopes"] = dict(sorted(conventional_stats["scopes"].items(), key=lambda x: x[1], reverse=True)[:5])

        return {
            "stats": conventional_stats,
            "conventional_commits": conventional_commits,
            "quality_score": self._calculate_conventional_quality_score(conventional_stats),
        }

    def _calculate_conventional_quality_score(self, conventional_stats: ConventionalStats) -> float:
        """Calculate a quality score based on conventional commit adherence."""
        score = 0.0

        total_commits = conventional_stats["total_commits"]
        conventional_commits_count = conventional_stats["conventional_commits"]
        breaking_changes_count = conventional_stats["breaking_changes"]
        types = conventional_stats["types"]
        scopes = conventional_stats["scopes"]

        # Conventional commit adoption (40 points max)
        if total_commits > 0:
            conventional_percentage = (conventional_commits_count / total_commits) * 100
            score += min(conventional_percentage * 0.4, 40)

        # Type diversity (30 points max)
        unique_types = len(types)
        score += min(unique_types * 10, 30)

        # Scope usage (20 points max)
        scope_usage = len(scopes)
        score += min(scope_usage * 5, 20)

        # Breaking changes (10 points max, penalize if too many, reward if handled well)
        # For simplicity, we'll give points for having breaking changes as it implies significant work,
        # but ideally, this would be more nuanced.
        score += min(breaking_changes_count * 2, 10)

        return round(score, 1)

    def _perform_commit_analysis(self, commits: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Perform comprehensive analysis of commits."""
        if not commits:
            return self._empty_commit_analysis()

        commit_messages = [commit["message"].lower() for commit in commits]

        # Enhanced commit analysis with conventional commit parsing
        conventional_analysis = self._analyze_conventional_commits(commits)
        impact_analysis = self._analyze_commit_impacts(commits)

        # Analyze what the user excels at (action patterns) - enhanced with conventional commit data
        excellence_patterns = self._analyze_excellence_patterns(commit_messages, conventional_analysis)

        # Analyze tools and features added
        tools_and_features = self._analyze_tools_and_features(commit_messages)

        # Analyze commit frequency and consistency - enhanced with impact data
        commit_patterns = self._analyze_commit_patterns(commits, impact_analysis)

        # Extract technical contributions - enhanced with conventional commit categories
        technical_contributions = self._analyze_technical_contributions(commit_messages, conventional_analysis)

        # Calculate contributor-specific metrics - enhanced with impact analysis
        contributor_metrics = self._calculate_contributor_metrics(commits, impact_analysis)

        return {
            "total_commits_analyzed": len(commits),
            "contributor_focused": True,
            "analysis_method": "contributor_specific_enhanced",
            "conventional_commit_analysis": conventional_analysis,
            "impact_analysis": impact_analysis,
            "excellence_areas": excellence_patterns,
            "tools_and_features": tools_and_features,
            "commit_patterns": commit_patterns,
            "technical_contributions": technical_contributions,
            "top_repositories": self._get_top_commit_repositories(commits),
            "contributor_metrics": contributor_metrics,
        }

    def _analyze_excellence_patterns(self, commit_messages: List[str], conventional_analysis: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Identify what the user excels at based on commit message patterns with enhanced analysis."""
        excellence_keywords = {
            "bug_fixing": ["fix", "bug", "resolve", "patch", "correct", "debug", "issue", "error", "crash", "hotfix", "quickfix", "workaround", "regression", "defect", "fault", "problem"],
            "feature_development": ["add", "implement", "create", "build", "develop", "feature", "new", "introduce", "launch", "deploy", "rollout", "integrate", "connect", "establish", "setup"],
            "optimization": ["optimize", "improve", "enhance", "performance", "speed", "efficient", "faster", "quicker", "accelerate", "boost", "streamline", "refine", "tune", "polish"],
            "refactoring": ["refactor", "restructure", "reorganize", "clean", "simplify", "tidy", "modernize", "upgrade", "migrate", "consolidate", "extract", "split", "merge", "rename"],
            "testing": ["test", "testing", "spec", "coverage", "unit", "integration", "e2e", "qa", "verify", "validate", "assert", "mock", "stub", "fixture", "suite"],
            "documentation": ["doc", "comment", "documentation", "guide", "wiki", "tutorial", "example", "sample", "demo", "explain", "describe", "clarify"],
            "security": ["security", "auth", "secure", "vulnerability", "encrypt", "protect", "safe", "access", "permission", "authorization", "authentication", "ssl", "https"],
            "ui_ux": ["ui", "ux", "interface", "design", "styling", "css", "frontend", "user", "experience", "interaction", "responsive", "mobile", "web", "layout", "theme"],
            "data_handling": ["data", "database", "query", "sql", "nosql", "migration", "schema", "model", "entity", "table", "collection", "index", "cache", "store"],
            "api_development": ["api", "endpoint", "rest", "graphql", "http", "request", "response", "service", "microservice", "client", "server", "route", "controller"],
            "devops_automation": ["ci", "cd", "pipeline", "deploy", "build", "automation", "script", "config", "infrastructure", "docker", "kubernetes", "cloud", "aws", "azure"],
            "code_quality": ["lint", "format", "style", "quality", "standard", "convention", "consistency", "maintain", "sustainable", "readable", "clear"],
        }

        pattern_counts = {}
        total_commits = len(commit_messages)

        # Base keyword analysis
        for category, keywords in excellence_keywords.items():
            count = sum(1 for message in commit_messages if any(keyword in message for keyword in keywords))
            if count > 0:
                pattern_counts[category] = {
                    "count": count,
                    "percentage": round((count / total_commits) * 100, 1),
                }

        # Enhance with conventional commit analysis if available
        if conventional_analysis:
            conventional_stats = conventional_analysis.get("stats", {})

            # Map conventional commit categories to excellence areas
            conventional_to_excellence = {
                "feature_development": "feature_development",
                "bug_fixing": "bug_fixing",
                "refactoring": "refactoring",
                "testing": "testing",
                "documentation": "documentation",
                "optimization": "optimization",
                "code_quality": "refactoring",
                "maintenance": "refactoring",
                "ci_cd": "testing",
                "build": "refactoring",
            }

            # Boost categories that have conventional commit evidence
            for conv_category, excellence_category in conventional_to_excellence.items():
                if conv_category in conventional_stats.get("categories", {}):
                    conv_count = conventional_stats["categories"][conv_category]

                    if excellence_category in pattern_counts:
                        # Boost existing category
                        pattern_counts[excellence_category]["count"] += conv_count * 0.5  # Partial boost
                        pattern_counts[excellence_category]["percentage"] = round((pattern_counts[excellence_category]["count"] / total_commits) * 100, 1)
                    else:
                        # Add new category based on conventional commits
                        pattern_counts[excellence_category] = {
                            "count": conv_count,
                            "percentage": round((conv_count / total_commits) * 100, 1),
                        }

            # Add conventional commit quality score
            conventional_quality = conventional_analysis.get("quality_score", 0)
            if conventional_quality > 70:
                # Boost code quality if they use conventional commits well
                if "refactoring" in pattern_counts:
                    pattern_counts["refactoring"]["count"] += conventional_quality * 0.1
                    pattern_counts["refactoring"]["percentage"] = round((pattern_counts["refactoring"]["count"] / total_commits) * 100, 1)

        # Sort by frequency
        sorted_patterns = dict(
            sorted(
                pattern_counts.items(),
                key=lambda x: x[1]["count"],
                reverse=True,
            )
        )

        # Infer soft skills from technical patterns
        soft_skills_inference = self._infer_soft_skills_from_patterns(sorted_patterns)

        return {
            "patterns": sorted_patterns,
            "primary_strength": (list(sorted_patterns.keys())[0] if sorted_patterns else None),
            "conventional_commit_enhanced": conventional_analysis is not None,
            "inferred_soft_skills": soft_skills_inference,
        }

    def _infer_soft_skills_from_patterns(self, excellence_patterns: Dict[str, Any], pr_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Infer soft skills from technical excellence patterns and PR data."""
        soft_skills_map = {
            "problem_solving": {
                "patterns": ["bug_fixing", "optimization", "refactoring"],
                "description": "Analytical thinking and problem-solving abilities",
                "evidence": "Consistently addresses complex technical challenges",
            },
            "attention_to_detail": {
                "patterns": ["testing", "code_quality", "security"],
                "description": "Meticulous attention to detail and quality",
                "evidence": "Focuses on thorough testing and code quality assurance",
            },
            "innovation_creativity": {
                "patterns": ["feature_development", "optimization", "ui_ux"],
                "description": "Creative problem-solving and innovative thinking",
                "evidence": "Develops new features and optimizes existing solutions",
            },
            "reliability": {
                "patterns": ["bug_fixing", "testing", "security"],
                "description": "Reliable and dependable work approach",
                "evidence": "Consistently fixes issues and maintains system stability",
            },
            "continuous_learning": {
                "patterns": ["feature_development", "api_development", "devops_automation"],
                "description": "Commitment to learning and adopting new technologies",
                "evidence": "Works with diverse technologies and modern frameworks",
            },
            "collaboration": {
                "patterns": ["documentation", "code_quality", "refactoring"],
                "description": "Team-oriented approach to development",
                "evidence": "Creates well-documented, maintainable code for team success",
            },
            "communication": {
                "patterns": ["documentation", "code_quality"],
                "description": "Clear and effective communication skills",
                "evidence": "Articulates technical decisions and maintains clear documentation",
            },
            "leadership": {
                "patterns": ["refactoring", "devops_automation", "api_development"],
                "description": "Technical leadership and system architecture",
                "evidence": "Architects and refactors complex systems",
            },
            "adaptability": {
                "patterns": ["data_handling", "api_development", "devops_automation"],
                "description": "Flexibility in working with different technologies",
                "evidence": "Adapts to various technical domains and challenges",
            },
        }

        inferred_skills = {}
        pattern_names = set(excellence_patterns.keys())

        for soft_skill, config in soft_skills_map.items():
            matching_patterns = pattern_names.intersection(set(config["patterns"]))
            if matching_patterns:
                # Calculate confidence based on number of matching patterns and their strength
                confidence = min(len(matching_patterns) * 25, 100)  # Max 100 confidence
                # Boost confidence if primary pattern matches
                primary_pattern = list(excellence_patterns.keys())[0] if excellence_patterns else None
                if primary_pattern and primary_pattern in matching_patterns:
                    confidence = min(confidence + 20, 100)

                inferred_skills[soft_skill] = {"description": config["description"], "evidence": config["evidence"], "confidence": confidence, "supporting_patterns": list(matching_patterns)}

        # Enhance with PR data if available
        if pr_data and "pr_analysis" in pr_data:
            pr_analysis = pr_data["pr_analysis"]

            # Boost collaboration skill based on PR review participation
            collaboration_patterns = pr_analysis.get("collaboration_patterns", {})
            if collaboration_patterns.get("discussion_quality") == "high":
                if "collaboration" in inferred_skills:
                    inferred_skills["collaboration"]["confidence"] = min(inferred_skills["collaboration"]["confidence"] + 15, 100)
                    inferred_skills["collaboration"]["evidence"] += " | Active PR review participation"
                else:
                    inferred_skills["collaboration"] = {
                        "description": "Team-oriented approach to development",
                        "evidence": "Active PR review participation and constructive feedback",
                        "confidence": 70,
                        "supporting_patterns": ["pr_collaboration"],
                    }

            # Boost communication skill based on PR discussions
            if collaboration_patterns.get("avg_review_comments_per_pr", 0) > 2:
                if "communication" in inferred_skills:
                    inferred_skills["communication"]["confidence"] = min(inferred_skills["communication"]["confidence"] + 15, 100)
                    inferred_skills["communication"]["evidence"] += " | Engages in detailed code review discussions"
                else:
                    inferred_skills["communication"] = {
                        "description": "Clear and effective communication skills",
                        "evidence": "Engages in detailed code review discussions",
                        "confidence": 70,
                        "supporting_patterns": ["pr_communication"],
                    }

            # Boost reliability based on PR merge rate
            pr_metrics = pr_analysis.get("pr_metrics", {})
            if pr_metrics.get("merge_rate", 0) > 70:
                if "reliability" in inferred_skills:
                    inferred_skills["reliability"]["confidence"] = min(inferred_skills["reliability"]["confidence"] + 10, 100)
                    inferred_skills["reliability"]["evidence"] += f" | High PR merge rate ({pr_metrics['merge_rate']}%)"

        # Sort by confidence
        sorted_skills = dict(
            sorted(
                inferred_skills.items(),
                key=lambda x: x[1]["confidence"],
                reverse=True,
            )
        )

        return {"skills": sorted_skills, "top_soft_skill": list(sorted_skills.keys())[0] if sorted_skills else None, "inference_method": "pattern_and_pr_based_analysis" if pr_data else "pattern_based_analysis"}

    def _analyze_tools_and_features(self, commit_messages: List[str]) -> Dict[str, Any]:
        """Extract tools, libraries, and features mentioned in commits."""
        # Common tools and technologies to look for
        tool_patterns = {
            "databases": [
                "sql",
                "mongodb",
                "postgres",
                "mysql",
                "redis",
                "sqlite",
            ],
            "frameworks": [
                "react",
                "vue",
                "angular",
                "django",
                "flask",
                "express",
                "spring",
            ],
            "cloud_services": [
                "aws",
                "azure",
                "gcp",
                "docker",
                "kubernetes",
                "heroku",
            ],
            "testing_tools": [
                "jest",
                "pytest",
                "mocha",
                "cypress",
                "selenium",
            ],
            "build_tools": [
                "webpack",
                "vite",
                "gulp",
                "grunt",
                "maven",
                "gradle",
            ],
            "monitoring": [
                "logging",
                "monitoring",
                "metrics",
                "analytics",
                "sentry",
            ],
        }

        found_tools = {}
        feature_keywords = []

        # Extract tools
        for category, tools in tool_patterns.items():
            category_tools = []
            for message in commit_messages:
                for tool in tools:
                    if tool in message and tool not in category_tools:
                        category_tools.append(tool)
            if category_tools:
                found_tools[category] = category_tools

        # Extract feature-related keywords using regex
        feature_pattern = re.compile(r"(?:add|implement|create|build)\s+([a-zA-Z\s]{3,20})")
        for message in commit_messages:
            matches = feature_pattern.findall(message)
            feature_keywords.extend([match.strip() for match in matches])

        # Count feature frequencies
        feature_counter = Counter(feature_keywords)
        top_features = dict(feature_counter.most_common(10))

        return {
            "tools_by_category": found_tools,
            "features_implemented": top_features,
            "total_unique_tools": sum(len(tools) for tools in found_tools.values()),
        }

    def _analyze_commit_patterns(self, commits: List[Dict[str, Any]], impact_analysis: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Analyze commit frequency and timing patterns."""
        if not commits:
            return {}

        dates = [datetime.fromisoformat(commit["date"].replace("Z", "+00:00")) for commit in commits if commit["date"]]

        if not dates:
            return {}

        # Calculate time spans and frequency
        dates.sort()
        total_days = (dates[-1] - dates[0]).days if len(dates) > 1 else 1
        commits_per_day = len(commits) / max(total_days, 1)

        # Analyze file change patterns
        files_changed = [commit["files_changed"] for commit in commits if commit["files_changed"]]
        avg_files_per_commit = sum(files_changed) / len(files_changed) if files_changed else 0

        result = {
            "commits_per_day": round(commits_per_day, 2),
            "avg_files_per_commit": round(avg_files_per_commit, 1),
            "total_days_active": total_days,
            "consistency_score": min(commits_per_day * 10, 100),  # Scale to 0-100
        }

        # Enhance with impact analysis if available
        if impact_analysis:
            result.update(
                {
                    "impact_distribution": impact_analysis.get("distribution", {}),
                    "average_impact_score": impact_analysis.get("average_impact_score", 0),
                    "high_impact_commits_count": len(impact_analysis.get("high_impact_commits", [])),
                    "impact_quality_distribution": impact_analysis.get("quality_distribution", {}),
                }
            )

            # Calculate impact-weighted consistency score
            avg_impact = impact_analysis.get("average_impact_score", 0)
            base_consistency = result["consistency_score"]
            impact_weighted_score = min((base_consistency + avg_impact) / 2, 100)
            result["impact_weighted_consistency"] = round(impact_weighted_score, 1)

        return result

    def _analyze_technical_contributions(self, commit_messages: List[str], conventional_analysis: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Analyze technical depth and contribution types."""
        technical_indicators = {
            "architecture": [
                "architecture",
                "design pattern",
                "structure",
                "architecture",
            ],
            "performance": [
                "performance",
                "optimization",
                "caching",
                "lazy loading",
            ],
            "scalability": [
                "scalable",
                "scale",
                "horizontal",
                "vertical",
                "load",
            ],
            "maintainability": [
                "maintainable",
                "clean code",
                "readable",
                "modular",
            ],
            "integration": [
                "api",
                "integration",
                "webhook",
                "service",
                "endpoint",
            ],
        }

        contributions = {}
        for category, indicators in technical_indicators.items():
            count = sum(1 for message in commit_messages if any(indicator in message for indicator in indicators))
            if count > 0:
                contributions[category] = count

        # Enhance with conventional commit analysis if available
        if conventional_analysis:
            conventional_stats = conventional_analysis.get("stats", {})

            # Map conventional commit types to technical contributions
            conventional_to_technical = {
                "architecture": ["feat", "refactor"],
                "performance": ["perf", "optimize"],
                "scalability": ["feat", "refactor"],
                "maintainability": ["refactor", "docs"],
                "integration": ["feat", "ci"],
            }

            # Boost technical contributions based on conventional commit evidence
            for tech_category, conv_types in conventional_to_technical.items():
                conv_count = sum(conventional_stats.get("types", {}).get(conv_type, 0) for conv_type in conv_types)

                if conv_count > 0:
                    if tech_category in contributions:
                        contributions[tech_category] += conv_count
                    else:
                        contributions[tech_category] = conv_count

            # Add conventional commit quality metrics
            conventional_quality = conventional_analysis.get("quality_score", 0)
            if conventional_quality > 0:
                contributions["conventional_commit_quality"] = conventional_quality

        return contributions

    def _get_top_commit_repositories(self, commits: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Get repositories with most commits from the user."""
        repo_counts = Counter(commit["repository"] for commit in commits)
        top_repos = []

        for repo_name, count in repo_counts.most_common(5):
            top_repos.append(
                {
                    "repository": repo_name,
                    "commits": count,
                    "percentage": round((count / len(commits)) * 100, 1),
                }
            )

        return top_repos

    def _calculate_contributor_metrics(self, commits: List[Dict[str, Any]], impact_analysis: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Calculate contributor-specific metrics from commits."""
        if not commits:
            return {
                "repositories_with_commits": 0,
                "avg_commits_per_repo": 0,
                "most_active_repository": None,
                "commit_frequency_analysis": {},
                "contribution_span_days": 0,
            }

        # Repository analysis
        repo_counts: Dict[str, int] = {}
        for commit in commits:
            repo_name = commit.get("repository", "unknown")
            repo_counts[repo_name] = repo_counts.get(repo_name, 0) + 1

        repositories_with_commits = len(repo_counts)
        avg_commits_per_repo = len(commits) / repositories_with_commits if repositories_with_commits > 0 else 0
        most_active_repo = max(repo_counts.items(), key=lambda x: x[1]) if repo_counts else None

        # Time span analysis
        dates = []
        for commit in commits:
            if commit.get("date"):
                try:
                    commit_date = datetime.fromisoformat(commit["date"].replace("Z", "+00:00"))
                    dates.append(commit_date)
                except Exception:
                    continue

        contribution_span_days = 0
        if len(dates) > 1:
            dates.sort()
            contribution_span_days = (dates[-1] - dates[0]).days

        # Frequency analysis
        commit_frequency_analysis = {
            "daily_average": (len(commits) / max(1, contribution_span_days) if contribution_span_days > 0 else 0),
            "most_productive_repo": most_active_repo[0] if most_active_repo else None,
            "most_productive_repo_commits": (most_active_repo[1] if most_active_repo else 0),
            "repository_diversity_score": (min(100, (repositories_with_commits / len(commits)) * 100) if commits else 0),
        }

        result = {
            "repositories_with_commits": repositories_with_commits,
            "avg_commits_per_repo": round(avg_commits_per_repo, 1),
            "most_active_repository": most_active_repo[0] if most_active_repo else None,
            "commit_frequency_analysis": commit_frequency_analysis,
            "contribution_span_days": contribution_span_days,
        }

        # Enhance with impact analysis if available
        if impact_analysis:
            result.update(
                {
                    "impact_metrics": {
                        "average_impact_score": impact_analysis.get("average_impact_score", 0),
                        "high_impact_commits": len(impact_analysis.get("high_impact_commits", [])),
                        "impact_distribution": impact_analysis.get("distribution", {}),
                        "conventional_high_impact": len(impact_analysis.get("conventional_high_impact", [])),
                    },
                    "quality_metrics": {
                        "impact_quality_distribution": impact_analysis.get("quality_distribution", {}),
                        "impact_score_range": impact_analysis.get("impact_score_range", {}),
                    },
                }
            )

            # Calculate impact-weighted productivity metrics
            high_impact_count = len(impact_analysis.get("high_impact_commits", []))
            total_commits = len(commits)
            if total_commits > 0:
                impact_productivity_ratio = high_impact_count / total_commits
                result["impact_productivity_ratio"] = round(impact_productivity_ratio * 100, 1)

        return result

    def _empty_commit_analysis(self) -> Dict[str, Any]:
        """Return empty commit analysis structure for contributor-focused analysis."""
        return {
            "total_commits_analyzed": 0,
            "contributor_focused": True,
            "analysis_method": "contributor_specific_enhanced",
            "conventional_commit_analysis": {
                "stats": {
                    "total_commits": 0,
                    "conventional_commits": 0,
                    "breaking_changes": 0,
                    "types": {},
                    "scopes": {},
                    "categories": {},
                    "conventional_percentage": 0,
                    "top_types": {},
                    "top_categories": {},
                    "top_scopes": {},
                },
                "conventional_commits": [],
                "quality_score": 0,
            },
            "impact_analysis": {
                "distribution": {"high": 0, "moderate": 0, "low": 0, "minimal": 0},
                "average_impact_score": 0,
                "high_impact_commits": [],
                "conventional_high_impact": [],
                "impact_score_range": {"min": 0, "max": 0, "median": 0},
                "quality_distribution": {"high": 0, "moderate": 0, "low": 0, "minimal": 0},
            },
            "excellence_areas": {"patterns": {}, "primary_strength": None, "conventional_commit_enhanced": False},
            "tools_and_features": {
                "tools_by_category": {},
                "features_implemented": {},
                "total_unique_tools": 0,
            },
            "commit_patterns": {},
            "technical_contributions": {},
            "top_repositories": [],
            "contributor_metrics": {
                "repositories_with_commits": 0,
                "avg_commits_per_repo": 0,
                "most_active_repository": None,
            },
        }

    async def generate_contributor_commit_summary(self, username: str, repository_full_name: str, max_commits: int = 50) -> Dict[str, Any]:
        """Generate a comprehensive summary of a contributor's commits and PRs for recommendation purposes."""
        try:
            if not self.github_client:
                logger.warning("⚠️  GitHub client not available for commit summary generation")
                return self._empty_contributor_summary()

            # Parse repository info
            repo_parts = repository_full_name.split("/")
            if len(repo_parts) != 2:
                logger.error(f"Invalid repository name format: {repository_full_name}")
                return self._empty_contributor_summary()

            owner, repo_name = repo_parts

            # Get repository and user data
            repo = self.github_client.get_repo(repository_full_name)
            user = self.github_client.get_user(username)

            # Get contributor's commits
            contributor_commits = []
            try:
                commits = repo.get_commits(author=user, since=None)
                for commit in commits[:max_commits]:
                    commit_data = {
                        "sha": commit.sha,
                        "message": commit.commit.message,
                        "date": commit.commit.author.date.isoformat() if commit.commit.author else None,
                        "files_changed": len(list(commit.files)) if commit.files else 0,
                        "additions": commit.stats.additions if commit.stats else 0,
                        "deletions": commit.stats.deletions if commit.stats else 0,
                        "repository": repository_full_name,
                    }
                    contributor_commits.append(commit_data)
            except Exception as e:
                logger.warning(f"Could not fetch commits for {username} in {repository_full_name}: {e}")

            # Get contributor's pull requests
            contributor_prs = []
            try:
                pulls = repo.get_pulls(state="all", sort="created", direction="desc")
                for pr in pulls:
                    if pr.user.login == username:
                        pr_data = {
                            "number": pr.number,
                            "title": pr.title,
                            "body": pr.body[:500] if pr.body else "",  # Truncate body
                            "state": pr.state,
                            "created_at": pr.created_at.isoformat(),
                            "merged_at": pr.merged_at.isoformat() if pr.merged_at else None,
                            "additions": pr.additions,
                            "deletions": pr.deletions,
                            "changed_files": pr.changed_files,
                            "review_comments": pr.review_comments,
                            "labels": [label.name for label in pr.labels],
                        }
                        contributor_prs.append(pr_data)
            except Exception as e:
                logger.warning(f"Could not fetch PRs for {username} in {repository_full_name}: {e}")

            # Analyze commits and PRs
            summary = self._analyze_contributor_activity(contributor_commits, contributor_prs)

            return {
                "contributor": username,
                "repository": repository_full_name,
                "total_commits": len(contributor_commits),
                "total_prs": len(contributor_prs),
                "summary": summary,
                "generated_at": datetime.now().isoformat(),
            }

        except Exception as e:
            logger.error(f"Error generating contributor commit summary: {e}")
            return self._empty_contributor_summary()

    def _analyze_contributor_activity(self, commits: List[Dict[str, Any]], prs: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze contributor's commits and PRs to generate insights for recommendations."""
        insights = {
            "technical_focus": [],
            "collaboration_patterns": [],
            "problem_solving_approaches": [],
            "code_quality_indicators": [],
            "impact_areas": [],
            "key_achievements": [],
            "work_patterns": [],
        }

        # Analyze commit messages for technical focus
        commit_messages = [commit["message"] for commit in commits]
        technical_patterns = self._extract_technical_patterns(commit_messages)
        insights["technical_focus"] = technical_patterns

        # Analyze PR patterns
        if prs:
            pr_analysis = self._analyze_pr_patterns(prs)
            insights.update(pr_analysis)

        # Extract key achievements
        achievements = self._extract_key_achievements(commits, prs)
        insights["key_achievements"] = achievements

        # Analyze work patterns
        patterns = self._analyze_work_patterns(commits, prs)
        insights["work_patterns"] = patterns

        return insights

    def _extract_technical_patterns(self, commit_messages: List[str]) -> List[str]:
        """Extract technical focus areas from commit messages with enhanced pattern detection."""
        patterns = []

        # Enhanced technical patterns with specific problem types
        tech_indicators = {
            "frontend": ["ui", "component", "react", "vue", "angular", "frontend", "interface", "ux", "styling"],
            "backend": ["api", "server", "database", "endpoint", "service", "backend", "authentication", "security"],
            "testing": ["test", "spec", "unit", "integration", "coverage", "assert", "mock"],
            "performance": ["optimize", "performance", "speed", "memory", "cache", "efficiency"],
            "architecture": ["refactor", "architecture", "structure", "design", "pattern"],
            "bug_fixing": ["fix", "bug", "issue", "resolve", "correct", "patch"],
            "features": ["feature", "implement", "add", "create", "build", "develop"],
        }

        # Specific problem types (enhanced detection)
        problem_types = {
            "memory_management": ["memory leak", "memory optimization", "garbage collection", "heap", "memory usage"],
            "concurrency": ["race condition", "deadlock", "thread", "concurrency", "async", "parallel"],
            "database_optimization": ["query optimization", "index", "database performance", "n+1", "slow query"],
            "security_fixes": ["vulnerability", "xss", "sql injection", "csrf", "authentication", "authorization"],
        }

        # Architectural patterns (enhanced detection)
        architectural_patterns = {
            "design_patterns": ["singleton", "factory", "observer", "strategy", "decorator", "adapter"],
            "architectural_styles": ["mvc", "mvvm", "microservices", "event-driven", "layered", "hexagonal"],
        }

        # Integration patterns (enhanced detection)
        integration_patterns = {
            "api_types": ["rest api", "graphql", "websocket", "grpc", "soap"],
            "messaging": ["message queue", "pub/sub", "event bus", "kafka", "rabbitmq"],
        }

        # Check standard technical indicators
        for category, keywords in tech_indicators.items():
            matches = sum(1 for msg in commit_messages for keyword in keywords if keyword.lower() in msg.lower())
            if matches > 0:
                patterns.append(f"{category.replace('_', ' ').title()}: {matches} contributions")

        # Check specific problem types
        for category, keywords in problem_types.items():
            matches = sum(1 for msg in commit_messages for keyword in keywords if keyword.lower() in msg.lower())
            if matches > 0:
                patterns.append(f"{category.replace('_', ' ').title()}: {matches} instances")

        # Check architectural patterns
        for category, keywords in architectural_patterns.items():
            matches = sum(1 for msg in commit_messages for keyword in keywords if keyword.lower() in msg.lower())
            if matches > 0:
                patterns.append(f"{category.replace('_', ' ').title()}: {matches} implementations")

        # Check integration patterns
        for category, keywords in integration_patterns.items():
            matches = sum(1 for msg in commit_messages for keyword in keywords if keyword.lower() in msg.lower())
            if matches > 0:
                patterns.append(f"{category.replace('_', ' ').title()}: {matches} integrations")

        return patterns

    def _analyze_pr_patterns(self, prs: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze pull request patterns for collaboration insights."""
        patterns = {"collaboration_patterns": [], "code_quality_indicators": [], "impact_areas": []}

        # Analyze PR sizes and complexity
        for pr in prs:
            additions = pr.get("additions", 0)
            deletions = pr.get("deletions", 0)
            files_changed = pr.get("changed_files", 0)

            if additions + deletions > 500:
                patterns["impact_areas"].append("Large-scale feature implementation")
            elif files_changed > 10:
                patterns["impact_areas"].append("Cross-cutting changes affecting multiple components")

            if pr.get("review_comments", 0) > 5:
                patterns["collaboration_patterns"].append("Active participation in code review discussions")

        # Analyze PR labels for additional insights
        all_labels = []
        for pr in prs:
            all_labels.extend(pr.get("labels", []))

        if all_labels:
            label_counts = Counter(all_labels)
            top_labels = [label for label, count in label_counts.most_common(3)]
            if "bug" in [label.lower() for label in top_labels]:
                patterns["code_quality_indicators"].append("Focus on bug fixes and issue resolution")
            if "enhancement" in [label.lower() for label in top_labels]:
                patterns["code_quality_indicators"].append("Feature development and enhancement work")

        return patterns

    def _extract_key_achievements(self, commits: List[Dict[str, Any]], prs: List[Dict[str, Any]]) -> List[str]:
        """Extract key achievements from commits and PRs."""
        achievements = []

        # Analyze commit impact
        total_additions = sum(commit.get("additions", 0) for commit in commits)

        if total_additions > 1000:
            achievements.append(f"Added {total_additions} lines of code demonstrating significant development contributions")

        # Analyze PR achievements
        merged_prs = [pr for pr in prs if pr.get("state") == "closed" and pr.get("merged_at")]
        if len(merged_prs) > 0:
            achievements.append(f"Successfully merged {len(merged_prs)} pull requests")

        # Look for patterns in commit messages
        commit_messages = [commit["message"] for commit in commits]
        performance_commits = [msg for msg in commit_messages if "performance" in msg.lower() or "optimize" in msg.lower()]
        if len(performance_commits) > 2:
            achievements.append("Performance optimization and code efficiency improvements")

        return achievements

    def _analyze_work_patterns(self, commits: List[Dict[str, Any]], prs: List[Dict[str, Any]]) -> List[str]:
        """Analyze work patterns and consistency."""
        patterns = []

        if commits:
            # Analyze commit frequency
            dates = [commit.get("date") for commit in commits if commit.get("date")]
            if len(dates) > 5:
                patterns.append("Consistent and regular contribution pattern")

            # Analyze commit sizes
            avg_additions = sum(commit.get("additions", 0) for commit in commits) / len(commits)
            if avg_additions > 100:
                patterns.append("Substantial code contributions with meaningful changes")
            else:
                patterns.append("Focused, incremental development approach")

        # Analyze PR patterns
        if prs:
            pr_states = [pr.get("state") for pr in prs]
            closed_prs = sum(1 for state in pr_states if state == "closed")
            if closed_prs > len(prs) * 0.7:
                patterns.append("High success rate in pull request completion")

        return patterns

    def _empty_contributor_summary(self) -> Dict[str, Any]:
        """Return empty contributor summary structure."""
        return {
            "contributor": "unknown",
            "repository": "unknown",
            "total_commits": 0,
            "total_prs": 0,
            "summary": {
                "technical_focus": [],
                "collaboration_patterns": [],
                "problem_solving_approaches": [],
                "code_quality_indicators": [],
                "impact_areas": [],
                "key_achievements": [],
                "work_patterns": [],
            },
            "generated_at": datetime.now().isoformat(),
        }

    def _analyze_commit_impacts(self, commits: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze the impact distribution across all commits."""
        impact_distribution = {
            "high": 0,
            "moderate": 0,
            "low": 0,
            "minimal": 0,
        }

        impact_scores = []
        high_impact_commits = []
        conventional_high_impact = []

        for commit in commits:
            impact_analysis = self._analyze_commit_impact(commit)
            impact_level = impact_analysis["impact_level"]
            impact_score = impact_analysis["impact_score"]

            impact_distribution[impact_level] += 1
            impact_scores.append(impact_score)

            # Track high impact commits
            if impact_level in ["high", "moderate"]:
                high_impact_commits.append(
                    {
                        "commit": commit,
                        "impact_analysis": impact_analysis,
                    }
                )

                # Track conventional commits that are high impact
                if impact_analysis["conventional_info"]["is_conventional"]:
                    conventional_high_impact.append(
                        {
                            "commit": commit,
                            "impact_analysis": impact_analysis,
                        }
                    )

        # Calculate statistics
        total_commits = len(commits)
        avg_impact_score = sum(impact_scores) / len(impact_scores) if impact_scores else 0

        return {
            "distribution": impact_distribution,
            "average_impact_score": round(avg_impact_score, 1),
            "high_impact_commits": high_impact_commits[:10],  # Top 10
            "conventional_high_impact": conventional_high_impact[:5],  # Top 5
            "impact_score_range": {
                "min": min(impact_scores) if impact_scores else 0,
                "max": max(impact_scores) if impact_scores else 0,
                "median": sorted(impact_scores)[len(impact_scores) // 2] if impact_scores else 0,
            },
            "quality_distribution": {level: round((count / total_commits) * 100, 1) if total_commits > 0 else 0 for level, count in impact_distribution.items()},
        }

    async def fetch_user_pull_requests_across_repos(
        self,
        username: str,
        repositories: List[Dict[str, Any]],
        max_prs: int = 50,
    ) -> Dict[str, Any]:
        """Fetch pull requests from a user across all their repositories with async batch processing."""
        try:
            if not self.github_client:
                return self._empty_pr_analysis()

            logger.info(f"🎯 PR ANALYSIS: Targeting {max_prs} PRs from user: {username}")

            # Create semaphore to limit concurrent GitHub API requests
            semaphore = asyncio.Semaphore(self.MAX_CONCURRENT_REQUESTS)

            # Split repositories into batches
            repo_batches = [repositories[i : i + self.REPOSITORY_BATCH_SIZE] for i in range(0, len(repositories), self.REPOSITORY_BATCH_SIZE)]

            all_prs = []
            prs_collected = 0

            logger.info(f"📝 Fetching PRs from user '{username}' across {len(repositories)} repositories")
            logger.info(f"⚡ Processing in {len(repo_batches)} batches with {self.MAX_CONCURRENT_REQUESTS} concurrent requests")

            # Process repository batches concurrently
            for batch_idx, repo_batch in enumerate(repo_batches):
                if prs_collected >= max_prs:
                    break

                logger.info(f"🔄 Processing PR batch {batch_idx + 1}/{len(repo_batches)}")

                # Create tasks for concurrent fetching
                batch_tasks = []
                for repo_data in repo_batch:
                    if prs_collected >= max_prs:
                        break

                    remaining_prs = max_prs - prs_collected
                    prs_per_repo = min(10, remaining_prs)  # Max 10 PRs per repo

                    task = self._fetch_user_prs_from_repo_async(semaphore, username, repo_data, prs_per_repo)
                    batch_tasks.append(task)

                # Execute batch concurrently
                batch_results = await asyncio.gather(*batch_tasks, return_exceptions=True)

                # Process results
                for result in batch_results:
                    if isinstance(result, Exception):
                        logger.warning(f"Error in PR batch task: {result}")
                        continue

                    if isinstance(result, list) and result:
                        prs_to_add = min(len(result), max_prs - prs_collected)
                        all_prs.extend(result[:prs_to_add])
                        prs_collected += prs_to_add

                        if prs_collected >= max_prs:
                            break

            logger.info(f"🎉 PR COLLECTION COMPLETED: {len(all_prs)} PRs collected from {username}")

            # Analyze the collected PRs
            pr_analysis = self._perform_pr_analysis(all_prs, username)

            return {
                "pull_requests": all_prs,
                "pr_analysis": pr_analysis,
                "total_prs_collected": len(all_prs),
            }

        except Exception as e:
            logger.error(f"Error fetching PRs for {username}: {e}")
            return self._empty_pr_analysis()

    async def fetch_repository_pull_requests(
        self,
        repository_full_name: str,
        author_username: Optional[str] = None,
        max_prs: int = 50,
        force_refresh: bool = False,
    ) -> List[Dict[str, Any]]:
        """Fetch pull requests from a specific repository, optionally filtered by author."""
        cache_key = f"repo_prs:{repository_full_name}:{author_username or 'all'}:{max_prs}"

        # Check cache first
        if not force_refresh:
            from app.core.redis_client import get_cache
            cached_data = await get_cache(cache_key)
            if cached_data:
                logger.info(f"💨 CACHE HIT for PRs: {repository_full_name}")
                return cached_data

        try:
            if not self.github_client:
                return []

            repo = self.github_client.get_repo(repository_full_name)
            pulls = repo.get_pulls(state="all", sort="created", direction="desc")

            prs_data = []
            count = 0

            for pr in pulls:
                if count >= max_prs:
                    break

                # Filter by author if specified
                if author_username and pr.user.login != author_username:
                    continue

                pr_data = {
                    "number": pr.number,
                    "title": pr.title,
                    "body": pr.body[:1000] if pr.body else "",  # Truncate body
                    "state": pr.state,
                    "created_at": pr.created_at.isoformat() if pr.created_at else None,
                    "updated_at": pr.updated_at.isoformat() if pr.updated_at else None,
                    "merged_at": pr.merged_at.isoformat() if pr.merged_at else None,
                    "closed_at": pr.closed_at.isoformat() if pr.closed_at else None,
                    "author": pr.user.login if pr.user else None,
                    "additions": pr.additions,
                    "deletions": pr.deletions,
                    "changed_files": pr.changed_files,
                    "comments": pr.comments,
                    "review_comments": pr.review_comments,
                    "commits": pr.commits,
                    "labels": [label.name for label in pr.labels] if pr.labels else [],
                    "milestone": pr.milestone.title if pr.milestone else None,
                    "repository": repository_full_name,
                }
                prs_data.append(pr_data)
                count += 1

            # Cache the results
            from app.core.redis_client import set_cache
            await set_cache(cache_key, prs_data, ttl=self.COMMIT_ANALYSIS_CACHE_TTL)
            logger.info(f"💾 Cached {len(prs_data)} PRs for: {repository_full_name}")

            return prs_data

        except Exception as e:
            logger.error(f"Error fetching PRs from {repository_full_name}: {e}")
            return []

    async def _fetch_user_prs_from_repo_async(
        self,
        semaphore: asyncio.Semaphore,
        username: str,
        repo_data: Dict[str, Any],
        max_prs_per_repo: int,
    ) -> List[Dict[str, Any]]:
        """Fetch PRs from a single repository asynchronously with rate limiting."""
        async with semaphore:
            try:
                loop = asyncio.get_event_loop()
                prs = await loop.run_in_executor(
                    None,
                    self._fetch_user_prs_from_repo_sync,
                    username,
                    repo_data,
                    max_prs_per_repo,
                )
                return prs

            except Exception as e:
                logger.warning(f"Error fetching PRs from {repo_data.get('name', 'unknown')}: {e}")
                return []

    def _fetch_user_prs_from_repo_sync(
        self,
        username: str,
        repo_data: Dict[str, Any],
        max_prs_per_repo: int,
    ) -> List[Dict[str, Any]]:
        """Synchronous helper to fetch PRs from a repository (runs in thread pool)."""
        if not self.github_client:
            return []

        try:
            # Try to get the repository
            repo_full_name = repo_data.get("full_name") or f"{username}/{repo_data['name']}"
            repo = self.github_client.get_repo(repo_full_name)

            pulls = repo.get_pulls(state="all", sort="created", direction="desc")

            prs_data = []
            count = 0

            for pr in pulls:
                if count >= max_prs_per_repo:
                    break

                # Only get PRs authored by this user
                if pr.user and pr.user.login == username:
                    pr_data = {
                        "number": pr.number,
                        "title": pr.title,
                        "body": pr.body[:1000] if pr.body else "",
                        "state": pr.state,
                        "created_at": pr.created_at.isoformat() if pr.created_at else None,
                        "merged_at": pr.merged_at.isoformat() if pr.merged_at else None,
                        "author": pr.user.login,
                        "additions": pr.additions,
                        "deletions": pr.deletions,
                        "changed_files": pr.changed_files,
                        "comments": pr.comments,
                        "review_comments": pr.review_comments,
                        "labels": [label.name for label in pr.labels] if pr.labels else [],
                        "repository": repo_data.get("name", ""),
                        "repository_full_name": repo_full_name,
                    }
                    prs_data.append(pr_data)
                    count += 1

            if prs_data:
                logger.debug(f"✅ Found {len(prs_data)} PRs from {username} in {repo_data.get('name', '')}")

            return prs_data

        except Exception as e:
            logger.debug(f"Error fetching PRs from {repo_data.get('name', '')}: {e}")
            return []

    def _perform_pr_analysis(self, prs: List[Dict[str, Any]], username: str) -> Dict[str, Any]:
        """Perform comprehensive analysis of pull requests."""
        if not prs:
            return self._empty_pr_analysis()

        # Analyze collaboration patterns
        collaboration_patterns = self._analyze_pr_collaboration_patterns(prs)

        # Analyze problem-solving approaches
        problem_solving = self._analyze_pr_problem_solving(prs)

        # Analyze code quality focus
        code_quality = self._analyze_pr_code_quality_focus(prs)

        # Calculate PR metrics
        pr_metrics = self._calculate_pr_metrics(prs)

        return {
            "total_prs_analyzed": len(prs),
            "collaboration_patterns": collaboration_patterns,
            "problem_solving": problem_solving,
            "code_quality_focus": code_quality,
            "pr_metrics": pr_metrics,
        }

    def _analyze_pr_collaboration_patterns(self, prs: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Extract collaboration insights from PRs."""
        patterns = {
            "review_participation": 0,
            "discussion_quality": "unknown",
            "responsiveness": "unknown",
            "mentorship_indicators": [],
        }

        total_review_comments = 0
        total_comments = 0
        prs_with_reviews = 0

        for pr in prs:
            review_comments = pr.get("review_comments", 0)
            comments = pr.get("comments", 0)

            total_review_comments += review_comments
            total_comments += comments

            if review_comments > 0:
                prs_with_reviews += 1

            # Check for mentorship patterns
            if review_comments > 5:
                patterns["mentorship_indicators"].append("Active in code review discussions")

        patterns["review_participation"] = prs_with_reviews
        patterns["avg_review_comments_per_pr"] = round(total_review_comments / len(prs), 1) if prs else 0
        patterns["avg_comments_per_pr"] = round(total_comments / len(prs), 1) if prs else 0

        # Determine discussion quality
        if patterns["avg_review_comments_per_pr"] > 3:
            patterns["discussion_quality"] = "high"
        elif patterns["avg_review_comments_per_pr"] > 1:
            patterns["discussion_quality"] = "moderate"
        else:
            patterns["discussion_quality"] = "low"

        return patterns

    def _analyze_pr_problem_solving(self, prs: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Extract problem-solving approaches from PRs."""
        problem_patterns = {
            "architectural_decisions": 0,
            "trade_offs_discussed": 0,
            "problem_types": [],
            "solution_approaches": [],
        }

        architectural_keywords = ["architecture", "design", "pattern", "refactor", "restructure"]
        trade_off_keywords = ["trade-off", "tradeoff", "vs", "versus", "alternative", "option"]
        problem_keywords = {
            "bug_fix": ["bug", "fix", "issue", "error", "crash"],
            "performance": ["performance", "optimize", "speed", "memory", "cache"],
            "security": ["security", "auth", "vulnerability", "encrypt"],
            "feature": ["feature", "implement", "add", "new"],
        }

        for pr in prs:
            title_lower = pr.get("title", "").lower()
            body_lower = pr.get("body", "").lower()
            combined = title_lower + " " + body_lower

            # Check for architectural discussions
            if any(keyword in combined for keyword in architectural_keywords):
                problem_patterns["architectural_decisions"] += 1

            # Check for trade-off discussions
            if any(keyword in combined for keyword in trade_off_keywords):
                problem_patterns["trade_offs_discussed"] += 1

            # Identify problem types
            for problem_type, keywords in problem_keywords.items():
                if any(keyword in title_lower for keyword in keywords):
                    if problem_type not in problem_patterns["problem_types"]:
                        problem_patterns["problem_types"].append(problem_type)

        return problem_patterns

    def _analyze_pr_code_quality_focus(self, prs: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Identify code quality indicators from PRs."""
        quality_indicators = {
            "test_focus": 0,
            "refactoring_focus": 0,
            "documentation_focus": 0,
            "security_focus": 0,
            "quality_score": 0,
        }

        test_keywords = ["test", "testing", "spec", "coverage"]
        refactor_keywords = ["refactor", "clean", "improve", "optimize"]
        doc_keywords = ["doc", "documentation", "comment", "readme"]
        security_keywords = ["security", "auth", "secure", "vulnerability"]

        for pr in prs:
            title_lower = pr.get("title", "").lower()
            labels = [label.lower() for label in pr.get("labels", [])]
            combined = title_lower + " " + " ".join(labels)

            if any(keyword in combined for keyword in test_keywords):
                quality_indicators["test_focus"] += 1

            if any(keyword in combined for keyword in refactor_keywords):
                quality_indicators["refactoring_focus"] += 1

            if any(keyword in combined for keyword in doc_keywords):
                quality_indicators["documentation_focus"] += 1

            if any(keyword in combined for keyword in security_keywords):
                quality_indicators["security_focus"] += 1

        # Calculate quality score
        total_prs = len(prs)
        if total_prs > 0:
            quality_score = (
                (quality_indicators["test_focus"] / total_prs) * 30
                + (quality_indicators["refactoring_focus"] / total_prs) * 25
                + (quality_indicators["documentation_focus"] / total_prs) * 25
                + (quality_indicators["security_focus"] / total_prs) * 20
            )
            quality_indicators["quality_score"] = round(min(quality_score * 100, 100), 1)

        return quality_indicators

    def _calculate_pr_metrics(self, prs: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate various PR metrics."""
        metrics = {
            "total_prs": len(prs),
            "merged_prs": 0,
            "open_prs": 0,
            "closed_prs": 0,
            "avg_additions": 0,
            "avg_deletions": 0,
            "avg_files_changed": 0,
            "merge_rate": 0,
        }

        total_additions = 0
        total_deletions = 0
        total_files_changed = 0

        for pr in prs:
            state = pr.get("state", "")
            if pr.get("merged_at"):
                metrics["merged_prs"] += 1
            elif state == "open":
                metrics["open_prs"] += 1
            else:
                metrics["closed_prs"] += 1

            total_additions += pr.get("additions", 0)
            total_deletions += pr.get("deletions", 0)
            total_files_changed += pr.get("changed_files", 0)

        if prs:
            metrics["avg_additions"] = round(total_additions / len(prs), 1)
            metrics["avg_deletions"] = round(total_deletions / len(prs), 1)
            metrics["avg_files_changed"] = round(total_files_changed / len(prs), 1)
            metrics["merge_rate"] = round((metrics["merged_prs"] / len(prs)) * 100, 1)

        return metrics

    def _empty_pr_analysis(self) -> Dict[str, Any]:
        """Return empty PR analysis structure."""
        return {
            "pull_requests": [],
            "pr_analysis": {
                "total_prs_analyzed": 0,
                "collaboration_patterns": {
                    "review_participation": 0,
                    "discussion_quality": "unknown",
                    "avg_review_comments_per_pr": 0,
                    "avg_comments_per_pr": 0,
                    "mentorship_indicators": [],
                },
                "problem_solving": {
                    "architectural_decisions": 0,
                    "trade_offs_discussed": 0,
                    "problem_types": [],
                    "solution_approaches": [],
                },
                "code_quality_focus": {
                    "test_focus": 0,
                    "refactoring_focus": 0,
                    "documentation_focus": 0,
                    "security_focus": 0,
                    "quality_score": 0,
                },
                "pr_metrics": {
                    "total_prs": 0,
                    "merged_prs": 0,
                    "open_prs": 0,
                    "closed_prs": 0,
                    "merge_rate": 0,
                },
            },
            "total_prs_collected": 0,
        }

    def _sanitize_pr_data_for_prompt(self, prs: List[Dict[str, Any]], repo_names_to_sanitize: List[str]) -> List[Dict[str, Any]]:
        """Clean PR data by replacing repository names with generic terms."""
        sanitized_prs = []

        for pr in prs:
            sanitized_pr = pr.copy()

            # Replace repo names in title
            title = sanitized_pr.get("title", "")
            for repo_name in repo_names_to_sanitize:
                # Replace various forms of the repo name
                title = re.sub(rf'\b{re.escape(repo_name)}\b', 'the project', title, flags=re.IGNORECASE)
                title = re.sub(rf'\b{re.escape(repo_name.replace("-", " "))}\b', 'the project', title, flags=re.IGNORECASE)
            sanitized_pr["title"] = title

            # Replace repo names in body
            body = sanitized_pr.get("body", "")
            if body:
                for repo_name in repo_names_to_sanitize:
                    body = re.sub(rf'\b{re.escape(repo_name)}\b', 'the application', body, flags=re.IGNORECASE)
                    body = re.sub(rf'\b{re.escape(repo_name.replace("-", " "))}\b', 'the application', body, flags=re.IGNORECASE)
                sanitized_pr["body"] = body

            # Remove repository field (not needed in prompt)
            sanitized_pr.pop("repository", None)
            sanitized_pr.pop("repository_full_name", None)

            sanitized_prs.append(sanitized_pr)

        return sanitized_prs
