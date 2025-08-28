# LinkedIn Recommendation Writer

Generate professional LinkedIn recommendations using GitHub data and AI.

## Overview

This application analyzes GitHub profiles and generates personalized, professional LinkedIn recommendations using Google Gemini AI. It transforms technical contributions and coding patterns into compelling professional narratives.

## Features

- 🔍 **GitHub Analysis**: Analyzes repositories, languages, and contribution patterns
- 🤖 **AI-Powered**: Uses Google Gemini AI for natural recommendation generation
- ⚙️ **Customizable**: Multiple types, tones, and lengths available
- 💾 **History Tracking**: Save and manage all generated recommendations
- 🚀 **Fast Results**: Intelligent caching for quick responses
- 🔒 **Privacy-Focused**: Only uses public GitHub data

## 🚀 One Command Setup

**Get everything running with a single command!**

The one-command setup automatically:

- ✅ Checks system requirements (Docker, Docker Compose)
- ✅ Creates `.env` file from template if needed
- ✅ Builds all Docker images with optimized caching
- ✅ Starts all services (frontend, backend, database, Redis)
- ✅ Shows service status and access URLs
- ✅ Provides helpful next steps

### Quick Start (Recommended)

```bash
git clone <repository-url>
cd linkedin-recommendation-writer-app
cp env.template .env
# Edit .env with your API keys (GITHUB_TOKEN, GEMINI_API_KEY)
./start.sh
```

**That's it!** Your application will be running at:

- **Frontend**: http://localhost:5173
- **Backend**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs

### What happens during setup?

1. **System Check**: Verifies Docker and Docker Compose are installed
2. **Environment Setup**: Creates `.env` file if missing
3. **Dependency Installation**: Builds Docker images with all dependencies
4. **Service Startup**: Starts frontend, backend, database, and Redis
5. **Health Checks**: Waits for services to be ready
6. **Status Display**: Shows all running services and their URLs

### After Setup

```bash
# View logs
./setup.sh dev logs

# Stop services
./setup.sh dev stop

# Run tests
./setup.sh test test

# Clean up everything
./setup.sh clean
```

### Even Easier Commands (Optional)

For the ultimate convenience, load the aliases:

```bash
source .aliases.sh

# Now you can use ultra-short commands:
q           # Quick start
dev         # Full development setup
prod        # Full production setup
l           # Show logs
test        # Run tests
up          # Start services
down        # Stop services
clean       # Clean up
```

### Advanced Setup Options

#### Using the Full Setup Script

```bash
# Development environment (default)
./setup.sh dev setup

# Production environment
./setup.sh prod setup

# Testing environment
./setup.sh test setup

# Other commands
./setup.sh dev logs       # Show logs
./setup.sh dev stop       # Stop services
./setup.sh dev status     # Show status
./setup.sh test test      # Run tests
./setup.sh clean          # Clean up everything
```

#### Manual Setup (Alternative)

**Prerequisites**

- Docker and Docker Compose
- GitHub Personal Access Token
- Google Gemini API Key

**Setup Steps**

1. **Clone and configure**:

   ```bash
   git clone <repository-url>
   cd linkedin-recommendation-writer-app
   cp env.template .env
   # Edit .env with your API keys
   ```

2. **Required API Keys**:

   - **GitHub Token**: Get from [GitHub Settings > Developer settings > Personal access tokens](https://github.com/settings/tokens)
     - Scopes needed: `repo`, `read:org`, `read:user`
   - **Gemini API Key**: Get from [Google AI Studio](https://makersuite.google.com/app/apikey)

3. **Start the application**:

   ```bash
   # Development mode
   docker-compose up -d

   # Production mode
   docker-compose -f docker-compose.prod.yml up -d
   ```

4. **Access the application**:
   - **Frontend**: http://localhost:5173
   - **Backend**: http://localhost:8000
   - **API Documentation**: http://localhost:8000/docs

## Environment Configuration

Key environment variables in `.env`:

```bash
# Required API Keys
GITHUB_TOKEN=your_github_token_here
GEMINI_API_KEY=your_gemini_api_key_here

# Database (default values work for Docker)
POSTGRES_PASSWORD=your_secure_password_here

# Optional customization
GEMINI_MODEL=gemini-2.5-flash-lite
LOG_LEVEL=info
```

## Architecture

### Backend (FastAPI)

- **Framework**: FastAPI with async/await
- **Database**: PostgreSQL with SQLAlchemy
- **Cache**: Redis for GitHub data and AI responses
- **AI**: Google Gemini for recommendation generation
- **API**: RESTful API with automatic documentation

### Frontend (React)

- **Framework**: React 18 with TypeScript
- **Styling**: Tailwind CSS
- **State Management**: React Query for server state
- **Build Tool**: Vite for fast development and building
- **UI Components**: Custom components with Lucide icons

### Infrastructure

- **Containerization**: Docker with multi-stage builds
- **Reverse Proxy**: Nginx for production
- **Development**: Hot reload for both frontend and backend
- **Production**: Optimized builds with health checks

## API Endpoints

### GitHub Analysis

- `POST /api/v1/github/analyze` - Analyze GitHub profile
- `GET /api/v1/github/user/{username}` - Get cached profile data

### Recommendations

- `POST /api/v1/recommendations/generate` - Generate new recommendation
- `GET /api/v1/recommendations/` - List recommendations
- `GET /api/v1/recommendations/{id}` - Get specific recommendation

### Health

- `GET /health` - Application health check

## Development

### Backend Development

```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

### Frontend Development

```bash
cd frontend
npm install
npm run dev
```

### Database Management

```bash
# Initialize database
docker-compose exec backend python -c "from app.core.database import init_database; import asyncio; asyncio.run(init_database())"

# View logs
docker-compose logs backend
docker-compose logs frontend
```

## Troubleshooting

### Docker Build Issues

Use the included troubleshooting script:

```bash
./fix-docker-build.sh
```

### Common Issues

1. **GitHub API Rate Limits**:

   - Ensure your GitHub token has correct permissions
   - Check rate limit status at https://api.github.com/rate_limit

2. **Gemini API Errors**:

   - Verify your API key is correct
   - Check quota limits in Google AI Studio

3. **Database Connection**:

   - Ensure PostgreSQL container is healthy
   - Check database credentials in `.env`

4. **Port Conflicts**:
   - Default ports: 3000 (frontend), 8000 (backend), 5432 (postgres), 6379 (redis)
   - Modify ports in docker-compose.yml if needed

## Production Deployment

1. **Use production compose file**:

   ```bash
   docker-compose -f docker-compose.prod.yml up -d
   ```

2. **Configure environment**:

   - Set strong passwords
   - Use your domain in `ALLOWED_ORIGINS`
   - Set `NODE_ENV=production`
   - Configure SSL certificates if needed

3. **Security considerations**:
   - Change default passwords
   - Use environment-specific secrets
   - Configure firewall rules
   - Set up monitoring and logging

## License

MIT License - see LICENSE file for details.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## Support

- 📖 Documentation: Check this README and API docs
- 🐛 Issues: Create GitHub issues for bugs
- 💡 Features: Suggest features via GitHub discussions
- 📧 Contact: [Your contact information]
