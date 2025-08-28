# Docker Setup for LinkedIn Recommendation Writer

This document provides comprehensive instructions for using Docker with the LinkedIn Recommendation Writer application.

## 🚀 Quick Start

### Initial Setup

```bash
# Clone the repository
git clone <repository-url>
cd linkedin-recommendation-writer-app

# Copy environment template
cp env.template .env

# Edit .env file with your configuration
# Required: GITHUB_TOKEN, GEMINI_API_KEY

# Start the development environment
make setup
```

### Development Workflow

```bash
# Start all services
make up

# View logs
make logs

# Run tests
make test

# Stop services
make down
```

## 📋 Available Commands

### Development Commands

```bash
# Build and start services
make build          # Build all services
make up             # Start all services
make down           # Stop all services
make logs           # Show logs from all services

# Individual services
make dev-frontend   # Start frontend with logs
make dev-backend    # Start backend with logs
make restart        # Restart all services

# Database operations
make db-connect     # Connect to development database
make db-migrate     # Run database migrations
```

### Testing Commands

```bash
# Run all tests
make test

# Run individual test suites
make test-frontend          # Frontend tests only
make test-backend           # Backend tests only

# Interactive testing
make test-frontend-interactive  # Frontend test UI

# CI/CD testing
make ci-test               # Run CI-optimized tests
make ci-build              # Build for CI/CD
```

### Production Commands

```bash
# Production setup
make prod-build    # Build production images
make prod-up       # Start production services
make prod-down     # Stop production services
make prod-logs     # Show production logs
```

### Utility Commands

```bash
# Shell access
make shell-frontend    # Open frontend container shell
make shell-backend     # Open backend container shell

# Cleaning
make clean             # Remove all containers and volumes
make clean-volumes     # Remove all volumes only

# Status and information
make ps                # Show running containers
make status            # Show status of all services
make info              # Show useful information
```

## 🏗️ Docker Architecture

### Multi-Stage Builds

The frontend uses a sophisticated multi-stage Docker build:

1. **Base Stage**: Common setup with security hardening
2. **Dependencies Stage**: Caches npm dependencies
3. **Development Dependencies Stage**: Includes dev dependencies
4. **Testing Stage**: Runs linting, type checking, and tests
5. **Build Stage**: Creates production build
6. **Development Stage**: Development server with hot reload
7. **Production Stage**: Optimized production server

### Service Overview

#### Development Environment (`docker-compose.yml`)

- **Frontend**: Vite dev server with hot reload (port 5173)
- **Backend**: FastAPI with auto-reload (port 8000)
- **Database**: PostgreSQL with development tuning (port 5432)
- **Cache**: Redis for session and data caching (port 6379)

#### Testing Environment (`docker-compose.test.yml`)

- **Frontend Tests**: Isolated test environment with coverage reporting
- **Backend Tests**: Separate test database and Redis instances
- **Interactive Testing**: Test UI available on port 5174

#### Production Environment (`docker-compose.prod.yml`)

- **Frontend**: Optimized React Router production server (internal port 3000)
- **Backend**: FastAPI production server (internal port 8000)
- **Nginx**: Reverse proxy and load balancer (port 80/443)
- **Database**: PostgreSQL with production tuning (internal only)
- **Cache**: Redis with persistence (internal only)

#### CI/CD Environment (`docker-compose.ci.yml`)

- **Optimized for automation**: Fast startup and teardown
- **Separate databases**: Isolated test data
- **Coverage reporting**: Generates test coverage reports

## 🔧 Configuration

### Environment Variables

#### Required Variables (`.env`)

```bash
# GitHub API
GITHUB_TOKEN=your_github_token

# Gemini AI API
GEMINI_API_KEY=your_gemini_api_key

# Database
POSTGRES_PASSWORD=your_secure_password

# Optional: Custom configuration
NODE_ENV=development
API_DEBUG=true
LOG_LEVEL=INFO
```

#### Frontend Environment Variables

```bash
VITE_API_BASE_URL=http://localhost:8000  # Development
VITE_API_BASE_URL=http://backend:8000    # Production (internal)
VITE_API_TIMEOUT=30000
```

### Docker-Specific Configuration

#### Development Volume Mounting

```yaml
volumes:
  - ./frontend:/app # Source code
  - /app/node_modules # Container node_modules
```

#### Production Security

```yaml
security_opt:
  - no-new-privileges:true
read_only: true
tmpfs:
  - /tmp:noexec,nosuid,size=100m
```

## 🧪 Testing Strategy

### Frontend Testing

- **Framework**: Vitest with happy-dom
- **UI Testing**: React Testing Library
- **Coverage**: Generated in `frontend/coverage/`
- **Linting**: ESLint with React Router rules
- **Type Checking**: TypeScript compiler

### Backend Testing

- **Framework**: pytest with async support
- **Database**: Separate test database instance
- **Coverage**: Generated in `backend/coverage/`
- **Linting**: black, isort, flake8

### Running Tests

#### Development Testing

```bash
# Run all tests
make test

# Run with coverage
make test-frontend  # Generates coverage reports

# Interactive testing
make test-frontend-interactive
```

#### CI/CD Testing

```bash
# Fast testing for CI
make ci-test

# Individual services
make ci-test-frontend
make ci-test-backend
```

## 🚀 Deployment

### Production Deployment

```bash
# Build production images
make prod-build

# Deploy
make prod-up

# Check logs
make prod-logs

# Access application
# Frontend: http://localhost
# Backend: http://localhost/api (via nginx)
```

### Production Checklist

- [ ] Set `NODE_ENV=production`
- [ ] Configure production database credentials
- [ ] Set secure `SECRET_KEY`
- [ ] Configure allowed CORS origins
- [ ] Set up SSL certificates for nginx
- [ ] Configure log aggregation
- [ ] Set up monitoring and alerting

## 🔍 Debugging

### Common Issues

#### Permission Issues

```bash
# Fix node_modules permissions
sudo chown -R $(whoami) frontend/node_modules
```

#### Port Conflicts

```bash
# Check what's using ports
lsof -i :5173
lsof -i :8000

# Use different ports in .env
FRONTEND_PORT=5174
BACKEND_PORT=8001
```

#### Database Connection Issues

```bash
# Check database connectivity
make db-connect

# Reset database
make clean-volumes
make up
```

### Logs and Monitoring

```bash
# All logs
make logs

# Specific service logs
make logs-frontend
make logs-backend

# Production logs
make prod-logs
```

## 📊 Performance Optimization

### Development Optimizations

- **Hot reload**: Enabled for both frontend and backend
- **Volume mounting**: Optimized for live development
- **Dependency caching**: Multi-stage builds cache dependencies

### Production Optimizations

- **Multi-stage builds**: Minimal production image size
- **Security hardening**: Non-root user, read-only filesystem
- **Resource limits**: CPU and memory constraints
- **Health checks**: Automatic service monitoring

### Database Optimizations

- **Development**: Fast startup, relaxed constraints
- **Production**: Optimized for performance and reliability
- **Testing**: Isolated instances with fast cleanup

## 🔒 Security

### Container Security

- **Non-root user**: All containers run as nodejs user
- **Minimal base images**: Alpine Linux for smaller attack surface
- **Security options**: no-new-privileges, read-only filesystem
- **Dependency scanning**: Regular updates and security patches

### Runtime Security

- **Internal networking**: Services not exposed externally
- **Environment segregation**: Separate secrets for each environment
- **Log security**: Sensitive data not logged
- **Rate limiting**: Implemented at nginx level

## 📚 Additional Resources

- [Docker Compose Documentation](https://docs.docker.com/compose/)
- [React Router v7 Documentation](https://reactrouter.com/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Vitest Documentation](https://vitest.dev/)
- [PostgreSQL Docker](https://hub.docker.com/_/postgres)
- [Redis Docker](https://hub.docker.com/_/redis)

## 🤝 Contributing

When making changes to Docker configuration:

1. Test all environments (dev, test, prod)
2. Update this documentation
3. Ensure security best practices
4. Test with `make ci-test` before pushing

## 📞 Support

For Docker-related issues:

1. Check the logs: `make logs`
2. Verify environment variables in `.env`
3. Ensure all required services are running: `make ps`
4. Check network connectivity: `docker network ls`

---

## Happy Dockerizing! 🐳
