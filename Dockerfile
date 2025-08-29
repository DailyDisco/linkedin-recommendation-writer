# =================================================================================================
# Root Dockerfile for LinkedIn Recommendation Writer
#
# This single, multi-stage Dockerfile builds the entire application for all environments.
# - Optimized for build speed with layer caching.
# - Creates lean, secure production images.
# - Serves as the single source of truth for building the application.
# =================================================================================================

# =================================================================================================
# BASE STAGE
# Common dependencies for both backend and frontend.
# =================================================================================================
FROM python:3.11-slim as base
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    NODE_ENV=production \
    # Path setup for node and npm
    PATH="/root/.local/bin:$PATH"

# Install base system dependencies and Node.js for frontend build
RUN apt-get update && \
    apt-get install -y curl build-essential nodejs npm && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

# =================================================================================================
# BACKEND DEPENDENCIES STAGE
# Installs Python dependencies. This layer is cached as long as requirements.txt doesn't change.
# =================================================================================================
FROM base as backend-deps
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# =================================================================================================
# FRONTEND DEPENDENCIES STAGE
# Installs Node.js dependencies. This layer is cached as long as package-lock.json doesn't change.
# =================================================================================================
FROM base as frontend-deps
WORKDIR /app/frontend
COPY frontend/package.json frontend/package-lock.json* ./
RUN npm ci --only=production

# =================================================================================================
# FRONTEND BUILDER STAGE
# Builds the static frontend assets. Re-runs only if frontend source code changes.
# =================================================================================================
FROM base as frontend-builder
WORKDIR /app/frontend
COPY frontend/package.json frontend/package-lock.json* ./
# Install all dependencies (including dev dependencies) needed for building
RUN npm ci --include=dev
COPY frontend ./
RUN npm run build

# =================================================================================================
# DEVELOPMENT STAGE
# Used for local development with docker-compose.yml. Includes dev dependencies and source code.
# =================================================================================================
FROM base as development
WORKDIR /app

# Install Python dev dependencies
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt && \
    pip install --no-cache-dir "uvicorn[standard]" black isort flake8 mypy pytest pytest-asyncio

# Install frontend dev dependencies
WORKDIR /app/frontend
COPY frontend/package.json frontend/package-lock.json* ./
RUN npm ci

# Set back to root app directory
WORKDIR /app

# The docker-compose.yml will mount the source code.
# The command will be provided in docker-compose.yml.

# =================================================================================================
# PRODUCTION STAGE
# Creates the final, lean production image.
# =================================================================================================
FROM backend-deps as production

# Create a non-root user for security
RUN useradd --create-home --shell /bin/bash app
WORKDIR /app

# Copy built frontend assets from the builder stage to the backend's static directory
# The target directory must exist, so we create it inside the backend structure.
COPY ./backend /app/backend
RUN mkdir -p /app/backend/app/static
COPY --from=frontend-builder /app/frontend/build/client /app/backend/app/static

# Adjust ownership and switch to non-root user
RUN chown -R app:app /app
USER app

WORKDIR /app/backend

EXPOSE 8000

# Healthcheck to ensure the application is running correctly
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:${PORT:-8000}/health || exit 1

# Start the application using Uvicorn directly
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
