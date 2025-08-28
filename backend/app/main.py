"""
LinkedIn Recommendation Writer - FastAPI Main Application

This is the main entry point for the LinkedIn Recommendation Writer backend.
It provides APIs to analyze GitHub profiles and generate professional LinkedIn recommendations.
"""

import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.v1 import api_router
from app.core.config import settings
from app.core.database import (check_database_health, init_database,
                               run_migrations)
from app.core.exceptions import BaseApplicationError
from app.core.logging_config import setup_logging
from app.core.middleware import (ErrorHandlingMiddleware, LoggingMiddleware,
                                 RateLimitingMiddleware, RequestIDMiddleware,
                                 SecurityHeadersMiddleware)
from app.core.redis_client import check_redis_health, init_redis

# Setup logging
setup_logging()
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup
    logger.info("Starting LinkedIn Recommendation Writer Backend...")

    # Initialize database
    if settings.RUN_MIGRATIONS:
        await run_migrations()
        logger.info("Database migrations completed successfully")
    elif settings.INIT_DB:
        await init_database()
        logger.info("Database initialized successfully")

    # Initialize Redis
    await init_redis()
    logger.info("Redis initialized successfully")

    logger.info("Application startup complete")

    yield

    # Shutdown
    logger.info("Shutting down application...")


# Create FastAPI application
app = FastAPI(
    title="LinkedIn Recommendation Writer",
    description="Generate professional LinkedIn recommendations using GitHub data and AI",
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
    allow_origins=settings.cors_origins,  # type: ignore
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(api_router, prefix="/api/v1")


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "LinkedIn Recommendation Writer API",
        "version": "1.0.0",
        "docs": "/docs",
        "status": "running",
    }


@app.get("/health")
async def health_check():
    """Health check endpoint for Docker and load balancers."""
    checks = {"api": "ok", "environment": settings.ENVIRONMENT}

    overall_status = "healthy"
    status_code = 200

    try:
        # Check database connectivity
        db_status = await check_database_health()
        checks["database"] = db_status
        if db_status != "ok":
            overall_status = "degraded"
            status_code = 503
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        checks["database"] = "error"
        overall_status = "unhealthy"
        status_code = 503

    try:
        # Check Redis connectivity
        redis_status = await check_redis_health()
        checks["redis"] = redis_status
        if redis_status != "ok" and overall_status == "healthy":
            overall_status = "degraded"
            # Redis is non-critical, don't fail health check
    except Exception as e:
        logger.error(f"Redis health check failed: {e}")
        checks["redis"] = "error"
        if overall_status == "healthy":
            overall_status = "degraded"

    response_data = {
        "status": overall_status,
        "service": "linkedin-recommendation-writer",
        "version": "1.0.0",
        "environment": settings.ENVIRONMENT,
        "checks": checks,
    }

    if status_code != 200:
        return JSONResponse(status_code=status_code, content=response_data)

    return response_data


# Custom exception handlers
@app.exception_handler(BaseApplicationError)
async def application_exception_handler(request: Request, exc: BaseApplicationError):
    """Handle custom application exceptions."""
    request_id = getattr(request.state, "request_id", "unknown")

    logger.warning(
        f"Application error in request {request_id}: {exc.error_code} - {exc.message}",
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
async def global_exception_handler(request: Request, exc: Exception):
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
        workers=settings.API_WORKERS if settings.ENVIRONMENT == "production" else 1,
        log_level=settings.LOG_LEVEL.lower(),
    )
