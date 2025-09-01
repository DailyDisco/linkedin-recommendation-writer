"""Enhanced database health monitoring service."""

import asyncio
import logging
import time
from contextlib import asynccontextmanager
from datetime import datetime, timedelta
from typing import Any, Dict, List

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import AsyncSessionLocal, engine

logger = logging.getLogger(__name__)


class ConnectionHealthMetrics:
    """Tracks connection health metrics."""

    def __init__(self):
        self.connection_attempts = 0
        self.connection_successes = 0
        self.connection_failures = 0
        self.connection_timeouts = 0
        self.pool_exhaustions = 0
        self.last_health_check = None
        self.last_failure_time = None
        self.consecutive_failures = 0

    def record_success(self):
        """Record a successful connection."""
        self.connection_attempts += 1
        self.connection_successes += 1
        self.consecutive_failures = 0
        self.last_health_check = datetime.now()

    def record_failure(self, error_type: str = "unknown"):
        """Record a failed connection."""
        self.connection_attempts += 1
        self.connection_failures += 1
        self.consecutive_failures += 1
        self.last_failure_time = datetime.now()
        self.last_health_check = datetime.now()

        if "timeout" in error_type.lower():
            self.connection_timeouts += 1

    def record_pool_exhaustion(self):
        """Record pool exhaustion event."""
        self.pool_exhaustions += 1

    def get_health_score(self) -> float:
        """Calculate health score (0-100)."""
        if self.connection_attempts == 0:
            return 100.0

        success_rate = self.connection_successes / self.connection_attempts

        # Penalize for consecutive failures
        penalty = min(self.consecutive_failures * 10, 50)

        # Penalize for recent failures (last 5 minutes)
        recency_penalty = 0
        if self.last_failure_time:
            since_failure = datetime.now() - self.last_failure_time
            if since_failure < timedelta(minutes=5):
                recency_penalty = 20

        score = (success_rate * 100) - penalty - recency_penalty
        return max(0, min(100, score))

    def to_dict(self) -> Dict[str, Any]:
        """Convert metrics to dictionary."""
        return {
            "connection_attempts": self.connection_attempts,
            "connection_successes": self.connection_successes,
            "connection_failures": self.connection_failures,
            "connection_timeouts": self.connection_timeouts,
            "pool_exhaustions": self.pool_exhaustions,
            "success_rate": (self.connection_successes / self.connection_attempts * 100) if self.connection_attempts > 0 else 100,
            "consecutive_failures": self.consecutive_failures,
            "last_health_check": self.last_health_check.isoformat() if self.last_health_check else None,
            "last_failure_time": self.last_failure_time.isoformat() if self.last_failure_time else None,
            "health_score": self.get_health_score(),
        }


class DatabaseHealthMonitor:
    """Enhanced database health monitoring and connection management."""

    def __init__(self):
        self.metrics = ConnectionHealthMetrics()
        self._health_check_interval = 30  # seconds
        self._last_detailed_check = None
        self._circuit_breaker_state = "closed"  # closed, open, half-open
        self._circuit_breaker_failures = 0
        self._circuit_breaker_last_failure = None
        self._circuit_breaker_timeout = 60  # seconds

    async def check_connection_health(self, detailed: bool = False) -> Dict[str, Any]:
        """Perform comprehensive connection health check."""
        try:
            start_time = time.time()

            # Basic connectivity test
            async with AsyncSessionLocal() as session:
                result = await session.execute(text("SELECT 1 as health_check, version() as version"))
                row = result.first()
                response_time = time.time() - start_time

                self.metrics.record_success()

                health_data = {
                    "status": "healthy",
                    "response_time_ms": round(response_time * 1000, 2),
                    "database_version": row[1] if row else "Unknown",
                    "timestamp": datetime.now().isoformat(),
                    "circuit_breaker_state": self._circuit_breaker_state,
                }

                if detailed:
                    health_data.update(await self._get_detailed_health_metrics(session))

                self._last_detailed_check = datetime.now()
                return health_data

        except Exception as e:
            error_type = type(e).__name__
            self.metrics.record_failure(error_type)

            # Update circuit breaker
            self._update_circuit_breaker()

            return {
                "status": "unhealthy",
                "error": str(e),
                "error_type": error_type,
                "timestamp": datetime.now().isoformat(),
                "circuit_breaker_state": self._circuit_breaker_state,
                "consecutive_failures": self.metrics.consecutive_failures,
            }

    async def _get_detailed_health_metrics(self, session: AsyncSession) -> Dict[str, Any]:
        """Get detailed health metrics."""
        try:
            metrics = {}

            # Connection pool status
            pool_info = await self._get_pool_status()
            metrics["pool_status"] = pool_info

            # Active connections
            conn_result = await session.execute(
                text(
                    """
                SELECT
                    count(*) as total_connections,
                    count(*) filter (where state = 'active') as active_connections,
                    count(*) filter (where state = 'idle') as idle_connections,
                    count(*) filter (where state = 'idle in transaction') as idle_in_transaction
                FROM pg_stat_activity
                WHERE datname = current_database()
            """
                )
            )
            conn_row = conn_result.first()
            metrics["connections"] = {
                "total": conn_row[0] if conn_row else 0,
                "active": conn_row[1] if conn_row else 0,
                "idle": conn_row[2] if conn_row else 0,
                "idle_in_transaction": conn_row[3] if conn_row else 0,
            }

            # Database size and growth
            size_result = await session.execute(
                text(
                    """
                SELECT
                    pg_size_pretty(pg_database_size(current_database())) as size,
                    pg_database_size(current_database()) as size_bytes
            """
                )
            )
            size_row = size_result.first()
            metrics["database_size"] = {"size": size_row[0] if size_row else "Unknown", "size_bytes": size_row[1] if size_row else 0}

            # Cache hit ratios
            cache_result = await session.execute(
                text(
                    """
                SELECT
                    sum(heap_blks_hit) as heap_hit,
                    sum(heap_blks_read) as heap_read,
                    sum(idx_blks_hit) as idx_hit,
                    sum(idx_blks_read) as idx_read
                FROM pg_statio_user_tables
            """
                )
            )
            cache_row = cache_result.first()

            heap_hit = cache_row[0] or 0
            heap_read = cache_row[1] or 0
            idx_hit = cache_row[2] or 0
            idx_read = cache_row[3] or 0

            metrics["cache_hit_ratio"] = {
                "heap_cache_hit_ratio": (heap_hit / (heap_hit + heap_read) * 100) if (heap_hit + heap_read) > 0 else 0,
                "index_cache_hit_ratio": (idx_hit / (idx_hit + idx_read) * 100) if (idx_hit + idx_read) > 0 else 0,
            }

            # Long-running queries
            long_queries_result = await session.execute(
                text(
                    """
                SELECT
                    pid,
                    now() - pg_stat_activity.query_start as duration,
                    query
                FROM pg_stat_activity
                WHERE state = 'active'
                AND now() - pg_stat_activity.query_start > interval '30 seconds'
                AND query NOT LIKE '%pg_stat_activity%'
                ORDER BY duration DESC
                LIMIT 5
            """
                )
            )

            long_queries = []
            for row in long_queries_result:
                long_queries.append({"pid": row[0], "duration": str(row[1]), "query": row[2][:100] + "..." if len(row[2]) > 100 else row[2]})
            metrics["long_running_queries"] = long_queries

            return metrics

        except Exception as e:
            logger.error(f"Failed to get detailed metrics: {e}")
            return {"error": str(e)}

    async def _get_pool_status(self) -> Dict[str, Any]:
        """Get connection pool status."""
        try:
            pool = getattr(engine, "pool", None)
            if pool is None:
                return {"error": "No pool available"}

            return {
                "pool_size": getattr(pool, "size", lambda: 0)(),
                "checked_out": getattr(pool, "checkedout", lambda: 0)(),
                "overflow": getattr(pool, "overflow", lambda: 0)(),
                "checked_in": getattr(pool, "checkedin", lambda: 0)(),
                "invalid": getattr(pool, "invalid", lambda: 0)(),
            }
        except Exception as e:
            return {"error": str(e)}

    def _update_circuit_breaker(self):
        """Update circuit breaker state based on failures."""
        now = datetime.now()

        # If we're in open state, check if timeout has passed
        if self._circuit_breaker_state == "open":
            if self._circuit_breaker_last_failure:
                time_since_failure = (now - self._circuit_breaker_last_failure).total_seconds()
                if time_since_failure > self._circuit_breaker_timeout:
                    self._circuit_breaker_state = "half-open"
                    logger.info("Circuit breaker moved to half-open state")

        # Update failure tracking
        self._circuit_breaker_failures += 1
        self._circuit_breaker_last_failure = now

        # Open circuit breaker if too many consecutive failures
        if self.metrics.consecutive_failures >= 5 and self._circuit_breaker_state == "closed":
            self._circuit_breaker_state = "open"
            logger.warning("Circuit breaker opened due to consecutive failures")

    async def get_health_metrics(self) -> Dict[str, Any]:
        """Get comprehensive health metrics."""
        return {
            "connection_metrics": self.metrics.to_dict(),
            "circuit_breaker": {
                "state": self._circuit_breaker_state,
                "failures": self._circuit_breaker_failures,
                "last_failure": self._circuit_breaker_last_failure.isoformat() if self._circuit_breaker_last_failure else None,
            },
            "last_detailed_check": self._last_detailed_check.isoformat() if self._last_detailed_check else None,
            "health_check_interval": self._health_check_interval,
        }

    @asynccontextmanager
    async def resilient_connection(self, max_retries: int = 3, backoff_factor: float = 1.5):
        """Context manager for resilient database connections with retry logic."""
        last_exception = None

        for attempt in range(max_retries):
            try:
                # Check circuit breaker
                if self._circuit_breaker_state == "open":
                    raise Exception("Circuit breaker is open - database unavailable")

                async with AsyncSessionLocal() as session:
                    # If we're in half-open state and this succeeds, close the circuit
                    if self._circuit_breaker_state == "half-open":
                        self._circuit_breaker_state = "closed"
                        self._circuit_breaker_failures = 0
                        logger.info("Circuit breaker closed - connection restored")

                    yield session
                    return

            except Exception as e:
                last_exception = e
                error_type = type(e).__name__
                self.metrics.record_failure(error_type)

                # Update circuit breaker
                self._update_circuit_breaker()

                if attempt < max_retries - 1:
                    sleep_time = backoff_factor**attempt
                    logger.warning(".2f")
                    await asyncio.sleep(sleep_time)
                else:
                    logger.error(f"Connection failed after {max_retries} attempts: {e}")

        raise last_exception

    async def monitor_long_running_queries(self, threshold_seconds: int = 30) -> List[Dict[str, Any]]:
        """Monitor and return long-running queries."""
        try:
            async with AsyncSessionLocal() as session:
                result = await session.execute(
                    text(
                        f"""
                    SELECT
                        pid,
                        pg_stat_activity.query_start,
                        now() - pg_stat_activity.query_start as duration,
                        query,
                        state
                    FROM pg_stat_activity
                    WHERE state = 'active'
                    AND now() - pg_stat_activity.query_start > interval '{threshold_seconds} seconds'
                    AND query NOT LIKE '%pg_stat_activity%'
                    ORDER BY duration DESC
                """
                    )
                )

                long_queries = []
                for row in result:
                    long_queries.append(
                        {"pid": row[0], "query_start": row[1].isoformat() if row[1] else None, "duration": str(row[2]), "query": row[3][:200] + "..." if len(row[3]) > 200 else row[3], "state": row[4]}
                    )

                return long_queries

        except Exception as e:
            logger.error(f"Failed to monitor long-running queries: {e}")
            return []

    async def get_database_performance_stats(self) -> Dict[str, Any]:
        """Get database performance statistics."""
        try:
            async with AsyncSessionLocal() as session:
                # Query performance stats (if pg_stat_statements is available)
                try:
                    extension_check = await session.execute(
                        text(
                            """
                        SELECT count(*) FROM pg_extension WHERE extname = 'pg_stat_statements'
                    """
                        )
                    )

                    if extension_check.scalar() > 0:
                        stats_result = await session.execute(
                            text(
                                """
                            SELECT
                                sum(calls) as total_calls,
                                sum(total_time) as total_time,
                                avg(mean_time) as avg_time,
                                count(*) as unique_queries
                            FROM pg_stat_statements
                            WHERE query NOT LIKE '%pg_stat_statements%'
                        """
                            )
                        )

                        stats_row = stats_result.first()
                        query_stats = {
                            "total_calls": stats_row[0] if stats_row else 0,
                            "total_time": stats_row[1] if stats_row else 0,
                            "avg_time": stats_row[2] if stats_row else 0,
                            "unique_queries": stats_row[3] if stats_row else 0,
                        }
                    else:
                        query_stats = {"note": "pg_stat_statements extension not available"}

                except Exception as e:
                    query_stats = {"error": f"Failed to get query stats: {str(e)}"}

                # Database locks
                locks_result = await session.execute(
                    text(
                        """
                    SELECT
                        mode,
                        count(*) as count
                    FROM pg_locks
                    WHERE database = (SELECT oid FROM pg_database WHERE datname = current_database())
                    GROUP BY mode
                    ORDER BY count DESC
                """
                    )
                )

                locks = []
                for row in locks_result:
                    locks.append({"mode": row[0], "count": row[1]})

                return {"query_performance": query_stats, "active_locks": locks, "timestamp": datetime.now().isoformat()}

        except Exception as e:
            logger.error(f"Failed to get performance stats: {e}")
            return {"error": str(e)}


# Global health monitor instance
health_monitor = DatabaseHealthMonitor()
