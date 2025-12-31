# Services Architecture

This directory contains all business logic services for the LinkedIn Recommendation Writer application, organized by domain responsibility.

## Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Service Domains](#service-domains)
- [Data Flow](#data-flow)
- [Key Patterns](#key-patterns)
- [Service Reference](#service-reference)

## Overview

The services layer implements a **domain-driven architecture** where each service subdirectory handles a specific aspect of the application's functionality. Services are designed to be:

- **Stateless**: No instance-level state beyond configuration
- **Async-first**: Heavy use of `async/await` for I/O operations
- **Cacheable**: Redis caching for expensive operations
- **Testable**: Clear interfaces and dependency injection

## Architecture

```
services/
├── ai/                    # AI model interactions and content generation
├── github/                # GitHub API integration and data fetching
├── recommendation/        # Recommendation generation orchestration
├── analysis/             # Data analysis and insight extraction
└── infrastructure/       # System services (users, monitoring, database)
```

### Service Dependencies

```
┌─────────────────────────────────────────────────────────────┐
│                      API Endpoints                           │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│              Recommendation Engine Service                   │
│  (Orchestrates the entire recommendation workflow)           │
└─────────────────────────────────────────────────────────────┘
          ↓                   ↓                    ↓
┌──────────────────┐  ┌──────────────┐  ┌──────────────────┐
│  GitHub Services │  │ AI Services  │  │ Analysis Services│
│  - User Data     │  │ - Gemini API │  │ - Skill Extract  │
│  - Commits       │  │ - Prompts    │  │ - Profile Analyze│
│  - Repositories  │  │ - Generation │  │ - Keywords       │
└──────────────────┘  └──────────────┘  └──────────────────┘
          ↓                   ↓                    ↓
┌─────────────────────────────────────────────────────────────┐
│              Infrastructure Services                         │
│  (Users, Monitoring, Database Management)                    │
└─────────────────────────────────────────────────────────────┘
```

## Service Domains

### 1. AI Services (`ai/`)

Handles all AI model interactions using Google Gemini.

**Main Services:**

- **AIService** (`ai_service_new.py`)
  - Main orchestrator for all AI functionality
  - Delegates to specialized services
  - Provides unified interface for AI operations

- **AIRecommendationService** (`ai_recommendation_service.py`)
  - Generates LinkedIn recommendations
  - Supports streaming progress updates
  - Validates output quality and naturalness
  - Implements semantic alignment checking
  - Detects and removes generic content

- **PromptService** (`prompt_service.py`)
  - Builds prompts for AI models
  - Supports multiple recommendation types (professional, academic, personal)
  - Handles tone (professional, casual, friendly, formal)
  - Manages length guidelines (short, medium, long)

- **HumanStoryGenerator** (`human_story_generator.py`)
  - Creates natural, human-sounding narratives
  - Infers personality traits from GitHub data
  - Validates naturalness of generated content

**Key Features:**
- Multiple recommendation options with different focuses
- Streaming generation with progress updates
- Content validation (structure, semantics, naturalness)
- Rate limit handling with retry logic
- Redis caching (24-hour TTL)

### 2. GitHub Services (`github/`)

Manages all GitHub API interactions with async batch processing.

**Main Services:**

- **GitHubUserService** (`github_user_service.py`)
  - Fetches comprehensive user profile data
  - Analyzes starred repositories for interests
  - Fetches user organizations
  - Caches results (4-hour TTL)
  - **Pipeline Performance**:
    - 7-step analysis pipeline with timing
    - Concurrent batch processing
    - Rate limit protection

- **GitHubCommitService** (`github_commit_service.py`)
  - Analyzes up to 150 commits per user
  - Async batch processing (3 concurrent requests)
  - Processes repositories in batches of 5
  - **Advanced Analysis**:
    - Conventional commit parsing
    - Impact scoring (high/moderate/low/minimal)
    - Excellence pattern detection
    - Technical contribution categorization
    - Soft skill inference from patterns

- **GitHubRepositoryService** (`github_repository_service.py`)
  - Repository-specific data fetching
  - Dependency file parsing
  - Technology stack detection

**Key Features:**
- Async batch processing with semaphores
- Comprehensive error handling
- Detailed logging with emoji indicators
- Cache-first strategy with force refresh option
- Contributor-focused analysis

### 3. Recommendation Services (`recommendation/`)

Orchestrates the recommendation generation workflow.

**Main Services:**

- **RecommendationEngineService** (`recommendation_engine_service.py`)
  - Orchestrates entire generation process
  - Coordinates GitHub data fetching
  - Manages AI service interactions
  - Handles recommendation options
  - Quality analysis and validation

- **RecommendationService** (`recommendation_service.py`)
  - Database persistence
  - CRUD operations for recommendations
  - Status management

**Key Features:**
- Multi-option generation (2+ variations)
- Quality scoring system
- Regeneration with refinement
- Keyword-based refinement

### 4. Analysis Services (`analysis/`)

Extracts insights from GitHub data.

**Main Services:**

- **ProfileAnalysisService** (`profile_analysis_service.py`)
  - **Skill Extraction**:
    - Technical skills (languages, frameworks)
    - Tools (AWS, Docker, databases)
    - Domains (ML, Web Dev, DevOps)
    - Dependencies from package files
  - **Activity Analysis**:
    - Repository patterns
    - Collaboration indicators
    - Technical maturity assessment
    - High-impact contribution detection

- **KeywordRefinementService** (`keyword_refinement_service.py`)
  - Keyword-based recommendation refinement
  - Intelligent keyword weighting
  - Exclusion and inclusion filters

- **SkillAnalysisService** (`skill_analysis_service.py`)
  - Deep skill categorization
  - Skill frequency analysis
  - Technology trend detection

**Key Features:**
- Pattern-based skill detection
- Technology mapping (50+ frameworks/tools)
- Domain classification
- Collaboration pattern analysis
- Technical maturity scoring

### 5. Infrastructure Services (`infrastructure/`)

System-level services for core functionality.

**Main Services:**

- **UserService** (`user_service.py`)
  - User CRUD operations
  - Profile management
  - Authentication support

- **HealthMonitor** (`health_monitor.py`)
  - System health checks
  - Service availability monitoring
  - Performance metrics

- **DatabaseAnalyzer** (`database_analyzer.py`)
  - Database performance analysis
  - Query optimization suggestions
  - Schema validation

- **DatabaseOptimizer** (`database_optimizer.py`)
  - Index optimization
  - Query performance tuning
  - Cache warming

- **DatabaseTester** (`database_tester.py`)
  - Database connection testing
  - Data integrity validation
  - Migration verification

## Data Flow

### Recommendation Generation Flow

```
1. API Request
   └─> /api/recommendations/generate
       - GitHub username
       - Options (tone, length, type)

2. Recommendation Engine Service
   └─> Orchestrates workflow
       ├─> Check cache (Redis)
       └─> If miss, proceed to generation

3. GitHub Data Collection
   └─> GitHub User Service
       ├─> User profile (4-hour cache)
       ├─> Repositories (top 10, sorted by update)
       ├─> Starred repos (interest analysis)
       └─> Organizations

4. Commit Analysis
   └─> GitHub Commit Service
       ├─> Fetch up to 150 commits (async batch)
       ├─> Parse conventional commits
       ├─> Calculate impact scores
       └─> Identify excellence patterns

5. Pull Request Analysis
   └─> GitHub Commit Service
       ├─> Fetch up to 50 PRs (async batch)
       ├─> Analyze collaboration patterns
       ├─> Calculate merge rate
       └─> Extract problem-solving approaches

6. Skill Extraction
   └─> Profile Analysis Service
       ├─> Extract from repositories
       ├─> Parse dependency files
       ├─> Map to frameworks/tools
       └─> Infer technical maturity

7. AI Generation
   └─> AI Recommendation Service
       ├─> Build prompt (Prompt Service)
       ├─> Generate options (2 variations)
       ├─> Validate structure & semantics
       ├─> Check naturalness
       └─> Format output (proper paragraphs)

8. Cache & Return
   └─> Cache result (24-hour TTL)
       └─> Return to client
```

### Caching Strategy

| Service | Cache Key Pattern | TTL | Purpose |
|---------|------------------|-----|---------|
| GitHub User Data | `github:user_data:{username}` | 4 hours | User profile info |
| GitHub Repos | `github:repos:{username}:{count}` | 4 hours | Repository list |
| GitHub Profile | `github_profile:{username}:{context}` | 4 hours | Full analysis |
| AI Recommendation | `ai_recommendation_v3:{hash}:{context}` | 24 hours | Generated content |
| Repository PRs | `repo_prs:{repo}:{author}:{max}` | 4 hours | Pull requests |

## Key Patterns

### 1. Async Batch Processing

Used extensively in GitHub services to handle rate limits:

```python
# Example from GitHubCommitService
semaphore = asyncio.Semaphore(MAX_CONCURRENT_REQUESTS)  # 3 concurrent
repo_batches = [repos[i:i+5] for i in range(0, len(repos), 5)]  # Batch of 5

for batch in repo_batches:
    tasks = [fetch_commits_async(semaphore, repo) for repo in batch]
    results = await asyncio.gather(*tasks, return_exceptions=True)
```

**Benefits:**
- Respects rate limits
- Maximizes throughput
- Handles errors gracefully

### 2. Service Composition

Services delegate to specialized sub-services:

```python
class AIService:
    def __init__(self):
        self.prompt_service = PromptService()
        self.recommendation_service = AIRecommendationService(self.prompt_service)
        self.keyword_refinement_service = KeywordRefinementService(self.prompt_service)
```

**Benefits:**
- Single Responsibility Principle
- Easier testing
- Flexible composition

### 3. Streaming Progress

AI generation provides real-time progress updates:

```python
async def generate_recommendation_stream():
    yield {"stage": "Initializing AI service...", "progress": 5}
    yield {"stage": "Analyzing GitHub profile...", "progress": 15}
    # ... more stages
    yield {"stage": "Recommendation ready!", "progress": 100, "result": data}
```

**Benefits:**
- Better UX for long operations
- Transparency into process
- Early error detection

### 4. Multi-Layer Validation

AI output goes through multiple validation layers:

1. **Structure Validation**: Paragraph count, word count, sentence completeness
2. **Semantic Validation**: Data coverage, username mention, skill alignment
3. **Generic Content Detection**: Buzzword detection, vague descriptor filtering
4. **Naturalness Validation**: Robotic phrase detection, human-like flow

### 5. Cache-First Architecture

All expensive operations check cache before execution:

```python
async def analyze_github_profile(username, force_refresh=False):
    cache_key = f"github_profile:{username}"

    if not force_refresh:
        cached = await get_cache(cache_key)
        if cached:
            return cached

    # Expensive operation
    result = await fetch_and_analyze()
    await set_cache(cache_key, result, ttl=14400)
    return result
```

## Service Reference

### AI Services

| Service | Primary Methods | Purpose |
|---------|----------------|---------|
| AIService | `generate_recommendation()`, `regenerate_recommendation()` | Main AI orchestrator |
| AIRecommendationService | `generate_recommendation_stream()`, `_generate_single_option()` | Gemini API integration |
| PromptService | `build_prompt()`, `extract_title()` | Prompt engineering |
| HumanStoryGenerator | `generate_human_story()`, `validate_naturalness()` | Natural narrative generation |

### GitHub Services

| Service | Primary Methods | Purpose |
|---------|----------------|---------|
| GitHubUserService | `analyze_github_profile()`, `get_repository_contributors()` | User profile analysis |
| GitHubCommitService | `analyze_contributor_commits()`, `fetch_user_pull_requests_across_repos()` | Commit & PR analysis |
| GitHubRepositoryService | Repository data fetching | Repository-specific operations |

### Recommendation Services

| Service | Primary Methods | Purpose |
|---------|----------------|---------|
| RecommendationEngineService | `generate_recommendation()`, `generate_recommendation_options()` | Workflow orchestration |
| RecommendationService | CRUD operations | Database persistence |

### Analysis Services

| Service | Primary Methods | Purpose |
|---------|----------------|---------|
| ProfileAnalysisService | `extract_skills()`, `analyze_user_profile()` | Skill & profile analysis |
| KeywordRefinementService | `refine_recommendation_with_keywords()` | Keyword-based refinement |
| SkillAnalysisService | Skill categorization | Deep skill analysis |

### Infrastructure Services

| Service | Primary Methods | Purpose |
|---------|----------------|---------|
| UserService | `get_user_by_id()`, `update_user_profile()` | User management |
| HealthMonitor | Health check operations | System monitoring |
| DatabaseAnalyzer | Performance analysis | Database insights |
| DatabaseOptimizer | Optimization operations | Performance tuning |

## Configuration

### Environment Variables

Services rely on these environment variables:

```bash
# GitHub API
GITHUB_TOKEN=ghp_xxxxxxxxxxxxx

# Google Gemini AI
GEMINI_API_KEY=xxxxxxxxxxxxx
GEMINI_MODEL=gemini-2.0-flash-exp
GEMINI_TEMPERATURE=0.7
GEMINI_MAX_TOKENS=8192

# Redis Cache
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=
REDIS_DB=0

# Application
ENVIRONMENT=development  # development|production
```

### Performance Tuning

Key parameters for optimization:

```python
# GitHubCommitService
MAX_CONCURRENT_REQUESTS = 3      # Concurrent GitHub API requests
REPOSITORY_BATCH_SIZE = 5        # Repos per batch
MAX_COMMITS_PER_REPO = 30        # Commits per repository
COMMIT_ANALYSIS_CACHE_TTL = 14400  # 4 hours

# AIRecommendationService
rate_limit_requests_per_minute = 15  # Gemini API rate limit
```

## Best Practices

### 1. Adding a New Service

1. Create service file in appropriate domain directory
2. Inherit common patterns (async, caching, logging)
3. Add initialization in `__init__.py`
4. Write comprehensive tests
5. Update this README

### 2. Error Handling

Always handle GitHub API errors gracefully:

```python
try:
    user = self.github_client.get_user(username)
except GithubException as e:
    if e.status == 404:
        logger.error(f"User '{username}' not found")
    elif e.status == 403:
        logger.error("API rate limit exceeded")
    return None
```

### 3. Logging

Use structured logging with emoji indicators:

```python
logger.info("🎯 COMMIT ANALYSIS: Targeting 150 commits")
logger.info("✅ Analysis completed successfully")
logger.warning("⚠️  GitHub token not configured")
logger.error("❌ Failed to fetch user data")
```

### 4. Caching

Always provide cache invalidation:

```python
async def fetch_data(username, force_refresh=False):
    cache_key = f"data:{username}"

    if not force_refresh:
        cached = await get_cache(cache_key)
        if cached:
            return cached

    # Fetch fresh data
```

### 5. Testing

Mock external dependencies:

```python
@pytest.fixture
def mock_github_client():
    client = Mock()
    client.get_user.return_value = Mock(login="testuser")
    return client
```

## Monitoring

### Key Metrics to Track

1. **GitHub API Usage**
   - Rate limit remaining
   - Requests per minute
   - Cache hit rate

2. **AI Generation**
   - Generation time per request
   - Validation failure rate
   - Cache hit rate

3. **Service Performance**
   - Average response time
   - Error rate
   - Concurrent requests

### Logging Levels

- **INFO**: Normal operations, pipeline progress
- **WARNING**: Recoverable errors, cache misses
- **ERROR**: Failed operations, API errors
- **DEBUG**: Detailed analysis, validation results

## Troubleshooting

### Common Issues

**1. GitHub Rate Limit Exceeded**
```
Error: API rate limit reached. Please wait X seconds.
Solution: Reduce MAX_CONCURRENT_REQUESTS or implement exponential backoff
```

**2. Gemini API Rate Limit**
```
Error: 429 RESOURCE_EXHAUSTED
Solution: Service automatically extracts retry delay and raises helpful error
```

**3. Cache Connection Issues**
```
Error: Redis connection failed
Solution: Check REDIS_HOST and REDIS_PORT, ensure Redis is running
```

**4. Low Quality Recommendations**
```
Issue: Generic or non-specific content
Solution: Check validation results, adjust prompts, increase data coverage
```

## Contributing

When adding or modifying services:

1. Maintain async-first approach
2. Implement proper error handling
3. Add comprehensive logging
4. Include Redis caching where appropriate
5. Write unit and integration tests
6. Update this documentation

## Related Documentation

- [API Documentation](../../docs/api/)
- [Database Schema](../../docs/database/)
- [Deployment Guide](../../docs/deployment/)
- [Testing Guide](../../docs/testing/)

## License

See main project LICENSE file.
