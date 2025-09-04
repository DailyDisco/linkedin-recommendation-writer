"""Database optimization and performance monitoring utilities."""

import logging
import time
from typing import Any, Dict, List

from sqlalchemy import text

from app.core.database import AsyncSessionLocal, engine

logger = logging.getLogger(__name__)


class DatabaseOptimizer:
    """Database optimization and performance monitoring utilities."""

    @staticmethod
    async def analyze_query_performance() -> Dict[str, Any]:
        """Analyze query performance and suggest optimizations."""
        try:
            async with AsyncSessionLocal() as session:
                # Get slow queries (if pg_stat_statements is available)
                try:
                    extension_check = await session.execute(
                        text(
                            """
                        SELECT count(*) FROM pg_extension WHERE extname = 'pg_stat_statements'
                    """
                        )
                    )

                    if extension_check.scalar() > 0:
                        slow_queries = await session.execute(
                            text(
                                """
                            SELECT
                                query,
                                calls,
                                total_time,
                                mean_time,
                                rows
                            FROM pg_stat_statements
                            WHERE mean_time > 100  -- queries taking > 100ms on average
                            AND query NOT LIKE '%pg_stat_statements%'
                            ORDER BY mean_time DESC
                            LIMIT 20
                        """
                            )
                        )

                        slow_query_list = []
                        for row in slow_queries:
                            slow_query_list.append(
                                {
                                    "query": row[0][:200] + "..." if len(row[0]) > 200 else row[0],
                                    "calls": row[1],
                                    "total_time": row[2],
                                    "mean_time": row[3],
                                    "rows_returned": row[4],
                                    "efficiency": row[4] / row[1] if row[1] > 0 else 0,  # rows per call
                                }
                            )

                        return {"slow_queries_found": len(slow_query_list), "slow_queries": slow_query_list, "recommendations": DatabaseOptimizer._generate_query_optimizations(slow_query_list)}
                    else:
                        return {
                            "note": "pg_stat_statements extension not available for detailed query analysis",
                            "slow_queries_found": 0,
                            "slow_queries": [],
                            "recommendations": ["Install pg_stat_statements extension for detailed query analysis"],
                        }

                except Exception as e:
                    logger.warning(f"Query performance analysis failed: {e}")
                    return {"error": f"Failed to analyze query performance: {str(e)}"}

        except Exception as e:
            logger.error(f"Database optimization analysis failed: {e}")
            return {"error": str(e)}

    @staticmethod
    def _generate_query_optimizations(slow_queries: List[Dict[str, Any]]) -> List[str]:
        """Generate optimization recommendations based on slow queries."""
        recommendations = []

        for query_info in slow_queries:
            query = query_info.get("query", "").lower()

            # Check for common optimization opportunities
            if "select *" in query:
                recommendations.append("Consider selecting only required columns instead of SELECT *")

            if "like" in query and "%" in query:
                recommendations.append("Consider using full-text search or trigram indexes for LIKE queries with wildcards")

            if "order by" in query and "limit" not in query:
                recommendations.append("Consider adding LIMIT to ORDER BY queries for better performance")

            if "join" in query and "index" not in query_info.get("query", "").lower():
                recommendations.append("Review JOIN operations - ensure foreign keys have indexes")

            if query_info.get("efficiency", 0) < 1:
                recommendations.append("Query returns less than 1 row per call - consider if it's needed")

        # Remove duplicates and add general recommendations
        recommendations = list(set(recommendations))

        if not recommendations:
            recommendations.append("No specific optimization opportunities identified")

        # Add general recommendations
        general_recs = [
            "Consider adding appropriate indexes for frequently queried columns",
            "Review and optimize complex JOIN operations",
            "Consider query result caching for frequently accessed data",
            "Monitor database connection pool usage",
            "Consider partitioning large tables if applicable",
        ]

        recommendations.extend(general_recs)
        return recommendations[:10]  # Limit to top 10 recommendations

    @staticmethod
    async def analyze_index_usage() -> Dict[str, Any]:
        """Analyze index usage and identify unused or missing indexes."""
        try:
            async with AsyncSessionLocal() as session:
                # Get index usage statistics
                index_stats = await session.execute(
                    text(
                        """
                    SELECT
                        schemaname,
                        tablename,
                        indexname,
                        idx_scan,
                        idx_tup_read,
                        idx_tup_fetch,
                        pg_size_pretty(pg_relation_size(indexrelid)) as size
                    FROM pg_stat_user_indexes
                    WHERE schemaname = 'public'
                    ORDER BY idx_scan DESC
                """
                    )
                )

                indexes = []
                unused_indexes = []
                total_indexes = 0

                for row in index_stats:
                    index_info = {"schema": row[0], "table": row[1], "index_name": row[2], "scans": row[3], "tuples_read": row[4], "tuples_fetched": row[5], "size": row[6]}

                    indexes.append(index_info)
                    total_indexes += 1

                    # Consider index unused if it has 0 scans
                    if row[3] == 0:
                        unused_indexes.append(index_info)

                # Get table statistics for missing index recommendations
                table_stats = await session.execute(
                    text(
                        """
                    SELECT
                        schemaname,
                        tablename,
                        n_tup_ins,
                        n_tup_upd,
                        n_tup_del,
                        seq_scan,
                        idx_scan
                    FROM pg_stat_user_tables
                    WHERE schemaname = 'public'
                    ORDER BY n_tup_ins + n_tup_upd + n_tup_del DESC
                """
                    )
                )

                tables_needing_indexes = []
                for row in table_stats:
                    total_operations = row[2] + row[3] + row[4]  # inserts + updates + deletes
                    seq_scans = row[5]
                    idx_scans = row[6]

                    # If table has many sequential scans and few index scans, might need indexes
                    if seq_scans > idx_scans and total_operations > 1000:
                        tables_needing_indexes.append(
                            {"table": row[1], "total_operations": total_operations, "seq_scans": seq_scans, "idx_scans": idx_scans, "scan_ratio": seq_scans / (idx_scans + 1)}  # Avoid division by zero
                        )

                return {
                    "total_indexes": total_indexes,
                    "unused_indexes": len(unused_indexes),
                    "unused_index_list": unused_indexes[:10],  # Top 10 unused
                    "tables_needing_indexes": tables_needing_indexes[:5],  # Top 5 candidates
                    "index_usage_efficiency": DatabaseOptimizer._calculate_index_efficiency(indexes),
                    "recommendations": DatabaseOptimizer._generate_index_recommendations(unused_indexes, tables_needing_indexes),
                }

        except Exception as e:
            logger.error(f"Index usage analysis failed: {e}")
            return {"error": str(e)}

    @staticmethod
    def _calculate_index_efficiency(indexes: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate index usage efficiency metrics."""
        if not indexes:
            return {"efficiency_score": 0, "usage_distribution": {}}

        total_scans = sum(idx.get("scans", 0) for idx in indexes)
        used_indexes = [idx for idx in indexes if idx.get("scans", 0) > 0]

        efficiency_score = len(used_indexes) / len(indexes) * 100 if indexes else 0

        # Categorize index usage
        usage_distribution = {
            "heavily_used": len([idx for idx in indexes if idx.get("scans", 0) > 1000]),
            "moderately_used": len([idx for idx in indexes if 100 < idx.get("scans", 0) <= 1000]),
            "lightly_used": len([idx for idx in indexes if 0 < idx.get("scans", 0) <= 100]),
            "unused": len([idx for idx in indexes if idx.get("scans", 0) == 0]),
        }

        return {"efficiency_score": round(efficiency_score, 2), "total_scans": total_scans, "used_indexes": len(used_indexes), "usage_distribution": usage_distribution}

    @staticmethod
    def _generate_index_recommendations(unused_indexes: List[Dict[str, Any]], tables_needing_indexes: List[Dict[str, Any]]) -> List[str]:
        """Generate index optimization recommendations."""
        recommendations = []

        # Recommendations for unused indexes
        if unused_indexes:
            recommendations.append(f"Consider removing {len(unused_indexes)} unused indexes to improve write performance")

        # Recommendations for missing indexes
        if tables_needing_indexes:
            recommendations.append(f"Consider adding indexes to {len(tables_needing_indexes)} tables with high sequential scan ratios")

        # Specific recommendations
        if len(unused_indexes) > len(tables_needing_indexes):
            recommendations.append("Focus on removing unused indexes before adding new ones")
        elif tables_needing_indexes:
            recommendations.append("Add indexes on frequently queried columns to improve read performance")

        # General recommendations
        general_recs = [
            "Regularly review index usage statistics",
            "Consider composite indexes for multi-column WHERE clauses",
            "Monitor index bloat and rebuild when necessary",
            "Use partial indexes for filtered queries",
            "Consider index-only scans for covering indexes",
        ]

        recommendations.extend(general_recs)
        return recommendations[:8]  # Limit recommendations

    @staticmethod
    async def analyze_connection_pool() -> Dict[str, Any]:
        """Analyze connection pool usage and provide optimization recommendations."""
        try:
            pool_stats = {
                "pool_size": getattr(engine.pool, "size", lambda: 0)(),
                "checked_out": getattr(engine.pool, "checkedout", lambda: 0)(),
                "overflow": getattr(engine.pool, "overflow", lambda: 0)(),
                "checked_in": getattr(engine.pool, "checkedin", lambda: 0)(),
                "invalid": getattr(engine.pool, "invalid", lambda: 0)(),
            }

            # Calculate pool utilization
            utilization_rate = (pool_stats["checked_out"] / pool_stats["pool_size"] * 100) if pool_stats["pool_size"] > 0 else 0

            # Get database connection statistics
            async with AsyncSessionLocal() as session:
                db_connections = await session.execute(
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

                conn_row = db_connections.first()
                db_connection_stats = {
                    "total_connections": conn_row[0] if conn_row else 0,
                    "active_connections": conn_row[1] if conn_row else 0,
                    "idle_connections": conn_row[2] if conn_row else 0,
                    "idle_in_transaction": conn_row[3] if conn_row else 0,
                }

            # Generate recommendations
            recommendations = []

            if utilization_rate > 80:
                recommendations.append("High connection pool utilization - consider increasing pool size")
            elif utilization_rate < 20:
                recommendations.append("Low connection pool utilization - consider reducing pool size")

            if pool_stats["overflow"] > 0:
                recommendations.append("Connection pool overflow detected - review connection usage patterns")

            idle_in_transaction = db_connection_stats.get("idle_in_transaction", 0)
            if idle_in_transaction > 0:
                recommendations.append(f"Found {idle_in_transaction} connections idle in transaction - review transaction handling")

            if not recommendations:
                recommendations.append("Connection pool configuration appears optimal")

            return {
                "pool_statistics": pool_stats,
                "db_connection_statistics": db_connection_stats,
                "utilization_rate": round(utilization_rate, 2),
                "pool_health_score": DatabaseOptimizer._calculate_pool_health_score(pool_stats, utilization_rate),
                "recommendations": recommendations,
            }

        except Exception as e:
            logger.error(f"Connection pool analysis failed: {e}")
            return {"error": str(e)}

    @staticmethod
    def _calculate_pool_health_score(pool_stats: Dict[str, Any], utilization_rate: float) -> int:
        """Calculate a health score for the connection pool (0-100)."""
        score = 100

        # Penalize high utilization
        if utilization_rate > 90:
            score -= 30
        elif utilization_rate > 80:
            score -= 15

        # Penalize overflow
        if pool_stats.get("overflow", 0) > 0:
            score -= 20

        # Penalize invalid connections
        if pool_stats.get("invalid", 0) > 0:
            score -= 10

        return max(0, score)

    @staticmethod
    async def optimize_connection_pool() -> Dict[str, Any]:
        """Provide connection pool optimization recommendations."""
        try:
            analysis = await DatabaseOptimizer.analyze_connection_pool()
            pool_stats = analysis.get("pool_statistics", {})
            utilization = analysis.get("utilization_rate", 0)

            optimizations = []

            # Pool size optimization
            current_size = pool_stats.get("pool_size", 10)
            if utilization > 80:
                recommended_size = int(current_size * 1.5)
                optimizations.append(f"Increase pool size from {current_size} to {recommended_size}")
            elif utilization < 30 and current_size > 5:
                recommended_size = max(5, int(current_size * 0.8))
                optimizations.append(f"Decrease pool size from {current_size} to {recommended_size}")

            # Connection timeout optimization
            if pool_stats.get("overflow", 0) > 0:
                optimizations.append("Consider increasing connection timeout to reduce overflow")

            # Connection recycling
            optimizations.append("Enable connection recycling for long-running applications")

            return {"current_configuration": pool_stats, "utilization_rate": utilization, "optimizations": optimizations, "expected_improvement": "Better connection availability and reduced latency"}

        except Exception as e:
            logger.error(f"Connection pool optimization failed: {e}")
            return {"error": str(e)}

    @staticmethod
    async def run_performance_test(queries: List[str], iterations: int = 10) -> Dict[str, Any]:
        """Run performance tests on specific queries."""
        results = []

        for query in queries:
            query_results = {
                "query": query[:100] + "..." if len(query) > 100 else query,
                "iterations": iterations,
                "execution_times": [],
                "min_time": float("inf"),
                "max_time": float("inf"),
                "avg_time": 0,
                "total_time": 0,
            }

            for i in range(iterations):
                try:
                    start_time = time.time()

                    async with AsyncSessionLocal() as session:
                        await session.execute(text(query))
                        await session.commit()

                    execution_time = (time.time() - start_time) * 1000  # Convert to ms
                    query_results["execution_times"].append(execution_time)
                    query_results["min_time"] = min(query_results["min_time"], execution_time)
                    query_results["max_time"] = max(query_results["max_time"], execution_time)
                    query_results["total_time"] += execution_time

                except Exception as e:
                    logger.error(f"Query performance test failed for query {i+1}: {e}")
                    query_results["execution_times"].append(-1)  # Mark as failed

            if query_results["execution_times"]:
                successful_times = [t for t in query_results["execution_times"] if t >= 0]
                if successful_times:
                    query_results["avg_time"] = sum(successful_times) / len(successful_times)
                    query_results["success_rate"] = len(successful_times) / iterations * 100

            results.append(query_results)

        return {
            "test_results": results,
            "summary": {
                "total_queries_tested": len(results),
                "avg_execution_time": sum(r["avg_time"] for r in results if r["avg_time"] > 0) / len([r for r in results if r["avg_time"] > 0]) if results else 0,
                "fastest_query": min((r for r in results if r["min_time"] < float("inf")), key=lambda x: x["min_time"], default=None),
                "slowest_query": max((r for r in results if r["max_time"] < float("inf")), key=lambda x: x["max_time"], default=None),
            },
        }

    @staticmethod
    async def create_recommended_indexes() -> Dict[str, Any]:
        """Analyze and recommend indexes to create."""
        try:
            async with AsyncSessionLocal() as session:
                # Find tables with high sequential scan ratios
                candidates = await session.execute(
                    text(
                        """
                    SELECT
                        schemaname,
                        tablename,
                        seq_scan,
                        idx_scan,
                        n_tup_ins + n_tup_upd + n_tup_del as write_operations
                    FROM pg_stat_user_tables
                    WHERE schemaname = 'public'
                    AND seq_scan > idx_scan * 5  -- Much more sequential than index scans
                    AND n_tup_ins + n_tup_upd + n_tup_del > 1000  -- Significant write load
                    ORDER BY seq_scan DESC
                    LIMIT 5
                """
                    )
                )

                recommendations = []
                for row in candidates:
                    table_name = row[1]
                    seq_scans = row[2]
                    idx_scans = row[3]
                    write_ops = row[4]

                    # Get most queried columns for this table (simplified approach)
                    columns_result = await session.execute(
                        text(
                            f"""
                        SELECT
                            attname,
                            n_distinct
                        FROM pg_stats
                        WHERE schemaname = 'public'
                        AND tablename = '{table_name}'
                        AND n_distinct > 0
                        ORDER BY n_distinct DESC
                        LIMIT 3
                    """
                        )
                    )

                    suggested_columns = [col[0] for col in columns_result]

                    recommendations.append(
                        {
                            "table": table_name,
                            "seq_scans": seq_scans,
                            "idx_scans": idx_scans,
                            "write_operations": write_ops,
                            "suggested_index_columns": suggested_columns,
                            "index_type": "btree",  # Most common
                            "estimated_benefit": "high" if seq_scans > idx_scans * 10 else "medium",
                        }
                    )

                return {
                    "recommended_indexes": recommendations,
                    "implementation_notes": [
                        "Create indexes during low-traffic periods",
                        "Monitor index usage after creation",
                        "Consider composite indexes for multiple WHERE conditions",
                        "Balance read performance gains with write performance costs",
                    ],
                }

        except Exception as e:
            logger.error(f"Index recommendation failed: {e}")
            return {"error": str(e)}
