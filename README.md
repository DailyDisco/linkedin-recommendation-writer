<div align="center">

# LinkedIn Recommendation Writer

_(Your Logo Here)_

</div>

[![Live Demo](https://img.shields.io/badge/Live_Demo-View_App-brightgreen?style=flat&logo=vercel)](https://linkedin-recommendation-writer-production.up.railway.app/)
[![CI/CD Pipeline](https://github.com/day0009/linkedin-recommendation-writer-app/actions/workflows/ci.yml/badge.svg)](https://github.com/day0009/linkedin-recommendation-writer-app/actions/workflows/ci.yml)
[![Python CI](https://github.com/day0009/linkedin-recommendation-writer-app/actions/workflows/python-ci.yml/badge.svg)](https://github.com/day0009/linkedin-recommendation-writer-app/actions/workflows/python-ci.yml)
[![React CI](https://github.com/day0009/linkedin-recommendation-writer-app/actions/workflows/react-ci.yml/badge.svg)](https://github.com/day0009/linkedin-recommendation-writer-app/actions/workflows/react-ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Docker](https://img.shields.io/badge/docker-%230db7ed.svg?style=flat&logo=docker&logoColor=white)](https://docker.com)

Generate professional LinkedIn recommendations using GitHub data and AI.

## Table of Contents

- [🌐 Live Demo](#-live-demo)
- [✨ Features](#-features)
- [🏗️ Project Architecture](#️-project-architecture)
- [💻 Technology Stack](#-technology-stack)
- [🚀 Deployment](#-deployment)
- [🛠️ Installation & Local Development](#️-installation--local-development)
- [⚙️ Configuration & API Keys](#️-configuration--api-keys)
- [🤝 Contributing](#-contributing)
- [📄 License](#-license)
- [📞 Support](#-support)

## 🌐 Live Demo

Try the live application: **[linkedin-recommendation-writer-production.up.railway.app](https://linkedin-recommendation-writer-production.up.railway.app/)**

## 🖼️ Screenshots / Demos

_(Add your application screenshots or GIFs here to showcase key features.)_

## ✨ Features

- 🔍 **GitHub Analysis**: Analyzes repositories, languages, and contribution patterns
- 🤖 **AI-Powered**: Uses Google Gemini AI for natural recommendation generation
- ⚙️ **Customizable**: Multiple types, tones, and lengths available
- 💾 **History Tracking**: Save and manage all generated recommendations
- 🚀 **Fast Results**: Intelligent caching for quick responses

## 🏗️ Project Architecture

The project is organized into a monorepo structure with distinct frontend and backend directories, promoting a clean separation of concerns.

```
linkedin-recommendation-writer-app/
├── .github/          # GitHub Actions workflows for CI/CD
├── backend/          # FastAPI application
│   ├── app/          # Core application code
│   │   ├── api/      # API endpoints (routers)
│   │   ├── core/     # Configuration and core settings
│   │   ├── models/   # SQLAlchemy database models
│   │   └── services/ # Business logic and services
│   ├── alembic/      # Database migrations
│   └── tests/        # Backend tests
├── frontend/         # React (Vite) application
│   ├── app/          # Source code for the frontend
│   │   ├── components/ # Reusable UI components
│   │   ├── routes/     # Page components and layouts
│   │   ├── services/   # API communication layer
│   │   └── hooks/      # Custom React hooks
│   └── tests/        # Frontend tests
├── deployment/       # Deployment scripts and guides
├── docker/           # Docker configurations
└── scripts/          # Helper scripts for development
```

## 💻 Technology Stack

This project leverages a modern full-stack architecture with the following key technologies:

**Frontend:**

- **React 19.1.1**: A JavaScript library for building user interfaces.
- **React Router 7.7.1**: Full-stack web framework with file-based routing.
- **Tailwind CSS 4.1.12**: A utility-first CSS framework for styling.
- **ShadCN UI**: A collection of reusable components built with Radix UI and Tailwind CSS.
- **Vite 7.1.3**: Fast build tool and development server.
- **TypeScript 5.9.2**: Type-safe JavaScript development.
- **Vitest 3.2.4**: Modern testing framework for unit and integration tests.

**Backend:**

- **FastAPI 0.116.1**: A modern, fast web framework for building APIs with Python.
- **Python 3.11+**: Modern Python with type hints and async support.
- **Pydantic 2.11.7**: Data validation and settings management using Python type hints.
- **SQLAlchemy 2.0.43**: Async-capable SQL toolkit and Object-Relational Mapper (ORM).
- **PostgreSQL**: A powerful, open-source object-relational database system.
- **Redis 6.4.0**: In-memory data store for caching and session management.
- **Alembic 1.16.5**: Database migration tool for SQLAlchemy.

**AI/Machine Learning:**

- **Google Gemini 1.32.0**: Advanced AI model for natural language processing and recommendation generation.
- **PyGithub 2.7.0**: Python library for GitHub API integration and repository analysis.
- **Structured Analysis**: Advanced GitHub profile and repository analysis with skill extraction.

**Deployment & Containerization:**

- **Docker & Docker Compose**: Multi-service containerization with development and production configurations.
- **Railway**: Recommended platform for full-stack deployment with auto-scaling.
- **Vercel**: Optional platform for frontend deployment.
- **Nginx**: Production-ready reverse proxy and static file serving.

## 🚀 Deployment

The application can be deployed using a full-stack approach on Railway or with separate frontend/backend deployments using Vercel and Railway, respectively. Docker Compose is also available for self-hosted production environments.

### Railway Full-Stack (Recommended)

Deploy the entire application to Railway directly from your GitHub repository. Railway automatically detects the Dockerfile, sets up PostgreSQL and Redis plugins, and handles environment variables.

1.  **Go to Railway Dashboard**: [https://railway.app/dashboard](https://railway.app/dashboard)
2.  **Click "New Project"** and choose "Deploy from GitHub repo".
3.  **Select your repository** and Railway will auto-deploy.
4.  **Add PostgreSQL and Redis plugins** in your Railway project to auto-configure `DATABASE_URL` and `REDIS_URL`.
5.  **Set environment variables** in the Railway dashboard, including `GITHUB_TOKEN`, `GEMINI_API_KEY`, and `POSTGRES_PASSWORD`.

### Vercel + Railway (Scalable)

For independent scaling, deploy the backend to Railway and the frontend to Vercel.

**Backend (Railway):**
Follow steps 1-5 from "Railway Full-Stack" for your backend service. Copy the Railway app URL (e.g., `https://your-backend.up.railway.app`) as your API base URL.

**Frontend (Vercel):**

1.  **Go to Vercel Dashboard**: [https://vercel.com/dashboard](https://vercel.com/dashboard)
2.  **Click "New Project"** and import your GitHub repository.
3.  **Configure Build Settings**: Framework Preset: `Vite`, Build Command: `npm run build`, Output Directory: `dist`.
4.  **Set Environment Variables**: `VITE_API_URL` (your Railway backend URL) and `VITE_APP_ENV=production`.

### Docker Production

For self-hosted deployments, use `docker-compose -f docker-compose.prod.yml up -d`. Ensure you set `GITHUB_TOKEN`, `GEMINI_API_KEY`, `DATABASE_URL`, and `REDIS_URL` environment variables.

### Troubleshooting

- **Check Logs**: Review logs on Railway/Vercel dashboards for deployment issues.
- **Environment Variables**: Verify all required environment variables (`GITHUB_TOKEN`, `GEMINI_API_KEY`, `POSTGRES_PASSWORD`, `VITE_API_URL`) are correctly set for your chosen deployment method.
- **CORS Issues**: Ensure your frontend URL is added to backend CORS settings.
- **Database**: Confirm PostgreSQL and Redis plugins are active on Railway, or that `DATABASE_URL` and `REDIS_URL` are correctly configured for Docker deployments.

## 🛠️ Installation & Local Development

Clone the repository and set up your local environment:

```bash
git clone https://github.com/day0009/linkedin-recommendation-writer-app
cd linkedin-recommendation-writer-app
cp .env.example .env
# Edit .env with your GITHUB_TOKEN and GEMINI_API_KEY
make build
make up
```

Access your local app:

- **Frontend**: [http://localhost:5173](http://localhost:5173)
- **Backend API**: [http://localhost:8000](http://localhost:8000)
- **API Documentation**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **PostgreSQL**: localhost:5432
- **Redis**: localhost:6379

### Development Workflow

The project includes a comprehensive Makefile for managing development tasks:

**Container Management:**

```bash
make build          # Build all services for development
make build-no-cache # Build without cache
make up             # Start all services in detached mode
make up-logs        # Start services and show logs
make down           # Stop all services and remove volumes
make restart        # Restart all services
make logs           # Show application logs
make shell          # Open shell in app container
```

**Testing & Code Quality:**

```bash
make test-frontend    # Run frontend tests
make test-backend     # Run backend tests
make lint-frontend    # Run frontend linting
make lint-backend     # Run backend linting
make format-frontend  # Format frontend code
make format-backend   # Format backend code
```

**Production Commands:**

```bash
make prod-build  # Build for production
make prod-up     # Start production services
make prod-down   # Stop production services
make prod-logs   # Show production logs
```

**Utility Commands:**

```bash
make clean       # Remove all containers, volumes, and images
make db-connect  # Connect to development database
make help        # Show all available commands
```

## ⚙️ Configuration & API Keys

### Environment Variables

Create a `.env` file from `env.example` for local development. For production, configure environment variables directly in your deployment platform (Railway, Vercel, or Docker).

**Required:**

```bash
# External API Keys
GITHUB_TOKEN=your_github_personal_access_token
GEMINI_API_KEY=your_google_gemini_api_key

# Database Configuration
POSTGRES_PASSWORD=your_secure_database_password
DATABASE_URL=postgresql+asyncpg://postgres:password@postgres:5432/github_recommender

# Redis Configuration
REDIS_URL=redis://redis:6379/0

# Security
SECRET_KEY=your_super_secure_unique_key_here_at_least_32_characters_long
```

**Development Environment:**

```bash
# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
API_DEBUG=true
ENVIRONMENT=development

# Frontend Configuration
VITE_API_BASE_URL=http://backend:8000
NODE_ENV=development
```

**Production Environment:**

```bash
# Railway Auto-configured
DATABASE_URL=<auto-configured>
REDIS_URL=<auto-configured>

# Vercel Frontend
VITE_API_URL=<your-railway-backend-url>
VITE_APP_ENV=production
```

### Getting API Keys

1.  **GitHub Personal Access Token**: Go to [GitHub Settings > Developer settings > Personal access tokens](https://github.com/settings/tokens), generate a new token with `repo`, `read:user`, `read:org` scopes.
2.  **Google Gemini API Key**: Visit [Google AI Studio](https://makersuite.google.com/app/apikey) and create an API key.

**Security Notes**: Never commit API keys to version control. Use environment variables for production and rotate keys regularly.

## 🤝 Contributing

We welcome contributions to the LinkedIn Recommendation Writer! To ensure a smooth collaboration process, please follow these guidelines:

### Getting Started

1.  **Fork the repository** on GitHub.
2.  **Clone your forked repository** to your local machine:
    ```bash
    git clone https://github.com/day0009/linkedin-recommendation-writer-app
    cd linkedin-recommendation-writer-app
    ```
3.  **Set up your development environment** by following the [Installation & Local Development](#️-installation--local-development) instructions.
4.  **Create a new feature branch** for your changes:
    ```bash
    git checkout -b feature/your-feature-name
    ```
    (Use `fix/bug-description` for bug fixes, `chore/task-description` for maintenance, etc.)

### Coding Standards

- **Follow existing code style**: We use `black` for Python and `ESLint` with `Prettier` for JavaScript/TypeScript.
- **Type Hinting**: Ensure all Python functions and complex variables use type hints.
- **Docstrings**: Add clear and concise docstrings to all public functions and classes.
- **Comments**: Use comments sparingly for explaining _why_ something is done, not _what_ it does (which should be clear from the code).

### Testing

- **Write tests**: All new features and bug fixes should be accompanied by appropriate unit and integration tests.
- **Run tests**: Before submitting a pull request, ensure all tests pass:
  ```bash
  make test
  ```
- **Test coverage**: Aim for high test coverage, focusing on critical paths and edge cases.

### Pull Request Guidelines

1.  **Keep it focused**: Each pull request should address a single feature or bug fix.
2.  **Descriptive title**: Use a clear and concise title that summarizes your changes (e.g., `feat: Add dark mode toggle`).
3.  **Detailed description**: Provide a detailed description of your changes, including:
    - The problem it solves.
    - How you solved it.
    - Any relevant design decisions or trade-offs.
    - Instructions for testing (if applicable).
4.  **Link to issues**: If your pull request addresses an open issue, link to it in the description (e.g., `Closes #123`).
5.  **Review**: Your pull request will be reviewed by a maintainer. Please be responsive to feedback.
6.  **Merge**: Once approved, your changes will be merged into the `main` branch.

Thank you for contributing to the LinkedIn Recommendation Writer!

## 📄 License

MIT License - see [LICENSE](LICENSE) file for details.

## 📞 Support

- 📖 **API Docs**: `/docs` (when running locally or deployed)
- 🐛 **Bug Reports**: [Create GitHub issues](https://github.com/day0009/linkedin-recommendation-writer-app/issues)
- 💬 **Discussions**: [Start GitHub discussions](https://github.com/day0009/linkedin-recommendation-writer-app/discussions)

---

<div align="center">
Made with ❤️ for the developer community
</div>
