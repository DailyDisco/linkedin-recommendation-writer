"""Health check and diagnostic endpoints."""

import logging
from datetime import datetime
from typing import Any, Dict, Union

from fastapi import APIRouter
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.core.database import check_database_health, test_database_connection
from app.core.redis_client import check_redis_health
from app.services.infrastructure import DatabaseAnalyzer

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/health", response_model=None)
async def health_check() -> Union[Dict[str, Any], JSONResponse]:
    """Health check endpoint for Docker and load balancers."""
    logger.info("🏥 Health check requested")

    checks: Dict[str, Any] = {"api": "ok", "environment": settings.ENVIRONMENT, "timestamp": "2024-01-01T00:00:00Z"}

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


@router.get("/db-test", response_model=None)
async def database_connection_test():
    """Test database connection with detailed diagnostics."""
    logger.info("🔍 Database connection test requested")

    try:
        result = await test_database_connection()

        status_code = 200 if result["connection_test"] == "success" else 500

        return JSONResponse(
            status_code=status_code, content={"status": "success" if result["connection_test"] == "success" else "error", "message": "Database connection test completed", "diagnostics": result}
        )
    except Exception as e:
        logger.error(f"❌ Database test endpoint failed: {e}")
        return JSONResponse(status_code=500, content={"status": "error", "message": "Database test endpoint failed", "error": str(e)})


@router.get("/db-analysis", response_model=None)
async def database_analysis():
    """Comprehensive database analysis and assessment."""
    logger.info("📊 Database analysis requested")

    try:
        analysis = await DatabaseAnalyzer.analyze_current_state()
        recommendations = await DatabaseAnalyzer.generate_recommendations(analysis)

        analysis["recommendations"] = recommendations

        return JSONResponse(status_code=200, content={"status": "success", "message": "Database analysis completed", "analysis": analysis, "timestamp": datetime.now().isoformat()})
    except Exception as e:
        logger.error(f"❌ Database analysis failed: {e}")
        return JSONResponse(status_code=500, content={"status": "error", "message": "Database analysis failed", "error": str(e), "timestamp": datetime.now().isoformat()})


@router.post("/db-performance-test", response_model=None)
async def database_performance_test(duration: int = 30):
    """Run database performance test."""
    logger.info(f"⚡ Database performance test requested (duration: {duration}s)")

    if duration < 1 or duration > 300:
        return JSONResponse(status_code=400, content={"status": "error", "message": "Duration must be between 1 and 300 seconds"})

    try:
        results = await DatabaseAnalyzer.run_performance_test(duration)

        return JSONResponse(status_code=200, content={"status": "success", "message": f"Performance test completed ({duration}s)", "results": results})
    except Exception as e:
        logger.error(f"❌ Database performance test failed: {e}")
        return JSONResponse(status_code=500, content={"status": "error", "message": "Database performance test failed", "error": str(e)})
