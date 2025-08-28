# Multi-stage Dockerfile for LinkedIn Recommendation Writer
# Single container deployment - backend serves frontend

FROM python:3.11-slim as base

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    NODE_ENV=production

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    nodejs \
    npm \
    && rm -rf /var/lib/apt/lists/*

# Create app directory
WORKDIR /app

# Copy backend requirements first for better caching
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend code
COPY backend/ .

# Copy frontend and build it
COPY frontend/ ./frontend/
WORKDIR /app/frontend

# Fix path aliases for Docker build by replacing @/lib/utils with relative paths
RUN find app -name "*.tsx" -o -name "*.ts" | xargs sed -i 's|@/lib/utils|../../lib/utils|g'

# Install dependencies and build
RUN npm ci --production=false && npm run build

# Copy built frontend to backend static directory
RUN mkdir -p /app/frontend_static && cp -r build/* /app/frontend_static/

# Set working directory back to app root
WORKDIR /app

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Start the application
CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
