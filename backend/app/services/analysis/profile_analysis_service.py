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
        """Analyze a complete user profile including skills and activity patterns."""
        # Extract skills
        skills_data = self.extract_skills(user_data, repositories)

        # Analyze activity patterns
        activity_analysis = self._analyze_activity_patterns(repositories)

        # Combine all analysis
        return {
            **skills_data,
            **activity_analysis,
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
