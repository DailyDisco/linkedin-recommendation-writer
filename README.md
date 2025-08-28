# LinkedIn Recommendation Writer

[![Live Demo](https://img.shields.io/badge/Live_Demo-View_App-brightgreen?style=flat&logo=vercel)](https://linkedin-recommendation-writer-production.up.railway.app/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Docker](https://img.shields.io/badge/docker-%230db7ed.svg?style=flat&logo=docker&logoColor=white)](https://docker.com)

Generate professional LinkedIn recommendations using GitHub data and AI.

## 🌐 Live Demo

Try the live application: **[linkedin-recommendation-writer-production.up.railway.app](https://linkedin-recommendation-writer-production.up.railway.app/)**

## ✨ Features

- 🔍 **GitHub Analysis**: Analyzes repositories, languages, and contribution patterns
- 🤖 **AI-Powered**: Uses Google Gemini AI for natural recommendation generation
- ⚙️ **Customizable**: Multiple types, tones, and lengths available
- 💾 **History Tracking**: Save and manage all generated recommendations
- 🚀 **Fast Results**: Intelligent caching for quick responses

## 🚀 Railway Deployment (Recommended)

**Deploy to Railway in 5 minutes:**

1. **Go to Railway Dashboard**: https://railway.app/dashboard
2. **Click "New Project"**
3. **Choose "Deploy from GitHub repo"**
4. **Select your repository**
5. **Railway auto-detects Dockerfile and deploys**

**That's it!** Your app will be live with:

- ✅ **Frontend served automatically**
- ✅ **Backend API running**
- ✅ **PostgreSQL database**
- ✅ **Redis cache**

### Local Development

**Get everything running locally:**

```bash
git clone <repository-url>
cd linkedin-recommendation-writer-app
cp env.example .env
# Edit .env with your API keys
make setup
```

Access your local app at:

- **Frontend**: http://localhost:5173
- **Backend**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs

## 📋 Prerequisites

- **Docker & Docker Compose** (v20.10+)
- **Git** (v2.30+)
- **GitHub Personal Access Token** - Get from [GitHub Settings > Developer settings > Personal access tokens](https://github.com/settings/tokens)
- **Google Gemini API Key** - Get from [Google AI Studio](https://makersuite.google.com/app/apikey)

## 🛠️ Installation

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

## ⚙️ Configuration

Create a `.env` file with these required variables:

```bash
# Required API Keys
GITHUB_TOKEN=your_github_token_here
GEMINI_API_KEY=your_gemini_api_key_here

# Database (optional - will use defaults if not set)
POSTGRES_PASSWORD=your_secure_password_here
DATABASE_URL=postgresql://postgres:your_password@localhost:5432/linkedin_recommendations

# Redis (optional - will use defaults if not set)
REDIS_URL=redis://localhost:6379/0
```

## 🚀 Deployment Options

### Railway (Recommended - Single Project)

**Easiest deployment - everything in one project:**

1. Push your code to GitHub
2. Go to Railway Dashboard
3. New Project → Deploy from GitHub → Select your repo
4. Railway auto-detects Dockerfile and deploys
5. Add PostgreSQL and Redis plugins to the same project

**Result:** One URL with frontend + backend + database + cache!

### Docker (Local Development)

```bash
make setup-prod
```

### Advanced: Separate Services

If you need separate frontend/backend deployments:

- Deploy frontend to Vercel/Netlify
- Deploy backend to Railway
- Set `VITE_API_URL` to your Railway backend URL

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

- **API Docs**: http://localhost:8000/docs
- **Frontend**: http://localhost:5173

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests: `make test`
5. Submit a pull request

## 📄 License

MIT License - see [LICENSE](LICENSE) file for details.

## 📞 Support

- 📖 **Documentation**: Check the API docs at `/docs`
- 🐛 **Bug Reports**: [Create GitHub issues](https://github.com/your-repo/issues)
- 💬 **Discussions**: [Start GitHub discussions](https://github.com/your-repo/discussions)

---

<div align="center">
Made with ❤️ for the developer community
</div>
