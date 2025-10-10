"""
LinkedIn Recommendation Writer - FastAPI Main Application

This is the main entry point for the LinkedIn Recommendation Writer backend.
It provides APIs to analyze GitHub profiles and generate professional
LinkedIn recommendations.
"""

import logging
import os

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.api.health import router as health_router
from app.api.v1 import api_router
from app.core.config import settings
from app.core.lifecycle import lifespan
from app.core.logging_config import setup_logging
from app.core.middleware import setup_middleware

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

# Mount static files
static_dir = os.path.join(os.path.dirname(__file__), "static")
if os.path.exists(static_dir):
    app.mount("/assets", StaticFiles(directory=os.path.join(static_dir, "assets")), name="assets")
    app.mount("/static", StaticFiles(directory=static_dir), name="static")
    logger.info("📁 Static files mounted at /assets and /static")


# Root route to serve the frontend
@app.get("/")
async def root():
    """Serve the main frontend application."""
    index_path = os.path.join(static_dir, "index.html") if os.path.exists(static_dir) else None

    if index_path and os.path.exists(index_path):
        logger.info("🎨 Serving frontend index.html")
        return FileResponse(index_path)
    else:
        logger.warning("⚠️ Frontend index.html not found, returning API info")
        return {"message": "LinkedIn Recommendation Writer API", "docs": "/docs" if settings.ENVIRONMENT != "production" else None, "health": "/health", "api": "/api/v1"}


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
