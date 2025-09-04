"""Logging configuration."""

import logging
import sys
from pathlib import Path

from app.core.config import settings


def setup_logging() -> None:
    """Setup application logging configuration."""

    # Create logs directory if it doesn't exist (use relative path for local dev)
    is_production = bool(settings.is_production)
    log_dir = Path("logs") if not is_production else Path("/app/logs")
    log_dir.mkdir(exist_ok=True, parents=True)

    # Configure root logger
    handlers = [logging.StreamHandler(sys.stdout)]

    # Add file handler for detailed logs
    if not is_production:
        # Development: write all logs to file
        file_handler = logging.FileHandler(log_dir / "app.log")
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(logging.Formatter(settings.LOG_FORMAT))
        handlers.append(file_handler)

        # Separate debug file for AI services
        ai_handler = logging.FileHandler(log_dir / "ai_service.log")
        ai_handler.setLevel(logging.DEBUG)
        ai_handler.setFormatter(logging.Formatter(settings.LOG_FORMAT))
        ai_handler.addFilter(lambda record: record.name.startswith("app.services.ai"))
        handlers.append(ai_handler)

    logging.basicConfig(
        level=getattr(logging, settings.LOG_LEVEL),
        format=settings.LOG_FORMAT,
        handlers=handlers,
    )

    # Explicitly set app logger to DEBUG
    logging.getLogger("app").setLevel(logging.DEBUG)

    # Set specific loggers based on environment
    if is_production:
        # More restrictive logging in production
        logging.getLogger("uvicorn").setLevel(logging.WARNING)
        logging.getLogger("sqlalchemy.engine").setLevel(logging.ERROR)
        logging.getLogger("httpx").setLevel(logging.ERROR)
        logging.getLogger("github").setLevel(logging.ERROR)
        logging.getLogger("uvicorn.access").setLevel(logging.INFO)
    else:
        # Development logging
        logging.getLogger("uvicorn").setLevel(logging.INFO)
        logging.getLogger("uvicorn.access").setLevel(logging.INFO)
        logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
        logging.getLogger("httpx").setLevel(logging.WARNING)

    # Suppress overly verbose third-party loggers
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("requests").setLevel(logging.WARNING)
