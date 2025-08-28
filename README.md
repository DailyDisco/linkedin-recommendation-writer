# LinkedIn Recommendation Writer

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Docker](https://img.shields.io/badge/docker-%230db7ed.svg?style=flat&logo=docker&logoColor=white)](https://docker.com)

Generate professional LinkedIn recommendations using GitHub data and AI.

## ✨ Features

- 🔍 **GitHub Analysis**: Analyzes repositories, languages, and contribution patterns
- 🤖 **AI-Powered**: Uses Google Gemini AI for natural recommendation generation
- ⚙️ **Customizable**: Multiple types, tones, and lengths available
- 💾 **History Tracking**: Save and manage all generated recommendations
- 🚀 **Fast Results**: Intelligent caching for quick responses

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

## 🚀 Deployment

### Docker (Recommended)

```bash
make setup-prod
```

### Railway (Easiest)

Connect your repository to Railway - it auto-detects the Dockerfile and provides PostgreSQL/Redis.

### Vercel + Railway

- Deploy frontend to Vercel
- Deploy backend to Railway
- Set `VITE_API_URL` in Vercel to your Railway backend URL

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
