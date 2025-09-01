"""Security monitoring and alerting system."""

import json
import logging
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from app.core.redis_client import get_redis


@dataclass
class SecurityEvent:
    """Represents a security event."""

    event_type: str
    severity: str  # 'low', 'medium', 'high', 'critical'
    message: str
    source_ip: Optional[str] = None
    user_id: Optional[str] = None
    request_id: Optional[str] = None
    details: Optional[Dict[str, Any]] = None
    timestamp: datetime = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow()

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        data = asdict(self)
        data["timestamp"] = self.timestamp.isoformat()
        return data


class SecurityMonitor:
    """Monitor security events and provide alerting."""

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.redis_prefix = "security_events:"
        self.alert_thresholds = {
            "failed_login": {"count": 5, "window_minutes": 15},
            "suspicious_request": {"count": 10, "window_minutes": 60},
            "rate_limit_hit": {"count": 20, "window_minutes": 60},
            "sql_injection_attempt": {"count": 1, "window_minutes": 5},  # Immediate alert
        }

    async def log_security_event(self, event: SecurityEvent) -> None:
        """Log a security event and check for alerts."""
        # Store event in Redis
        redis_client = await get_redis()
        event_key = f"{self.redis_prefix}{event.event_type}:{event.timestamp.strftime('%Y%m%d%H%M%S')}"

        await redis_client.setex(event_key, 86400 * 30, json.dumps(event.to_dict()))  # Keep events for 30 days

        # Add to event type index
        type_key = f"{self.redis_prefix}type:{event.event_type}"
        await redis_client.lpush(type_key, event_key)
        await redis_client.expire(type_key, 86400 * 30)

        # Log the event
        log_level = {"low": logging.INFO, "medium": logging.WARNING, "high": logging.ERROR, "critical": logging.CRITICAL}.get(event.severity, logging.INFO)

        self.logger.log(log_level, f"Security event: {event.event_type} - {event.message}", extra=event.to_dict())

        # Check for alerts
        await self._check_alert_thresholds(event)

    async def _check_alert_thresholds(self, event: SecurityEvent) -> None:
        """Check if event triggers an alert based on thresholds."""
        if event.event_type not in self.alert_thresholds:
            return

        thresholds = self.alert_thresholds[event.event_type]
        window_minutes = thresholds["window_minutes"]
        threshold_count = thresholds["count"]

        # Count events in the time window
        redis_client = await get_redis()
        window_start = datetime.utcnow() - timedelta(minutes=window_minutes)

        # Get all events of this type in the window
        type_key = f"{self.redis_prefix}type:{event.event_type}"
        event_keys = await redis_client.lrange(type_key, 0, -1)

        recent_count = 0
        for event_key in event_keys[:100]:  # Limit to avoid performance issues
            event_data = await redis_client.get(event_key.decode())
            if event_data:
                event_dict = json.loads(event_data)
                event_time = datetime.fromisoformat(event_dict["timestamp"])
                if event_time >= window_start:
                    recent_count += 1

        if recent_count >= threshold_count:
            await self._trigger_alert(event, recent_count, window_minutes)

    async def _trigger_alert(self, event: SecurityEvent, count: int, window_minutes: int) -> None:
        """Trigger a security alert."""
        alert_message = f"🚨 SECURITY ALERT: {count} {event.event_type} events " f"in {window_minutes} minutes. Latest: {event.message}"

        self.logger.critical(alert_message)

        # In production, this would:
        # 1. Send email/SMS alerts
        # 2. Create incident tickets
        # 3. Trigger automated responses (block IPs, etc.)
        # 4. Send to SIEM system

        # For now, we'll just log it prominently
        print(f"\n{alert_message}")
        print(f"Source IP: {event.source_ip}")
        print(f"User ID: {event.user_id}")
        print(f"Request ID: {event.request_id}")
        print("-" * 80)

    async def get_security_report(self, hours: int = 24) -> Dict[str, Any]:
        """Generate a security report for the specified time period."""
        redis_client = await get_redis()
        report_start = datetime.utcnow() - timedelta(hours=hours)

        # Get all event types
        type_pattern = f"{self.redis_prefix}type:*"
        type_keys = await redis_client.keys(type_pattern)

        report = {"period_hours": hours, "total_events": 0, "events_by_type": {}, "events_by_severity": {}, "top_source_ips": {}, "recent_events": []}

        for type_key in type_keys:
            event_type = type_key.decode().replace(f"{self.redis_prefix}type:", "")
            event_keys = await redis_client.lrange(type_key, 0, -1)

            type_count = 0
            type_events = []

            for event_key in event_keys[:50]:  # Limit for performance
                event_data = await redis_client.get(event_key.decode())
                if event_data:
                    event_dict = json.loads(event_data)
                    event_time = datetime.fromisoformat(event_dict["timestamp"])

                    if event_time >= report_start:
                        type_count += 1
                        type_events.append(event_dict)

                        # Track by severity
                        severity = event_dict.get("severity", "unknown")
                        report["events_by_severity"][severity] = report["events_by_severity"].get(severity, 0) + 1

                        # Track source IPs
                        source_ip = event_dict.get("source_ip")
                        if source_ip:
                            report["top_source_ips"][source_ip] = report["top_source_ips"].get(source_ip, 0) + 1

            if type_count > 0:
                report["events_by_type"][event_type] = type_count
                report["total_events"] += type_count

                # Add recent events (last 10 per type)
                report["recent_events"].extend(type_events[:10])

        # Sort recent events by timestamp
        report["recent_events"].sort(key=lambda x: x["timestamp"], reverse=True)
        report["recent_events"] = report["recent_events"][:50]  # Limit total recent events

        return report

    async def get_active_threats(self) -> List[Dict[str, Any]]:
        """Identify active security threats based on patterns."""
        report = await self.get_security_report(hours=1)  # Last hour
        threats = []

        # Check for brute force attacks
        failed_logins = report["events_by_type"].get("failed_login", 0)
        if failed_logins > 10:
            threats.append(
                {"type": "brute_force", "severity": "high", "description": f"{failed_logins} failed login attempts in the last hour", "recommendation": "Consider implementing IP blocking or CAPTCHA"}
            )

        # Check for suspicious requests
        suspicious_requests = report["events_by_type"].get("suspicious_request", 0)
        if suspicious_requests > 20:
            threats.append(
                {
                    "type": "suspicious_activity",
                    "severity": "medium",
                    "description": f"{suspicious_requests} suspicious requests in the last hour",
                    "recommendation": "Review request patterns and implement WAF rules",
                }
            )

        # Check for rate limiting hits
        rate_limit_hits = report["events_by_type"].get("rate_limit_hit", 0)
        if rate_limit_hits > 50:
            threats.append(
                {
                    "type": "dos_attempt",
                    "severity": "high",
                    "description": f"{rate_limit_hits} rate limit hits in the last hour",
                    "recommendation": "Consider implementing more aggressive rate limiting",
                }
            )

        # Check for SQL injection attempts
        sql_injection_attempts = report["events_by_type"].get("sql_injection_attempt", 0)
        if sql_injection_attempts > 0:
            threats.append(
                {
                    "type": "sql_injection",
                    "severity": "critical",
                    "description": f"{sql_injection_attempts} SQL injection attempts detected",
                    "recommendation": "Immediate review required - potential security breach",
                }
            )

        return threats


class SecurityMetricsCollector:
    """Collect and expose security metrics."""

    def __init__(self):
        self.metrics = {"security_events_total": 0, "security_events_by_type": {}, "active_alerts": 0, "blocked_requests": 0, "suspicious_activities": 0}

    def increment_event_count(self, event_type: str) -> None:
        """Increment the count for a specific event type."""
        self.metrics["security_events_total"] += 1
        self.metrics["security_events_by_type"][event_type] = self.metrics["security_events_by_type"].get(event_type, 0) + 1

    def increment_blocked_requests(self) -> None:
        """Increment blocked requests counter."""
        self.metrics["blocked_requests"] += 1

    def increment_suspicious_activities(self) -> None:
        """Increment suspicious activities counter."""
        self.metrics["suspicious_activities"] += 1

    def set_active_alerts(self, count: int) -> None:
        """Set the number of active alerts."""
        self.metrics["active_alerts"] = count

    def get_metrics(self) -> Dict[str, Any]:
        """Get current metrics."""
        return self.metrics.copy()

    def get_prometheus_metrics(self) -> str:
        """Generate Prometheus-formatted metrics."""
        lines = [
            "# HELP security_events_total Total number of security events",
            "# TYPE security_events_total counter",
            f"security_events_total {self.metrics['security_events_total']}",
            "",
            "# HELP security_events_by_type Security events by type",
            "# TYPE security_events_by_type counter",
        ]

        for event_type, count in self.metrics["security_events_by_type"].items():
            lines.append(f'security_events_by_type{{type="{event_type}"}} {count}')

        lines.extend(
            [
                "",
                "# HELP active_security_alerts Number of active security alerts",
                "# TYPE active_security_alerts gauge",
                f"active_security_alerts {self.metrics['active_alerts']}",
                "",
                "# HELP blocked_requests_total Total number of blocked requests",
                "# TYPE blocked_requests_total counter",
                f"blocked_requests_total {self.metrics['blocked_requests']}",
                "",
                "# HELP suspicious_activities_total Total number of suspicious activities",
                "# TYPE suspicious_activities_total counter",
                f"suspicious_activities_total {self.metrics['suspicious_activities']}",
            ]
        )

        return "\n".join(lines)


# Global instances
security_monitor = SecurityMonitor()
security_metrics = SecurityMetricsCollector()
