"""GitHub API service for fetching and analyzing GitHub data."""

import asyncio
import logging
import re
from collections import Counter
from datetime import datetime
from typing import Any, Dict, List, Optional, cast

from github import Github
from github.GithubException import GithubException

from app.core.config import settings
from app.core.redis_client import get_cache, set_cache

logger = logging.getLogger(__name__)


class GitHubService:
    """Service for interacting with GitHub API."""

    # Async batch processing configuration
    MAX_CONCURRENT_REQUESTS = 3  # Limit concurrent GitHub API requests
    REPOSITORY_BATCH_SIZE = 5  # Process repositories in batches
    MAX_COMMITS_PER_REPO = 30  # Max commits per repository for better distribution
    COMMIT_ANALYSIS_CACHE_TTL = 14400  # 4 hours cache for expensive operations

    def __init__(self) -> None:
        """Initialize GitHub service."""
        self.github_client = None
        if settings.GITHUB_TOKEN:
            logger.info("🔧 Initializing GitHub client with token")
            self.github_client = Github(settings.GITHUB_TOKEN)
        else:
            logger.warning("⚠️  GitHub token not configured - GitHub API calls will fail")

    async def analyze_github_profile(
        self,
        username: str,
        force_refresh: bool = False,
        max_repositories: int = 10,
    ) -> Optional[Dict[str, Any]]:
        """Analyze a GitHub profile and return comprehensive data."""
        import time

        logger.info("🐙 GITHUB PROFILE ANALYSIS STARTED")
        logger.info("=" * 60)
        logger.info(f"👤 Target user: {username}")
        logger.info(f"🔄 Force refresh: {force_refresh}")
        logger.info(f"📦 Max repositories: {max_repositories}")

        analysis_start = time.time()
        cache_key = f"github_profile:{username}"

        # Check cache first
        if not force_refresh:
            logger.info("🔍 Checking cache...")
            cached_data = await get_cache(cache_key)
            if cached_data:
                logger.info("💨 CACHE HIT! Returning cached GitHub data")
                logger.info(f"   • Cached repositories: {len(cached_data.get('repositories', []))}")
                logger.info(f"   • Cached commits: {cached_data.get('commit_analysis', {}).get('total_commits_analyzed', 0)}")
                return cast(Dict[str, Any], cached_data)
            logger.info("🚀 CACHE MISS: Proceeding with fresh analysis")

        try:
            # Check if GitHub client is initialized
            if not self.github_client:
                logger.error("❌ GitHub client not initialized")
                logger.error("💡 Make sure GITHUB_TOKEN environment variable is set")
                logger.error("   • Check your .env file or environment variables")
                logger.error("   • Token should start with 'ghp_' or 'github_pat_'")
                return None

            # Get user data
            logger.info("👤 STEP 1: FETCHING USER DATA")
            logger.info("-" * 40)
            user_start = time.time()

            user_data = await self._get_user_data(username)
            if not user_data:
                logger.error(f"❌ Failed to fetch user data for {username}")
                logger.error("💡 This could mean:")
                logger.error("   • User doesn't exist")
                logger.error("   • User profile is private")
                logger.error("   • GitHub API rate limit exceeded")
                logger.error("   • Network connectivity issues")
                return None

            user_end = time.time()
            logger.info(f"⏱️  User data fetched in {user_end - user_start:.2f} seconds")
            logger.info("✅ User data retrieved:")
            logger.info(f"   • Name: {user_data.get('full_name', 'N/A')}")
            logger.info(f"   • Public repos: {user_data.get('public_repos', 0)}")
            logger.info(f"   • Followers: {user_data.get('followers', 0)}")

            # Get repositories
            logger.info("📦 STEP 2: FETCHING REPOSITORIES")
            logger.info("-" * 40)
            repos_start = time.time()

            repositories = await self._get_repositories(username, max_repositories)

            repos_end = time.time()
            logger.info(f"⏱️  Repositories fetched in {repos_end - repos_start:.2f} seconds")
            logger.info(f"✅ Found {len(repositories)} repositories")

            # Analyze languages
            logger.info("💻 STEP 3: ANALYZING LANGUAGES")
            logger.info("-" * 40)
            lang_start = time.time()

            languages = await self._analyze_languages(repositories)

            lang_end = time.time()
            logger.info(f"⏱️  Language analysis completed in {lang_end - lang_start:.2f} seconds")
            logger.info(f"✅ Found {len(languages)} programming languages")
            if languages:
                top_langs = [lang["language"] for lang in languages[:3]]
                logger.info(f"   • Top languages: {', '.join(top_langs)}")

            # Extract skills
            logger.info("🔧 STEP 4: EXTRACTING SKILLS")
            logger.info("-" * 40)
            skills_start = time.time()

            skills = await self._extract_skills(user_data, repositories)

            skills_end = time.time()
            logger.info(f"⏱️  Skills extraction completed in {skills_end - skills_start:.2f} seconds")
            logger.info("✅ Skills extracted:")
            logger.info(f"   • Technical skills: {len(skills.get('technical_skills', []))}")
            logger.info(f"   • Frameworks: {len(skills.get('frameworks', []))}")
            logger.info(f"   • Tools: {len(skills.get('tools', []))}")

            # Analyze commits (up to 150)
            logger.info("📝 STEP 5: ANALYZING COMMITS (ASYNC BATCH PROCESSING)")
            logger.info("-" * 40)
            commits_start = time.time()

            commit_analysis = await self._analyze_commits(username, repositories)

            commits_end = time.time()
            logger.info(f"⏱️  Commit analysis completed in {commits_end - commits_start:.2f} seconds")
            logger.info("✅ Commit analysis results:")
            logger.info(f"   • Total commits analyzed: {commit_analysis.get('total_commits_analyzed', 0)}")

            excellence = commit_analysis.get("excellence_areas", {})
            if excellence.get("primary_strength"):
                logger.info(f"   • Primary strength: {excellence['primary_strength'].replace('_', ' ').title()}")

            # Compile analysis
            analysis = {
                "user_data": user_data,
                "repositories": repositories,
                "languages": languages,
                "skills": skills,
                "commit_analysis": commit_analysis,
                "analyzed_at": datetime.utcnow().isoformat(),
                "analysis_context_type": "profile",
            }

            # Cache for longer due to more expensive commit analysis
            logger.info("💾 STEP 6: CACHING RESULTS")
            logger.info("-" * 40)
            cache_start = time.time()

            await set_cache(cache_key, analysis, ttl=self.COMMIT_ANALYSIS_CACHE_TTL)

            cache_end = time.time()
            logger.info(f"⏱️  Results cached in {cache_end - cache_start:.2f} seconds")
            logger.info(f"✅ Cache TTL: {self.COMMIT_ANALYSIS_CACHE_TTL/3600:.1f} hours")

            analysis_end = time.time()
            total_time = analysis_end - analysis_start

            logger.info("🎉 GITHUB ANALYSIS COMPLETED")
            logger.info("-" * 40)
            logger.info(f"⏱️  Total analysis time: {total_time:.2f} seconds")
            logger.info("📊 Step breakdown:")
            logger.info(f"   • User Data: {user_end - user_start:.2f}s ({((user_end - user_start)/total_time)*100:.1f}%)")
            logger.info(f"   • Repositories: {repos_end - repos_start:.2f}s ({((repos_end - repos_start)/total_time)*100:.1f}%)")
            logger.info(f"   • Languages: {lang_end - lang_start:.2f}s ({((lang_end - lang_start)/total_time)*100:.1f}%)")
            logger.info(f"   • Skills: {skills_end - skills_start:.2f}s ({((skills_end - skills_start)/total_time)*100:.1f}%)")
            logger.info(f"   • Commits: {commits_end - commits_start:.2f}s ({((commits_end - commits_start)/total_time)*100:.1f}%)")
            logger.info(f"   • Caching: {cache_end - cache_start:.2f}s ({((cache_end - cache_start)/total_time)*100:.1f}%)")
            logger.info("=" * 60)

            return analysis

        except Exception as e:
            logger.error(f"💥 ERROR analyzing GitHub profile {username}: {e}")
            logger.error(f"⏱️  Failed after {time.time() - analysis_start:.2f} seconds")
            return None

    async def _get_user_data(self, username: str) -> Optional[Dict[str, Any]]:
        """Get basic user data from GitHub."""
        try:
            logger.info(f"🔍 Looking up GitHub user: {username}")

            if not self.github_client:
                logger.error("❌ GitHub client not initialized - check GITHUB_TOKEN configuration")
                raise ValueError("GitHub token not configured")

            logger.info("📡 Making GitHub API call to get user data...")
            user = self.github_client.get_user(username)

            logger.info("✅ GitHub user found successfully")
            logger.info(f"   • Username: {user.login}")
            logger.info(f"   • Name: {user.name or 'Not provided'}")
            logger.info(f"   • Public repos: {user.public_repos}")

            # Fetch starred repositories (indicates interests and technologies they follow)
            logger.info("⭐ Fetching starred repositories...")
            starred_repositories = await self._get_starred_repositories(user)
            logger.info(f"   • Found {len(starred_repositories)} starred repositories")

            # Fetch organizations (shows community involvement and professional networks)
            logger.info("🏢 Fetching organizations...")
            organizations = await self._get_user_organizations(user)
            logger.info(f"   • Found {len(organizations)} organizations")

            # Analyze starred repositories for technology interests
            starred_tech_analysis = await self._analyze_starred_technologies(starred_repositories)

            return {
                "github_username": user.login,
                "github_id": user.id,
                "full_name": user.name,
                "bio": user.bio,
                "company": user.company,
                "location": user.location,
                "email": user.email,
                "blog": user.blog,
                "avatar_url": user.avatar_url,
                "public_repos": user.public_repos,
                "followers": user.followers,
                "following": user.following,
                "public_gists": user.public_gists,
                "created_at": user.created_at.isoformat() if user.created_at else None,
                "updated_at": user.updated_at.isoformat() if user.updated_at else None,
                # Enhanced data
                "starred_repositories": starred_repositories,
                "organizations": organizations,
                "starred_technologies": starred_tech_analysis,
            }

        except GithubException as e:
            logger.error(f"❌ GitHub API error for user {username}:")
            logger.error(f"   • Status: {e.status if hasattr(e, 'status') else 'Unknown'}")
            logger.error(f"   • Data: {e.data if hasattr(e, 'data') else 'No data'}")
            logger.error(f"   • Message: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"💥 Unexpected error fetching user data for {username}:")
            logger.error(f"   • Error type: {type(e).__name__}")
            logger.error(f"   • Error message: {str(e)}")
            logger.error(f"   • Stack trace: {e.__trace__ if hasattr(e, '__trace__') else 'No trace'}")
            return None

    async def _get_starred_repositories(self, user) -> List[Dict[str, Any]]:
        """Fetch user's starred repositories to understand their interests."""
        try:
            starred = []
            max_starred = 20  # Limit to avoid rate limits and focus on most recent/most relevant

            for repo in user.get_starred()[:max_starred]:
                starred_repo = {
                    "name": repo.name,
                    "full_name": repo.full_name,
                    "description": repo.description,
                    "language": repo.language,
                    "stars": repo.stargazers_count,
                    "forks": repo.forks_count,
                    "topics": list(repo.get_topics()) if hasattr(repo, "get_topics") else [],
                    "url": repo.html_url,
                    "owner": repo.owner.login,
                    "is_fork": repo.fork,
                    "archived": getattr(repo, "archived", False),
                    "updated_at": repo.updated_at.isoformat() if repo.updated_at else None,
                }
                starred.append(starred_repo)

            return starred

        except Exception as e:
            logger.debug(f"Error fetching starred repositories: {e}")
            return []

    async def _get_user_organizations(self, user) -> List[Dict[str, Any]]:
        """Fetch user's organizations to understand their professional networks."""
        try:
            organizations = []

            for org in user.get_orgs():
                org_data = {
                    "login": org.login,
                    "name": getattr(org, "name", None),
                    "description": getattr(org, "description", None),
                    "url": org.html_url,
                    "avatar_url": org.avatar_url,
                    "public_repos": getattr(org, "public_repos", 0),
                    "members_count": getattr(org, "members_count", 0),
                    "location": getattr(org, "location", None),
                    "blog": getattr(org, "blog", None),
                    "email": getattr(org, "email", None),
                }
                organizations.append(org_data)

            return organizations

        except Exception as e:
            logger.debug(f"Error fetching user organizations: {e}")
            return []

    async def _analyze_starred_technologies(self, starred_repositories: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze starred repositories to understand technology interests and preferences."""
        if not starred_repositories:
            return {
                "languages": {},
                "topics": {},
                "technology_focus": {},
                "interest_score": 0,
            }

        # Count languages
        language_counts = {}
        topic_counts = {}
        technology_focus = {}

        for repo in starred_repositories:
            # Count languages
            language = repo.get("language")
            if language:
                language_counts[language] = language_counts.get(language, 0) + 1

            # Count topics
            topics = repo.get("topics", [])
            for topic in topics:
                topic_counts[topic] = topic_counts.get(topic, 0) + 1

        # Determine technology focus based on starred repos
        # This helps understand what technologies they find interesting vs what they use
        technology_patterns = {
            "Web Development": ["javascript", "typescript", "react", "vue", "angular", "html", "css", "web"],
            "Backend": ["python", "java", "go", "rust", "c#", "php", "ruby", "backend", "api"],
            "Data Science": ["python", "r", "jupyter", "pandas", "tensorflow", "pytorch", "machine-learning"],
            "DevOps": ["docker", "kubernetes", "terraform", "ansible", "ci/cd", "jenkins"],
            "Mobile": ["swift", "kotlin", "react-native", "flutter", "ios", "android"],
            "Systems": ["c", "c++", "rust", "go", "systems", "embedded"],
            "Frontend": ["javascript", "typescript", "react", "vue", "angular", "frontend"],
            "Database": ["postgresql", "mysql", "mongodb", "redis", "database"],
            "Cloud": ["aws", "gcp", "azure", "cloud", "serverless"],
            "Security": ["security", "cryptography", "authentication", "authorization"],
        }

        for focus_area, patterns in technology_patterns.items():
            score = 0
            for pattern in patterns:
                # Check languages
                for lang, count in language_counts.items():
                    if pattern.lower() in lang.lower():
                        score += count * 2  # Languages are more significant

                # Check topics
                for topic, count in topic_counts.items():
                    if pattern.lower() in topic.lower():
                        score += count

            if score > 0:
                technology_focus[focus_area] = score

        # Calculate interest diversity score
        total_starred = len(starred_repositories)
        language_diversity = len(language_counts)
        topic_diversity = len(topic_counts)

        interest_score = min(100, (language_diversity * 10) + (topic_diversity * 5) + (total_starred * 2))

        return {
            "languages": dict(sorted(language_counts.items(), key=lambda x: x[1], reverse=True)),
            "topics": dict(sorted(topic_counts.items(), key=lambda x: x[1], reverse=True)[:15]),  # Top 15 topics
            "technology_focus": dict(sorted(technology_focus.items(), key=lambda x: x[1], reverse=True)),
            "interest_score": interest_score,
            "total_starred": total_starred,
            "language_diversity": language_diversity,
            "topic_diversity": topic_diversity,
        }

    async def _get_repositories(self, username: str, max_count: int) -> List[Dict[str, Any]]:
        """Get user's repositories with details."""
        try:
            if not self.github_client:
                return []

            user = self.github_client.get_user(username)
            repos = user.get_repos(sort="updated", direction="desc")

            repositories = []
            count = 0

            for repo in repos:
                if count >= max_count:
                    break

                if repo.fork:  # Skip forked repositories
                    continue

                repo_data = {
                    "name": repo.name,
                    "description": repo.description,
                    "language": repo.language,
                    "stars": repo.stargazers_count,
                    "forks": repo.forks_count,
                    "size": repo.size,
                    "created_at": (repo.created_at.isoformat() if repo.created_at else None),
                    "updated_at": (repo.updated_at.isoformat() if repo.updated_at else None),
                    "topics": list(repo.get_topics()),
                    "url": repo.html_url,
                    "clone_url": repo.clone_url,
                    "is_private": repo.private,
                }

                repositories.append(repo_data)
                count += 1

            return repositories

        except Exception as e:
            logger.error(f"Error fetching repositories for {username}: {e}")
            return []

    async def _analyze_languages(self, repositories: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Analyze programming languages used across repositories."""
        language_stats = {}
        total_repos = len(repositories)

        for repo in repositories:
            language = repo.get("language")
            if language:
                if language not in language_stats:
                    language_stats[language] = {
                        "language": language,
                        "repository_count": 0,
                        "percentage": 0.0,
                        "lines_of_code": repo.get("size", 0),  # Approximation
                    }

                language_stats[language]["repository_count"] += 1
                language_stats[language]["lines_of_code"] += repo.get("size", 0)

        # Calculate percentages
        for lang_data in language_stats.values():
            lang_data["percentage"] = (lang_data["repository_count"] / total_repos * 100) if total_repos > 0 else 0

        # Sort by repository count
        return sorted(
            language_stats.values(),
            key=lambda x: x["repository_count"],
            reverse=True,
        )

    async def _fetch_dependency_data(self, repo_data: Dict[str, Any]) -> List[str]:
        """Fetch and analyze dependency files from a repository."""
        if not self.github_client:
            return []

        try:
            # Common dependency file patterns
            dependency_files = {
                # Python
                "requirements.txt": "python",
                "pyproject.toml": "python",
                "setup.py": "python",
                "Pipfile": "python",
                "poetry.lock": "python",
                # JavaScript/Node.js
                "package.json": "javascript",
                "yarn.lock": "javascript",
                "package-lock.json": "javascript",
                # Java
                "pom.xml": "java",
                "build.gradle": "java",
                "build.gradle.kts": "java",
                # .NET/C#
                ".csproj": "dotnet",
                "packages.config": "dotnet",
                "project.json": "dotnet",
                # Go
                "go.mod": "go",
                "go.sum": "go",
                # Rust
                "Cargo.toml": "rust",
                "Cargo.lock": "rust",
                # PHP
                "composer.json": "php",
                "composer.lock": "php",
                # Ruby
                "Gemfile": "ruby",
                "Gemfile.lock": "ruby",
                # Swift/iOS
                "Package.swift": "swift",
                "Podfile": "swift",
                "Cartfile": "swift",
                # Infrastructure/DevOps
                "Dockerfile": "docker",
                "docker-compose.yml": "docker",
                "docker-compose.yaml": "docker",
            }

            repo_full_name = repo_data.get("full_name") or f"{repo_data.get('name', '')}"
            if not repo_full_name:
                return []

            # Try to get repository object
            try:
                repo = self.github_client.get_repo(repo_full_name)
            except Exception:
                # If we can't access the repo, skip dependency analysis
                return []

            dependencies = []
            max_files_to_check = 3  # Limit to avoid rate limits

            for filename, language in dependency_files.items():
                if len(dependencies) >= max_files_to_check:
                    break

                try:
                    # Check if file exists and get its content
                    file_content = repo.get_contents(filename)

                    # Skip if it's a directory
                    if hasattr(file_content, "type") and file_content.type == "dir":
                        continue

                    # Decode content
                    if hasattr(file_content, "decoded_content"):
                        content = file_content.decoded_content.decode("utf-8", errors="ignore")
                    else:
                        continue

                    # Parse dependencies based on file type
                    file_dependencies = self._parse_dependency_file(content, filename, language)
                    dependencies.extend(file_dependencies)

                except Exception:
                    # File doesn't exist or can't be read, continue
                    continue

            # Remove duplicates and return
            return list(set(dependencies))

        except Exception as e:
            logger.debug(f"Error fetching dependency data for {repo_data.get('name', 'unknown')}: {e}")
            return []

    def _parse_dependency_file(self, content: str, filename: str, language: str) -> List[str]:
        """Parse dependency file content to extract package/library names."""
        dependencies = []

        try:
            if filename == "requirements.txt" or filename.endswith("requirements-"):
                # Python requirements.txt
                for line in content.split("\n"):
                    line = line.strip()
                    if line and not line.startswith("#") and not line.startswith("-"):
                        # Extract package name (everything before version specifiers)
                        package_name = line.split(">=")[0].split("==")[0].split("<")[0].split(">")[0].split("~")[0].strip()
                        if package_name and len(package_name) > 1:
                            dependencies.append(package_name.lower())

            elif filename == "package.json":
                # Node.js package.json
                import json

                try:
                    data = json.loads(content)
                    # Get dependencies
                    deps = data.get("dependencies", {})
                    dev_deps = data.get("devDependencies", {})

                    for dep_dict in [deps, dev_deps]:
                        for package_name in dep_dict.keys():
                            # Clean package name (remove @scope/ prefix)
                            clean_name = package_name.split("/")[-1] if "/" in package_name else package_name
                            dependencies.append(clean_name.lower())
                except json.JSONDecodeError:
                    pass

            elif filename == "go.mod":
                # Go modules
                for line in content.split("\n"):
                    line = line.strip()
                    if line.startswith("require ") or line.startswith("\t"):
                        parts = line.split()
                        if len(parts) >= 2:
                            module_path = parts[1]
                            # Extract the main module name (e.g., github.com/gin-gonic/gin -> gin-gonic/gin)
                            if "/" in module_path:
                                module_name = "/".join(module_path.split("/")[-2:])
                                dependencies.append(module_name.lower())

            elif filename == "Cargo.toml":
                # Rust Cargo.toml
                in_dependencies = False
                for line in content.split("\n"):
                    line = line.strip()
                    if line == "[dependencies]":
                        in_dependencies = True
                        continue
                    elif line.startswith("[") and in_dependencies:
                        in_dependencies = False
                        continue

                    if in_dependencies and "=" in line:
                        package_name = line.split("=")[0].strip()
                        if package_name and not package_name.startswith("#"):
                            dependencies.append(package_name.lower())

            elif filename == "composer.json":
                # PHP Composer
                import json

                try:
                    data = json.loads(content)
                    deps = data.get("require", {})
                    dev_deps = data.get("require-dev", {})

                    for dep_dict in [deps, dev_deps]:
                        for package_name in dep_dict.keys():
                            # Remove vendor prefix for well-known packages
                            if "/" in package_name:
                                package_name = package_name.split("/")[1]
                            dependencies.append(package_name.lower())
                except json.JSONDecodeError:
                    pass

            elif filename == "Gemfile":
                # Ruby Gemfile
                for line in content.split("\n"):
                    line = line.strip()
                    if line.startswith("gem '") or line.startswith('gem "'):
                        # Extract gem name
                        start_quote = "'" if "'" in line else '"'
                        parts = line.split(start_quote)
                        if len(parts) >= 3:
                            gem_name = parts[1]
                            dependencies.append(gem_name.lower())

        except Exception as e:
            logger.debug(f"Error parsing dependency file {filename}: {e}")

        return dependencies

    async def _extract_skills(self, user_data: Dict[str, Any], repositories: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Extract skills from user profile and repositories with enhanced analysis."""
        technical_skills = set()
        frameworks = set()
        tools = set()
        domains = set()
        dependencies_found = set()

        # Enhanced framework and technology mappings
        framework_patterns = {
            # JavaScript Frameworks
            "React": ["react", "reactjs", "react.js", "next.js", "nextjs", "create-react-app", "react-native"],
            "Vue": ["vue", "vuejs", "vue.js", "nuxt", "nuxtjs", "nuxt.js"],
            "Angular": ["angular", "angularjs", "angular.js", "@angular"],
            "Svelte": ["svelte", "sveltekit"],
            "Express": ["express", "expressjs", "express.js"],
            "NestJS": ["nestjs", "nest.js", "@nestjs"],
            # Python Frameworks
            "Django": ["django", "django-rest-framework", "djangorestframework"],
            "Flask": ["flask", "flask-restful", "flask-sqlalchemy"],
            "FastAPI": ["fastapi", "fastapi-users", "fastapi-admin"],
            "TensorFlow": ["tensorflow", "tf-", "keras"],
            "PyTorch": ["torch", "pytorch", "torchvision"],
            "Scikit-learn": ["scikit-learn", "sklearn"],
            "Pandas": ["pandas", "pandas-profiling"],
            "NumPy": ["numpy", "numpy-financial"],
            "Matplotlib": ["matplotlib", "matplotlib.pyplot"],
            # Java Frameworks
            "Spring": ["spring", "spring-boot", "spring-framework", "spring-mvc", "spring-data", "spring-security"],
            "Hibernate": ["hibernate", "hibernate-core"],
            "Maven": ["maven", "maven-plugin"],
            "Gradle": ["gradle", "gradle-wrapper"],
            # .NET Frameworks
            "ASP.NET": ["asp.net", "asp.net-core", "asp.net-mvc", "asp.net-web-api"],
            "Entity Framework": ["entity-framework", "entityframework", "ef-core"],
            # Go Frameworks
            "Gin": ["gin", "gin-gonic/gin"],
            "Echo": ["echo", "labstack/echo"],
            "Fiber": ["fiber", "gofiber/fiber"],
            # Ruby Frameworks
            "Rails": ["rails", "ruby-on-rails", "ror"],
            "Sinatra": ["sinatra"],
            # PHP Frameworks
            "Laravel": ["laravel", "laravel/framework"],
            "Symfony": ["symfony", "symfony/framework"],
            "CodeIgniter": ["codeigniter"],
            # Rust Frameworks
            "Actix": ["actix", "actix-web"],
            "Rocket": ["rocket", "rocket_contrib"],
            "Tokio": ["tokio", "tokio-util"],
        }

        tool_patterns = {
            # Cloud Platforms
            "AWS": ["aws", "amazon-web-services", "boto3", "aws-sdk", "aws-cli", "ec2", "s3", "lambda"],
            "Google Cloud": ["gcp", "google-cloud", "google-cloud-platform", "gcloud", "firebase"],
            "Azure": ["azure", "microsoft-azure", "azure-sdk"],
            "Heroku": ["heroku", "heroku-cli"],
            "Vercel": ["vercel", "vercel-cli"],
            "Netlify": ["netlify", "netlify-cli"],
            # Containers & Orchestration
            "Docker": ["docker", "docker-compose", "dockerfile", "containerd"],
            "Kubernetes": ["kubernetes", "k8s", "kubectl", "helm", "istio"],
            "Podman": ["podman", "buildah"],
            # Databases
            "PostgreSQL": ["postgresql", "psycopg2", "postgres", "pg"],
            "MySQL": ["mysql", "pymysql", "mysql-connector"],
            "MongoDB": ["mongodb", "pymongo", "mongoose"],
            "Redis": ["redis", "redis-py"],
            "SQLite": ["sqlite", "sqlite3"],
            "Elasticsearch": ["elasticsearch", "elasticsearch-py"],
            # CI/CD & DevOps
            "Jenkins": ["jenkins", "jenkins-pipeline"],
            "GitLab CI": ["gitlab-ci", "gitlab-ci.yml"],
            "GitHub Actions": ["github-actions", "actions"],
            "CircleCI": ["circleci", "circle-ci"],
            "Travis CI": ["travis-ci", ".travis.yml"],
            # Version Control
            "Git": ["git", "git-flow", "git-lfs"],
            "GitHub": ["github", "github-api"],
            # Testing
            "Jest": ["jest", "@testing-library"],
            "Mocha": ["mocha", "chai"],
            "PyTest": ["pytest", "pytest-django"],
            "JUnit": ["junit", "junit5"],
            "Selenium": ["selenium", "selenium-webdriver"],
            # Build Tools
            "Webpack": ["webpack", "webpack-cli"],
            "Vite": ["vite", "vitejs"],
            "Babel": ["babel", "@babel"],
            "TypeScript": ["typescript", "ts-node", "@types"],
        }

        # Extract from languages
        languages = {repo.get("language") for repo in repositories if repo.get("language")}
        technical_skills.update(languages)

        # Process each repository
        for repo in repositories:
            # Extract from repository topics
            topics = repo.get("topics", [])
            technical_skills.update(topics)

            # Enhanced description analysis
            description = repo.get("description", "")
            if description:
                description_lower = description.lower()

                # Check for frameworks in description
                for framework, patterns in framework_patterns.items():
                    if any(pattern in description_lower for pattern in patterns):
                        frameworks.add(framework)

                # Check for tools in description
                for tool, patterns in tool_patterns.items():
                    if any(pattern in description_lower for pattern in patterns):
                        tools.add(tool)

            # Analyze repository dependencies (new feature)
            try:
                repo_dependencies = await self._fetch_dependency_data(repo)
                dependencies_found.update(repo_dependencies)

                # Map dependencies to frameworks and tools
                for dep in repo_dependencies:
                    dep_lower = dep.lower()

                    # Check if dependency matches known frameworks
                    for framework, patterns in framework_patterns.items():
                        if any(pattern in dep_lower or dep_lower in pattern for pattern in patterns):
                            frameworks.add(framework)
                            break

                    # Check if dependency matches known tools
                    for tool, patterns in tool_patterns.items():
                        if any(pattern in dep_lower or dep_lower in pattern for pattern in patterns):
                            tools.add(tool)
                            break

                    # Add dependency as technical skill if it's a well-known library
                    if len(dep) > 2 and not any(char.isdigit() for char in dep):
                        technical_skills.add(dep.title())

            except Exception as e:
                logger.debug(f"Error analyzing dependencies for {repo.get('name', 'unknown')}: {e}")

        # Extract from repository names (additional signal)
        for repo in repositories:
            repo_name = repo.get("name", "").lower()
            for framework, patterns in framework_patterns.items():
                if any(pattern in repo_name for pattern in patterns):
                    frameworks.add(framework)

        # Extract from bio with enhanced pattern matching
        bio = user_data.get("bio", "")
        if bio:
            bio_lower = bio.lower()

            # Domain detection
            domain_patterns = {
                "Machine Learning": ["machine learning", "ml", "deep learning", "neural network", "ai", "artificial intelligence"],
                "Data Science": ["data science", "data analysis", "data visualization", "statistics", "analytics"],
                "Web Development": ["web development", "web dev", "frontend", "backend", "fullstack", "web application"],
                "Mobile Development": ["mobile", "ios", "android", "react native", "flutter", "swift", "kotlin"],
                "DevOps": ["devops", "infrastructure", "deployment", "ci/cd", "automation", "cloud"],
                "Cybersecurity": ["security", "cybersecurity", "encryption", "authentication", "penetration testing"],
                "Game Development": ["game", "unity", "unreal", "godot", "game engine"],
                "Blockchain": ["blockchain", "ethereum", "smart contract", "web3", "cryptocurrency"],
                "IoT": ["iot", "internet of things", "embedded", "raspberry pi", "arduino"],
                "API Development": ["api", "rest", "graphql", "microservices", "soap"],
            }

            for domain, patterns in domain_patterns.items():
                if any(pattern in bio_lower for pattern in patterns):
                    domains.add(domain)

            # Extract additional frameworks and tools from bio
            for framework, patterns in framework_patterns.items():
                if any(pattern in bio_lower for pattern in patterns):
                    frameworks.add(framework)

            for tool, patterns in tool_patterns.items():
                if any(pattern in bio_lower for pattern in patterns):
                    tools.add(tool)

        # Extract from user company/location (additional context)
        company = user_data.get("company", "")
        location = user_data.get("location", "")

        for field in [company, location]:
            if field:
                field_lower = field.lower()
                for tool, patterns in tool_patterns.items():
                    if any(pattern in field_lower for pattern in patterns):
                        tools.add(tool)

        # Clean up and deduplicate
        technical_skills = {skill for skill in technical_skills if skill and len(str(skill)) > 1}
        frameworks = {framework for framework in frameworks if framework}
        tools = {tool for tool in tools if tool}
        domains = {domain for domain in domains if domain}

        return {
            "technical_skills": sorted(list(technical_skills)),
            "frameworks": sorted(list(frameworks)),
            "tools": sorted(list(tools)),
            "domains": sorted(list(domains)),
            "dependencies_found": sorted(list(dependencies_found)),
            "soft_skills": [],  # Could be enhanced with more analysis
        }

    async def _analyze_commits(
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
        import re

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
        conventional_commits = []
        conventional_stats = {
            "total_commits": len(commits),
            "conventional_commits": 0,
            "breaking_changes": 0,
            "types": {},
            "scopes": {},
            "categories": {},
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
            round((conventional_stats["conventional_commits"] / conventional_stats["total_commits"]) * 100, 1)
            if conventional_stats["total_commits"] > 0
            else 0
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

    def _analyze_repository_content_for_readme(self, repo_data: Dict[str, Any], repository) -> Dict[str, Any]:
        """Analyze repository content specifically for README generation."""
        analysis = {
            "existing_readme": False,
            "readme_content": None,
            "main_files": [],
            "documentation_files": [],
            "configuration_files": [],
            "source_directories": [],
            "license_info": None,
            "has_tests": False,
            "has_ci_cd": False,
            "has_docker": False,
            "api_endpoints": [],
            "key_features": [],
        }

        try:
            # Check for existing README files
            readme_files = ["README.md", "README.rst", "README.txt", "readme.md", "Readme.md"]
            for readme_file in readme_files:
                try:
                    readme_content = repository.get_contents(readme_file)
                    if readme_content and hasattr(readme_content, "decoded_content"):
                        analysis["existing_readme"] = True
                        analysis["readme_content"] = readme_content.decoded_content.decode("utf-8", errors="ignore")
                        break
                except Exception:
                    continue

            # Get repository structure (limited to avoid rate limits)
            try:
                contents = repository.get_contents("")
                max_items = 50  # Limit to avoid processing too many files

                for item in contents[:max_items]:
                    if item.type == "file":
                        filename = item.name.lower()

                        # Main application files
                        if any(filename.endswith(ext) for ext in [".py", ".js", ".ts", ".java", ".cpp", ".c", ".go", ".rs", ".php", ".rb"]):
                            analysis["main_files"].append(item.name)

                        # Documentation files
                        elif any(filename.endswith(ext) for ext in [".md", ".rst", ".txt"]) or "doc" in filename:
                            analysis["documentation_files"].append(item.name)

                        # Configuration files
                        elif any(filename in ["package.json", "setup.py", "requirements.txt", "cargo.toml", "pom.xml", "build.gradle"]):
                            analysis["configuration_files"].append(item.name)

                        # CI/CD files
                        elif any(term in filename for term in [".yml", ".yaml", "ci", "cd", "github", "actions"]):
                            analysis["has_ci_cd"] = True

                        # Docker files
                        elif "docker" in filename:
                            analysis["has_docker"] = True

                        # Test files
                        elif "test" in filename or "spec" in filename:
                            analysis["has_tests"] = True

                    elif item.type == "dir":
                        dirname = item.name.lower()

                        # Source directories
                        if any(term in dirname for term in ["src", "source", "lib", "core", "main"]):
                            analysis["source_directories"].append(item.name)

            except Exception as e:
                logger.debug(f"Error analyzing repository structure: {e}")

            # Extract license information
            try:
                license_info = repository.get_license()
                if license_info:
                    analysis["license_info"] = {
                        "name": license_info.license.name if license_info.license else "Unknown",
                        "key": license_info.license.key if license_info.license else None,
                    }
            except Exception:
                pass

            # Extract key features from description and topics
            description = repo_data.get("description", "")
            topics = repo_data.get("topics", [])

            if description:
                # Simple feature extraction from description
                sentences = [s.strip() for s in description.split(".") if s.strip()]
                analysis["key_features"] = sentences[:3]  # First 3 sentences as features

            # Add topics as features
            for topic in topics[:5]:  # Top 5 topics
                if len(analysis["key_features"]) < 5:
                    analysis["key_features"].append(f"Built with {topic}")

        except Exception as e:
            logger.debug(f"Error analyzing repository content for README: {e}")

        return analysis

    def _extract_api_endpoints_from_code(self, repository, main_files: List[str]) -> List[str]:
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
                        import re

                        # Flask/Django patterns
                        flask_patterns = [
                            r'@app\.route\([\'"]([^\'"]*)[\'"]',
                            r'@api\.route\([\'"]([^\'"]*)[\'"]',
                            r'path\([\'"]([^\'"]*)[\'"]',
                        ]

                        # Express.js patterns
                        express_patterns = [
                            r'app\.(get|post|put|delete|patch)\([\'"]([^\'"]*)[\'"]',
                            r'router\.(get|post|put|delete|patch)\([\'"]([^\'"]*)[\'"]',
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
                            if isinstance(matches[0], tuple) if matches else False:
                                # Handle patterns with method prefix
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
            "quality_distribution": {
                level: round((count / total_commits) * 100, 1) if total_commits > 0 else 0 for level, count in impact_distribution.items()
            },
        }

    def _calculate_conventional_quality_score(self, conventional_stats: Dict[str, Any]) -> int:
        """Calculate a quality score based on conventional commit usage."""
        score = 0

        # Conventional commit adoption (40 points max)
        conventional_percentage = conventional_stats["conventional_percentage"]
        score += min(conventional_percentage * 0.4, 40)

        # Type diversity (30 points max)
        unique_types = len(conventional_stats["types"])
        type_diversity_score = min(unique_types * 10, 30)
        score += type_diversity_score

        # Scope usage (20 points max)
        scope_usage = len(conventional_stats["scopes"])
        scope_score = min(scope_usage * 5, 20)
        score += scope_score

        # Breaking changes (10 points max)
        if conventional_stats["breaking_changes"] > 0:
            breaking_score = min(conventional_stats["breaking_changes"] * 2, 10)
            score += breaking_score

        return int(score)

    def _perform_commit_analysis(self, commits: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Perform detailed analysis on commit messages and patterns."""
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
        """Identify what the user excels at based on commit message patterns."""
        excellence_keywords = {
            "bug_fixing": [
                "fix",
                "bug",
                "resolve",
                "patch",
                "correct",
                "debug",
            ],
            "feature_development": [
                "add",
                "implement",
                "create",
                "build",
                "develop",
                "feature",
            ],
            "optimization": [
                "optimize",
                "improve",
                "enhance",
                "performance",
                "speed",
                "efficient",
            ],
            "refactoring": [
                "refactor",
                "restructure",
                "reorganize",
                "clean",
                "simplify",
            ],
            "testing": [
                "test",
                "testing",
                "spec",
                "coverage",
                "unit",
                "integration",
            ],
            "documentation": [
                "doc",
                "readme",
                "comment",
                "documentation",
                "guide",
            ],
            "security": [
                "security",
                "auth",
                "secure",
                "vulnerability",
                "encrypt",
            ],
            "ui_ux": [
                "ui",
                "ux",
                "interface",
                "design",
                "styling",
                "css",
                "frontend",
            ],
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
                        pattern_counts[excellence_category]["percentage"] = round(
                            (pattern_counts[excellence_category]["count"] / total_commits) * 100, 1
                        )
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

        return {
            "patterns": sorted_patterns,
            "primary_strength": (list(sorted_patterns.keys())[0] if sorted_patterns else None),
            "conventional_commit_enhanced": conventional_analysis is not None,
        }

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

    async def analyze_repository(self, repository_full_name: str, force_refresh: bool = False) -> Optional[Dict[str, Any]]:
        """Analyze a specific GitHub repository and return comprehensive data."""
        import time

        logger.info("📁 REPOSITORY ANALYSIS STARTED")
        logger.info("=" * 60)
        logger.info(f"🏗️  Target repository: {repository_full_name}")
        logger.info(f"🔄 Force refresh: {force_refresh}")

        analysis_start = time.time()
        cache_key = f"repository:{repository_full_name}"

        # Check cache first
        if not force_refresh:
            logger.info("🔍 Checking cache...")
            cached_data = await get_cache(cache_key)
            if cached_data and isinstance(cached_data, dict):
                logger.info("💨 CACHE HIT! Returning cached repository data")
                logger.info(f"   • Repository: {cached_data.get('repository_info', {}).get('name', 'N/A')}")
                logger.info(f"   • Language: {cached_data.get('repository_info', {}).get('language', 'N/A')}")
                return cast(Dict[str, Any], cached_data)
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
                return None

            repo_end = time.time()
            logger.info(f"⏱️  Repository info fetched in {repo_end - repo_start:.2f} seconds")
            logger.info("✅ Repository info retrieved:")
            logger.info(f"   • Name: {repo_info.get('name', 'N/A')}")
            logger.info(f"   • Language: {repo_info.get('language', 'N/A')}")
            logger.info(f"   • Stars: {repo_info.get('stars', 0)}")
            logger.info(f"   • Description: {repo_info.get('description', 'N/A')[:50]}...")

            # Get repository languages
            logger.info("💻 STEP 2: ANALYZING REPOSITORY LANGUAGES")
            logger.info("-" * 40)
            lang_start = time.time()

            repo_languages = await self._get_repository_languages(owner, repo_name)

            lang_end = time.time()
            logger.info(f"⏱️  Language analysis completed in {lang_end - lang_start:.2f} seconds")
            logger.info(f"✅ Found {len(repo_languages)} programming languages in repository")

            # Get repository commits (limited for performance)
            logger.info("📝 STEP 3: ANALYZING REPOSITORY COMMITS")
            logger.info("-" * 40)
            commits_start = time.time()

            repo_commits = await self._get_repository_commits(owner, repo_name, limit=50)

            commits_end = time.time()
            logger.info(f"⏱️  Commit analysis completed in {commits_end - commits_start:.2f} seconds")
            logger.info(f"✅ Analyzed {len(repo_commits)} commits from repository")

            # Extract repository-specific skills and technologies
            logger.info("🔧 STEP 4: EXTRACTING REPOSITORY SKILLS")
            logger.info("-" * 40)
            skills_start = time.time()

            repo_skills = await self._extract_repository_skills(repo_info, repo_languages, repo_commits)

            skills_end = time.time()
            logger.info(f"⏱️  Skills extraction completed in {skills_end - skills_start:.2f} seconds")

            # Analyze repository-specific commit patterns
            logger.info("📊 STEP 5: ANALYZING COMMIT PATTERNS")
            logger.info("-" * 40)
            patterns_start = time.time()

            commit_patterns = await self._analyze_repository_commit_patterns(repo_commits, repo_languages)

            patterns_end = time.time()
            logger.info(f"⏱️  Pattern analysis completed in {patterns_end - patterns_start:.2f} seconds")

            # Compile final repository analysis
            analysis_end = time.time()
            total_time = analysis_end - analysis_start

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
            }
        except Exception as e:
            logger.error(f"Error fetching repository info for {owner}/{repo_name}: {e}")
            return None

    async def _get_repository_languages(self, owner: str, repo_name: str) -> List[Dict[str, Any]]:
        """Get programming languages used in the repository."""
        try:
            if not self.github_client:
                return []

            repo = self.github_client.get_repo(f"{owner}/{repo_name}")
            languages = repo.get_languages()

            # Convert to our format
            total_bytes = sum(languages.values())
            language_stats = []

            for language, bytes_count in languages.items():
                percentage = (bytes_count / total_bytes * 100) if total_bytes > 0 else 0
                language_stats.append(
                    {
                        "language": language,
                        "percentage": round(percentage, 2),
                        "lines_of_code": bytes_count,
                        "repository_count": 1,  # Since we're analyzing a single repo
                    }
                )

            # Sort by percentage
            language_stats.sort(key=lambda x: float(cast(float, x["percentage"])), reverse=True)

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
                                "additions": (commit.stats.additions if commit.stats else 0),
                                "deletions": (commit.stats.deletions if commit.stats else 0),
                                "total": commit.stats.total if commit.stats else 0,
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
        languages: List[Dict[str, Any]],
        commits: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Extract skills and technologies from repository data."""
        try:
            # Extract technical skills from languages
            technical_skills = [lang["language"] for lang in languages[:5]]  # Top 5 languages

            # Extract frameworks and tools from commit messages and file names
            frameworks = []
            tools: List[str] = []
            domains = []

            # Common framework patterns
            framework_patterns = {
                "React": ["react", "jsx", "tsx", "component"],
                "Vue": ["vue", "vuex", "vue-router"],
                "Angular": ["angular", "ng-", "@angular"],
                "Django": ["django", "models.py", "views.py", "urls.py"],
                "Flask": ["flask", "app.py", "routes"],
                "Express": ["express", "app.js", "routes"],
                "Spring": ["spring", "@controller", "@service"],
                "Laravel": ["laravel", "artisan"],
                "Rails": ["rails", "ruby on rails"],
                "Next.js": ["next.js", "next.config"],
                "Nuxt.js": ["nuxt", "nuxt.config"],
                "Svelte": ["svelte", ".svelte"],
                "FastAPI": ["fastapi", "pydantic"],
                "GraphQL": ["graphql", ".graphql"],
                "Docker": ["docker", "dockerfile", "docker-compose"],
                "Kubernetes": ["kubernetes", "k8s", "helm"],
                "AWS": ["aws", "lambda", "s3", "ec2"],
                "Azure": ["azure", "blob", "function"],
                "GCP": ["google cloud", "firebase", "gcp"],
            }

            # Check commit messages and file names for frameworks
            for commit in commits[:20]:  # Check first 20 commits
                message = commit.get("message", "").lower()
                for framework, patterns in framework_patterns.items():
                    if any(pattern in message for pattern in patterns):
                        if framework not in frameworks:
                            frameworks.append(framework)

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

    async def _analyze_repository_commit_patterns(self, commits: List[Dict[str, Any]], languages: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze commit patterns specific to the repository."""
        try:
            if not commits:
                return self._empty_commit_analysis()

            # Basic commit statistics
            total_commits = len(commits)
            total_additions = sum([c.get("stats", {}).get("additions", 0) for c in commits])
            total_deletions = sum([c.get("stats", {}).get("deletions", 0) for c in commits])

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
                "documentation": ["doc", "readme", "comment", "document"],
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
            if languages:
                primary_lang = languages[0]["language"]
                tech_focus[f"{primary_lang} Development"] = len(
                    [c for c in commits if any(primary_lang.lower() in str(c).lower() for c in c.get("files", []))]
                )

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
            }
        except Exception as e:
            logger.error(f"Error analyzing repository commit patterns: {e}")
            return self._empty_commit_analysis()
