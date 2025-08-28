"""
LinkedIn Recommendation Writer - FastAPI Main Application

This is the main entry point for the LinkedIn Recommendation Writer backend.
It provides APIs to analyze GitHub profiles and generate professional
LinkedIn recommendations.
"""

import logging
import os
from contextlib import asynccontextmanager
from typing import Any, AsyncGenerator, Dict, Union

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from app.api.v1 import api_router
from app.core.config import settings
from app.core.database import check_database_health, init_database, run_migrations
from app.core.exceptions import BaseApplicationError
from app.core.logging_config import setup_logging
from app.core.middleware import ErrorHandlingMiddleware, LoggingMiddleware, RateLimitingMiddleware, RequestIDMiddleware, SecurityHeadersMiddleware
from app.core.redis_client import check_redis_health, init_redis

# Setup logging
setup_logging()
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan manager."""
    # Startup
    logger.info("🚀 Starting LinkedIn Recommendation Writer Backend...")

    # Log environment info
    logger.info(f"📊 Environment: {settings.ENVIRONMENT}")
    logger.info(f"🔌 API Host: {settings.API_HOST}")
    logger.info(f"🔌 API Port: {settings.API_PORT}")
    logger.info(f"🐛 Debug Mode: {settings.API_DEBUG}")

    # Check database URL
    if settings.DATABASE_URL:
        logger.info("✅ DATABASE_URL is configured")
    else:
        logger.error("❌ DATABASE_URL is not configured!")
        raise ValueError("DATABASE_URL environment variable is required")

    # Check Redis URL
    if settings.REDIS_URL:
        logger.info("✅ REDIS_URL is configured")
    else:
        logger.warning("⚠️ REDIS_URL is not configured - caching will be disabled")

    # Check API keys
    if settings.GITHUB_TOKEN:
        logger.info("✅ GITHUB_TOKEN is configured")
    else:
        logger.error("❌ GITHUB_TOKEN is not configured!")
        raise ValueError("GITHUB_TOKEN environment variable is required")

    if settings.GEMINI_API_KEY:
        logger.info("✅ GEMINI_API_KEY is configured")
    else:
        logger.error("❌ GEMINI_API_KEY is not configured!")
        raise ValueError("GEMINI_API_KEY environment variable is required")

    # Initialize database
    try:
        if settings.RUN_MIGRATIONS:
            logger.info("🗄️ Running database migrations...")
            await run_migrations()
            logger.info("✅ Database migrations completed successfully")
        elif settings.INIT_DB:
            logger.info("🗄️ Initializing database...")
            await init_database()
            logger.info("✅ Database initialized successfully")
        else:
            logger.info("⏭️ Skipping database initialization")
    except Exception as e:
        logger.error(f"❌ Database initialization failed: {e}")
        raise

    # Initialize Redis
    try:
        logger.info("🔄 Initializing Redis...")
        await init_redis()
        logger.info("✅ Redis initialized successfully")
    except Exception as e:
        logger.error(f"❌ Redis initialization failed: {e}")
        # Redis is not critical, don't raise error

    logger.info("🎉 Application startup complete - ready to serve requests!")

    yield

    # Shutdown
    logger.info("🔄 Shutting down application...")


# Create FastAPI application
app = FastAPI(
    title="LinkedIn Recommendation Writer",
    description="Generate professional LinkedIn recommendations using GitHub " "data and AI",
    version="1.0.0",
    docs_url="/docs" if settings.ENVIRONMENT != "production" else None,
    redoc_url="/redoc" if settings.ENVIRONMENT != "production" else None,
    debug=settings.API_DEBUG,
    lifespan=lifespan,
)

# Add custom middleware (order matters - last added is executed first)
app.add_middleware(ErrorHandlingMiddleware)
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(LoggingMiddleware)
app.add_middleware(RequestIDMiddleware)

# Rate limiting middleware
if settings.ENABLE_RATE_LIMITING:
    app.add_middleware(
        RateLimitingMiddleware,
        requests_per_minute=settings.RATE_LIMIT_REQUESTS_PER_MINUTE,
    )

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(api_router, prefix="/api/v1")

# Mount static files for frontend (only if frontend build exists)
frontend_build_path = os.path.join(os.path.dirname(__file__), "..", "frontend_static")
if os.path.exists(frontend_build_path):
    app.mount("/", StaticFiles(directory=frontend_build_path, html=True), name="frontend")

    @app.get("/{path:path}")
    async def serve_frontend(path: str) -> Union[JSONResponse, FileResponse]:
        """Serve frontend for SPA routing."""
        # If the path is an API route, let it pass through
        if path.startswith("api/") or path in ["docs", "redoc", "health"]:
            return JSONResponse(status_code=404, content={"error": "Not found"})

        # Try to serve the file if it exists
        file_path = os.path.join(frontend_build_path, path)
        if os.path.isfile(file_path):
            return FileResponse(file_path)

        # For SPA routing, serve index.html for all non-API routes
        index_path = os.path.join(frontend_build_path, "index.html")
        if os.path.exists(index_path):
            return FileResponse(index_path)

        return JSONResponse(status_code=404, content={"error": "Not found"})


@app.get("/")
async def root() -> Dict[str, Any]:
    """Root endpoint."""
    return {
        "message": "LinkedIn Recommendation Writer API",
        "version": "1.0.0",
        "docs": "/docs",
        "status": "running",
    }


@app.get("/health")
async def health_check() -> Union[Dict[str, Any], JSONResponse]:
    """Health check endpoint for Docker and load balancers."""
    logger.info("🏥 Health check requested")

    checks = {"api": "ok", "environment": settings.ENVIRONMENT, "timestamp": "2024-01-01T00:00:00Z"}

    overall_status = "healthy"
    status_code = 200

    # Check environment variables
    env_checks = {
        "database_url": bool(settings.DATABASE_URL),
        "redis_url": bool(settings.REDIS_URL),
        "github_token": bool(settings.GITHUB_TOKEN),
        "gemini_api_key": bool(settings.GEMINI_API_KEY),
    }

    checks["environment_variables"] = env_checks

    # Log environment variable status
    logger.info(f"🔍 Environment variables check: {env_checks}")

    if not env_checks["database_url"]:
        logger.error("❌ DATABASE_URL is missing!")
        overall_status = "unhealthy"
        status_code = 503

    if not env_checks["github_token"]:
        logger.error("❌ GITHUB_TOKEN is missing!")
        overall_status = "unhealthy"
        status_code = 503

    if not env_checks["gemini_api_key"]:
        logger.error("❌ GEMINI_API_KEY is missing!")
        overall_status = "unhealthy"
        status_code = 503

    # Only check database if we have DATABASE_URL
    if env_checks["database_url"]:
        try:
            logger.info("🗄️ Checking database connectivity...")
            db_status = await check_database_health()
            checks["database"] = db_status
            logger.info(f"🗄️ Database status: {db_status}")

            if db_status != "ok":
                overall_status = "degraded" if overall_status == "healthy" else overall_status
                if status_code == 200:
                    status_code = 503
        except Exception as e:
            logger.error(f"❌ Database health check failed: {e}")
            checks["database"] = f"error: {str(e)}"
            overall_status = "unhealthy"
            status_code = 503

    # Check Redis if available
    if env_checks["redis_url"]:
        try:
            logger.info("🔄 Checking Redis connectivity...")
            redis_status = await check_redis_health()
            checks["redis"] = redis_status
            logger.info(f"🔄 Redis status: {redis_status}")

            if redis_status != "ok" and overall_status == "healthy":
                overall_status = "degraded"
        except Exception as e:
            logger.error(f"⚠️ Redis health check failed: {e}")
            checks["redis"] = f"error: {str(e)}"
            if overall_status == "healthy":
                overall_status = "degraded"
    else:
        checks["redis"] = "not_configured"
        logger.warning("⚠️ Redis not configured - caching disabled")

    response_data = {
        "status": overall_status,
        "service": "linkedin-recommendation-writer",
        "version": "1.0.0",
        "environment": settings.ENVIRONMENT,
        "timestamp": "2024-01-01T00:00:00Z",
        "checks": checks,
        "message": f"Health check completed with status: {overall_status}",
    }

    logger.info(f"🏥 Health check completed: {overall_status} (HTTP {status_code})")

    if status_code != 200:
        logger.warning(f"⚠️ Health check returning error status: {status_code}")
        return JSONResponse(status_code=status_code, content=response_data)

    return response_data


# Custom exception handlers
@app.exception_handler(BaseApplicationError)
async def application_exception_handler(request: Request, exc: BaseApplicationError) -> JSONResponse:
    """Handle custom application exceptions."""
    request_id = getattr(request.state, "request_id", "unknown")

    logger.warning(
        f"Application error in request {request_id}: {exc.error_code} - " f"{exc.message}",
        extra={"error_code": exc.error_code, "details": exc.details},
    )

    status_map = {
        "VALIDATION_ERROR": 400,
        "NOT_FOUND": 404,
        "RATE_LIMIT_ERROR": 429,
        "EXTERNAL_SERVICE_ERROR": 503,
        "DATABASE_ERROR": 500,
        "CACHE_ERROR": 500,
        "CONFIGURATION_ERROR": 500,
    }

    status_code = status_map.get(exc.error_code, 500)

    return JSONResponse(
        status_code=status_code,
        content={
            "error": exc.error_code,
            "message": exc.message,
            "details": exc.details,
            "request_id": request_id,
        },
    )


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Global exception handler for unhandled exceptions."""
    request_id = getattr(request.state, "request_id", "unknown")
    logger.error(f"Unhandled exception in request {request_id}: {exc}", exc_info=True)

    if settings.API_DEBUG:
        return JSONResponse(
            status_code=500,
            content={
                "error": "INTERNAL_ERROR",
                "message": str(exc),
                "request_id": request_id,
            },
        )
    else:
        return JSONResponse(
            status_code=500,
            content={
                "error": "INTERNAL_ERROR",
                "message": "Internal server error",
                "request_id": request_id,
            },
        )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=settings.API_RELOAD and settings.ENVIRONMENT != "production",
        workers=(settings.API_WORKERS if settings.ENVIRONMENT == "production" else 1),
        log_level=settings.LOG_LEVEL.lower(),
    )
