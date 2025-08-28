# LinkedIn Recommendation Writer

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Docker](https://img.shields.io/badge/docker-%230db7ed.svg?style=flat&logo=docker&logoColor=white)](https://docker.com)
[![React](https://img.shields.io/badge/react-%2320232a.svg?style=flat&logo=react&logoColor=%2361DAFB)](https://reactjs.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-005571?style=flat&logo=fastapi)](https://fastapi.tiangolo.com)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-316192?style=flat&logo=postgresql&logoColor=white)](https://postgresql.org)
[![Redis](https://img.shields.io/badge/redis-%23DD0031.svg?style=flat&logo=redis&logoColor=white)](https://redis.io)

Generate professional LinkedIn recommendations using GitHub data and AI.

> Transform technical contributions into compelling professional narratives with AI-powered analysis.

## 📋 Table of Contents

- [✨ Features](#-features)
- [🚀 Quick Start](#-quick-start)
- [📋 Prerequisites](#-prerequisites)
- [🛠️ Installation](#️-installation)
- [⚙️ Configuration](#️-configuration)
- [🏗️ Architecture](#️-architecture)
- [📚 API Documentation](#-api-documentation)
- [🚀 Deployment](#-deployment)
- [🔧 Development](#-development)
- [🧪 Testing](#-testing)
- [🔍 Troubleshooting](#-troubleshooting)
- [🤝 Contributing](#-contributing)
- [📄 License](#-license)
- [❓ FAQ](#-faq)
- [📞 Support](#-support)

## ✨ Features

- 🔍 **GitHub Analysis**: Analyzes repositories, languages, and contribution patterns
- 🤖 **AI-Powered**: Uses Google Gemini AI for natural recommendation generation
- ⚙️ **Customizable**: Multiple types, tones, and lengths available
- 💾 **History Tracking**: Save and manage all generated recommendations
- 🚀 **Fast Results**: Intelligent caching for quick responses
- 🔒 **Privacy-Focused**: Only uses public GitHub data
- 🎨 **Modern UI**: Clean, responsive interface built with React & Tailwind CSS
- 📊 **Analytics**: Track usage patterns and recommendation performance
- 🌐 **Multi-format**: Generate recommendations for LinkedIn, emails, and more

## 🚀 Quick Start

**Get everything running in 3 minutes!**

```bash
git clone <repository-url>
cd linkedin-recommendation-writer-app
cp env.template .env
# Edit .env with your API keys
make setup
```

**That's it!** Access your app at:

- **Frontend**: <http://localhost:5173>
- **Backend**: <http://localhost:8000>
- **API Docs**: <http://localhost:8000/docs>

## 📋 Prerequisites

Before you begin, ensure you have the following:

### Required Software

- **Docker & Docker Compose** (v20.10+)
- **Git** (v2.30+)
- **Make** (build automation)

### API Keys Required

- **GitHub Personal Access Token**
  - Get from: [GitHub Settings > Developer settings > Personal access tokens](https://github.com/settings/tokens)
  - Required scopes: `repo`, `read:org`, `read:user`, `read:project`
- **Google Gemini API Key**
  - Get from: [Google AI Studio](https://makersuite.google.com/app/apikey)
  - Free tier available with generous limits

### System Requirements

- **RAM**: 4GB minimum, 8GB recommended
- **Disk Space**: 2GB for application + Docker images
- **Network**: Stable internet for API calls

## 🛠️ Installation

Choose your preferred installation method:

### Option 1: Docker (Recommended)

```bash
# Clone repository
git clone <repository-url>
cd linkedin-recommendation-writer-app

# Configure environment
cp env.template .env
# Edit .env with your API keys (GITHUB_TOKEN, GEMINI_API_KEY)

# Quick setup (builds and starts everything)
make setup
```

### Option 2: Local Development

#### Backend Setup

```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

#### Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

#### Database Setup

```bash
# Install PostgreSQL and Redis locally
# Or use Docker for just the database services
docker run -d -p 5432:5432 -e POSTGRES_PASSWORD=your_password postgres:15
docker run -d -p 6379:6379 redis:7-alpine
```

### Option 3: Using Docker Compose Manually

```bash
# Clone and configure
git clone <repository-url>
cd linkedin-recommendation-writer-app
cp env.template .env
# Edit .env with your API keys

# Build and start services
docker-compose build
docker-compose up -d

# View logs
docker-compose logs -f
```

### Verify Installation

Once running, verify everything is working:

```bash
# Check service health
curl http://localhost:8000/health

# Check API documentation
open http://localhost:8000/docs

# Check frontend
open http://localhost:5173
```

## ⚙️ Configuration

### Environment Variables

Create a `.env` file in the project root with the following variables:

```bash
# ============================================
# REQUIRED API KEYS
# ============================================

# GitHub Personal Access Token
# Get from: https://github.com/settings/tokens
# Required scopes: repo, read:org, read:user, read:project
GITHUB_TOKEN=your_github_token_here

# Google Gemini API Key
# Get from: https://makersuite.google.com/app/apikey
GEMINI_API_KEY=your_gemini_api_key_here

# ============================================
# DATABASE CONFIGURATION
# ============================================

# PostgreSQL Configuration
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your_secure_password_here
POSTGRES_DB=linkedin_recommendations

# Database URL (alternative to individual vars)
DATABASE_URL=postgresql://postgres:your_password@localhost:5432/linkedin_recommendations

# ============================================
# REDIS CONFIGURATION
# ============================================

# Redis for caching
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=
REDIS_DB=0

# Redis URL (alternative)
REDIS_URL=redis://localhost:6379/0

# ============================================
# APPLICATION SETTINGS
# ============================================

# Environment (development/production)
NODE_ENV=development
ENVIRONMENT=development

# Server Configuration
BACKEND_HOST=0.0.0.0
BACKEND_PORT=8000
FRONTEND_PORT=5173

# CORS Settings
ALLOWED_ORIGINS=http://localhost:5173,http://localhost:3000

# ============================================
# AI MODEL CONFIGURATION
# ============================================

# Gemini Model Settings
GEMINI_MODEL=gemini-2.0-flash-exp
GEMINI_TEMPERATURE=0.7
GEMINI_MAX_TOKENS=2048

# ============================================
# LOGGING & MONITORING
# ============================================

# Logging Level (DEBUG, INFO, WARNING, ERROR)
LOG_LEVEL=INFO
LOG_FORMAT=json

# Performance Monitoring
ENABLE_METRICS=true
METRICS_PORT=9090

# ============================================
# SECURITY SETTINGS
# ============================================

# JWT Secret (generate a strong random string)
JWT_SECRET=your_super_secret_jwt_key_here

# API Rate Limiting
RATE_LIMIT_REQUESTS=100
RATE_LIMIT_WINDOW=3600

# SSL/TLS (for production)
SSL_CERT_PATH=
SSL_KEY_PATH=
```

### Configuration Validation

The application validates your configuration on startup. Missing required variables will cause the application to fail with clear error messages.

### Security Best Practices

- 🔐 **Never commit `.env` files** to version control
- 🔑 **Use strong, unique passwords** for database
- 🛡️ **Rotate API keys regularly** for security
- 🔒 **Use environment-specific configurations** for different deployments

## 🚀 Deployment

Choose the deployment option that best fits your needs:

### Quick Comparison

| Platform         | Setup Time | Cost               | Scaling     | Best For             |
| ---------------- | ---------- | ------------------ | ----------- | -------------------- |
| Docker           | 5-10 min   | Free (self-hosted) | Manual      | Development/Testing  |
| Railway          | 10-15 min  | $5-15/month        | Automatic   | Quick prototyping    |
| Vercel + Railway | 15-20 min  | $15-30/month       | Automatic   | Full-stack web app   |
| AWS/GCP          | 30-60 min  | $20-100/month      | Enterprise  | Production workloads |
| DigitalOcean     | 20-30 min  | $12-50/month       | Manual/Auto | Small to medium apps |

### Option 1: Docker (Recommended for Development)

```bash
# Production-ready setup
make setup-prod

# Or manually
make prod-build
make prod-up

# Access at http://localhost:80
```

### Option 2: Railway (Easiest PaaS)

**Perfect for quick deployment and prototyping**

[![Deploy on Railway](https://railway.app/button.svg)](https://railway.app/template/your-template-id)

#### Manual Railway Setup:

1. **Connect Repository**:

   ```bash
   # Railway will detect your Dockerfile automatically
   ```

2. **Environment Variables**:

   - Add all variables from your `.env` file
   - Railway provides PostgreSQL and Redis add-ons

3. **Database Setup**:

   - Use Railway's PostgreSQL service
   - Use Railway's Redis service
   - Update `DATABASE_URL` and `REDIS_URL` accordingly

4. **Deploy**:
   ```bash
   # Railway deploys automatically on push
   git push origin main
   ```

### Option 3: Vercel + Railway (Frontend on Vercel, Backend on Railway)

**Best for performance and scalability**

#### Frontend (Vercel):

```bash
# Install Vercel CLI
npm i -g vercel

# Deploy frontend
cd frontend
vercel --prod

# Set environment variables in Vercel dashboard
# VITE_API_URL=https://your-railway-backend.railway.app
```

#### Backend (Railway):

```bash
# Deploy backend to Railway as above
# Update CORS settings for Vercel domain
ALLOWED_ORIGINS=https://your-app.vercel.app
```

### Option 4: AWS (Production-Ready)

#### Using AWS ECS (Elastic Container Service):

1. **Build and Push Docker Images**:

```bash
# Build for production
make prod-build

# Tag and push to ECR
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin your-account.dkr.ecr.us-east-1.amazonaws.com
docker tag linkedin-recommendation-writer:latest your-account.dkr.ecr.us-east-1.amazonaws.com/linkedin-recommendation-writer:latest
docker push your-account.dkr.ecr.us-east-1.amazonaws.com/linkedin-recommendation-writer:latest
```

2. **Infrastructure Setup**:

```bash
# Use AWS CDK or CloudFormation
# Create VPC, ECS Cluster, RDS PostgreSQL, ElastiCache Redis
```

3. **Deploy**:

```bash
# Update task definition with your ECR image
# Deploy service to ECS
```

#### Using AWS App Runner (Simpler):

```bash
# App Runner can deploy directly from ECR
# Automatic scaling and load balancing included
```

### Option 5: Google Cloud Platform

#### Using Cloud Run:

1. **Build and Push to GCR**:

```bash
# Build for production
make prod-build

# Tag and push to GCR
docker tag linkedin-recommendation-writer:latest gcr.io/your-project/linkedin-recommendation-writer:latest
docker push gcr.io/your-project/linkedin-recommendation-writer:latest
```

2. **Deploy to Cloud Run**:

```bash
gcloud run deploy linkedin-recommendation-writer \
  --image gcr.io/your-project/linkedin-recommendation-writer:latest \
  --platform managed \
  --port 8000 \
  --allow-unauthenticated \
  --set-env-vars "ENVIRONMENT=production"
```

3. **Set up Cloud SQL (PostgreSQL) and Memorystore (Redis)**:

```bash
# Create PostgreSQL instance
gcloud sql instances create linkedin-db --database-version=POSTGRES_15

# Create Redis instance
gcloud redis instances create linkedin-cache --size=1 --region=us-central1
```

### Option 6: DigitalOcean

#### App Platform (Easiest):

1. **Connect Repository**:

   - DigitalOcean will detect Dockerfile
   - Set up database and Redis through DigitalOcean Marketplace

2. **Environment Variables**:

   - Add all required environment variables
   - Use DigitalOcean Managed Databases for PostgreSQL and Redis

3. **Deploy**:
   ```bash
   # Automatic deployment on push
   git push origin main
   ```

#### Droplet (More Control):

```bash
# Create Ubuntu droplet
# SSH and run your deployment script
make setup-prod
```

### Option 7: Heroku (Legacy but Simple)

```bash
# Install Heroku CLI
# Create app
heroku create your-app-name

# Add buildpacks
heroku buildpacks:add heroku/python
heroku buildpacks:add heroku/nodejs

# Set environment variables
heroku config:set GITHUB_TOKEN=your_token
heroku config:set GEMINI_API_KEY=your_key

# Add PostgreSQL and Redis add-ons
heroku addons:create heroku-postgresql:hobby-dev
heroku addons:create heroku-redis:hobby-dev

# Deploy
git push heroku main
```

### Production Checklist

Before going live, ensure:

- ✅ **SSL/TLS enabled** (Let's Encrypt or platform certificates)
- ✅ **Environment variables** properly configured
- ✅ **Database backups** scheduled
- ✅ **Monitoring** set up (logs, metrics, alerts)
- ✅ **Rate limiting** configured for API endpoints
- ✅ **CORS settings** updated for your domain
- ✅ **DNS records** pointing to your deployment
- ✅ **Health checks** passing
- ✅ **Load testing** completed

## 🏗️ Architecture

### Backend (FastAPI)

- **Framework**: FastAPI with async/await support
- **Database**: PostgreSQL with SQLAlchemy ORM
- **Cache**: Redis for GitHub data and AI responses
- **AI Integration**: Google Gemini for recommendation generation
- **API**: RESTful API with automatic OpenAPI documentation
- **Authentication**: JWT-based authentication system
- **Validation**: Pydantic models for request/response validation

### Frontend (React)

- **Framework**: React 18 with TypeScript
- **Build Tool**: Vite for fast development and optimized production builds
- **Styling**: Tailwind CSS with custom design system
- **State Management**: React Query (TanStack Query) for server state
- **Routing**: React Router for client-side navigation
- **UI Components**: Custom components with Lucide icons
- **Forms**: React Hook Form with Zod validation

### Infrastructure

- **Containerization**: Docker with multi-stage builds for optimization
- **Reverse Proxy**: Nginx for production serving static files and API proxying
- **Development**: Hot reload for both frontend and backend
- **Production**: Optimized builds with health checks and monitoring
- **Caching Strategy**: Multi-layer caching (Redis + browser cache)
- **Security**: CORS, rate limiting, input validation, and secure headers

## 📚 API Documentation

The API is fully documented with OpenAPI/Swagger. Access the interactive documentation at:

- **Swagger UI**: <http://localhost:8000/docs>
- **ReDoc**: <http://localhost:8000/redoc>
- **OpenAPI Schema**: <http://localhost:8000/openapi.json>

### Core Endpoints

#### GitHub Analysis

| Method | Endpoint                            | Description                                         |
| ------ | ----------------------------------- | --------------------------------------------------- |
| `POST` | `/api/v1/github/analyze`            | Analyze GitHub profile and extract technical skills |
| `GET`  | `/api/v1/github/user/{username}`    | Get cached GitHub profile data                      |
| `GET`  | `/api/v1/github/stats/{username}`   | Get repository statistics and language breakdown    |
| `POST` | `/api/v1/github/refresh/{username}` | Force refresh cached GitHub data                    |

#### Recommendations

| Method   | Endpoint                              | Description                                |
| -------- | ------------------------------------- | ------------------------------------------ |
| `POST`   | `/api/v1/recommendations/generate`    | Generate new LinkedIn recommendation       |
| `GET`    | `/api/v1/recommendations/`            | List all generated recommendations         |
| `GET`    | `/api/v1/recommendations/{id}`        | Get specific recommendation by ID          |
| `PUT`    | `/api/v1/recommendations/{id}`        | Update recommendation content              |
| `DELETE` | `/api/v1/recommendations/{id}`        | Delete recommendation                      |
| `POST`   | `/api/v1/recommendations/{id}/export` | Export recommendation in different formats |

#### Analytics

| Method | Endpoint                            | Description                         |
| ------ | ----------------------------------- | ----------------------------------- |
| `GET`  | `/api/v1/analytics/overview`        | Get usage statistics and metrics    |
| `GET`  | `/api/v1/analytics/recommendations` | Get recommendation generation stats |
| `GET`  | `/api/v1/analytics/github`          | Get GitHub analysis statistics      |

#### System

| Method | Endpoint       | Description                     |
| ------ | -------------- | ------------------------------- |
| `GET`  | `/health`      | Application health check        |
| `GET`  | `/api/v1/info` | System information and version  |
| `GET`  | `/metrics`     | Prometheus metrics (if enabled) |

### Authentication

The API uses JWT (JSON Web Tokens) for authentication:

```bash
# Get authentication token
POST /api/v1/auth/login
{
  "username": "your_username",
  "password": "your_password"
}

# Use token in requests
Authorization: Bearer your_jwt_token_here
```

### Rate Limiting

- **Authenticated requests**: 1000 requests per hour
- **Unauthenticated requests**: 100 requests per hour
- **GitHub analysis**: 50 requests per hour per user

### Response Format

All API responses follow a consistent format:

```json
{
  "success": true,
  "data": { ... },
  "message": "Optional message",
  "timestamp": "2024-01-01T00:00:00Z"
}
```

### Error Handling

Standard HTTP status codes with detailed error messages:

```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid input parameters",
    "details": { ... }
  },
  "timestamp": "2024-01-01T00:00:00Z"
}
```

## 🔧 Development

### Getting Started

```bash
# Clone and setup
git clone <repository-url>
cd linkedin-recommendation-writer-app

# Quick development setup
make setup

# Or manual setup
cp env.template .env
# Edit .env with your API keys
make build
make up
```

### Backend Development

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install development dependencies
pip install -r requirements-dev.txt

# Run development server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Run with debugging
PYTHONPATH=. python -m debugpy --listen 0.0.0.0:5678 -m uvicorn app.main:app --reload
```

### Frontend Development

```bash
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview

# Run linting
npm run lint

# Fix linting issues
npm run lint:fix

# Run type checking
npm run type-check
```

### Database Management

```bash
# Initialize database (via container)
make shell-backend
# Then run: python -c "from app.core.database import init_database; import asyncio; asyncio.run(init_database())"

# Or connect directly to database
make db-connect

# Run migrations
make db-migrate

# Create new migration
make db-revision "Add new table"

# View database schema
make db-show

# Reset database (WARNING: Deletes all data)
make db-reset
```

### Development Commands

```bash
# View all logs
make logs

# View backend logs only
make logs-backend

# View frontend logs only
make logs-frontend

# Access backend container shell
make shell-backend

# Access frontend container shell
make shell-frontend

# Restart all services
make restart

# Stop all services
make down

# Clean up containers and volumes
make clean

# Clean up everything including images
make clean-all
```

### Code Quality

```bash
# Run all tests
make test

# Run backend tests only
make test-backend

# Run frontend tests only
make test-frontend

# Run with coverage
make test-coverage

# Run linting
make lint

# Format code
make format

# Run security checks
make security

# Run all quality checks
make quality
```

### Development Workflow

1. **Create Feature Branch**:

   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make Changes**:

   - Write code and tests
   - Follow conventional commits
   - Update documentation if needed

3. **Run Quality Checks**:

   ```bash
   make quality
   make test
   ```

4. **Commit Changes**:

   ```bash
   git add .
   git commit -m "feat: add new feature"
   ```

5. **Create Pull Request**:
   - Push branch to GitHub
   - Create PR with description
   - Request review

### Environment Setup

For team development, create a `.env.local` file:

```bash
# Development overrides
DEBUG=true
LOG_LEVEL=DEBUG
DATABASE_URL=postgresql://dev:dev@localhost:5432/dev_db
REDIS_URL=redis://localhost:6379/1

# Add your personal API keys
GITHUB_TOKEN=your_personal_token
GEMINI_API_KEY=your_personal_key
```

### IDE Setup

#### VS Code

Recommended extensions:

- Python
- Pylance
- Prettier
- ESLint
- Docker
- GitLens

#### PyCharm

- Configure Python interpreter
- Set up Django/FastAPI plugin
- Configure test runner
- Enable code coverage

### Troubleshooting Development

**Common Issues:**

1. **Port conflicts**:

   ```bash
   # Find what's using the port
   lsof -i :8000
   # Kill the process
   kill -9 <PID>
   ```

2. **Database connection issues**:

   ```bash
   # Reset database
   make db-reset
   # Check database status
   make db-connect
   ```

3. **Node modules issues**:

   ```bash
   # Clean and reinstall
   cd frontend
   rm -rf node_modules package-lock.json
   npm install
   ```

4. **Python environment issues**:
   ```bash
   # Recreate virtual environment
   rm -rf venv
   python -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

## 🧪 Testing

### Test Structure

```
├── backend/
│   ├── tests/
│   │   ├── unit/           # Unit tests
│   │   ├── integration/    # Integration tests
│   │   ├── e2e/           # End-to-end tests
│   │   └── fixtures/      # Test data
│   └── conftest.py        # Pytest configuration
├── frontend/
│   ├── src/
│   │   ├── __tests__/     # Unit tests
│   │   └── __mocks__/     # Mock data
│   └── e2e/              # E2E tests
└── docker-compose.test.yml  # Test environment
```

### Running Tests

```bash
# Run all tests
make test

# Run backend tests only
make test-backend

# Run frontend tests only
make test-frontend

# Run tests with coverage
make test-coverage

# Run specific test file
pytest backend/tests/test_github.py -v

# Run tests in watch mode
npm run test:watch  # Frontend
pytest-watch        # Backend
```

### Backend Testing

```bash
cd backend

# Run unit tests
pytest tests/unit/ -v

# Run integration tests
pytest tests/integration/ -v

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test class/method
pytest tests/test_recommendations.py::TestRecommendationService::test_generate -v
```

### Frontend Testing

```bash
cd frontend

# Run unit tests
npm test

# Run tests in watch mode
npm run test:watch

# Run tests with coverage
npm run test:coverage

# Run E2E tests
npm run test:e2e

# Update snapshots
npm run test:update-snapshots
```

### Writing Tests

#### Backend Test Example

```python
import pytest
from app.services.github import GitHubService

class TestGitHubService:
    @pytest.fixture
    def github_service(self):
        return GitHubService()

    def test_analyze_profile(self, github_service):
        # Arrange
        username = "testuser"

        # Act
        result = github_service.analyze_profile(username)

        # Assert
        assert result is not None
        assert "repositories" in result
        assert "languages" in result
```

#### Frontend Test Example

```typescript
import { render, screen } from '@testing-library/react';
import { RecommendationCard } from './RecommendationCard';

describe('RecommendationCard', () => {
  it('displays recommendation content', () => {
    const mockRecommendation = {
      id: '1',
      content: 'Great developer!',
      created_at: new Date().toISOString(),
    };

    render(<RecommendationCard recommendation={mockRecommendation} />);

    expect(screen.getByText('Great developer!')).toBeInTheDocument();
  });
});
```

### Test Coverage

We maintain high test coverage across the application:

- **Backend**: >85% coverage target
- **Frontend**: >80% coverage target
- **Integration Tests**: Critical user journeys

### Performance Testing

```bash
# Load testing with locust
locust -f tests/load_tests/locustfile.py

# API performance testing
artillery quick --count 100 --num 10 http://localhost:8000/health

# Frontend performance
lighthouse http://localhost:5173 --output=json
```

## 🔍 Troubleshooting

### Quick Diagnosis

```bash
# Check service health
curl http://localhost:8000/health

# View all service logs
make logs

# Check Docker containers
docker ps -a

# View resource usage
docker stats

# Check database connectivity
make db-connect
```

### Docker Issues

#### Build Issues

```bash
# Clear Docker cache and rebuild
make clean
make build

# Build with no cache
docker-compose build --no-cache

# Check Docker disk usage
docker system df

# Clean up unused resources
docker system prune -a --volumes
```

#### Container Issues

```bash
# View container logs
docker-compose logs backend
docker-compose logs frontend

# Access container shell
make shell-backend
make shell-frontend

# Restart specific service
docker-compose restart backend

# Rebuild and restart
docker-compose up --build backend
```

### Common Issues & Solutions

#### 1. GitHub API Rate Limits

**Symptoms:**

- `403 Forbidden` errors
- "API rate limit exceeded" messages

**Solutions:**

```bash
# Check current rate limit status
curl -H "Authorization: token YOUR_TOKEN" https://api.github.com/rate_limit

# Increase token permissions
# Go to GitHub Settings > Developer settings > Personal access tokens
# Ensure these scopes: repo, read:org, read:user, read:project

# Use authenticated requests (reduces limits but increases quota)
# The app automatically uses your token for requests
```

#### 2. Gemini API Errors

**Symptoms:**

- "Invalid API key" errors
- Quota exceeded messages
- Model not found errors

**Solutions:**

```bash
# Verify API key
curl "https://generativelanguage.googleapis.com/v1/models?key=YOUR_API_KEY"

# Check quota usage in Google AI Studio
# Visit: https://makersuite.google.com/app/apikey

# Update model name in .env
GEMINI_MODEL=gemini-1.5-flash  # or gemini-1.5-pro
```

#### 3. Database Connection Issues

**Symptoms:**

- "Connection refused" errors
- "FATAL: database does not exist"

**Solutions:**

```bash
# Check if database is running
docker-compose ps postgres

# Connect to database directly
make db-connect

# Reset database (WARNING: Deletes all data)
make db-reset

# Check database logs
docker-compose logs postgres

# Verify connection string in .env
cat .env | grep DATABASE_URL
```

#### 4. Port Conflicts

**Symptoms:**

- "Port already in use" errors
- Services fail to start

**Solutions:**

```bash
# Find what's using the ports
lsof -i :8000  # Backend
lsof -i :5173  # Frontend
lsof -i :5432  # PostgreSQL
lsof -i :6379  # Redis

# Kill conflicting processes
kill -9 <PID>

# Or change ports in docker-compose.yml
# Edit ports section for each service
```

#### 5. Memory Issues

**Symptoms:**

- Services crash unexpectedly
- "Out of memory" errors

**Solutions:**

```bash
# Check system resources
docker stats

# Increase Docker memory limit
# Docker Desktop > Settings > Resources > Memory

# Restart with more memory
docker-compose down
docker-compose up --scale backend=1 --scale frontend=1

# Monitor memory usage
docker-compose logs | grep -i memory
```

#### 6. Frontend Build Issues

**Symptoms:**

- White screen of death
- JavaScript errors in browser
- Build failures

**Solutions:**

```bash
# Clear frontend cache
cd frontend
rm -rf node_modules .next dist
npm install

# Check for TypeScript errors
npm run type-check

# Verify environment variables
cat .env | grep VITE_

# Check browser console for errors
# Open DevTools > Console
```

#### 7. CORS Issues

**Symptoms:**

- API requests blocked by CORS
- "Access-Control-Allow-Origin" errors

**Solutions:**

```bash
# Update ALLOWED_ORIGINS in .env
ALLOWED_ORIGINS=http://localhost:5173,http://localhost:3000,https://yourdomain.com

# Restart services
make restart

# Check CORS headers in API responses
curl -I -H "Origin: http://localhost:5173" http://localhost:8000/health
```

### Advanced Troubleshooting

#### Log Analysis

```bash
# Search for specific errors
make logs | grep -i error

# View logs with timestamps
make logs-backend | grep "2024-"

# Export logs for analysis
make logs > logs.txt

# Monitor logs in real-time
make logs -f
```

#### Performance Issues

```bash
# Profile backend performance
python -m cProfile -o profile.prof app/main.py

# Check Redis performance
redis-cli --latency

# Database query analysis
make db-connect
# Then: EXPLAIN ANALYZE SELECT * FROM recommendations;

# Frontend performance
# Open DevTools > Performance tab
# Run performance audit
```

#### Network Issues

```bash
# Test connectivity to external services
curl https://api.github.com/rate_limit
curl https://generativelanguage.googleapis.com/v1/models

# Check DNS resolution
nslookup api.github.com

# Test with different network
# Try connecting via different WiFi/mobile data
```

### Getting Help

If you can't resolve an issue:

1. **Check existing issues**: [GitHub Issues](https://github.com/your-repo/issues)
2. **Create a new issue** with:
   - Error messages and logs
   - Steps to reproduce
   - System information (`make info`)
   - Docker version (`docker --version`)
3. **Include diagnostic information**:
   ```bash
   make info > diagnostic.txt
   docker-compose config > compose-config.txt
   ```

## ❓ FAQ

### General Questions

**Q: Is my GitHub data secure?**

> A: Yes! We only access public GitHub data and never store or share your personal information. All API calls are made client-side when possible.

**Q: How many recommendations can I generate?**

> A: You're limited by your API quotas:
>
> - GitHub: 5,000 requests/hour with token
> - Gemini: Varies by your plan (free tier: 60 requests/minute)
> - App: 100 recommendations/hour per user

**Q: Can I use this commercially?**

> A: Yes, this project is MIT licensed. However, you'll need your own API keys and hosting.

**Q: What if I don't have a GitHub profile?**

> A: The app analyzes public GitHub data, so you'll need a GitHub account with some public repositories.

### Technical Questions

**Q: Why is the analysis taking so long?**

> A: Analysis time depends on repository count and complexity. Large profiles (>50 repos) may take 30-60 seconds.

**Q: Can I customize the recommendation style?**

> A: Yes! The app supports multiple tones (professional, casual, enthusiastic) and lengths (short, medium, detailed).

**Q: Does it work with private repositories?**

> A: No, we only analyze public repositories for privacy reasons. Private repos require additional GitHub permissions.

**Q: Can I export recommendations?**

> A: Yes! Recommendations can be exported as PDF, Word documents, or plain text for LinkedIn.

**Q: Is there a mobile app?**

> A: Currently web-only, but the responsive design works great on mobile devices.

### API Questions

**Q: Can I integrate this into my own application?**

> A: Yes! The API is fully documented with OpenAPI/Swagger. Contact us for integration support.

**Q: Are there SDKs available?**

> A: Currently we provide REST API. Python and JavaScript SDKs are planned for future releases.

**Q: What's the API rate limiting?**

> A: See the [API Documentation](#-api-documentation) section for detailed rate limits.

### Deployment Questions

**Q: Which deployment option should I choose?**

> A: See our [deployment comparison table](#-deployment) for guidance based on your needs.

**Q: Can I deploy to my own server?**

> A: Yes! Docker makes it easy to deploy anywhere that supports containers.

**Q: Do you offer hosted versions?**

> A: Currently self-hosted only. Cloud hosting options are available through the deployment guides.

### Troubleshooting Questions

**Q: Why am I getting "Invalid API key" errors?**

> A: Check that your API keys are correctly set in the `.env` file and have the required permissions.

**Q: The frontend shows a blank page. What should I do?**

> A: Check browser console for errors, clear browser cache, and ensure the backend is running.

**Q: Database connection fails. How to fix?**

> A: Ensure PostgreSQL container is running, check credentials in `.env`, and try resetting the database.

## 🤝 Contributing

We welcome contributions! Here's how you can help:

### Ways to Contribute

- 🐛 **Bug Reports**: Found a bug? [Open an issue](https://github.com/your-repo/issues)
- ✨ **Feature Requests**: Have an idea? [Start a discussion](https://github.com/your-repo/discussions)
- 💻 **Code Contributions**: Ready to code? See our development guide
- 📖 **Documentation**: Help improve docs and tutorials
- 🧪 **Testing**: Write tests or report test failures

### Development Workflow

1. **Fork the repository**
2. **Create a feature branch**: `git checkout -b feature/your-feature-name`
3. **Make your changes** following our [coding standards](#-code-quality)
4. **Write tests** for new functionality
5. **Run quality checks**: `make quality`
6. **Update documentation** if needed
7. **Submit a pull request** with a clear description

### Code Standards

We follow these guidelines:

- **Python**: PEP 8 with Black formatting
- **TypeScript**: ESLint + Prettier configuration
- **Commits**: Conventional commits format
- **Tests**: Minimum 80% coverage required
- **Documentation**: Clear, concise comments and docstrings

### Pull Request Process

1. **Title**: Use conventional commit format (`feat:`, `fix:`, `docs:`, etc.)
2. **Description**: Explain what and why, not just how
3. **Tests**: Include tests for new features
4. **Documentation**: Update README/docs if needed
5. **Labels**: Add appropriate labels (enhancement, bug, documentation)

### Recognition

Contributors are recognized in:

- Repository contributors list
- Changelog for significant contributions
- Special mention in release notes

### Getting Started for Contributors

```bash
# Fork and clone
git clone https://github.com/your-username/linkedin-recommendation-writer-app.git
cd linkedin-recommendation-writer-app

# Set up development environment
make setup

# Create feature branch
git checkout -b feature/amazing-new-feature

# Make changes and test
make test
make quality

# Submit pull request
```

## 📄 License

This project is licensed under the **MIT License** - see the [LICENSE](LICENSE) file for details.

### Permissions

- ✅ Commercial use
- ✅ Modification
- ✅ Distribution
- ✅ Private use

### Limitations

- ❌ No liability
- ❌ No warranty

### Conditions

- ℹ️ License and copyright notice must be included

## 📞 Support

### Getting Help

- 📖 **Documentation**: Check this README and API docs first
- 🐛 **Bug Reports**: [Create GitHub issues](https://github.com/your-repo/issues)
- 💡 **Feature Requests**: [Start GitHub discussions](https://github.com/your-repo/discussions)
- 💬 **Community**: Join our [Discord server](https://discord.gg/your-server) (coming soon)

### Contact Information

- **Email**: support@yourproject.com
- **Twitter**: [@yourproject](https://twitter.com/yourproject)
- **LinkedIn**: [Your Company](https://linkedin.com/company/yourcompany)

### Response Times

- **Bug fixes**: Within 24-48 hours
- **Feature requests**: Within 1 week
- **General questions**: Within 24 hours

### Professional Support

For enterprise support, custom integrations, or priority assistance:

- **Premium Support**: priority@yourproject.com
- **Custom Development**: dev@yourproject.com
- **Training**: training@yourproject.com

---

<div align="center">

**Made with ❤️ for the developer community**

⭐ **Star this repo** if you found it helpful!

[🌟 GitHub](https://github.com/your-repo) • [📧 Contact](mailto:support@yourproject.com) • [📖 Documentation](http://localhost:8000/docs)

</div>
