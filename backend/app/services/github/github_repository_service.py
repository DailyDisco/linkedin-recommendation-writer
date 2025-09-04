import re
from datetime import datetime
from typing import Any, Dict, List, Optional, cast

from github import Github
from github.GithubException import GithubException
from github.Repository import Repository as GithubRepository
from loguru import logger

from app.core.config import settings
from app.core.redis_client import get_cache, set_cache
from app.schemas.github import LanguageStats
from app.services.github.github_commit_service import GitHubCommitService


class GitHubRepositoryService:
    """Service for fetching and analyzing GitHub repository data, and its contributors."""

    COMMIT_ANALYSIS_CACHE_TTL = 14400  # 4 hours cache for expensive operations

    def __init__(self, commit_service: GitHubCommitService) -> None:
        """Initialize repository service."""
        self.github_client = None
        if settings.GITHUB_TOKEN:
            logger.info("🔧 Initializing GitHub client with token for repository service")
            self.github_client = Github(settings.GITHUB_TOKEN)
        else:
            logger.warning("⚠️  GitHub token not configured - GitHub API calls will fail in repository service")
        self.commit_service = commit_service

    async def get_repository_contributors(
        self,
        repo_name: str,
        max_contributors: int = 50,
        force_refresh: bool = False,
    ) -> Optional[Dict[str, Any]]:
        """Get contributors from a repository with their real names."""

        cache_key = f"repo_contributors:{repo_name}:{max_contributors}"

        # Check cache first
        if not force_refresh:
            cached_data = await get_cache(cache_key)
            if cached_data and isinstance(cached_data, dict):
                logger.info(f"Returning cached contributors for repository: " f"{repo_name}")
                logger.debug(f"Cached data for {repo_name}: {cached_data}")
                return cast(Dict[str, Any], cached_data)

        try:
            if not self.github_client:
                raise ValueError("GitHub token not configured")

            # Get repository
            repo = self.github_client.get_repo(repo_name)

            # Get repository details
            repo_info = {
                "name": repo.name,
                "full_name": repo.full_name,
                "description": repo.description,
                "language": repo.language,
                "stars": repo.stargazers_count,
                "forks": repo.forks_count,
                "url": repo.html_url,
                "topics": list(repo.get_topics()),
                "created_at": repo.created_at.isoformat() if repo.created_at else None,
                "updated_at": repo.updated_at.isoformat() if repo.updated_at else None,
                "owner": {
                    "login": repo.owner.login,
                    "avatar_url": repo.owner.avatar_url,
                    "html_url": repo.owner.html_url,
                },
            }

            # Get contributors
            contributors_list = []
            contributors = repo.get_contributors()

            count = 0
            for contributor in contributors:
                if count >= max_contributors:
                    break

                try:
                    # Get detailed user info to get real name
                    user = self.github_client.get_user(contributor.login)

                    # Debug logging to see what GitHub API returns
                    logger.info(f"🔍 GitHub API response for {contributor.login}:")
                    logger.info(f"   • user.name: '{user.name}'")
                    logger.info(f"   • user.login: '{user.login}'")
                    logger.info(f"   • name is None: {user.name is None}")
                    logger.info(f"   • name is empty: {user.name == '' if user.name else 'N/A'}")

                    contributor_info = {
                        "username": contributor.login,
                        "full_name": user.name if user.name else contributor.login,
                        "first_name": (self._extract_first_name(user.name) if user.name else ""),
                        "last_name": (self._extract_last_name(user.name) if user.name else ""),
                        "email": user.email,
                        "bio": user.bio,
                        "company": user.company,
                        "location": user.location,
                        "avatar_url": user.avatar_url,
                        "contributions": contributor.contributions,
                        "profile_url": user.html_url,
                        "followers": user.followers,
                        "public_repos": user.public_repos,
                    }

                    contributors_list.append(contributor_info)
                    count += 1

                except Exception as e:
                    logger.warning(f"Could not get details for contributor " f"{contributor.login}: {e}")
                    # Add basic info even if detailed lookup fails
                    contributors_list.append(
                        {
                            "username": contributor.login,
                            "full_name": contributor.login,
                            "first_name": "",
                            "last_name": "",
                            "email": None,
                            "bio": None,
                            "company": None,
                            "location": None,
                            "avatar_url": contributor.avatar_url,
                            "contributions": contributor.contributions,
                            "profile_url": (f"https://github.com/{contributor.login}"),
                            "followers": 0,
                            "public_repos": 0,
                        }
                    )
                    count += 1

            result = {
                "repository": repo_info,
                "contributors": contributors_list,
                "total_contributors": len(contributors_list),
                "fetched_at": "now",
            }

            # Cache for 1 hour
            await set_cache(cache_key, result, ttl=3600)

            return result

        except GithubException as e:
            if e.status == 404:
                logger.error(f"Repository not found: {repo_name}")
                return None
            else:
                logger.error(f"GitHub API error for repository {repo_name}: {e}")
                return None
        except Exception as e:
            logger.error(f"Error fetching contributors for repository {repo_name}: {e}")
            return None

    def _extract_first_name(self, full_name: str) -> str:
        """Extract first name from full name."""
        if not full_name:
            return ""
        parts = full_name.strip().split()
        return parts[0] if parts else ""

    def _extract_last_name(self, full_name: str) -> str:
        """Extract last name from full name."""
        if not full_name:
            return ""
        parts = full_name.strip().split()
        return parts[-1] if len(parts) > 1 else ""

    async def analyze_repository(
        self, repository_full_name: str, force_refresh: bool = False, analysis_context_type: str = "profile", repository_url: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """Analyze a specific GitHub repository and return comprehensive data."""
        import time

        logger.info("📁 REPOSITORY ANALYSIS STARTED")
        logger.info("=" * 60)
        logger.info(f"🏗️  Target repository: {repository_full_name}")
        logger.info(f"🔄 Force refresh: {force_refresh}")

        analysis_start = time.time()

        # Create context-aware cache key
        context_suffix = ""
        if analysis_context_type != "profile":
            context_suffix = f":{analysis_context_type}"
            if repository_url:
                # Use the provided repository URL for consistency
                repo_path = repository_url.replace("https://github.com/", "").split("?")[0]
                context_suffix += f":{repo_path}"

        cache_key = f"repository:{repository_full_name}{context_suffix}"

        # Check cache first
        if not force_refresh:
            logger.info("🔍 Checking cache...")
            cached_data = await get_cache(cache_key)
            if cached_data and isinstance(cached_data, dict):
                logger.info("💨 CACHE HIT! Returning cached repository data")
                logger.info(f"   • Repository: {cached_data.get('repository_info', {}).get('name', 'N/A')}")
                logger.info(f"   • Language: {cached_data.get('repository_info', {}).get('language', 'N/A')}")
                return cached_data
            logger.info("🚀 CACHE MISS: Proceeding with fresh repository analysis")

        try:
            # Parse repository full name
            if "/" not in repository_full_name:
                logger.error(f"❌ Invalid repository format: {repository_full_name}")
                return None

            owner, repo_name = repository_full_name.split("/", 1)

            # Get repository information
            logger.info("📦 STEP 1: FETCHING REPOSITORY INFO")
            logger.info("-" * 40)
            repo_start = time.time()

            repo_info = await self._get_repository_info(owner, repo_name)
            if not repo_info:
                logger.error(f"❌ Failed to fetch repository info for {repository_full_name}")
                logger.error("   • This is likely due to GitHub API authentication issues")
                logger.error("   • Check if GITHUB_TOKEN environment variable is set")
                return None

            repo_end = time.time()
            logger.info(f"⏱️  Repository info fetched in {repo_end - repo_start:.2f} seconds")
            logger.info("✅ Repository info retrieved:")
            logger.info(f"   • Name: {repo_info.get('name', 'N/A')}")
            logger.info(f"   • Language: {repo_info.get('language', 'N/A')}")
            logger.info(f"   • Stars: {repo_info.get('stars', 0)}")
            description = repo_info.get("description", "N/A") or "N/A"
            logger.info(f"   • Description: {description[:50]}...")

            # Get repository languages
            logger.info("💻 STEP 2: ANALYZING REPOSITORY LANGUAGES")
            logger.info("-" * 40)
            lang_start = time.time()

            repo_languages = await self._get_repository_languages(owner, repo_name)

            lang_end = time.time()
            logger.info(f"⏱️  Language analysis completed in {lang_end - lang_start:.2f} seconds")
            logger.info(f"✅ Found {len(repo_languages) if repo_languages else 0} programming languages in repository")

            # Get repository commits (limited for performance)
            logger.info("📝 STEP 3: ANALYZING REPOSITORY COMMITS")
            logger.info("-" * 40)
            commits_start = time.time()

            repo_commits = await self._get_repository_commits(owner, repo_name, limit=50)

            commits_end = time.time()
            logger.info(f"⏱️  Commit analysis completed in {commits_end - commits_start:.2f} seconds")
            logger.info(f"✅ Analyzed {len(repo_commits) if repo_commits else 0} commits from repository")

            # Debug: Check if any of the results are None
            logger.info("🔍 DEBUG: Checking analysis results...")
            logger.info(f"   • repo_info: {'OK' if repo_info else 'None'}")
            logger.info(f"   • repo_languages: {'OK' if repo_languages else 'None'}")
            logger.info(f"   • repo_commits: {'OK' if repo_commits else 'None'}")

            # Extract repository-specific skills and technologies
            logger.info("🔧 STEP 4: EXTRACTING REPOSITORY SKILLS")
            logger.info("-" * 40)
            skills_start = time.time()

            try:
                repo_skills = await self._extract_repository_skills(repo_info, repo_languages, repo_commits)
                logger.info("✅ Skills extraction method completed")
            except Exception as e:
                logger.error(f"💥 ERROR in skills extraction: {e}")
                import traceback

                logger.error(f"Stack trace: {traceback.format_exc()}")
                repo_skills = None

            skills_end = time.time()
            logger.info(f"⏱️  Skills extraction completed in {skills_end - skills_start:.2f} seconds")

            # Debug: Check skills result
            logger.info(f"🔍 DEBUG: Skills extraction result: {'OK' if repo_skills else 'None'}")
            if repo_skills:
                logger.info(f"   • Technical skills: {len(repo_skills.get('technical_skills', []))}")
                logger.info(f"   • Frameworks: {len(repo_skills.get('frameworks', []))}")

            # Analyze repository-specific commit patterns
            logger.info("📊 STEP 5: ANALYZING COMMIT PATTERNS")
            logger.info("-" * 40)
            patterns_start = time.time()

            try:
                commit_patterns = await self._analyze_repository_commit_patterns(repo_commits, repo_languages)
                logger.info("✅ Commit pattern analysis method completed")
            except Exception as e:
                logger.error(f"💥 ERROR in commit pattern analysis: {e}")
                import traceback

                logger.error(f"Stack trace: {traceback.format_exc()}")
                commit_patterns = None

            patterns_end = time.time()
            logger.info(f"⏱️  Pattern analysis completed in {patterns_end - patterns_start:.2f} seconds")

            # Debug: Check patterns result
            logger.info(f"🔍 DEBUG: Pattern analysis result: {'OK' if commit_patterns else 'None'}")
            if commit_patterns:
                logger.info(f"   • Pattern keys: {list(commit_patterns.keys())}")

            # Compile final repository analysis
            analysis_end = time.time()
            total_time = analysis_end - analysis_start

            logger.info("🔍 DEBUG: Constructing final result...")
            logger.info(f"   • repo_info type: {type(repo_info)}")
            logger.info(f"   • repo_languages type: {type(repo_languages)}")
            logger.info(f"   • repo_commits type: {type(repo_commits)}")
            logger.info(f"   • repo_skills type: {type(repo_skills)}")
            logger.info(f"   • commit_patterns type: {type(commit_patterns)}")

            try:
                result = {
                    "repository_info": repo_info,
                    "languages": repo_languages,
                    "commits": repo_commits,
                    "skills": repo_skills,
                    "commit_analysis": commit_patterns,
                    "analyzed_at": datetime.utcnow().isoformat(),
                    "analysis_time_seconds": round(total_time, 2),
                    "analysis_context_type": "repository",
                }
                logger.info("✅ Final result constructed successfully")
            except Exception as result_error:
                logger.error(f"💥 Error constructing final result: {result_error}")
                logger.error("   • Checking individual components...")
                # Try to identify which component is causing the issue
                if repo_info is None:
                    logger.error("   • repo_info is None!")
                if repo_languages is None:
                    logger.error("   • repo_languages is None!")
                if repo_commits is None:
                    logger.error("   • repo_commits is None!")
                if repo_skills is None:
                    logger.error("   • repo_skills is None!")
                if commit_patterns is None:
                    logger.error("   • commit_patterns is None!")
                raise

            # Cache the result
            await set_cache(cache_key, result, ttl=self.COMMIT_ANALYSIS_CACHE_TTL)

            logger.info("🎉 REPOSITORY ANALYSIS COMPLETED")
            logger.info("-" * 40)
            logger.info(f"⏱️  Total analysis time: {total_time:.2f} seconds")
            logger.info(f"📊 Repository: {repository_full_name}")
            logger.info(f"💾 Cached with key: {cache_key}")
            logger.info("=" * 60)

            return result

        except Exception as e:
            logger.error(f"💥 ERROR analyzing repository {repository_full_name}: {e}")
            return None

    async def _get_repository_info(self, owner: str, repo_name: str) -> Optional[Dict[str, Any]]:
        """Get basic repository information."""
        try:
            if not self.github_client:
                logger.error("🚨 GitHub client not initialized - cannot fetch repository info")
                logger.error("   • This usually means GITHUB_TOKEN is not configured")
                return None

            repo = self.github_client.get_repo(f"{owner}/{repo_name}")

            return {
                "name": repo.name,
                "full_name": repo.full_name,
                "description": repo.description,
                "language": repo.language,
                "languages_url": repo.languages_url,
                "html_url": repo.html_url,
                "clone_url": repo.clone_url,
                "git_url": repo.git_url,
                "ssh_url": repo.ssh_url,
                "size": repo.size,
                "stars": repo.stargazers_count,
                "forks": repo.forks_count,
                "watchers": repo.watchers_count,
                "open_issues": repo.open_issues_count,
                "has_issues": repo.has_issues,
                "has_projects": repo.has_projects,
                "has_wiki": repo.has_wiki,
                "has_pages": repo.has_pages,
                "archived": repo.archived,
                "disabled": getattr(repo, "disabled", False),
                "created_at": repo.created_at.isoformat() if repo.created_at else None,
                "updated_at": repo.updated_at.isoformat() if repo.updated_at else None,
                "pushed_at": repo.pushed_at.isoformat() if repo.pushed_at else None,
                "topics": repo.get_topics(),
                "visibility": getattr(repo, "visibility", "public"),  # For newer PyGitHub versions
                "owner": {
                    "login": repo.owner.login,
                    "avatar_url": repo.owner.avatar_url,
                    "html_url": repo.owner.html_url,
                },
            }
        except Exception as e:
            logger.error(f"Error fetching repository info for {owner}/{repo_name}: {e}")
            return None

    async def _get_repository_languages(self, owner: str, repo_name: str) -> List[LanguageStats]:
        """Get programming languages used in the repository."""
        try:
            if not self.github_client:
                return []

            repo = self.github_client.get_repo(f"{owner}/{repo_name}")
            languages = repo.get_languages()

            total_bytes = sum(languages.values())
            language_stats: List[LanguageStats] = []

            for language, bytes_count in languages.items():
                percentage = (bytes_count / total_bytes * 100) if total_bytes > 0 else 0
                language_stats.append(
                    LanguageStats(
                        language=language,
                        percentage=round(percentage, 2),
                        lines_of_code=bytes_count,
                        repository_count=1,
                    )
                )

            # Sort by percentage
            language_stats.sort(key=lambda x: x.percentage, reverse=True)

            return language_stats
        except Exception as e:
            logger.error(f"Error fetching languages for {owner}/{repo_name}: {e}")
            return []

    async def _get_repository_commits(self, owner: str, repo_name: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Get recent commits from the repository."""
        try:
            if not self.github_client:
                return []

            repo = self.github_client.get_repo(f"{owner}/{repo_name}")
            commits = repo.get_commits()[:limit]  # Get first 'limit' commits

            commit_data = []
            for commit in commits:  # type: Any
                commit_data.append(
                    {
                        "sha": commit.sha,
                        "message": commit.commit.message,
                        "author": {
                            "name": (commit.commit.author.name if commit.commit.author else None),
                            "email": (commit.commit.author.email if commit.commit.author else None),
                            "date": (commit.commit.author.date.isoformat() if commit.commit.author else None),
                        },
                        "committer": {
                            "name": (commit.commit.committer.name if commit.commit.committer else None),
                            "email": (commit.commit.committer.email if commit.commit.committer else None),
                            "date": (commit.commit.committer.date.isoformat() if commit.commit.committer else None),
                        },
                        "stats": (
                            {
                                "additions": (commit.stats.additions if commit.stats and hasattr(commit.stats, "additions") and commit.stats.additions is not None else 0),
                                "deletions": (commit.stats.deletions if commit.stats and hasattr(commit.stats, "deletions") and commit.stats.deletions is not None else 0),
                                "total": (commit.stats.total if commit.stats and hasattr(commit.stats, "total") and commit.stats.total is not None else 0),
                            }
                            if commit.stats
                            else None
                        ),
                        "files": (
                            [
                                {
                                    "filename": f.filename,
                                    "additions": f.additions,
                                    "deletions": f.deletions,
                                    "changes": f.changes,
                                    "status": f.status,
                                }
                                for f in commit.files
                            ]
                            if commit.files
                            else []
                        ),
                        "html_url": commit.html_url,
                    }
                )

            return commit_data
        except Exception as e:
            logger.error(f"Error fetching commits for {owner}/{repo_name}: {e}")
            return []

    async def _extract_repository_skills(
        self,
        repo_info: Dict[str, Any],
        languages: List[LanguageStats],
        commits: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Extract skills and technologies from repository data."""
        try:
            logger.info("🔍 DEBUG: Starting skills extraction...")
            logger.info(f"   • repo_info type: {type(repo_info)}")
            logger.info(f"   • languages type: {type(languages)}, length: {len(languages) if languages else 0}")
            logger.info(f"   • commits type: {type(commits)}, length: {len(commits) if commits else 0}")

            # Extract technical skills from languages
            technical_skills = [lang.language for lang in languages[:5]]  # Top 5 languages
            logger.info(f"   • technical_skills: {technical_skills}")

            # Extract frameworks and tools from commit messages and file names
            frameworks = []
            tools: List[str] = []
            domains = []

            # Common framework patterns - more specific to avoid false positives
            framework_patterns = {
                "React": ["react", "jsx", "tsx", "component", "react-dom", "create-react-app"],
                "Vue": ["vue", "vuex", "vue-router", "vue-cli"],
                "Angular": ["angular", "ng-", "@angular", "angular-cli"],
                "Django": ["django", "models.py", "views.py", "urls.py", "manage.py"],
                "Flask": ["flask", "app.py", "routes", "flask-sqlalchemy"],
                "Express": ["express", "app.js", "routes", "express-session"],
                "Spring": ["spring", "@controller", "@service", "spring-boot"],
                "Laravel": ["laravel", "artisan", "composer.json"],
                "Rails": ["rails", "ruby on rails", "rails-assets"],
                "Next.js": ["next.js", "next.config", "next-env"],
                "Nuxt.js": ["nuxt", "nuxt.config", "nuxt-build"],
                "Svelte": ["svelte", ".svelte", "svelte-kit"],
                "FastAPI": ["fastapi", "pydantic", "uvicorn"],
                "GraphQL": ["graphql", ".graphql", "apollo"],
                "Docker": ["docker", "dockerfile", "docker-compose", "containerd"],
                "Kubernetes": ["kubernetes", "k8s", "helm", "kubectl"],
                "AWS": ["aws", "lambda", "s3", "ec2", "boto3"],
                "Azure": ["azure", "azure-sdk", "azure-storage", "azure-functions", "azure-cli"],
                "GCP": ["google cloud", "firebase", "gcp", "google-cloud"],
            }

            # Check commit messages and file names for frameworks
            if commits:
                for commit in commits[:20]:  # Check first 20 commits
                    message = commit.get("message", "").lower()
                    for framework, patterns in framework_patterns.items():
                        for pattern in patterns:
                            if pattern in message:
                                # For cloud providers, require more context to avoid false positives
                                if framework in ["Azure", "AWS", "GCP"]:
                                    # Check if it's not just a generic word like "function"
                                    if pattern in ["function", "blob", "lambda"]:
                                        # Require additional context for generic terms
                                        context_words = ["azure", "aws", "gcp", "cloud", "storage", "sdk"]
                                        if not any(context_word in message for context_word in context_words):
                                            continue
                                if framework not in frameworks:
                                    frameworks.append(framework)
                                break  # Found this framework, move to next

                # Check file names for frameworks
                for commit in commits[:10]:
                    for file_info in commit.get("files", []):
                        filename = file_info.get("filename", "").lower()
                        for framework, patterns in framework_patterns.items():
                            if any(pattern in filename for pattern in patterns):
                                if framework not in frameworks:
                                    frameworks.append(framework)

            # Determine domains based on repository content
            repo_description = (repo_info.get("description") or "").lower()
            repo_name = (repo_info.get("name") or "").lower()

            domain_keywords = {
                "Web Development": [
                    "web",
                    "frontend",
                    "backend",
                    "fullstack",
                    "website",
                    "application",
                ],
                "Mobile Development": [
                    "mobile",
                    "android",
                    "ios",
                    "react native",
                    "flutter",
                    "swift",
                ],
                "Data Science": [
                    "data",
                    "machine learning",
                    "ml",
                    "ai",
                    "analytics",
                    "visualization",
                ],
                "DevOps": [
                    "devops",
                    "ci/cd",
                    "deployment",
                    "infrastructure",
                    "automation",
                ],
                "API Development": [
                    "api",
                    "rest",
                    "graphql",
                    "microservice",
                    "backend",
                ],
                "Database": [
                    "database",
                    "sql",
                    "nosql",
                    "mongodb",
                    "postgresql",
                ],
                "Cloud Computing": [
                    "cloud",
                    "aws",
                    "azure",
                    "gcp",
                    "serverless",
                ],
                "Security": [
                    "security",
                    "authentication",
                    "authorization",
                    "encryption",
                ],
                "Testing": ["test", "testing", "jest", "cypress", "selenium"],
                "Game Development": ["game", "unity", "unreal", "godot"],
            }

            for domain, keywords in domain_keywords.items():
                if any(keyword in repo_description or keyword in repo_name for keyword in keywords):
                    domains.append(domain)

            # Extract soft skills from commit patterns
            soft_skills = []
            if len(commits) > 10:
                soft_skills.append("Consistent Contributor")
            if len(set([c.get("author", {}).get("name") for c in commits if c.get("author")])) > 1:
                soft_skills.append("Team Collaboration")

            return {
                "technical_skills": technical_skills,
                "frameworks": frameworks,
                "tools": tools,
                "domains": domains,
                "soft_skills": soft_skills,
            }
        except Exception as e:
            logger.error(f"Error extracting repository skills: {e}")
            return {
                "technical_skills": [],
                "frameworks": [],
                "tools": [],
                "domains": [],
                "soft_skills": [],
            }

    async def _analyze_repository_commit_patterns(self, commits: List[Dict[str, Any]], languages: List[LanguageStats]) -> Dict[str, Any]:
        """Analyze commit patterns specific to the repository."""
        try:
            logger.info("🔍 DEBUG: Starting commit pattern analysis...")
            logger.info(f"   • commits type: {type(commits)}, length: {len(commits) if commits else 0}")
            logger.info(f"   • languages type: {type(languages)}, length: {len(languages) if languages else 0}")

            if not commits:
                logger.info("   • No commits to analyze, returning empty analysis")
                return self._empty_commit_analysis()

            # Basic commit statistics
            total_commits = len(commits)
            logger.info(f"   • Analyzing {total_commits} commits...")

            # Debug: Check if commit stats exist
            sample_commit = commits[0] if commits else None
            if sample_commit:
                logger.info(f"   • Sample commit keys: {list(sample_commit.keys())}")
                if "stats" in sample_commit and sample_commit["stats"] is not None:
                    logger.info(f"   • Sample stats: {sample_commit['stats']}")
                else:
                    logger.info("   • No stats in sample commit")

            # Safely handle commit stats that might be None
            total_additions = sum([c.get("stats", {}).get("additions", 0) if c.get("stats") is not None else 0 for c in commits])
            total_deletions = sum([c.get("stats", {}).get("deletions", 0) if c.get("stats") is not None else 0 for c in commits])

            # Analyze commit messages for patterns
            commit_messages = [c.get("message", "") for c in commits]
            message_patterns = {
                "feature_development": [
                    "add",
                    "feature",
                    "implement",
                    "create",
                    "new",
                ],
                "bug_fixes": ["fix", "bug", "issue", "resolve", "correct"],
                "refactoring": [
                    "refactor",
                    "clean",
                    "improve",
                    "optimize",
                    "update",
                ],
                "documentation": ["doc", "comment", "document"],
                "testing": ["test", "spec", "assert", "mock"],
            }

            pattern_counts = {}
            for pattern, keywords in message_patterns.items():
                count = sum(1 for msg in commit_messages if any(kw in msg.lower() for kw in keywords))
                pattern_counts[pattern] = count

            # Determine primary strength
            primary_strength = max(pattern_counts.items(), key=lambda x: x[1])[0] if pattern_counts else None

            # Analyze file types and technologies
            file_extensions: Dict[str, int] = {}
            for commit in commits:
                for file_info in commit.get("files", []):
                    filename = file_info.get("filename", "")
                    if "." in filename:
                        ext = filename.split(".")[-1].lower()
                        file_extensions[ext] = file_extensions.get(ext, 0) + 1

            # Determine technical focus areas
            tech_focus = {}
            if languages and len(languages) > 0 and hasattr(languages[0], "language"):
                primary_lang = languages[0].language  # Access .language attribute
                tech_focus[f"{primary_lang} Development"] = len([c for c in commits if any(primary_lang.lower() in str(c).lower() for c in c.get("files", []))])

            # Leverage commit service's analysis methods for more detail
            conventional_analysis = self.commit_service._analyze_conventional_commits(commits)  # Access directly for now
            impact_analysis = self.commit_service._analyze_commit_impacts(commits)  # Access directly for now

            return {
                "total_commits_analyzed": total_commits,
                "repository_focused": True,
                "analysis_method": "repository_specific",
                "excellence_areas": {
                    "patterns": pattern_counts,
                    "primary_strength": (primary_strength.replace("_", " ").title() if primary_strength else None),
                },
                "commit_statistics": {
                    "total_additions": total_additions,
                    "total_deletions": total_deletions,
                    "avg_changes_per_commit": (total_additions + total_deletions) / max(total_commits, 1),
                },
                "file_analysis": {
                    "file_types": file_extensions,
                    "most_common_extension": (max(file_extensions.items(), key=lambda x: x[1])[0] if file_extensions else None),
                },
                "technical_contributions": tech_focus,
                "conventional_commit_analysis": conventional_analysis,  # Added from commit service
                "impact_analysis": impact_analysis,  # Added from commit service
            }
        except Exception as e:
            logger.error(f"Error analyzing repository commit patterns: {e}")
            return self._empty_commit_analysis()

    def _extract_api_endpoints_from_code(self, repository: GithubRepository, main_files: List[str]) -> List[str]:
        """Extract API endpoints from source code files (basic implementation)."""
        endpoints = []

        try:
            max_files_to_check = 5  # Limit to avoid rate limits

            for filename in main_files[:max_files_to_check]:
                try:
                    file_content = repository.get_contents(filename)
                    if hasattr(file_content, "decoded_content"):
                        content = file_content.decoded_content.decode("utf-8", errors="ignore")

                        # Simple regex patterns for common API endpoints

                        # Flask/Django patterns
                        flask_patterns = [
                            r'@app\.route\([\'"]([^\'"]*)[\'"]',
                            r'@api\.route\([\'"]([^\'"]*)[\'"]',
                            r'path\([\'"]([^\'"]*)[\'"]',
                        ]

                        # Express.js patterns
                        express_patterns = [
                            r'app\.(get|post|put|delete|patch)\(?[\'"]([^\'"]*)[\'"]',
                            r'router\.(get|post|put|delete|patch)\(?[\'"]([^\'"]*)[\'"]',
                        ]

                        # Spring patterns
                        spring_patterns = [
                            r'@RequestMapping\([\'"]([^\'"]*)[\'"]',
                            r'@GetMapping\([\'"]([^\'"]*)[\'"]',
                            r'@PostMapping\([\'"]([^\'"]*)[\'"]',
                        ]

                        all_patterns = flask_patterns + express_patterns + spring_patterns

                        for pattern in all_patterns:
                            matches = re.findall(pattern, content, re.IGNORECASE)
                            # Handle patterns that capture method and path (e.g., Express.js)
                            if matches and isinstance(matches[0], tuple):
                                endpoints.extend([match[1] for match in matches if len(match) > 1])
                            else:
                                endpoints.extend(matches)

                except Exception:
                    continue

            # Remove duplicates and clean endpoints
            endpoints = list(set(endpoints))
            endpoints = [ep for ep in endpoints if ep and not ep.startswith("http")][:10]  # Limit to 10 endpoints

        except Exception as e:
            logger.debug(f"Error extracting API endpoints: {e}")

        return endpoints

    def _empty_commit_analysis(self) -> Dict[str, Any]:
        """Return empty commit analysis structure for repository-focused analysis, used as a fallback."""
        return {
            "total_commits_analyzed": 0,
            "repository_focused": True,
            "analysis_method": "repository_specific",
            "excellence_areas": {"patterns": {}, "primary_strength": None},
            "commit_statistics": {"total_additions": 0, "total_deletions": 0, "avg_changes_per_commit": 0},
            "file_analysis": {"file_types": {}, "most_common_extension": None},
            "technical_contributions": {},
            "conventional_commit_analysis": self.commit_service._empty_commit_analysis().get("conventional_commit_analysis", {}),
            "impact_analysis": self.commit_service._empty_commit_analysis().get("impact_analysis", {}),
        }
