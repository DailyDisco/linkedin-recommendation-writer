# Multi-stage Dockerfile for React Frontend with React Router v7
# Supports development, testing, and production builds

# ============================
# Base stage with common setup
# ============================
FROM node:20-alpine as base

# Install security updates and required packages
RUN apk add --no-cache \
    dumb-init \
    curl \
    wget \
    && rm -rf /var/cache/apk/*

# Create non-root user for security
RUN addgroup -g 1001 -S nodejs && \
    adduser -S nodejs -u 1001

# Set working directory
WORKDIR /app

# Change ownership of working directory
RUN chown -R nodejs:nodejs /app
USER nodejs

# Copy package files with correct ownership
COPY --chown=nodejs:nodejs package*.json ./

# ============================
# Dependencies stage - for caching
# ============================
FROM base as deps

# Copy lock file if it exists
COPY --chown=nodejs:nodejs package-lock.json* ./

# Install dependencies based on NODE_ENV
RUN npm ci --only=production && npm cache clean --force

# ============================
# Development dependencies stage
# ============================
FROM base as dev-deps

# Copy lock file if it exists
COPY --chown=nodejs:nodejs package-lock.json* ./

# Install all dependencies (including dev dependencies)
RUN npm ci && npm cache clean --force

# ============================
# Testing stage
# ============================
FROM dev-deps as testing

# Copy source code
COPY --chown=nodejs:nodejs . .

# Set environment for testing
ENV NODE_ENV=test
ENV CI=true

# Run linting
RUN npm run lint

# Run type checking
RUN npm run typecheck

# Run tests
RUN npm run test:fast

# ============================
# Build stage
# ============================
FROM dev-deps as builder

# Copy source code
COPY --chown=nodejs:nodejs . .

# Set build environment
ENV NODE_ENV=production

# Run linting and type checking before build
RUN npm run lint && npm run typecheck

# Build the application
RUN npm run build

# ============================
# Development stage
# ============================
FROM dev-deps as development

# Copy source code
COPY --chown=nodejs:nodejs . .

# Expose port for Vite dev server
EXPOSE 5173

# Add health check for development
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:5173/ || exit 1

# Use dumb-init for proper signal handling
ENTRYPOINT ["/usr/bin/dumb-init", "--"]
CMD ["npm", "run", "dev"]

# ============================
# Production stage
# ============================
FROM deps as production

# Copy built application from builder stage
COPY --from=builder --chown=nodejs:nodejs /app/build ./build

# Copy static files that might be needed at runtime
COPY --from=builder --chown=nodejs:nodejs /app/public ./public

# Set production environment
ENV NODE_ENV=production

# Expose port for React Router server
EXPOSE 3000

# Add health check for production
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:3000/ || exit 1

# Use dumb-init for proper signal handling
ENTRYPOINT ["/usr/bin/dumb-init", "--"]
CMD ["npm", "run", "start"]
