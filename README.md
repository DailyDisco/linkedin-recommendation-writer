# LinkedIn Recommendation Writer

[![Live Demo](https://img.shields.io/badge/Live_Demo-View_App-brightgreen?style=flat&logo=vercel)](https://linkedin-recommendation-writer-production.up.railway.app/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Docker](https://img.shields.io/badge/docker-%230db7ed.svg?style=flat&logo=docker&logoColor=white)](https://docker.com)

Generate professional LinkedIn recommendations using GitHub data and AI.

## Table of Contents

- [🌐 Live Demo](#-live-demo)
- [✨ Features](#-features)
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
- **Railway**: Recommended platform for full-stack deployment.
- **Vercel**: Optional platform for frontend deployment.

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
cp env.example .env
# Edit .env with your GITHUB_TOKEN and GEMINI_API_KEY
make setup
```

Access your local app:

- **Frontend**: [http://localhost:5173](http://localhost:5173)
- **Backend**: [http://localhost:8000](http://localhost:8000)

## ⚙️ Configuration & API Keys

### Environment Variables

Create a `.env` file from `env.example` for local development. For production, configure environment variables directly in your deployment platform (Railway, Vercel, or Docker).

**Required:**

```bash
GITHUB_TOKEN=your_github_personal_access_token
GEMINI_API_KEY=your_google_gemini_api_key
POSTGRES_PASSWORD=your_secure_database_password # Only for Railway full-stack or Docker
```

**Railway Auto-configured (for Railway deployments):**

`DATABASE_URL`, `REDIS_URL`

**Vercel Frontend (for Vercel deployments):**

`VITE_API_URL`, `VITE_APP_ENV`

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

- 📖 **API Docs**: `/docs` (when running locally or deployed)
- 🐛 **Bug Reports**: [Create GitHub issues](https://github.com/day0009/linkedin-recommendation-writer-app/issues)
- 💬 **Discussions**: [Start GitHub discussions](https://github.com/day0009/linkedin-recommendation-writer-app/discussions)

---

<div align="center">
Made with ❤️ for the developer community
</div>
