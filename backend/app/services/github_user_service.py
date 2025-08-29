import json
from datetime import datetime
from typing import Any, Dict, List, Optional

from github import Github
from github.GithubException import GithubException
from loguru import logger

from app.core.config import settings
from app.core.redis_client import get_cache, set_cache
from app.services.github_commit_service import GitHubCommitService


class GitHubUserService:
    """Service for fetching and analyzing GitHub user profile data."""

    COMMIT_ANALYSIS_CACHE_TTL = 14400  # 4 hours cache for expensive operations

    def __init__(self, commit_service: GitHubCommitService) -> None:
        """Initialize GitHub user service."""
        self.github_client = None
        if settings.GITHUB_TOKEN:
            logger.info("🔧 Initializing GitHub client with token for user service")
            self.github_client = Github(settings.GITHUB_TOKEN)
        else:
            logger.warning("⚠️  GitHub token not configured - GitHub API calls will fail in user service")
        self.commit_service = commit_service

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
                return cached_data
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

            # Analyze commits (up to 150) using the commit service
            logger.info("📝 STEP 5: ANALYZING COMMITS (ASYNC BATCH PROCESSING) with Commit Service")
            logger.info("-" * 40)
            commits_start = time.time()

            commit_analysis = await self.commit_service.analyze_contributor_commits(username, repositories)

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

            # Provide more specific error messages based on the GitHub API response
            if hasattr(e, "status"):
                if e.status == 404:
                    logger.error(f"   💡 User '{username}' was not found on GitHub")
                    logger.error("   💡 Possible reasons:")
                    logger.error("      • Username doesn't exist")
                    logger.error("      • Username has a typo")
                    logger.error("      • User profile is set to private")
                    logger.error(f"      • Username is case-sensitive (try: {username.lower()})")
                elif e.status == 403:
                    logger.error("   💡 Access forbidden - this could mean:")
                    logger.error("      • GitHub API rate limit exceeded")
                    logger.error("      • Repository is private and token lacks access")
                    logger.error("      • GitHub token needs additional permissions")
                elif e.status == 401:
                    logger.error("   💡 Authentication failed:")
                    logger.error("      • GitHub token is invalid or expired")
                    logger.error("      • Token doesn't have required permissions")
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
        language_counts: Dict[str, int] = {}
        topic_counts: Dict[str, int] = {}
        technology_focus: Dict[str, int] = {}

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

            dependencies: List[str] = []
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
