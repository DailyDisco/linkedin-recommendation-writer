"""Database security enhancements and query protection."""

import asyncio
import logging
import re
from contextlib import asynccontextmanager
from typing import Dict, List, Optional, Tuple

from sqlalchemy.exc import SQLAlchemyError

from app.core.config import settings

logger = logging.getLogger(__name__)


class DatabaseSecurityMonitor:
    """Monitor and secure database operations."""

    def __init__(self):
        self.query_log = []
        self.suspicious_patterns = [
            r";\s*DROP\s+TABLE",  # DROP TABLE statements
            r";\s*DELETE\s+FROM",  # DELETE statements
            r";\s*UPDATE\s+.*SET.*=",  # UPDATE statements
            r";\s*INSERT\s+INTO",  # INSERT statements
            r"UNION\s+SELECT",  # UNION-based injection
            r"--",  # SQL comments
            r"/\*.*\*/",  # Multi-line comments
            r";\s*EXEC",  # EXEC statements
            r";\s*EXECUTE",  # EXECUTE statements
        ]

        self.allowed_tables = ["users", "recommendations", "github_profiles", "user_sessions", "api_usage_logs", "rate_limits"]

    async def log_query(self, query: str, params: Optional[Dict] = None, execution_time: Optional[float] = None):
        """Log database query with security analysis."""
        # Analyze query for suspicious patterns
        security_analysis = self._analyze_query_security(query)

        log_entry = {
            "query": query[:500],  # Truncate long queries
            "params": str(params)[:200] if params else None,
            "execution_time": execution_time,
            "security_analysis": security_analysis,
            "timestamp": asyncio.get_event_loop().time(),
        }

        self.query_log.append(log_entry)

        # Keep only last 1000 queries
        if len(self.query_log) > 1000:
            self.query_log = self.query_log[-1000:]

        # Log suspicious queries
        if security_analysis["risk_level"] in ["high", "critical"]:
            logger.warning(f"🚨 Suspicious database query detected: {security_analysis}")

    def _analyze_query_security(self, query: str) -> Dict:
        """Analyze query for security issues."""
        analysis = {"risk_level": "low", "issues": [], "recommendations": []}

        # Check for suspicious patterns
        for pattern in self.suspicious_patterns:
            if re.search(pattern, query, re.IGNORECASE):
                analysis["issues"].append(f"Suspicious pattern detected: {pattern}")
                analysis["risk_level"] = "high"

        # Check for potential SQL injection indicators
        if "'" in query and "--" not in query:  # Allow comments
            analysis["issues"].append("Potential SQL injection indicator (single quotes)")

        # Check for multiple statements
        if ";" in query and query.count(";") > 1:
            analysis["issues"].append("Multiple statements in single query")
            analysis["risk_level"] = "medium"

        # Check for dangerous keywords
        dangerous_keywords = ["DROP", "DELETE", "UPDATE", "INSERT", "ALTER", "CREATE"]
        for keyword in dangerous_keywords:
            if re.search(r"\b" + keyword + r"\b", query.upper()):
                analysis["issues"].append(f"Dangerous keyword: {keyword}")
                if analysis["risk_level"] == "low":
                    analysis["risk_level"] = "medium"

        # Set critical risk for high-risk operations
        if any(issue for issue in analysis["issues"] if "DROP" in issue):
            analysis["risk_level"] = "critical"

        # Generate recommendations
        if analysis["issues"]:
            analysis["recommendations"].append("Use parameterized queries")
            analysis["recommendations"].append("Validate input data")
            analysis["recommendations"].append("Use stored procedures for complex operations")

        return analysis

    def get_security_report(self) -> Dict:
        """Generate a security report from logged queries."""
        if not self.query_log:
            return {"status": "no_data"}

        total_queries = len(self.query_log)
        risk_counts = {"low": 0, "medium": 0, "high": 0, "critical": 0}

        for entry in self.query_log:
            risk_level = entry["security_analysis"]["risk_level"]
            risk_counts[risk_level] += 1

        return {
            "total_queries": total_queries,
            "risk_distribution": risk_counts,
            "high_risk_queries": [entry for entry in self.query_log[-100:] if entry["security_analysis"]["risk_level"] in ["high", "critical"]],  # Last 100 queries
            "average_execution_time": (
                sum(entry["execution_time"] for entry in self.query_log if entry["execution_time"] is not None) / len([e for e in self.query_log if e["execution_time"] is not None])
                if self.query_log
                else 0
            ),
        }


class SecureQueryBuilder:
    """Build secure database queries with validation."""

    def __init__(self, allowed_tables: Optional[List[str]] = None):
        self.allowed_tables = allowed_tables or ["users", "recommendations", "github_profiles", "user_sessions", "api_usage_logs", "rate_limits"]

    def build_select_query(self, table: str, columns: List[str] = None, where_clause: str = None, order_by: str = None, limit: int = None) -> Tuple[str, Dict]:
        """Build a secure SELECT query."""
        if table not in self.allowed_tables:
            raise ValueError(f"Access to table '{table}' is not allowed")

        if not columns:
            columns = ["*"]
        else:
            # Validate column names (basic check)
            for col in columns:
                if not re.match(r"^[a-zA-Z_][a-zA-Z0-9_]*$", col):
                    raise ValueError(f"Invalid column name: {col}")

        query = f"SELECT {', '.join(columns)} FROM {table}"

        params = {}

        if where_clause:
            query += f" WHERE {where_clause}"

        if order_by:
            query += f" ORDER BY {order_by}"

        if limit:
            if not isinstance(limit, int) or limit < 1 or limit > 1000:
                raise ValueError("Invalid limit value")
            query += f" LIMIT {limit}"

        return query, params

    def build_insert_query(self, table: str, data: Dict) -> Tuple[str, Dict]:
        """Build a secure INSERT query."""
        if table not in self.allowed_tables:
            raise ValueError(f"Access to table '{table}' is not allowed")

        if not data:
            raise ValueError("No data provided for insert")

        columns = list(data.keys())
        placeholders = [f":{col}" for col in columns]

        # Validate column names
        for col in columns:
            if not re.match(r"^[a-zA-Z_][a-zA-Z0-9_]*$", col):
                raise ValueError(f"Invalid column name: {col}")

        query = f"INSERT INTO {table} ({', '.join(columns)}) VALUES ({', '.join(placeholders)})"
        return query, data

    def build_update_query(self, table: str, data: Dict, where_clause: str) -> Tuple[str, Dict]:
        """Build a secure UPDATE query."""
        if table not in self.allowed_tables:
            raise ValueError(f"Access to table '{table}' is not allowed")

        if not data:
            raise ValueError("No data provided for update")

        if not where_clause:
            raise ValueError("WHERE clause is required for UPDATE operations")

        columns = list(data.keys())
        set_clause = ", ".join([f"{col} = :{col}" for col in columns])

        # Validate column names
        for col in columns:
            if not re.match(r"^[a-zA-Z_][a-zA-Z0-9_]*$", col):
                raise ValueError(f"Invalid column name: {col}")

        query = f"UPDATE {table} SET {set_clause} WHERE {where_clause}"
        return query, data


class DatabaseConnectionPoolMonitor:
    """Monitor database connection pool health and security."""

    def __init__(self):
        self.connection_attempts = 0
        self.failed_connections = 0
        self.active_connections = 0
        self.connection_pool_size = getattr(settings, "DATABASE_POOL_SIZE", 10)

    async def monitor_connection_health(self) -> Dict:
        """Monitor database connection pool health."""
        return {
            "connection_attempts": self.connection_attempts,
            "failed_connections": self.failed_connections,
            "active_connections": self.active_connections,
            "pool_size": self.connection_pool_size,
            "failure_rate": (self.failed_connections / max(1, self.connection_attempts)) * 100,
            "pool_utilization": (self.active_connections / self.connection_pool_size) * 100,
        }

    def record_connection_attempt(self):
        """Record a connection attempt."""
        self.connection_attempts += 1

    def record_connection_failure(self):
        """Record a connection failure."""
        self.failed_connections += 1
        self.connection_attempts += 1

    def record_connection_success(self):
        """Record a successful connection."""
        self.active_connections += 1

    def record_connection_release(self):
        """Record a connection release."""
        self.active_connections = max(0, self.active_connections - 1)


@asynccontextmanager
async def secure_database_session():
    """Context manager for secure database sessions."""
    from app.core.database import get_database_session

    session = None
    try:
        session = await get_database_session()
        yield session
    except SQLAlchemyError as e:
        logger.error(f"Database error in secure session: {e}")
        if session:
            await session.rollback()
        raise
    finally:
        if session:
            await session.close()


# Global instances
db_security_monitor = DatabaseSecurityMonitor()
secure_query_builder = SecureQueryBuilder()
db_connection_monitor = DatabaseConnectionPoolMonitor()
