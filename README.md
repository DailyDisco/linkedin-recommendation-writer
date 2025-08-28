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

## 🚀 Quick Setup

**Get everything running with simple commands!**

### Quick Start (Recommended)

```bash
git clone <repository-url>
cd linkedin-recommendation-writer-app
cp env.template .env
# Edit .env with your API keys (GITHUB_TOKEN, GEMINI_API_KEY)
make setup
```

**That's it!** Your application will be running at:

- **Frontend**: <http://localhost:5173>
- **Backend**: <http://localhost:8000>
- **API Docs**: <http://localhost:8000/docs>

### What happens during setup?

1. **Environment Setup**: Creates `.env` file if missing (do this manually)
2. **Build**: Builds all Docker images with optimized caching
3. **Startup**: Starts frontend, backend, database, and Redis services
4. **Status Display**: Shows service status and access URLs

### After Setup

```bash
# View logs
make logs

# Stop services
make down

# Run tests
make test

# Clean up everything
make clean

# Get help with all available commands
make help
```

### Development Workflow

```bash
# Start services
make up

# Start with logs (don't detach)
make up-logs

# Restart services
make restart

# View status
make status

# Access service shells
make shell-frontend    # Frontend container
make shell-backend     # Backend container

# Database operations
make db-connect        # Connect to database
make db-migrate        # Run migrations
```

#### Manual Setup (Alternative)

##### Prerequisites

- Docker and Docker Compose
- GitHub Personal Access Token
- Google Gemini API Key

##### Setup Steps

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
   # Development mode (recommended)
   make setup

   # Or build and start separately
   make build
   make up

   # Production mode
   make setup-prod
   ```

4. **Access the application**:
   - **Frontend**: <http://localhost:5173>
   - **Backend**: <http://localhost:8000>
   - **API Documentation**: <http://localhost:8000/docs>

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
# Initialize database (via container)
make shell-backend
# Then run: python -c "from app.core.database import init_database; import asyncio; asyncio.run(init_database())"

# Or connect directly to database
make db-connect

# Run migrations
make db-migrate

# View logs
make logs-backend
make logs-frontend
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
   - Check rate limit status at <https://api.github.com/rate_limit>

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

1. **Use production setup**:

   ```bash
   make setup-prod
   ```

   Or manually:

   ```bash
   make prod-build
   make prod-up
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

4. **Production commands**:

   ```bash
   make prod-logs      # View production logs
   make prod-down      # Stop production services
   make prod-up-logs   # Start with logs
   ```

## Makefile Commands

The Makefile provides convenient commands for development and deployment:

### Development Commands

- `make setup` - Complete development setup (build + start)
- `make build` - Build all services
- `make up` - Start all services
- `make down` - Stop all services
- `make logs` - Show all service logs
- `make status` - Show service status
- `make restart` - Restart all services

### Testing & Quality

- `make test` - Run frontend tests
- `make test-frontend` - Run frontend tests only
- `make test-coverage` - Run tests with coverage
- `make lint-frontend` - Lint frontend code
- `make format-frontend` - Format frontend code

### Production Commands

- `make setup-prod` - Complete production setup
- `make prod-build` - Build for production
- `make prod-up` - Start production services
- `make prod-down` - Stop production services
- `make prod-logs` - Show production logs

### Utility Commands

- `make clean` - Remove all containers, volumes, and images
- `make clean-volumes` - Remove all volumes
- `make shell-frontend` - Open shell in frontend container
- `make shell-backend` - Open shell in backend container
- `make db-connect` - Connect to development database
- `make info` - Show useful information and URLs
- `make help` - Show all available commands

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
