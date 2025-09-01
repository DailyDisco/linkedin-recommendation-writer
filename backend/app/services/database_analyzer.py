"""Database analyzer service for assessing current database usage and performance."""

import asyncio
import logging
import time
from datetime import datetime
from typing import Any, Dict, List

from sqlalchemy import text

from app.core.database import AsyncSessionLocal, engine

logger = logging.getLogger(__name__)


class DatabaseAnalyzer:
    """Comprehensive database analysis and assessment tool."""

    @staticmethod
    async def analyze_current_state() -> Dict[str, Any]:
        """Analyze current database state and usage patterns."""
        try:
            # Get each piece of information separately to avoid transaction issues
            connection_info = await DatabaseAnalyzer._get_connection_info()
            table_stats = await DatabaseAnalyzer._get_table_statistics()
            index_usage = await DatabaseAnalyzer._get_index_usage()
            query_patterns = await DatabaseAnalyzer._get_query_patterns()
            performance_metrics = await DatabaseAnalyzer._get_performance_metrics()

            return {
                "connection_info": connection_info,
                "table_stats": table_stats,
                "index_usage": index_usage,
                "query_patterns": query_patterns,
                "performance_metrics": performance_metrics,
                "recommendations": [],
            }
        except Exception as e:
            logger.error(f"Database analysis failed: {e}")
            return {"error": str(e)}

    @staticmethod
    async def _get_connection_info() -> Dict[str, Any]:
        """Get current connection information."""
        try:
            async with AsyncSessionLocal() as session:
                # Connection pool statistics
                pool_stats = {
                    "pool_size": getattr(engine.pool, "size", lambda: 0)(),
                    "checked_out": getattr(engine.pool, "checkedout", lambda: 0)(),
                    "overflow": getattr(engine.pool, "overflow", lambda: 0)(),
                    "checked_in": getattr(engine.pool, "checkedin", lambda: 0)(),
                }

                # Database version and settings
                version_result = await session.execute(text("SELECT version()"))
                version = version_result.scalar()

                db_result = await session.execute(text("SELECT current_database()"))
                db_name = db_result.scalar()

                # Active connections
                active_conn_result = await session.execute(
                    text(
                        """
                    SELECT count(*) as active_connections
                    FROM pg_stat_activity
                    WHERE state = 'active' AND pid <> pg_backend_pid()
                """
                    )
                )
                active_connections = active_conn_result.scalar()

                return {
                    "database_version": version,
                    "database_name": db_name,
                    "active_connections": active_connections,
                    "pool_statistics": pool_stats,
                    "max_connections": await DatabaseAnalyzer._get_max_connections(),
                }
        except Exception as e:
            logger.error(f"Failed to get connection info: {e}")
            return {"error": str(e)}

    @staticmethod
    async def _get_max_connections() -> int:
        """Get maximum allowed connections."""
        try:
            async with AsyncSessionLocal() as session:
                result = await session.execute(text("SHOW max_connections"))
                return int(result.scalar())
        except Exception:
            return 100  # Default PostgreSQL limit

    @staticmethod
    async def _get_table_statistics() -> List[Dict[str, Any]]:
        """Get statistics for all tables."""
        try:
            async with AsyncSessionLocal() as session:
                # Get basic table information
                result = await session.execute(
                    text(
                        """
                    SELECT
                        schemaname,
                        tablename,
                        pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size,
                        pg_total_relation_size(schemaname||'.'||tablename) as size_bytes
                    FROM pg_tables
                    WHERE schemaname = 'public'
                    ORDER BY size_bytes DESC
                    LIMIT 10
                """
                    )
                )

                stats = []
                for row in result:
                    stats.append({"schema": row[0], "table": row[1], "size": row[2], "size_bytes": row[3]})

                return stats
        except Exception as e:
            logger.error(f"Failed to get table statistics: {e}")
            return []

    @staticmethod
    async def _get_index_usage() -> List[Dict[str, Any]]:
        """Get index usage statistics."""
        try:
            async with AsyncSessionLocal() as session:
                result = await session.execute(
                    text(
                        """
                    SELECT
                        schemaname,
                        tablename,
                        indexname
                    FROM pg_indexes
                    WHERE schemaname = 'public'
                    ORDER BY tablename, indexname
                    LIMIT 20
                """
                    )
                )

                indexes = []
                for row in result:
                    indexes.append({"schema": row[0], "table": row[1], "index_name": row[2]})

                return indexes
        except Exception as e:
            logger.error(f"Failed to get index usage: {e}")
            return []

    @staticmethod
    async def _get_query_patterns() -> Dict[str, Any]:
        """Analyze query patterns and usage."""
        try:
            async with AsyncSessionLocal() as session:
                # Check if pg_stat_statements is available
                extension_check = await session.execute(
                    text(
                        """
                    SELECT count(*) FROM pg_extension WHERE extname = 'pg_stat_statements'
                """
                    )
                )

                if extension_check.scalar() == 0:
                    return {
                        "note": "pg_stat_statements extension not available. Install with: CREATE EXTENSION pg_stat_statements;",
                        "top_queries": [],
                        "total_query_time": 0,
                        "total_query_calls": 0,
                        "avg_query_time": 0,
                    }

                # Get recent query statistics
                result = await session.execute(
                    text(
                        """
                    SELECT
                        query,
                        calls,
                        total_time,
                        mean_time,
                        rows
                    FROM pg_stat_statements
                    WHERE query NOT LIKE '%pg_stat_statements%'
                    ORDER BY total_time DESC
                    LIMIT 10
                """
                    )
                )

                queries = []
                total_time = 0
                total_calls = 0

                for row in result:
                    query_info = {"query": row[0][:100] + "..." if len(row[0]) > 100 else row[0], "calls": row[1], "total_time": row[2], "mean_time": row[3], "rows_returned": row[4]}
                    queries.append(query_info)
                    total_time += row[2] or 0
                    total_calls += row[1] or 0

                return {"top_queries": queries, "total_query_time": total_time, "total_query_calls": total_calls, "avg_query_time": total_time / total_calls if total_calls > 0 else 0}
        except Exception as e:
            logger.error(f"Failed to get query patterns: {e}")
            return {"error": str(e)}

    @staticmethod
    async def _get_performance_metrics() -> Dict[str, Any]:
        """Get database performance metrics."""
        try:
            async with AsyncSessionLocal() as session:
                # Database size
                size_result = await session.execute(
                    text(
                        """
                    SELECT
                        pg_size_pretty(pg_database_size(current_database())) as db_size,
                        pg_database_size(current_database()) as db_size_bytes
                """
                    )
                )
                size_row = size_result.first()

                # Table sizes
                table_sizes_result = await session.execute(
                    text(
                        """
                    SELECT
                        schemaname,
                        tablename,
                        pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size,
                        pg_total_relation_size(schemaname||'.'||tablename) as size_bytes
                    FROM pg_tables
                    WHERE schemaname = 'public'
                    ORDER BY size_bytes DESC
                    LIMIT 10
                """
                    )
                )

                table_sizes = []
                for row in table_sizes_result:
                    table_sizes.append({"schema": row[0], "table": row[1], "size": row[2], "size_bytes": row[3]})

                # Cache hit ratio
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

                total_heap = heap_hit + heap_read
                total_idx = idx_hit + idx_read

                cache_hit_ratio = {"heap_cache_hit_ratio": (heap_hit / total_heap * 100) if total_heap > 0 else 0, "index_cache_hit_ratio": (idx_hit / total_idx * 100) if total_idx > 0 else 0}

                return {"database_size": size_row[0] if size_row else "Unknown", "database_size_bytes": size_row[1] if size_row else 0, "table_sizes": table_sizes, "cache_hit_ratio": cache_hit_ratio}
        except Exception as e:
            logger.error(f"Failed to get performance metrics: {e}")
            return {"error": str(e)}

    @staticmethod
    async def generate_recommendations(analysis: Dict[str, Any]) -> List[str]:
        """Generate recommendations based on analysis."""
        recommendations = []

        try:
            # Connection pool recommendations
            pool_stats = analysis.get("connection_info", {}).get("pool_statistics", {})
            max_conn = analysis.get("connection_info", {}).get("max_connections", 100)

            if pool_stats.get("overflow", 0) > 0:
                recommendations.append(f"⚠️ Connection pool overflow detected ({pool_stats.get('overflow')} connections). " "Consider increasing pool size or optimizing connection usage.")

            active_conn = analysis.get("connection_info", {}).get("active_connections", 0)
            if active_conn > max_conn * 0.8:
                recommendations.append(f"⚠️ High connection usage ({active_conn}/{max_conn}). " "Monitor for connection leaks or consider connection pooling optimization.")

            # Index usage recommendations
            indexes = analysis.get("index_usage", [])
            unused_indexes = [idx for idx in indexes if idx.get("index_scans", 0) == 0]
            if unused_indexes:
                recommendations.append(f"📊 Found {len(unused_indexes)} potentially unused indexes. " "Consider removing them to improve write performance.")

            # Cache hit ratio recommendations
            cache_ratio = analysis.get("performance_metrics", {}).get("cache_hit_ratio", {})
            heap_ratio = cache_ratio.get("heap_cache_hit_ratio", 0)
            idx_ratio = cache_ratio.get("index_cache_hit_ratio", 0)

            if heap_ratio < 95:
                recommendations.append(".1f" "Consider increasing shared_buffers or optimizing query patterns.")

            if idx_ratio < 95:
                recommendations.append(".1f" "Consider increasing shared_buffers or creating better indexes.")

            # Query performance recommendations
            query_patterns = analysis.get("query_patterns", {})
            top_queries = query_patterns.get("top_queries", [])

            slow_queries = [q for q in top_queries if q.get("mean_time", 0) > 100]  # > 100ms
            if slow_queries:
                recommendations.append(f"🐌 Found {len(slow_queries)} slow queries (>100ms average). " "Consider query optimization or indexing.")

            # Database size recommendations
            db_size_bytes = analysis.get("performance_metrics", {}).get("database_size_bytes", 0)
            if db_size_bytes > 1_000_000_000:  # > 1GB
                recommendations.append(f"📏 Database size is {analysis.get('performance_metrics', {}).get('database_size', 'large')}. " "Consider archiving old data or implementing partitioning.")

        except Exception as e:
            logger.error(f"Failed to generate recommendations: {e}")
            recommendations.append("❌ Failed to generate recommendations due to analysis error.")

        if not recommendations:
            recommendations.append("✅ No immediate issues detected. Database appears to be running optimally.")

        return recommendations

    @staticmethod
    async def run_performance_test(duration_seconds: int = 30) -> Dict[str, Any]:
        """Run a basic performance test to measure database responsiveness."""
        results = {
            "test_duration": duration_seconds,
            "total_queries": 0,
            "successful_queries": 0,
            "failed_queries": 0,
            "avg_response_time": 0,
            "min_response_time": float("inf"),
            "max_response_time": 0,
            "response_times": [],
        }

        start_time = time.time()
        query_times = []

        try:
            async with AsyncSessionLocal() as session:
                end_time = start_time + duration_seconds

                while time.time() < end_time:
                    query_start = time.time()

                    try:
                        # Simple test query
                        await session.execute(text("SELECT 1"))
                        results["total_queries"] += 1
                        results["successful_queries"] += 1

                        query_time = (time.time() - query_start) * 1000  # Convert to ms
                        query_times.append(query_time)

                        results["min_response_time"] = min(results["min_response_time"], query_time)
                        results["max_response_time"] = max(results["max_response_time"], query_time)

                    except Exception as e:
                        results["total_queries"] += 1
                        results["failed_queries"] += 1
                        logger.warning(f"Query failed: {e}")

                    # Small delay to avoid overwhelming the database
                    await asyncio.sleep(0.01)

                if query_times:
                    results["avg_response_time"] = sum(query_times) / len(query_times)
                    results["response_times"] = query_times[:100]  # Keep first 100 samples

        except Exception as e:
            logger.error(f"Performance test failed: {e}")
            results["error"] = str(e)

        results["test_completed_at"] = datetime.now().isoformat()
        return results
