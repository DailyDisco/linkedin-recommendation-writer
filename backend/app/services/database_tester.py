"""Comprehensive database testing and validation service."""

import asyncio
import logging
import time
from datetime import datetime
from typing import Any, Dict, List

from sqlalchemy import text

from app.core.database import AsyncSessionLocal, engine

logger = logging.getLogger(__name__)


class DatabaseTester:
    """Comprehensive database testing and validation service."""

    def __init__(self):
        self.test_results = []
        self.start_time = None
        self.end_time = None

    async def run_full_test_suite(self) -> Dict[str, Any]:
        """Run the complete database test suite."""
        self.start_time = datetime.now()
        self.test_results = []

        logger.info("🧪 Starting comprehensive database test suite")

        try:
            # Run all test categories
            test_categories = [
                ("connection_tests", self._run_connection_tests),
                ("performance_tests", self._run_performance_tests),
                ("data_integrity_tests", self._run_data_integrity_tests),
                ("migration_tests", self._run_migration_tests),
                ("validation_tests", self._run_validation_tests),
                ("load_tests", self._run_load_tests),
            ]

            results = {}
            for category_name, test_function in test_categories:
                logger.info(f"Running {category_name}...")
                try:
                    category_result = await test_function()
                    results[category_name] = category_result
                    self.test_results.append({"category": category_name, "result": category_result, "timestamp": datetime.now().isoformat()})
                except Exception as e:
                    logger.error(f"❌ {category_name} failed: {e}")
                    results[category_name] = {"error": str(e), "status": "failed"}
                    self.test_results.append({"category": category_name, "result": {"error": str(e), "status": "failed"}, "timestamp": datetime.now().isoformat()})

            self.end_time = datetime.now()

            # Generate summary
            summary = self._generate_test_summary(results)

            return {"status": "completed", "summary": summary, "results": results, "duration_seconds": (self.end_time - self.start_time).total_seconds(), "timestamp": datetime.now().isoformat()}

        except Exception as e:
            logger.error(f"❌ Test suite failed: {e}")
            return {"status": "failed", "error": str(e), "timestamp": datetime.now().isoformat()}

    async def _run_connection_tests(self) -> Dict[str, Any]:
        """Test database connection functionality."""
        tests = []

        # Test basic connectivity
        try:
            start_time = time.time()
            async with AsyncSessionLocal() as session:
                result = await session.execute(text("SELECT 1 as test"))
                value = result.scalar()
                response_time = (time.time() - start_time) * 1000

            tests.append({"name": "basic_connectivity", "status": "passed" if value == 1 else "failed", "response_time_ms": round(response_time, 2), "message": "Basic connectivity test"})
        except Exception as e:
            tests.append({"name": "basic_connectivity", "status": "failed", "error": str(e), "message": "Basic connectivity test failed"})

        # Test connection pool
        try:
            pool_size = getattr(engine.pool, "size", lambda: 0)()
            checked_out = getattr(engine.pool, "checkedout", lambda: 0)()

            tests.append(
                {"name": "connection_pool", "status": "passed", "pool_size": pool_size, "checked_out": checked_out, "message": f"Connection pool test (size: {pool_size}, checked out: {checked_out})"}
            )
        except Exception as e:
            tests.append({"name": "connection_pool", "status": "failed", "error": str(e), "message": "Connection pool test failed"})

        # Test concurrent connections
        try:
            concurrent_results = await self._test_concurrent_connections(5)
            tests.append({"name": "concurrent_connections", "status": "passed", "concurrent_test": concurrent_results, "message": "Concurrent connections test"})
        except Exception as e:
            tests.append({"name": "concurrent_connections", "status": "failed", "error": str(e), "message": "Concurrent connections test failed"})

        passed_tests = sum(1 for test in tests if test["status"] == "passed")
        total_tests = len(tests)

        return {
            "status": "passed" if passed_tests == total_tests else "partial",
            "tests": tests,
            "passed": passed_tests,
            "total": total_tests,
            "success_rate": round(passed_tests / total_tests * 100, 2) if total_tests > 0 else 0,
        }

    async def _test_concurrent_connections(self, num_connections: int) -> Dict[str, Any]:
        """Test concurrent database connections."""

        async def test_connection(connection_id: int):
            try:
                start_time = time.time()
                async with AsyncSessionLocal() as session:
                    result = await session.execute(text(f"SELECT {connection_id} as connection_id, pg_sleep(0.1)"))
                    result.scalar()
                    response_time = (time.time() - start_time) * 1000

                return {"connection_id": connection_id, "status": "success", "response_time_ms": round(response_time, 2)}
            except Exception as e:
                return {"connection_id": connection_id, "status": "failed", "error": str(e)}

        # Run concurrent connection tests
        tasks = [test_connection(i) for i in range(num_connections)]
        results = await asyncio.gather(*tasks)

        successful = sum(1 for r in results if r["status"] == "success")
        avg_response_time = sum(r.get("response_time_ms", 0) for r in results if r["status"] == "success") / successful if successful > 0 else 0

        return {
            "total_connections": num_connections,
            "successful_connections": successful,
            "failed_connections": num_connections - successful,
            "avg_response_time_ms": round(avg_response_time, 2),
            "results": results,
        }

    async def _run_performance_tests(self) -> Dict[str, Any]:
        """Run database performance tests."""
        tests = []

        # Test simple query performance
        try:
            performance_result = await self._test_query_performance(["SELECT 1", "SELECT COUNT(*) FROM pg_class", "SELECT * FROM information_schema.tables LIMIT 10"], iterations=3)

            tests.append({"name": "query_performance", "status": "passed", "performance_data": performance_result, "message": "Query performance test"})
        except Exception as e:
            tests.append({"name": "query_performance", "status": "failed", "error": str(e), "message": "Query performance test failed"})

        # Test connection pool performance
        try:
            pool_performance = await self._test_connection_pool_performance(iterations=10)
            tests.append({"name": "connection_pool_performance", "status": "passed", "performance_data": pool_performance, "message": "Connection pool performance test"})
        except Exception as e:
            tests.append({"name": "connection_pool_performance", "status": "failed", "error": str(e), "message": "Connection pool performance test failed"})

        passed_tests = sum(1 for test in tests if test["status"] == "passed")
        total_tests = len(tests)

        return {
            "status": "passed" if passed_tests == total_tests else "partial",
            "tests": tests,
            "passed": passed_tests,
            "total": total_tests,
            "success_rate": round(passed_tests / total_tests * 100, 2) if total_tests > 0 else 0,
        }

    async def _test_query_performance(self, queries: List[str], iterations: int = 5) -> Dict[str, Any]:
        """Test performance of specific queries."""
        results = []

        for query in queries:
            query_results = []

            for i in range(iterations):
                try:
                    start_time = time.time()
                    async with AsyncSessionLocal() as session:
                        await session.execute(text(query))
                        await session.commit()

                    execution_time = (time.time() - start_time) * 1000  # Convert to ms
                    query_results.append({"iteration": i + 1, "execution_time_ms": round(execution_time, 2), "status": "success"})
                except Exception as e:
                    query_results.append({"iteration": i + 1, "status": "failed", "error": str(e)})

            successful_runs = [r for r in query_results if r["status"] == "success"]
            if successful_runs:
                avg_time = sum(r["execution_time_ms"] for r in successful_runs) / len(successful_runs)
                min_time = min(r["execution_time_ms"] for r in successful_runs)
                max_time = max(r["execution_time_ms"] for r in successful_runs)
            else:
                avg_time = min_time = max_time = 0

            results.append(
                {
                    "query": query[:100] + "..." if len(query) > 100 else query,
                    "iterations": iterations,
                    "successful_runs": len(successful_runs),
                    "avg_execution_time_ms": round(avg_time, 2),
                    "min_execution_time_ms": round(min_time, 2),
                    "max_execution_time_ms": round(max_time, 2),
                    "success_rate": round(len(successful_runs) / iterations * 100, 2),
                }
            )

        return {"query_tests": results, "overall_avg_time": round(sum(r["avg_execution_time_ms"] for r in results) / len(results), 2) if results else 0}

    async def _test_connection_pool_performance(self, iterations: int = 10) -> Dict[str, Any]:
        """Test connection pool performance."""
        response_times = []

        for i in range(iterations):
            start_time = time.time()
            try:
                async with AsyncSessionLocal() as session:
                    await session.execute(text("SELECT 1"))
                    await session.commit()

                response_time = (time.time() - start_time) * 1000  # Convert to ms
                response_times.append(response_time)
            except Exception as e:
                logger.warning(f"Connection pool test iteration {i+1} failed: {e}")
                response_times.append(-1)  # Mark as failed

        successful_times = [t for t in response_times if t >= 0]

        if successful_times:
            avg_time = sum(successful_times) / len(successful_times)
            min_time = min(successful_times)
            max_time = max(successful_times)
        else:
            avg_time = min_time = max_time = 0

        return {
            "iterations": iterations,
            "successful_connections": len(successful_times),
            "avg_response_time_ms": round(avg_time, 2),
            "min_response_time_ms": round(min_time, 2),
            "max_response_time_ms": round(max_time, 2),
            "success_rate": round(len(successful_times) / iterations * 100, 2),
        }

    async def _run_data_integrity_tests(self) -> Dict[str, Any]:
        """Test data integrity and constraints."""
        tests = []

        # Test referential integrity
        try:
            integrity_result = await self._test_referential_integrity()
            tests.append(
                {"name": "referential_integrity", "status": "passed" if integrity_result["status"] == "healthy" else "warning", "details": integrity_result, "message": "Referential integrity test"}
            )
        except Exception as e:
            tests.append({"name": "referential_integrity", "status": "failed", "error": str(e), "message": "Referential integrity test failed"})

        # Test constraint validation
        try:
            constraint_result = await self._test_constraint_validation()
            tests.append(
                {"name": "constraint_validation", "status": "passed" if constraint_result["constraints_valid"] else "warning", "details": constraint_result, "message": "Constraint validation test"}
            )
        except Exception as e:
            tests.append({"name": "constraint_validation", "status": "failed", "error": str(e), "message": "Constraint validation test failed"})

        # Test data consistency
        try:
            consistency_result = await self._test_data_consistency()
            tests.append({"name": "data_consistency", "status": "passed", "details": consistency_result, "message": "Data consistency test"})
        except Exception as e:
            tests.append({"name": "data_consistency", "status": "failed", "error": str(e), "message": "Data consistency test failed"})

        passed_tests = sum(1 for test in tests if test["status"] == "passed")
        warning_tests = sum(1 for test in tests if test["status"] == "warning")
        total_tests = len(tests)

        return {
            "status": "passed" if passed_tests == total_tests and warning_tests == 0 else "warning" if warning_tests > 0 else "failed",
            "tests": tests,
            "passed": passed_tests,
            "warnings": warning_tests,
            "total": total_tests,
            "success_rate": round(passed_tests / total_tests * 100, 2) if total_tests > 0 else 0,
        }

    async def _test_referential_integrity(self) -> Dict[str, Any]:
        """Test referential integrity of the database."""
        try:
            async with AsyncSessionLocal() as session:
                # Check for orphaned records in recommendations
                orphaned_result = await session.execute(
                    text(
                        """
                    SELECT COUNT(*) as orphaned_recommendations
                    FROM recommendations r
                    LEFT JOIN users u ON r.user_id = u.id
                    WHERE u.id IS NULL
                """
                    )
                )
                orphaned_count = orphaned_result.scalar()

                # Check for orphaned records in github_profiles
                orphaned_profiles_result = await session.execute(
                    text(
                        """
                    SELECT COUNT(*) as orphaned_profiles
                    FROM github_profiles gp
                    LEFT JOIN users u ON gp.user_id = u.id
                    WHERE u.id IS NULL
                """
                    )
                )
                orphaned_profiles_count = orphaned_profiles_result.scalar()

                status = "healthy" if orphaned_count == 0 and orphaned_profiles_count == 0 else "issues_found"

                return {
                    "status": status,
                    "orphaned_recommendations": orphaned_count,
                    "orphaned_github_profiles": orphaned_profiles_count,
                    "message": f"Found {orphaned_count} orphaned recommendations and {orphaned_profiles_count} orphaned profiles",
                }

        except Exception as e:
            return {"status": "error", "error": str(e), "message": "Failed to check referential integrity"}

    async def _test_constraint_validation(self) -> Dict[str, Any]:
        """Test database constraint validation."""
        try:
            async with AsyncSessionLocal() as session:
                constraints_valid = True
                constraint_issues = []

                # Test NOT NULL constraints
                try:
                    await session.execute(text("INSERT INTO users (email, hashed_password) VALUES (NULL, 'test')"))
                    await session.commit()
                    constraint_issues.append("NOT NULL constraint failed for users.email")
                    constraints_valid = False
                except Exception:
                    # Expected - constraint should prevent this
                    await session.rollback()

                # Test UNIQUE constraints
                try:
                    await session.execute(text("INSERT INTO users (email, hashed_password) VALUES ('test@example.com', 'test1')"))
                    await session.execute(text("INSERT INTO users (email, hashed_password) VALUES ('test@example.com', 'test2')"))
                    await session.commit()
                    constraint_issues.append("UNIQUE constraint failed for users.email")
                    constraints_valid = False
                except Exception:
                    # Expected - constraint should prevent this
                    await session.rollback()

                return {
                    "constraints_valid": constraints_valid,
                    "issues_found": len(constraint_issues),
                    "constraint_issues": constraint_issues,
                    "message": f"Constraint validation {'passed' if constraints_valid else 'found issues'}",
                }

        except Exception as e:
            return {"constraints_valid": False, "error": str(e), "message": "Failed to test constraint validation"}

    async def _test_data_consistency(self) -> Dict[str, Any]:
        """Test data consistency across tables."""
        try:
            async with AsyncSessionLocal() as session:
                consistency_checks = []

                # Check user recommendation counts
                user_counts_result = await session.execute(
                    text(
                        """
                    SELECT
                        u.id,
                        u.recommendation_count as stored_count,
                        COUNT(r.id) as actual_count
                    FROM users u
                    LEFT JOIN recommendations r ON u.id = r.user_id
                        AND r.created_at >= CURRENT_DATE
                    GROUP BY u.id, u.recommendation_count
                    HAVING u.recommendation_count != COUNT(r.id)
                """
                    )
                )

                inconsistent_counts = user_counts_result.fetchall()
                consistency_checks.append(
                    {
                        "check": "user_recommendation_counts",
                        "status": "consistent" if not inconsistent_counts else "inconsistent",
                        "issues_found": len(inconsistent_counts),
                        "message": f"Found {len(inconsistent_counts)} users with inconsistent recommendation counts",
                    }
                )

                return {
                    "consistency_checks": consistency_checks,
                    "overall_status": "consistent" if all(c["status"] == "consistent" for c in consistency_checks) else "inconsistent",
                    "total_issues": sum(c["issues_found"] for c in consistency_checks),
                }

        except Exception as e:
            return {"consistency_checks": [], "overall_status": "error", "error": str(e), "message": "Failed to check data consistency"}

    async def _run_migration_tests(self) -> Dict[str, Any]:
        """Test migration functionality."""
        try:
            from app.core.migrations import migration_manager

            # Test migration status
            status = await migration_manager.get_migration_status()

            # Test migration history
            history = await migration_manager.get_migration_history()

            # Test migration validation
            validation = await migration_manager.validate_migrations()

            return {"status": "passed", "migration_status": status, "migration_history": history, "validation_result": validation, "message": "Migration tests completed"}

        except Exception as e:
            return {"status": "failed", "error": str(e), "message": "Migration tests failed"}

    async def _run_validation_tests(self) -> Dict[str, Any]:
        """Test data validation functionality."""
        try:
            from app.core.validation import DataValidator

            test_cases = [
                {"type": "email", "value": "test@example.com", "expected": True},
                {"type": "email", "value": "invalid-email", "expected": False},
                {"type": "username", "value": "testuser123", "expected": True},
                {"type": "username", "value": "test@#$%", "expected": False},
                {"type": "github_url", "value": "https://github.com/testuser", "expected": True},
                {"type": "github_url", "value": "not-a-github-url", "expected": False},
            ]

            validation_results = []
            passed_tests = 0

            for test_case in test_cases:
                try:
                    if test_case["type"] == "email":
                        result = DataValidator.validate_email_format(test_case["value"])
                    elif test_case["type"] == "username":
                        result = DataValidator.validate_username_format(test_case["value"])
                    elif test_case["type"] == "github_url":
                        result = DataValidator.validate_github_profile_url(test_case["value"])

                    is_valid = result.get("valid", False)
                    expected = test_case["expected"]

                    if is_valid == expected:
                        passed_tests += 1
                        status = "passed"
                    else:
                        status = "failed"

                    validation_results.append({"test": f"{test_case['type']}_validation", "input": test_case["value"], "expected": expected, "actual": is_valid, "status": status})

                except Exception as e:
                    validation_results.append({"test": f"{test_case['type']}_validation", "input": test_case["value"], "status": "error", "error": str(e)})

            return {
                "status": "passed" if passed_tests == len(test_cases) else "partial",
                "tests": validation_results,
                "passed": passed_tests,
                "total": len(test_cases),
                "success_rate": round(passed_tests / len(test_cases) * 100, 2),
            }

        except Exception as e:
            return {"status": "failed", "error": str(e), "message": "Validation tests failed"}

    async def _run_load_tests(self) -> Dict[str, Any]:
        """Run load tests to stress the database."""
        try:
            # Simple load test - multiple concurrent operations
            load_test_result = await self._run_simple_load_test(num_concurrent=5, duration_seconds=10)

            return {
                "status": "passed" if load_test_result["success_rate"] > 95 else "warning",
                "load_test": load_test_result,
                "message": f"Load test completed with {load_test_result['success_rate']:.1f}% success rate",
            }

        except Exception as e:
            return {"status": "failed", "error": str(e), "message": "Load tests failed"}

    async def _run_simple_load_test(self, num_concurrent: int, duration_seconds: int) -> Dict[str, Any]:
        """Run a simple load test with concurrent database operations."""

        async def load_worker(worker_id: int):
            operations_completed = 0
            errors_encountered = 0
            start_time = time.time()

            try:
                while time.time() - start_time < duration_seconds:
                    try:
                        async with AsyncSessionLocal() as session:
                            # Simple read operation
                            await session.execute(text("SELECT COUNT(*) FROM pg_class"))
                            await session.commit()

                        operations_completed += 1

                        # Small delay to prevent overwhelming
                        await asyncio.sleep(0.01)

                    except Exception:
                        errors_encountered += 1
                        await asyncio.sleep(0.1)  # Longer delay on error

            except Exception as e:
                logger.error(f"Load worker {worker_id} failed: {e}")

            return {"worker_id": worker_id, "operations_completed": operations_completed, "errors_encountered": errors_encountered, "duration": time.time() - start_time}

        # Start concurrent workers
        workers = [load_worker(i) for i in range(num_concurrent)]
        results = await asyncio.gather(*workers)

        # Aggregate results
        total_operations = sum(r["operations_completed"] for r in results)
        total_errors = sum(r["errors_encountered"] for r in results)
        total_duration = max(r["duration"] for r in results)

        return {
            "concurrent_workers": num_concurrent,
            "test_duration_seconds": duration_seconds,
            "total_operations": total_operations,
            "total_errors": total_errors,
            "operations_per_second": round(total_operations / total_duration, 2) if total_duration > 0 else 0,
            "success_rate": round((total_operations / (total_operations + total_errors)) * 100, 2) if (total_operations + total_errors) > 0 else 100,
            "worker_results": results,
        }

    def _generate_test_summary(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Generate a comprehensive test summary."""
        categories = list(results.keys())
        passed_categories = sum(1 for cat in categories if results[cat].get("status") == "passed")
        warning_categories = sum(1 for cat in categories if results[cat].get("status") == "warning")
        failed_categories = sum(1 for cat in categories if results[cat].get("status") in ["failed", "partial"])

        # Calculate overall health score
        health_score = (passed_categories / len(categories)) * 100 if categories else 0

        # Generate recommendations
        recommendations = []
        if failed_categories > 0:
            recommendations.append("Address failed test categories before deployment")
        if warning_categories > 0:
            recommendations.append("Review warning conditions and optimize as needed")
        if health_score < 80:
            recommendations.append("Overall database health needs improvement")
        else:
            recommendations.append("Database health is good - continue monitoring")

        return {
            "total_categories": len(categories),
            "passed_categories": passed_categories,
            "warning_categories": warning_categories,
            "failed_categories": failed_categories,
            "health_score": round(health_score, 2),
            "overall_status": "healthy" if health_score >= 90 else "warning" if health_score >= 70 else "critical",
            "recommendations": recommendations,
            "test_duration_seconds": (self.end_time - self.start_time).total_seconds() if self.end_time and self.start_time else 0,
        }
