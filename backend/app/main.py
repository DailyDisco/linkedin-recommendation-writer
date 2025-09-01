"""
LinkedIn Recommendation Writer - FastAPI Main Application

This is the main entry point for the LinkedIn Recommendation Writer backend.
It provides APIs to analyze GitHub profiles and generate professional
LinkedIn recommendations.
"""

import logging
import os
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Any, AsyncGenerator, Dict, List, Union

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from app.api.v1 import api_router
from app.core.config import settings
from app.core.csrf_protection import APICSRFProtectionMiddleware, CSRFProtectionMiddleware
from app.core.database import check_database_health, init_database, run_migrations
from app.core.exceptions import BaseApplicationError
from app.core.logging_config import setup_logging
from app.core.middleware import ErrorHandlingMiddleware, LoggingMiddleware, RateLimitingMiddleware, RequestIDMiddleware
from app.core.redis_client import check_redis_health, init_redis
from app.core.security_config import security_utils
from app.core.security_middleware import (
    EnhancedSecurityHeadersMiddleware,
    InputSanitizationMiddleware,
    PIIFilteringMiddleware,
    RequestSizeLimitMiddleware,
)

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
# Security middlewares (executed in reverse order)
app.add_middleware(ErrorHandlingMiddleware)
app.add_middleware(APICSRFProtectionMiddleware)  # API-specific CSRF protection
app.add_middleware(CSRFProtectionMiddleware)  # General CSRF protection
app.add_middleware(RequestSizeLimitMiddleware)
app.add_middleware(InputSanitizationMiddleware)
app.add_middleware(PIIFilteringMiddleware)
app.add_middleware(EnhancedSecurityHeadersMiddleware)  # Replace old SecurityHeadersMiddleware
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


# Health check endpoint (must be defined BEFORE frontend routes)
@app.get("/health", response_model=None)
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


@app.get("/db-test", response_model=None)
async def database_connection_test():
    """Test database connection with detailed diagnostics."""
    logger.info("🔍 Database connection test requested")

    try:
        from app.core.database import test_database_connection

        result = await test_database_connection()

        status_code = 200 if result["connection_test"] == "success" else 500

        return JSONResponse(
            status_code=status_code, content={"status": "success" if result["connection_test"] == "success" else "error", "message": "Database connection test completed", "diagnostics": result}
        )
    except Exception as e:
        logger.error(f"❌ Database test endpoint failed: {e}")
        return JSONResponse(status_code=500, content={"status": "error", "message": "Database test endpoint failed", "error": str(e)})


@app.get("/db-analysis", response_model=None)
async def database_analysis():
    """Comprehensive database analysis and assessment."""
    logger.info("📊 Database analysis requested")

    try:
        from app.services.database_analyzer import DatabaseAnalyzer

        analysis = await DatabaseAnalyzer.analyze_current_state()
        recommendations = await DatabaseAnalyzer.generate_recommendations(analysis)

        analysis["recommendations"] = recommendations

        return JSONResponse(status_code=200, content={"status": "success", "message": "Database analysis completed", "analysis": analysis, "timestamp": datetime.now().isoformat()})
    except Exception as e:
        logger.error(f"❌ Database analysis failed: {e}")
        return JSONResponse(status_code=500, content={"status": "error", "message": "Database analysis failed", "error": str(e), "timestamp": datetime.now().isoformat()})


@app.post("/db-performance-test", response_model=None)
async def database_performance_test(duration: int = 30):
    """Run database performance test."""
    logger.info(f"⚡ Database performance test requested (duration: {duration}s)")

    if duration < 1 or duration > 300:
        return JSONResponse(status_code=400, content={"status": "error", "message": "Duration must be between 1 and 300 seconds"})

    try:
        from app.services.database_analyzer import DatabaseAnalyzer

        results = await DatabaseAnalyzer.run_performance_test(duration)

        return JSONResponse(status_code=200, content={"status": "success", "message": f"Performance test completed ({duration}s)", "results": results})
    except Exception as e:
        logger.error(f"❌ Performance test failed: {e}")
        return JSONResponse(status_code=500, content={"status": "error", "message": "Performance test failed", "error": str(e)})


@app.get("/db-migrations/status", response_model=None)
async def get_migration_status():
    """Get current migration status."""
    logger.info("📋 Migration status requested")

    try:
        from app.core.migrations import migration_manager

        status = await migration_manager.get_migration_status()

        return JSONResponse(status_code=200, content={"status": "success", "message": "Migration status retrieved", "data": status})
    except Exception as e:
        logger.error(f"❌ Migration status failed: {e}")
        return JSONResponse(status_code=500, content={"status": "error", "message": "Failed to get migration status", "error": str(e)})


@app.post("/db-migrations/init", response_model=None)
async def initialize_migrations():
    """Initialize database migrations."""
    logger.info("🚀 Migration initialization requested")

    try:
        from app.core.migrations import migration_manager

        # Check current status
        status = await migration_manager.get_migration_status()

        if status["status"] == "initialized" and not status["needs_upgrade"]:
            return JSONResponse(status_code=200, content={"status": "success", "message": "Migrations already initialized and up to date"})

        # Create initial migration if needed
        result = await migration_manager.create_initial_migration()

        if result["status"] == "success":
            # Run the initial migration
            upgrade_result = await migration_manager.run_migrations_online()
            result["upgrade_result"] = upgrade_result

        return JSONResponse(status_code=200 if result["status"] == "success" else 500, content={"status": result["status"], "message": result["message"], "data": result})
    except Exception as e:
        logger.error(f"❌ Migration initialization failed: {e}")
        return JSONResponse(status_code=500, content={"status": "error", "message": "Migration initialization failed", "error": str(e)})


@app.post("/db-migrations/upgrade", response_model=None)
async def upgrade_migrations():
    """Upgrade database to latest migration."""
    logger.info("⬆️ Migration upgrade requested")

    try:
        from app.core.migrations import migration_manager

        result = await migration_manager.run_migrations_online()

        return JSONResponse(status_code=200 if result["status"] == "success" else 500, content={"status": result["status"], "message": result["message"]})
    except Exception as e:
        logger.error(f"❌ Migration upgrade failed: {e}")
        return JSONResponse(status_code=500, content={"status": "error", "message": "Migration upgrade failed", "error": str(e)})


@app.post("/db-migrations/rollback", response_model=None)
async def rollback_migrations(target_revision: str = "-1"):
    """Rollback database migrations."""
    logger.info(f"⬇️ Migration rollback requested to: {target_revision}")

    try:
        from app.core.migrations import migration_manager

        result = await migration_manager.rollback_migration(target_revision)

        return JSONResponse(status_code=200 if result["status"] == "success" else 500, content={"status": result["status"], "message": result["message"]})
    except Exception as e:
        logger.error(f"❌ Migration rollback failed: {e}")
        return JSONResponse(status_code=500, content={"status": "error", "message": "Migration rollback failed", "error": str(e)})


@app.get("/db-migrations/history", response_model=None)
async def get_migration_history(limit: int = 10):
    """Get migration history."""
    logger.info("📚 Migration history requested")

    try:
        from app.core.migrations import migration_manager

        result = await migration_manager.get_migration_history(limit)

        return JSONResponse(status_code=200 if result["status"] == "success" else 500, content={"status": result["status"], "message": "Migration history retrieved", "data": result})
    except Exception as e:
        logger.error(f"❌ Migration history failed: {e}")
        return JSONResponse(status_code=500, content={"status": "error", "message": "Failed to get migration history", "error": str(e)})


@app.get("/health/database/detailed", response_model=None)
async def database_health_detailed():
    """Get detailed database health information."""
    logger.info("🏥 Detailed database health check requested")

    try:
        from app.services.health_monitor import health_monitor

        health_data = await health_monitor.check_connection_health(detailed=True)
        metrics = await health_monitor.get_health_metrics()

        return JSONResponse(
            status_code=200 if health_data["status"] == "healthy" else 503,
            content={"status": "success", "message": "Detailed health check completed", "health": health_data, "metrics": metrics, "timestamp": datetime.now().isoformat()},
        )
    except Exception as e:
        logger.error(f"❌ Detailed health check failed: {e}")
        return JSONResponse(status_code=500, content={"status": "error", "message": "Detailed health check failed", "error": str(e)})


@app.get("/health/database/performance", response_model=None)
async def database_performance_stats():
    """Get database performance statistics."""
    logger.info("📊 Database performance stats requested")

    try:
        from app.services.health_monitor import health_monitor

        stats = await health_monitor.get_database_performance_stats()

        return JSONResponse(status_code=200, content={"status": "success", "message": "Performance stats retrieved", "data": stats})
    except Exception as e:
        logger.error(f"❌ Performance stats failed: {e}")
        return JSONResponse(status_code=500, content={"status": "error", "message": "Failed to get performance stats", "error": str(e)})


@app.get("/health/database/queries", response_model=None)
async def long_running_queries(threshold: int = 30):
    """Get long-running database queries."""
    logger.info("🔍 Long-running queries check requested")

    try:
        from app.services.health_monitor import health_monitor

        queries = await health_monitor.monitor_long_running_queries(threshold)

        return JSONResponse(
            status_code=200,
            content={
                "status": "success",
                "message": f"Found {len(queries)} long-running queries (>{threshold}s)",
                "threshold_seconds": threshold,
                "long_running_queries": queries,
                "timestamp": datetime.now().isoformat(),
            },
        )
    except Exception as e:
        logger.error(f"❌ Long-running queries check failed: {e}")
        return JSONResponse(status_code=500, content={"status": "error", "message": "Failed to check long-running queries", "error": str(e)})


@app.post("/db-validation/setup", response_model=None)
async def setup_database_validation():
    """Set up database validation constraints and triggers."""
    logger.info("🛡️ Setting up database validation")

    try:
        from app.core.database_constraints import DatabaseConstraints

        result = await DatabaseConstraints.setup_all_constraints()

        return JSONResponse(
            status_code=200 if result["status"] != "error" else 500,
            content={"status": result["status"], "message": result["message"], "details": result.get("details", []), "timestamp": datetime.now().isoformat()},
        )
    except Exception as e:
        logger.error(f"❌ Database validation setup failed: {e}")
        return JSONResponse(status_code=500, content={"status": "error", "message": "Database validation setup failed", "error": str(e)})


@app.post("/db-validation/test", response_model=None)
async def test_data_validation():
    """Test data validation functions."""
    logger.info("🧪 Testing data validation")

    try:
        from app.core.validation import RECOMMENDATION_SCHEMA, USER_SCHEMA, DataValidator

        test_results = {
            "email_validation": DataValidator.validate_email_format("test@example.com"),
            "username_validation": DataValidator.validate_username_format("testuser123"),
            "password_validation": DataValidator.validate_password_strength("StrongP@ss123"),
            "github_url_validation": DataValidator.validate_github_profile_url("https://github.com/testuser"),
            "schema_validation_user": DataValidator.validate_data_types({"email": "test@example.com", "username": "testuser", "role": "free"}, USER_SCHEMA),
            "schema_validation_recommendation": DataValidator.validate_data_types(
                {"title": "Great Developer", "content": "This person is an excellent developer with great skills and experience.", "recipient_name": "John Doe"}, RECOMMENDATION_SCHEMA
            ),
        }

        successful_tests = sum(1 for result in test_results.values() if result.get("valid", False))

        return JSONResponse(
            status_code=200,
            content={"status": "success", "message": f"Validation tests completed: {successful_tests}/{len(test_results)} passed", "results": test_results, "timestamp": datetime.now().isoformat()},
        )
    except Exception as e:
        logger.error(f"❌ Data validation test failed: {e}")
        return JSONResponse(status_code=500, content={"status": "error", "message": "Data validation test failed", "error": str(e)})


@app.post("/db-validation/validate", response_model=None)
async def validate_data(data: Dict[str, Any], schema_type: str = "user"):
    """Validate data against a schema."""
    logger.info(f"✅ Validating data against {schema_type} schema")

    try:
        from app.core.validation import GITHUB_PROFILE_SCHEMA, RECOMMENDATION_SCHEMA, USER_SCHEMA, DataValidator

        schemas = {"user": USER_SCHEMA, "recommendation": RECOMMENDATION_SCHEMA, "github_profile": GITHUB_PROFILE_SCHEMA}

        if schema_type not in schemas:
            return JSONResponse(status_code=400, content={"status": "error", "message": f"Unknown schema type: {schema_type}", "available_schemas": list(schemas.keys())})

        result = DataValidator.validate_data_types(data, schemas[schema_type])

        return JSONResponse(
            status_code=200 if result["valid"] else 400,
            content={
                "status": "success" if result["valid"] else "validation_failed",
                "message": result["message"],
                "validation_result": result,
                "schema_type": schema_type,
                "timestamp": datetime.now().isoformat(),
            },
        )
    except Exception as e:
        logger.error(f"❌ Data validation failed: {e}")
        return JSONResponse(status_code=500, content={"status": "error", "message": "Data validation failed", "error": str(e)})


@app.get("/db-optimization/query-performance", response_model=None)
async def analyze_query_performance():
    """Analyze query performance and provide optimization recommendations."""
    logger.info("⚡ Analyzing query performance")

    try:
        from app.services.database_optimizer import DatabaseOptimizer

        result = await DatabaseOptimizer.analyze_query_performance()

        return JSONResponse(status_code=200, content={"status": "success", "message": "Query performance analysis completed", "analysis": result, "timestamp": datetime.now().isoformat()})
    except Exception as e:
        logger.error(f"❌ Query performance analysis failed: {e}")
        return JSONResponse(status_code=500, content={"status": "error", "message": "Query performance analysis failed", "error": str(e)})


@app.get("/db-optimization/index-usage", response_model=None)
async def analyze_index_usage():
    """Analyze index usage and provide optimization recommendations."""
    logger.info("📊 Analyzing index usage")

    try:
        from app.services.database_optimizer import DatabaseOptimizer

        result = await DatabaseOptimizer.analyze_index_usage()

        return JSONResponse(status_code=200, content={"status": "success", "message": "Index usage analysis completed", "analysis": result, "timestamp": datetime.now().isoformat()})
    except Exception as e:
        logger.error(f"❌ Index usage analysis failed: {e}")
        return JSONResponse(status_code=500, content={"status": "error", "message": "Index usage analysis failed", "error": str(e)})


@app.get("/db-optimization/connection-pool", response_model=None)
async def analyze_connection_pool():
    """Analyze connection pool usage and provide optimization recommendations."""
    logger.info("🔗 Analyzing connection pool")

    try:
        from app.services.database_optimizer import DatabaseOptimizer

        result = await DatabaseOptimizer.analyze_connection_pool()

        return JSONResponse(status_code=200, content={"status": "success", "message": "Connection pool analysis completed", "analysis": result, "timestamp": datetime.now().isoformat()})
    except Exception as e:
        logger.error(f"❌ Connection pool analysis failed: {e}")
        return JSONResponse(status_code=500, content={"status": "error", "message": "Connection pool analysis failed", "error": str(e)})


@app.get("/db-optimization/recommended-indexes", response_model=None)
async def get_recommended_indexes():
    """Get recommended indexes to improve performance."""
    logger.info("📈 Getting recommended indexes")

    try:
        from app.services.database_optimizer import DatabaseOptimizer

        result = await DatabaseOptimizer.create_recommended_indexes()

        return JSONResponse(status_code=200, content={"status": "success", "message": "Index recommendations generated", "recommendations": result, "timestamp": datetime.now().isoformat()})
    except Exception as e:
        logger.error(f"❌ Index recommendations failed: {e}")
        return JSONResponse(status_code=500, content={"status": "error", "message": "Failed to generate index recommendations", "error": str(e)})


@app.post("/db-optimization/connection-pool/optimize", response_model=None)
async def optimize_connection_pool():
    """Optimize connection pool configuration."""
    logger.info("🔧 Optimizing connection pool")

    try:
        from app.services.database_optimizer import DatabaseOptimizer

        result = await DatabaseOptimizer.optimize_connection_pool()

        return JSONResponse(status_code=200, content={"status": "success", "message": "Connection pool optimization completed", "optimization": result, "timestamp": datetime.now().isoformat()})
    except Exception as e:
        logger.error(f"❌ Connection pool optimization failed: {e}")
        return JSONResponse(status_code=500, content={"status": "error", "message": "Connection pool optimization failed", "error": str(e)})


@app.post("/db-optimization/performance-test", response_model=None)
async def run_performance_test(queries: List[str], iterations: int = 5):
    """Run performance tests on database queries."""
    logger.info(f"🧪 Running performance test with {len(queries)} queries, {iterations} iterations each")

    if not queries:
        return JSONResponse(status_code=400, content={"status": "error", "message": "No queries provided for testing"})

    if iterations < 1 or iterations > 50:
        return JSONResponse(status_code=400, content={"status": "error", "message": "Iterations must be between 1 and 50"})

    try:
        from app.services.database_optimizer import DatabaseOptimizer

        result = await DatabaseOptimizer.run_performance_test(queries, iterations)

        return JSONResponse(
            status_code=200, content={"status": "success", "message": f"Performance test completed with {len(queries)} queries", "test_results": result, "timestamp": datetime.now().isoformat()}
        )
    except Exception as e:
        logger.error(f"❌ Performance test failed: {e}")
        return JSONResponse(status_code=500, content={"status": "error", "message": "Performance test failed", "error": str(e)})


@app.post("/db-testing/full-suite", response_model=None)
async def run_full_test_suite():
    """Run the complete database test suite."""
    logger.info("🧪 Running full database test suite")

    try:
        from app.services.database_tester import DatabaseTester

        tester = DatabaseTester()
        result = await tester.run_full_test_suite()

        status_code = 200 if result["status"] == "completed" else 500

        return JSONResponse(
            status_code=status_code,
            content={
                "status": result["status"],
                "message": f"Full test suite completed in {result.get('duration_seconds', 0):.1f} seconds",
                "summary": result.get("summary", {}),
                "results": result.get("results", {}),
                "timestamp": datetime.now().isoformat(),
            },
        )
    except Exception as e:
        logger.error(f"❌ Full test suite failed: {e}")
        return JSONResponse(status_code=500, content={"status": "error", "message": "Full test suite failed", "error": str(e)})


@app.post("/db-testing/connection-tests", response_model=None)
async def run_connection_tests():
    """Run database connection tests."""
    logger.info("🔗 Running connection tests")

    try:
        from app.services.database_tester import DatabaseTester

        tester = DatabaseTester()
        result = await tester._run_connection_tests()

        return JSONResponse(status_code=200, content={"status": "success", "message": "Connection tests completed", "results": result, "timestamp": datetime.now().isoformat()})
    except Exception as e:
        logger.error(f"❌ Connection tests failed: {e}")
        return JSONResponse(status_code=500, content={"status": "error", "message": "Connection tests failed", "error": str(e)})


@app.post("/db-testing/performance-tests", response_model=None)
async def run_performance_tests():
    """Run database performance tests."""
    logger.info("⚡ Running performance tests")

    try:
        from app.services.database_tester import DatabaseTester

        tester = DatabaseTester()
        result = await tester._run_performance_tests()

        return JSONResponse(status_code=200, content={"status": "success", "message": "Performance tests completed", "results": result, "timestamp": datetime.now().isoformat()})
    except Exception as e:
        logger.error(f"❌ Performance tests failed: {e}")
        return JSONResponse(status_code=500, content={"status": "error", "message": "Performance tests failed", "error": str(e)})


@app.post("/db-testing/integrity-tests", response_model=None)
async def run_integrity_tests():
    """Run database integrity tests."""
    logger.info("🔒 Running integrity tests")

    try:
        from app.services.database_tester import DatabaseTester

        tester = DatabaseTester()
        result = await tester._run_data_integrity_tests()

        return JSONResponse(status_code=200, content={"status": "success", "message": "Integrity tests completed", "results": result, "timestamp": datetime.now().isoformat()})
    except Exception as e:
        logger.error(f"❌ Integrity tests failed: {e}")
        return JSONResponse(status_code=500, content={"status": "error", "message": "Integrity tests failed", "error": str(e)})


@app.post("/db-testing/validation-tests", response_model=None)
async def run_validation_tests():
    """Run data validation tests."""
    logger.info("✅ Running validation tests")

    try:
        from app.services.database_tester import DatabaseTester

        tester = DatabaseTester()
        result = await tester._run_validation_tests()

        return JSONResponse(status_code=200, content={"status": "success", "message": "Validation tests completed", "results": result, "timestamp": datetime.now().isoformat()})
    except Exception as e:
        logger.error(f"❌ Validation tests failed: {e}")
        return JSONResponse(status_code=500, content={"status": "error", "message": "Validation tests failed", "error": str(e)})


@app.post("/db-testing/load-tests", response_model=None)
async def run_load_tests(num_concurrent: int = 5, duration: int = 10):
    """Run database load tests."""
    logger.info(f"🏋️ Running load tests with {num_concurrent} concurrent connections for {duration} seconds")

    if num_concurrent < 1 or num_concurrent > 20:
        return JSONResponse(status_code=400, content={"status": "error", "message": "Concurrent connections must be between 1 and 20"})

    if duration < 5 or duration > 60:
        return JSONResponse(status_code=400, content={"status": "error", "message": "Duration must be between 5 and 60 seconds"})

    try:
        from app.services.database_tester import DatabaseTester

        tester = DatabaseTester()
        result = await tester._run_load_tests()

        # Override the default load test parameters
        if "load_test" in result:
            result["load_test"]["concurrent_workers"] = num_concurrent
            result["load_test"]["test_duration_seconds"] = duration

        return JSONResponse(
            status_code=200, content={"status": "success", "message": f"Load tests completed with {num_concurrent} concurrent connections", "results": result, "timestamp": datetime.now().isoformat()}
        )
    except Exception as e:
        logger.error(f"❌ Load tests failed: {e}")
        return JSONResponse(status_code=500, content={"status": "error", "message": "Load tests failed", "error": str(e)})


@app.get("/db-testing/status", response_model=None)
async def get_testing_status():
    """Get current testing status and capabilities."""
    logger.info("📊 Getting testing status")

    try:
        # Get basic database information
        from app.core.database import engine

        pool_info = {
            "pool_size": getattr(engine.pool, "size", lambda: 0)(),
            "checked_out": getattr(engine.pool, "checkedout", lambda: 0)(),
            "overflow": getattr(engine.pool, "overflow", lambda: 0)(),
        }

        available_tests = [
            {"name": "connection_tests", "description": "Test database connectivity and connection pooling", "endpoint": "/db-testing/connection-tests", "estimated_duration": "2-5 seconds"},
            {"name": "performance_tests", "description": "Test query performance and connection pool efficiency", "endpoint": "/db-testing/performance-tests", "estimated_duration": "10-30 seconds"},
            {"name": "integrity_tests", "description": "Test data integrity and constraint validation", "endpoint": "/db-testing/integrity-tests", "estimated_duration": "5-15 seconds"},
            {"name": "validation_tests", "description": "Test data validation functions", "endpoint": "/db-testing/validation-tests", "estimated_duration": "1-3 seconds"},
            {"name": "load_tests", "description": "Test database under concurrent load", "endpoint": "/db-testing/load-tests", "estimated_duration": "10-60 seconds"},
            {"name": "full_test_suite", "description": "Run all tests in sequence", "endpoint": "/db-testing/full-suite", "estimated_duration": "30-120 seconds"},
        ]

        return JSONResponse(
            status_code=200,
            content={
                "status": "ready",
                "message": "Database testing service is ready",
                "connection_pool": pool_info,
                "available_tests": available_tests,
                "total_tests": len(available_tests),
                "timestamp": datetime.now().isoformat(),
            },
        )
    except Exception as e:
        logger.error(f"❌ Testing status check failed: {e}")
        return JSONResponse(status_code=500, content={"status": "error", "message": "Failed to get testing status", "error": str(e)})


# Include API routes (AFTER health check, BEFORE static files)
app.include_router(api_router, prefix="/api/v1")


# Mount static files for frontend (only if frontend build exists)
# This MUST come AFTER all API routes
static_files_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "static"))
if os.path.exists(static_files_path) and os.path.isdir(static_files_path):
    logger.info(f"Serving static files from: {static_files_path}")
    app.mount(
        "/",
        StaticFiles(directory=static_files_path, html=True),
        name="static",
    )


# Custom exception handlers
@app.exception_handler(BaseApplicationError)
async def application_exception_handler(request: Request, exc: BaseApplicationError) -> JSONResponse:
    """Handle custom application exceptions with enhanced security."""
    request_id = getattr(request.state, "request_id", "unknown")

    # Log sanitized error message
    safe_message = exc.get_safe_message()
    logger.warning(
        f"Application error in request {request_id}: {exc.error_code} - {safe_message}",
        extra={
            "error_code": exc.error_code,
            "request_id": request_id,
            "status_code": None,  # Will be set below
        },
    )

    status_map = {
        "VALIDATION_ERROR": 400,
        "NOT_FOUND": 404,
        "RATE_LIMIT_ERROR": 429,
        "EXTERNAL_SERVICE_ERROR": 503,
        "DATABASE_ERROR": 500,
        "CACHE_ERROR": 500,
        "CONFIGURATION_ERROR": 500,
        "AUTHENTICATION_ERROR": 401,
        "AUTHORIZATION_ERROR": 403,
        "INPUT_SANITIZATION_ERROR": 400,
    }

    status_code = status_map.get(exc.error_code, 500)

    # Return sanitized error response
    response_content = exc.to_dict(include_details=settings.API_DEBUG)
    response_content["request_id"] = request_id

    return JSONResponse(
        status_code=status_code,
        content=response_content,
    )


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Global exception handler for unhandled exceptions with security considerations."""
    request_id = getattr(request.state, "request_id", "unknown")

    # Sanitize exception message for logging
    safe_exc_message = security_utils.filter_pii_for_logging(str(exc))
    logger.error(f"Unhandled exception in request {request_id}: {safe_exc_message}", exc_info=not settings.API_DEBUG)

    if settings.API_DEBUG:
        # In debug mode, provide more details but still sanitized
        return JSONResponse(
            status_code=500,
            content={"error": "INTERNAL_ERROR", "message": safe_exc_message, "request_id": request_id, "debug_info": "Debug mode enabled - check server logs for full stack trace"},
        )
    else:
        # Production mode - minimal information
        return JSONResponse(
            status_code=500,
            content={
                "error": "INTERNAL_ERROR",
                "message": "An unexpected error occurred. Please try again later.",
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
        log_level=settings.LOG_LEVEL.lower(),  # Revert to use settings
    )
