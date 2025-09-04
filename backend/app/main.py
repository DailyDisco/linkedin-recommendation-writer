"""
LinkedIn Recommendation Writer - FastAPI Main Application

This is the main entry point for the LinkedIn Recommendation Writer backend.
It provides APIs to analyze GitHub profiles and generate professional
LinkedIn recommendations.
"""

import logging

from fastapi import FastAPI

from app.api.health import router as health_router
from app.api.v1 import api_router
from app.core.config import settings
from app.core.lifecycle import lifespan
from app.core.logging_config import setup_logging
from app.core.middleware_setup import setup_middleware

# Setup logging
setup_logging()
logger = logging.getLogger(__name__)


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

# Setup middleware
setup_middleware(app)

# Include health check routes
app.include_router(health_router, tags=["health"])

# Include API routes
app.include_router(api_router, prefix="/api/v1")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=settings.API_DEBUG,
        log_level="info" if not settings.API_DEBUG else "debug",
    )
