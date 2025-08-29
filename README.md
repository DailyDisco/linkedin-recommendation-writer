# LinkedIn Recommendation Writer

[![Live Demo](https://img.shields.io/badge/Live_Demo-View_App-brightgreen?style=flat&logo=vercel)](https://linkedin-recommendation-writer-production.up.railway.app/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Docker](https://img.shields.io/badge/docker-%230db7ed.svg?style=flat&logo=docker&logoColor=white)](https://docker.com)

Generate professional LinkedIn recommendations using GitHub data and AI.

## Table of Contents

- [🌐 Live Demo](#-live-demo)
- [✨ Features](#-features)
- [💻 Technology Stack](#-technology-stack)
- [🚀 Railway Deployment (Recommended)](#-railway-deployment-recommended)
  - [Option 1: Full-Stack Deployment (Easiest)](#option-1-full-stack-deployment-easiest)
  - [Option 2: Separate Frontend/Backend (Advanced)](#option-2-separate-frontendbackend-advanced)
  - [Railway Environment Setup](#railway-environment-setup)
  - [Local Development](#local-development)
- [📋 Prerequisites](#-prerequisites)
  - [Accounts & API Keys](#accounts--api-keys)
  - [API Keys Setup](#api-keys-setup)
  - [Development Tools](#development-tools)
  - [Deployment Platforms](#deployment-platforms)
  - [Quick Start Checklist](#quick-start-checklist)
- [🛠️ Installation](#️-installation)
- [⚙️ Configuration](#️-configuration)
  - [Environment Variables](#environment-variables)
  - [Getting API Keys](#getting-api-keys)
  - [Security Notes](#security-notes)
- [🚀 Deployment Options](#-deployment-options)
  - [Option A: Railway Full-Stack (Recommended)](#option-a-railway-full-stack-recommended)
  - [Option B: Vercel + Railway (Scalable)](#option-b-vercel--railway-scalable)
  - [Option C: Docker Production](#option-c-docker-production)
  - [Deployment Comparison](#deployment-comparison)
  - [Troubleshooting Deployment](#troubleshooting-deployment)
- [🔧 Development](#-development)
- [📚 API Documentation](#-api-documentation)
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

## 💻 Technology Stack

This project leverages a modern full-stack architecture with the following key technologies:

**Frontend:**

- **React**: A JavaScript library for building user interfaces.
- **Vite**: A fast frontend build tool.
- **Tailwind CSS**: A utility-first CSS framework for styling.
- **ShadCN UI**: A collection of reusable components built with Radix UI and Tailwind CSS.

**Backend:**

- **FastAPI**: A modern, fast (high-performance) web framework for building APIs with Python.
- **Pydantic**: Data validation and settings management using Python type hints.
- **SQLAlchemy**: An SQL toolkit and Object-Relational Mapper (ORM) for Python.
- **PostgreSQL**: A powerful, open-source object-relational database system.
- **Redis**: An open-source, in-memory data store, used as a cache and message broker.

**AI/Machine Learning:**

- **Google Gemini API**: For natural language processing and recommendation generation.

**Deployment & Containerization:**

- **Docker**: For containerizing the application and its services.
- **Docker Compose**: For defining and running multi-container Docker applications.
- **Railway**: Recommended platform for full-stack deployment.
- **Vercel**: Optional platform for frontend deployment.

## 🚀 Railway Deployment (Recommended)

### Option 1: Full-Stack Deployment (Easiest)

**Deploy everything to Railway in 5 minutes:**

1. **Go to Railway Dashboard**: [https://railway.app/dashboard](https://railway.app/dashboard)
2. **Click "New Project"**
3. **Choose "Deploy from GitHub repo"**
4. **Select your repository**
5. **Railway auto-detects Dockerfile and deploys**

**That's it!** Your app will be live with:

- ✅ **Frontend served automatically**
- ✅ **Backend API running**
- ✅ **PostgreSQL database**
- ✅ **Redis cache**

### Option 2: Separate Frontend/Backend (Advanced)

For better performance and scalability, deploy frontend and backend separately.

#### Deploy Backend to Railway

1. **Create Railway Project**:

   - Go to [https://railway.app/dashboard](https://railway.app/dashboard)
   - Click "New Project" → "Deploy from GitHub repo"
   - Select your repository

2. **Configure Environment Variables**:

   - In Railway dashboard, go to your project → Variables
   - Add these variables:

     ```bash
     GITHUB_TOKEN=your_github_token_here
     GEMINI_API_KEY=your_gemini_api_key_here
     POSTGRES_PASSWORD=your_secure_password_here
     ```

3. **Add Database Services**:

   - In your Railway project, click "Add Plugin"
   - Add PostgreSQL and Redis plugins
   - Railway will automatically set `DATABASE_URL` and `REDIS_URL`

4. **Get Backend URL**:
   - After deployment, copy your Railway app URL (e.g., `https://your-app.up.railway.app`)
   - This will be your API base URL

#### Deploy Frontend to Vercel

1. **Connect Repository**:

   - Go to [https://vercel.com/dashboard](https://vercel.com/dashboard)
   - Click "New Project"
   - Import your GitHub repository

2. **Configure Build Settings**:

   - **Framework Preset**: Vite
   - **Root Directory**: Leave empty (root)
   - **Build Command**: `npm run build`
   - **Output Directory**: `dist`

3. **Set Environment Variables**:

   - Add these environment variables in Vercel:

     ```bash
     VITE_API_URL=https://your-railway-backend.up.railway.app
     VITE_APP_ENV=production
     ```

4. **Deploy**:
   - Vercel will automatically build and deploy
   - Get your frontend URL (e.g., `https://your-app.vercel.app`)

### Railway Environment Setup

After deployment, configure these environment variables in Railway:

| Variable            | Description                           | Required |
| ------------------- | ------------------------------------- | -------- |
| `GITHUB_TOKEN`      | GitHub Personal Access Token          | ✅       |
| `GEMINI_API_KEY`    | Google Gemini API Key                 | ✅       |
| `POSTGRES_PASSWORD` | Database password                     | ✅       |
| `DATABASE_URL`      | Auto-set by Railway PostgreSQL plugin | 🔄       |
| `REDIS_URL`         | Auto-set by Railway Redis plugin      | 🔄       |

**Note**: `DATABASE_URL` and `REDIS_URL` are automatically configured when you add the PostgreSQL and Redis plugins to your Railway project.

### Local Development

**Get everything running locally:**

```bash
git clone https://github.com/day0009/linkedin-recommendation-writer-app
cd linkedin-recommendation-writer-app
cp env.example .env
# Edit .env with your API keys
make setup
```

Access your local app at:

- **Frontend**: [http://localhost:5173](http://localhost:5173)
- **Backend**: [http://localhost:8000](http://localhost:8000)
- **API Docs**: [http://localhost:8000/docs](http://localhost:8000/docs)

## 📋 Prerequisites

### Accounts & API Keys

- **GitHub Account** - For repository access and API token
- **Google AI Account** - For Gemini API access
- **Railway Account** (Recommended) - For backend deployment
- **Vercel Account** (Optional) - For frontend deployment

### API Keys Setup

- **GitHub Personal Access Token**:
  - Go to [GitHub Settings > Developer settings > Personal access tokens](https://github.com/settings/tokens)
  - Generate token with `repo`, `read:user`, `read:org` scopes
- **Google Gemini API Key**:
  - Visit [Google AI Studio](https://makersuite.google.com/app/apikey)
  - Create and copy your API key

### Development Tools

- **Docker & Docker Compose** (v20.10+) - For containerized development
- **Git** (v2.30+) - For version control
- **Node.js** (v18+) - For frontend development
- **Python** (v3.9+) - For backend development (optional)

### Deployment Platforms

- **Railway** - Backend, database, and full-stack deployment
- **Vercel** - Frontend deployment (optional)
- **GitHub** - Repository hosting

### Quick Start Checklist

- ✅ Create GitHub Personal Access Token
- ✅ Get Google Gemini API Key
- ✅ Set up Railway account
- ✅ Fork/clone this repository
- ✅ Choose your deployment method (Railway recommended)

## 🛠️ Installation

```bash
# Clone repository
git clone https://github.com/day0009/linkedin-recommendation-writer-app
cd linkedin-recommendation-writer-app

# Configure environment
cp env.example .env
# Edit .env with your API keys (GITHUB_TOKEN, GEMINI_API_KEY)

# Quick setup (builds and starts everything)
make setup
```

## ⚙️ Configuration

### Environment Variables

Configure these environment variables based on your deployment method:

#### Required Variables (All Deployments)

```bash
# GitHub API Access
GITHUB_TOKEN=your_github_personal_access_token

# AI Service
GEMINI_API_KEY=your_google_gemini_api_key
```

#### Railway Deployment (Auto-configured)

```bash
# These are automatically set by Railway plugins:
DATABASE_URL=postgresql://user:pass@containers-us-west-xxx.railway.app:xxxx/railway
REDIS_URL=redis://default:pass@containers-us-west-xxx.railway.app:xxxx

# Set this manually in Railway dashboard:
POSTGRES_PASSWORD=your_secure_database_password
```

#### Vercel Frontend Deployment

```bash
# Frontend environment variables
VITE_API_URL=https://your-railway-backend.up.railway.app
VITE_APP_ENV=production
```

#### Local Development (.env file)

```bash
# Create .env file in project root
GITHUB_TOKEN=your_github_token
GEMINI_API_KEY=your_gemini_key

# Database (optional - will use defaults if not set)
POSTGRES_PASSWORD=your_secure_password
DATABASE_URL=postgresql://postgres:your_password@localhost:5432/linkedin_recommendations

# Redis (optional - will use defaults if not set)
REDIS_URL=redis://localhost:6379/0
```

#### Docker Production

```bash
# Docker environment variables
GITHUB_TOKEN=your_github_token
GEMINI_API_KEY=your_gemini_key
DATABASE_URL=postgresql://postgres:your_password@db:5432/linkedin_recommendations
REDIS_URL=redis://redis:6379/0
```

### Getting API Keys

#### GitHub Personal Access Token

1. Go to [GitHub Settings > Developer settings > Personal access tokens](https://github.com/settings/tokens)
2. Click "Generate new token (classic)"
3. Select scopes: `repo`, `read:user`, `read:org`
4. Copy the token (keep it secure!)

#### Google Gemini API Key

1. Go to [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Click "Create API Key"
3. Copy the API key
4. Enable billing if needed for production use

### Security Notes

- 🔐 **Never commit API keys** to version control
- 🔐 **Use Railway/Vercel environment variables** for production
- 🔐 **Rotate keys regularly** and update deployments
- 🔐 **Monitor API usage** to avoid unexpected charges

## 🚀 Deployment Options

### Option A: Railway Full-Stack (Recommended)

**Best for simplicity and performance:**

1. **Push code to GitHub**
2. **Railway Dashboard** → New Project → Deploy from GitHub → Select repo
3. **Railway auto-detects** Dockerfile and deploys automatically
4. **Add plugins**: PostgreSQL and Redis (one-click in Railway)
5. **Set environment variables** in Railway dashboard

**Result:** Single URL with everything deployed together!

**Pros:** ✅ Simple, ✅ Fast setup, ✅ Everything managed together
**Cons:** ⚠️ Less flexible for scaling individual components

### Option B: Vercel + Railway (Scalable)

**Best for performance and custom domains:**

#### Backend (Railway)

```bash
# Deploy to Railway with database plugins
# URL: https://your-backend.up.railway.app
```

#### Frontend (Vercel)

```bash
# Deploy to Vercel with VITE_API_URL pointing to Railway
# URL: https://your-frontend.vercel.app
```

**Pros:** ✅ Better performance, ✅ Custom domains, ✅ Independent scaling
**Cons:** ⚠️ More complex setup, ⚠️ Multiple services to manage

### Option C: Docker Production

**For self-hosted deployments:**

```bash
# Build and run production containers
make setup-prod

# Or manually:
docker-compose -f docker-compose.prod.yml up -d
```

**Environment variables needed:**

```bash
GITHUB_TOKEN=your_token
GEMINI_API_KEY=your_key
DATABASE_URL=postgresql://...
REDIS_URL=redis://...
```

### Deployment Comparison

| Feature       | Railway Full-Stack | Vercel + Railway | Docker      |
| ------------- | ------------------ | ---------------- | ----------- |
| Setup Time    | 5 minutes          | 15 minutes       | 30+ minutes |
| Cost          | Low                | Medium           | Variable    |
| Scalability   | Good               | Excellent        | Excellent   |
| Custom Domain | ✅                 | ✅               | ✅          |
| Database      | ✅                 | ✅               | Manual      |
| Cache         | ✅                 | ✅               | Manual      |

### Troubleshooting Deployment

**Railway Issues:**

- Check Railway logs in dashboard
- Verify environment variables are set
- Ensure Dockerfile is in root directory

**Vercel Issues:**

- Check build logs in Vercel dashboard
- Verify `VITE_API_URL` is set correctly
- Ensure build commands match your setup

**CORS Issues:**

- Add your frontend URL to backend CORS settings
- Check that `VITE_API_URL` matches your backend URL exactly

**Database Connection:**

- Verify PostgreSQL plugin is added to Railway project
- Check `DATABASE_URL` is accessible
- Run database migrations if needed

## 🔧 Development

```bash
# Start development environment
make setup

# Run tests
make test

# View logs
make logs

# Access containers
make shell-backend  # Backend container
make shell-frontend # Frontend container
```

## 📚 API Documentation

Once running, visit:

- **API Docs**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **Frontend**: [http://localhost:5173](http://localhost:5173)

## 🤝 Contributing

We welcome contributions to the LinkedIn Recommendation Writer! To ensure a smooth collaboration process, please follow these guidelines:

### Getting Started

1.  **Fork the repository** on GitHub.
2.  **Clone your forked repository** to your local machine:
    ```bash
    git clone https://github.com/day0009/linkedin-recommendation-writer-app
    cd linkedin-recommendation-writer-app
    ```
3.  **Set up your development environment** by following the [Local Development](#local-development) instructions.
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

- 📖 **Documentation**: Check the API docs at `/docs`
- 🐛 **Bug Reports**: [Create GitHub issues](https://github.com/day0009/linkedin-recommendation-writer-app/issues)
- 💬 **Discussions**: [Start GitHub discussions](https://github.com/day0009/linkedin-recommendation-writer-app/discussions)

---

<div align="center">
Made with ❤️ for the developer community
</div>
