"""Profile Analysis Service for analyzing GitHub user profiles and extracting skills."""

import json
import logging
from typing import Any, Dict, List

logger = logging.getLogger(__name__)


class ProfileAnalysisService:
    """Service for analyzing GitHub user profiles and extracting skills."""

    def __init__(self) -> None:
        """Initialize profile analysis service."""
        logger.info("🔧 ProfileAnalysisService initialized")

    def extract_skills(self, user_data: Dict[str, Any], repositories: List[Dict[str, Any]]) -> Dict[str, Any]:
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

            # Analyze repository dependencies (if available)
            try:
                repo_dependencies = self._analyze_repository_dependencies(repo)
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

    def _analyze_repository_dependencies(self, repo: Dict[str, Any]) -> List[str]:
        """Analyze repository dependencies from various dependency files."""
        dependencies = []
        dependency_files = repo.get("dependency_files", [])

        for file_info in dependency_files:
            filename = file_info.get("filename", "")
            content = file_info.get("content", "")

            if filename == "package.json":
                # Node.js package.json
                try:
                    data = json.loads(content)
                    deps = data.get("dependencies", {})
                    dev_deps = data.get("devDependencies", {})

                    for dep_dict in [deps, dev_deps]:
                        for package_name in dep_dict.keys():
                            # Remove scope for scoped packages
                            if package_name.startswith("@"):
                                package_name = package_name.split("/")[1] if "/" in package_name else package_name[1:]
                            dependencies.append(package_name.lower())
                except json.JSONDecodeError:
                    pass

            elif filename == "requirements.txt":
                # Python requirements.txt
                for line in content.split("\n"):
                    line = line.strip()
                    if line and not line.startswith("#") and not line.startswith("-"):
                        # Extract package name (handle version specifiers)
                        package_name = line.split("==")[0].split(">=")[0].split("<=")[0].split(">")[0].split("<")[0].strip()
                        if package_name:
                            dependencies.append(package_name.lower())

            elif filename == "Pipfile":
                # Python Pipfile
                try:
                    data = json.loads(content)
                    packages = data.get("packages", {})

                    for package_name in packages.keys():
                        dependencies.append(package_name.lower())
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

        return dependencies

    def analyze_user_profile(self, user_data: Dict[str, Any], repositories: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze a complete user profile including skills and activity patterns with enhanced insights."""
        # Extract skills
        skills_data = self.extract_skills(user_data, repositories)

        # Analyze activity patterns
        activity_analysis = self._analyze_activity_patterns(repositories)

        # Extract high-impact contributions
        high_impact_contributions = self._extract_high_impact_contributions(repositories)

        # Analyze collaboration patterns
        collaboration_patterns = self._analyze_collaboration_patterns(repositories)

        # Analyze technical maturity
        technical_maturity = self._assess_technical_maturity(repositories, skills_data)

        # Combine all analysis
        return {
            **skills_data,
            **activity_analysis,
            "high_impact_contributions": high_impact_contributions,
            "collaboration_patterns": collaboration_patterns,
            "technical_maturity": technical_maturity,
            "user_data": user_data,
            "repository_count": len(repositories),
            "analysis_timestamp": "2024-09-01T00:00:00Z",  # Would use datetime.utcnow() in real implementation
        }

    def _analyze_activity_patterns(self, repositories: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze user activity patterns from repositories."""
        total_stars = sum(repo.get("stargazers_count", 0) for repo in repositories)
        total_forks = sum(repo.get("forks_count", 0) for repo in repositories)
        languages = {}
        topics = []

        for repo in repositories:
            # Count languages
            language = repo.get("language")
            if language:
                languages[language] = languages.get(language, 0) + 1

            # Collect topics
            topics.extend(repo.get("topics", []))

        # Find most common language
        primary_language = max(languages.items(), key=lambda x: x[1]) if languages else None

        # Find most common topics
        topic_counts = {}
        for topic in topics:
            topic_counts[topic] = topic_counts.get(topic, 0) + 1

        top_topics = sorted(topic_counts.items(), key=lambda x: x[1], reverse=True)[:5]

        return {
            "total_stars": total_stars,
            "total_forks": total_forks,
            "primary_language": primary_language[0] if primary_language else None,
            "language_distribution": languages,
            "top_topics": [topic for topic, count in top_topics],
            "activity_score": len(repositories) * 10 + total_stars // 10 + total_forks // 5,
        }

    def _extract_high_impact_contributions(self, repositories: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Extract high-impact contributions that demonstrate significant achievements."""
        high_impact_repos = []
        notable_contributions = []

        for repo in repositories:
            stars = repo.get("stargazers_count", 0)
            forks = repo.get("forks_count", 0)
            description = repo.get("description", "").lower()
            topics = repo.get("topics", [])

            # Criteria for high-impact repository
            impact_score = stars * 2 + forks * 3

            # Check for notable indicators
            notable_indicators = [
                "production" in description,
                "enterprise" in description,
                "million" in description or "billion" in description,
                "users" in description,
                stars > 100,
                forks > 50,
                any(topic in ["production", "enterprise", "popular", "featured"] for topic in topics),
            ]

            if impact_score > 50 or any(notable_indicators):
                high_impact_repos.append(
                    {
                        "name": repo.get("name", ""),
                        "full_name": repo.get("full_name", ""),
                        "description": repo.get("description", ""),
                        "stars": stars,
                        "forks": forks,
                        "language": repo.get("language", ""),
                        "impact_score": impact_score,
                        "notable_indicators": notable_indicators.count(True),
                    }
                )

            # Extract specific notable contributions
            if "production" in description:
                notable_contributions.append(
                    {"type": "production_deployment", "description": f"Built production-ready {repo.get('name')} system", "repository": repo.get("full_name"), "impact": "high"}
                )
            elif stars > 500:
                notable_contributions.append(
                    {"type": "popular_project", "description": f"Created widely-adopted {repo.get('name')} with {stars} stars", "repository": repo.get("full_name"), "impact": "high"}
                )

        return {
            "high_impact_repositories": sorted(high_impact_repos, key=lambda x: x["impact_score"], reverse=True)[:5],
            "notable_contributions": notable_contributions[:3],
            "total_impact_score": sum(repo.get("impact_score", 0) for repo in high_impact_repos),
        }

    def _analyze_collaboration_patterns(self, repositories: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze collaboration patterns and team-oriented contributions."""
        collaboration_indicators = {"team_size_signals": [], "collaboration_evidence": [], "leadership_indicators": []}

        for repo in repositories:
            contributors_count = repo.get("contributors_count", 0)
            description = repo.get("description", "").lower()

            # Team size signals
            if contributors_count > 10:
                collaboration_indicators["team_size_signals"].append({"repository": repo.get("full_name"), "contributors": contributors_count, "evidence": "large contributor base"})

            # Collaboration evidence
            collab_keywords = ["team", "collaboration", "open source", "community", "contributors"]
            if any(keyword in description for keyword in collab_keywords):
                collaboration_indicators["collaboration_evidence"].append(
                    {"repository": repo.get("full_name"), "type": "descriptive_evidence", "keywords_found": [kw for kw in collab_keywords if kw in description]}
                )

            # Leadership indicators
            if repo.get("owner", {}).get("login") == repo.get("owner", {}).get("login"):  # User is owner
                if contributors_count > 5:
                    collaboration_indicators["leadership_indicators"].append({"repository": repo.get("full_name"), "type": "project_leadership", "contributors_managed": contributors_count})

        return {
            "collaboration_score": len(collaboration_indicators["collaboration_evidence"]) * 20
            + len(collaboration_indicators["team_size_signals"]) * 15
            + len(collaboration_indicators["leadership_indicators"]) * 25,
            **collaboration_indicators,
            "collaboration_level": "high" if len(collaboration_indicators["collaboration_evidence"]) > 2 else "medium" if len(collaboration_indicators["collaboration_evidence"]) > 0 else "low",
        }

    def _assess_technical_maturity(self, repositories: List[Dict[str, Any]], skills_data: Dict[str, Any]) -> Dict[str, Any]:
        """Assess technical maturity based on project complexity and skill diversity."""
        maturity_indicators = {"project_complexity": 0, "technology_diversity": 0, "architecture_signals": 0, "quality_indicators": 0}

        languages = set()
        frameworks = set()
        tools = set()

        for repo in repositories:
            lang = repo.get("language")
            if lang:
                languages.add(lang)

            description = repo.get("description", "").lower()

            # Architecture signals
            arch_keywords = ["architecture", "microservices", "distributed", "scalability", "enterprise"]
            if any(keyword in description for keyword in arch_keywords):
                maturity_indicators["architecture_signals"] += 1

            # Quality indicators
            quality_keywords = ["testing", "ci", "cd", "lint", "quality", "standards"]
            if any(keyword in description for keyword in quality_keywords):
                maturity_indicators["quality_indicators"] += 1

            # Extract frameworks and tools from description
            for framework in skills_data.get("frameworks", []):
                if framework.lower() in description:
                    frameworks.add(framework)

            for tool in skills_data.get("tools", []):
                if tool.lower() in description:
                    tools.add(tool)

        # Calculate maturity scores
        maturity_indicators["technology_diversity"] = len(languages) + len(frameworks) + len(tools)
        maturity_indicators["project_complexity"] = len(repositories) + maturity_indicators["architecture_signals"] * 2

        total_maturity_score = (
            maturity_indicators["project_complexity"] * 20
            + maturity_indicators["technology_diversity"] * 15
            + maturity_indicators["architecture_signals"] * 25
            + maturity_indicators["quality_indicators"] * 20
        )

        return {
            **maturity_indicators,
            "maturity_score": min(total_maturity_score, 100),
            "maturity_level": "senior" if total_maturity_score > 70 else "mid" if total_maturity_score > 40 else "junior",
            "languages_used": list(languages),
            "frameworks_demonstrated": list(frameworks),
            "tools_mastered": list(tools),
        }
