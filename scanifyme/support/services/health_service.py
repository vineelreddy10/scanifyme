"""
Health Service - Environment and operational health validation.

This module provides:
- Environment health checks (Redis, scheduler, workers, email)
- Operational health aggregation
- Readiness validation
- Health status constants

Usage:
    from scanifyme.support.services.health_service import (
        get_environment_health_summary,
        get_operational_health_summary,
        validate_email_readiness,
        validate_queue_readiness,
    )
"""

import frappe
import redis
import socket
from frappe.utils import now_datetime, add_to_date, get_datetime
from typing import Dict, Any, List, Optional
import logging

logger = logging.getLogger(__name__)


class HealthStatus:
    """Health status constants."""
    HEALTHY = "healthy"
    WARNING = "warning"
    CRITICAL = "critical"
    UNKNOWN = "unknown"


class DependencyCheck:
    """Result of a dependency check."""
    def __init__(
        self,
        name: str,
        status: str,
        message: str = "",
        details: Optional[Dict[str, Any]] = None,
    ):
        self.name = name
        self.status = status
        self.message = message
        self.details = details or {}
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "status": self.status,
            "message": self.message,
            **self.details,
        }


def get_site_url() -> str:
    """Get the configured site URL."""
    try:
        return frappe.utils.get_url()
    except Exception:
        return "http://localhost:8002"


def check_redis_connection() -> DependencyCheck:
    """
    Check Redis cache connection.
    
    Returns:
        DependencyCheck with status and details
    """
    try:
        # Get Redis config from site_config
        redis_cache = frappe.conf.get("redis_cache")
        if not redis_cache:
            # Try default
            redis_cache = "redis://localhost:13000"
        
        # Parse connection string
        if isinstance(redis_cache, str):
            if "redis://" in redis_cache:
                redis_cache = redis_cache.replace("redis://", "")
            
            if ":" in redis_cache:
                host, port = redis_cache.rsplit(":", 1)
                port = int(port)
            else:
                host = redis_cache
                port = 13000
        else:
            host = "localhost"
            port = 13000
        
        # Attempt connection
        r = redis.Redis(host=host, port=port, socket_connect_timeout=2)
        r.ping()
        
        return DependencyCheck(
            name="redis_cache",
            status=HealthStatus.HEALTHY,
            message=f"Connected to {host}:{port}",
            details={"host": host, "port": port},
        )
    except Exception as e:
        return DependencyCheck(
            name="redis_cache",
            status=HealthStatus.CRITICAL,
            message=f"Redis connection failed: {str(e)}",
            details={"error": str(e)},
        )


def check_redis_queue() -> DependencyCheck:
    """
    Check Redis queue connection.
    
    Returns:
        DependencyCheck with status and details
    """
    try:
        # Get Redis queue config from site_config
        redis_queue = frappe.conf.get("redis_queue")
        if not redis_queue:
            redis_queue = "redis://localhost:13002"
        
        # Parse connection string
        if isinstance(redis_queue, str):
            if "redis://" in redis_queue:
                redis_queue = redis_queue.replace("redis://", "")
            
            if ":" in redis_queue:
                host, port = redis_queue.rsplit(":", 1)
                port = int(port)
            else:
                host = redis_queue
                port = 13002
        else:
            host = "localhost"
            port = 13002
        
        # Attempt connection
        r = redis.Redis(host=host, port=port, socket_connect_timeout=2)
        r.ping()
        
        return DependencyCheck(
            name="redis_queue",
            status=HealthStatus.HEALTHY,
            message=f"Connected to {host}:{port}",
            details={"host": host, "port": port},
        )
    except Exception as e:
        return DependencyCheck(
            name="redis_queue",
            status=HealthStatus.CRITICAL,
            message=f"Redis queue connection failed: {str(e)}",
            details={"error": str(e)},
        )


def check_scheduler() -> DependencyCheck:
    """
    Check if scheduler is enabled and processing.
    
    Returns:
        DependencyCheck with status and details
    """
    try:
        # Check scheduler status via frappe.db
        scheduler_status = frappe.db.get_single_value(
            "System Settings",
            "enable_scheduler",
            cache=True,
        )
        
        if scheduler_status is None:
            # System Settings might not have this field, default to enabled
            scheduler_status = True
        
        # Check for recent scheduler events
        last_scheduler_event = frappe.db.get_value(
            "Scheduled Job Log",
            {"status": "Success"},
            "modified",
            order_by="modified desc",
        )
        
        if last_scheduler_event:
            hours_ago = (now_datetime() - get_datetime(last_scheduler_event)).total_seconds() / 3600
            recent_activity = hours_ago < 1
        else:
            recent_activity = False
        
        if scheduler_status and recent_activity:
            status = HealthStatus.HEALTHY
            message = "Scheduler is enabled and active"
        elif scheduler_status:
            status = HealthStatus.WARNING
            message = "Scheduler is enabled but no recent activity"
        else:
            status = HealthStatus.WARNING
            message = "Scheduler is disabled"
        
        return DependencyCheck(
            name="scheduler",
            status=status,
            message=message,
            details={
                "enabled": bool(scheduler_status),
                "last_activity": str(last_scheduler_event) if last_scheduler_event else None,
            },
        )
    except Exception as e:
        return DependencyCheck(
            name="scheduler",
            status=HealthStatus.UNKNOWN,
            message=f"Could not check scheduler: {str(e)}",
            details={"error": str(e)},
        )


def check_web_worker() -> DependencyCheck:
    """
    Check if web worker is responding.
    
    Returns:
        DependencyCheck with status and details
    """
    try:
        site_url = get_site_url()
        
        # Try to connect to the site
        import urllib.request
        import urllib.error
        
        url = f"{site_url}/api/method/ping"
        
        try:
            with urllib.request.urlopen(url, timeout=5) as response:
                if response.status == 200:
                    return DependencyCheck(
                        name="web_worker",
                        status=HealthStatus.HEALTHY,
                        message=f"Web worker responding at {site_url}",
                        details={"url": url, "response_code": response.status},
                    )
        except urllib.error.HTTPError as e:
            # HTTP errors still mean worker is running
            return DependencyCheck(
                name="web_worker",
                status=HealthStatus.HEALTHY,
                message=f"Web worker responding (HTTP {e.code})",
                details={"url": url, "response_code": e.code},
            )
        except Exception:
            pass
        
        # If we can't reach the API, check if the port is listening
        from urllib.parse import urlparse
        parsed = urlparse(site_url)
        host = parsed.hostname or "localhost"
        port = parsed.port or 8000
        
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(2)
        result = sock.connect_ex((host, port))
        sock.close()
        
        if result == 0:
            return DependencyCheck(
                name="web_worker",
                status=HealthStatus.HEALTHY,
                message=f"Port {port} is open",
                details={"host": host, "port": port},
            )
        else:
            return DependencyCheck(
                name="web_worker",
                status=HealthStatus.CRITICAL,
                message=f"Cannot connect to {host}:{port}",
                details={"host": host, "port": port},
            )
    except Exception as e:
        return DependencyCheck(
            name="web_worker",
            status=HealthStatus.UNKNOWN,
            message=f"Could not check web worker: {str(e)}",
            details={"error": str(e)},
        )


def check_email_account() -> DependencyCheck:
    """
    Check if email account is configured.
    
    Returns:
        DependencyCheck with status and details
    """
    try:
        # Check for outgoing email accounts
        email_accounts = frappe.get_all(
            "Email Account",
            filters={"enable_outgoing": 1, "enabled": 1},
            fields=["name", "email_id", "default_outgoing"],
        )
        
        if not email_accounts:
            return DependencyCheck(
                name="email_account",
                status=HealthStatus.CRITICAL,
                message="No outgoing email account configured",
                details={"configured_accounts": 0},
            )
        
        # Check for default outgoing
        default_account = [a for a in email_accounts if a.get("default_outgoing")]
        
        if default_account:
            return DependencyCheck(
                name="email_account",
                status=HealthStatus.HEALTHY,
                message=f"Default email account configured: {default_account[0]['email_id']}",
                details={
                    "configured_accounts": len(email_accounts),
                    "default_account": default_account[0]["email_id"],
                },
            )
        else:
            return DependencyCheck(
                name="email_account",
                status=HealthStatus.WARNING,
                message=f"Email accounts exist but no default configured",
                details={
                    "configured_accounts": len(email_accounts),
                    "accounts": [a["email_id"] for a in email_accounts],
                },
            )
    except Exception as e:
        return DependencyCheck(
            name="email_account",
            status=HealthStatus.UNKNOWN,
            message=f"Could not check email account: {str(e)}",
            details={"error": str(e)},
        )


def check_database() -> DependencyCheck:
    """
    Check database connectivity.
    
    Returns:
        DependencyCheck with status and details
    """
    try:
        # Simple query to verify DB connection
        frappe.db.sql("SELECT 1")
        
        # Get database stats
        db_type = frappe.conf.db_type or "mariadb"
        
        return DependencyCheck(
            name="database",
            status=HealthStatus.HEALTHY,
            message=f"Database connected ({db_type})",
            details={"db_type": db_type},
        )
    except Exception as e:
        return DependencyCheck(
            name="database",
            status=HealthStatus.CRITICAL,
            message=f"Database connection failed: {str(e)}",
            details={"error": str(e)},
        )


def get_environment_health_summary() -> Dict[str, Any]:
    """
    Get comprehensive environment health summary.
    
    This checks all critical infrastructure dependencies:
    - Redis cache
    - Redis queue
    - Database
    - Web worker
    - Scheduler
    - Email account
    
    Returns:
        Dict with overall status and detailed checks
    """
    checks = [
        check_database(),
        check_redis_connection(),
        check_redis_queue(),
        check_web_worker(),
        check_scheduler(),
        check_email_account(),
    ]
    
    # Determine overall status
    status_weights = {
        HealthStatus.HEALTHY: 0,
        HealthStatus.WARNING: 1,
        HealthStatus.UNKNOWN: 2,
        HealthStatus.CRITICAL: 3,
    }
    
    overall_score = max(
        status_weights.get(c.status, 3) for c in checks
    )
    
    status_map = {
        0: HealthStatus.HEALTHY,
        1: HealthStatus.WARNING,
        2: HealthStatus.WARNING,
        3: HealthStatus.CRITICAL,
    }
    
    overall_status = status_map.get(overall_score, HealthStatus.UNKNOWN)
    
    # Build response
    checks_data = [c.to_dict() for c in checks]
    
    critical_issues = [
        c for c in checks_data if c["status"] == HealthStatus.CRITICAL
    ]
    
    return {
        "success": True,
        "overall_status": overall_status,
        "timestamp": str(now_datetime()),
        "site_url": get_site_url(),
        "checks": checks_data,
        "issues": critical_issues,
        "summary": {
            "total_checks": len(checks),
            "healthy": sum(1 for c in checks if c.status == HealthStatus.HEALTHY),
            "warnings": sum(1 for c in checks if c.status == HealthStatus.WARNING),
            "critical": sum(1 for c in checks if c.status == HealthStatus.CRITICAL),
            "unknown": sum(1 for c in checks if c.status == HealthStatus.UNKNOWN),
        },
    }


def get_operational_health_summary() -> Dict[str, Any]:
    """
    Get operational health summary.
    
    This aggregates business-level health metrics:
    - Notification backlog
    - Recovery case stats
    - Finder session stats
    - Recent failures
    
    Returns:
        Dict with operational health status
    """
    try:
        # Get notification backlog
        from scanifyme.notifications.services.reliability_service import (
            get_notification_backlog,
        )
        
        # Get cleanup service summary
        from scanifyme.recovery.services.cleanup_service import (
            get_operational_health_summary as cleanup_summary,
        )
        
        notification_backlog = get_notification_backlog()
        cleanup_health = cleanup_summary()
        
        # Get current counts
        open_cases = frappe.db.count(
            "Recovery Case",
            {"status": ["in", ["Open", "Owner Responded", "Return Planned"]]},
        )
        
        closed_cases = frappe.db.count(
            "Recovery Case",
            {"status": ["in", ["Recovered", "Closed", "Invalid", "Spam"]]},
        )
        
        active_sessions = frappe.db.count(
            "Finder Session",
            {"status": "Active"},
        )
        
        expired_sessions = frappe.db.count(
            "Finder Session",
            {"status": "Expired"},
        )
        
        # Get recent failures
        recent_failures = []
        try:
            failed_notifications = frappe.get_list(
                "Notification Event Log",
                filters={"status": "Failed"},
                fields=["name", "event_type", "error_message", "triggered_on"],
                order_by="triggered_on desc",
                limit=10,
            )
            recent_failures = [
                {
                    "id": n.name,
                    "event_type": n.event_type,
                    "error": n.error_message,
                    "triggered_on": str(n.triggered_on),
                }
                for n in failed_notifications
            ]
        except Exception:
            pass
        
        # Determine health status
        failed_count = notification_backlog.get("backlog", {}).get("failed", 0)
        
        if failed_count > 10:
            health_status = HealthStatus.CRITICAL
        elif failed_count > 5:
            health_status = HealthStatus.WARNING
        else:
            health_status = HealthStatus.HEALTHY
        
        return {
            "success": True,
            "overall_status": health_status,
            "timestamp": str(now_datetime()),
            "notifications": notification_backlog.get("backlog", {}),
            "recent_failures": recent_failures,
            "recovery_cases": {
                "open": open_cases,
                "closed": closed_cases,
            },
            "finder_sessions": {
                "active": active_sessions,
                "expired": expired_sessions,
            },
        }
    except Exception as e:
        logger.error(f"Error getting operational health: {e}")
        return {
            "success": False,
            "error": str(e),
            "overall_status": HealthStatus.UNKNOWN,
        }


def validate_email_readiness() -> Dict[str, Any]:
    """
    Validate email system readiness.
    
    Returns:
        Dict with email readiness status
    """
    try:
        email_check = check_email_account()
        
        if email_check.status != HealthStatus.HEALTHY:
            return {
                "ready": False,
                "status": email_check.status,
                "message": email_check.message,
                "checks": [email_check.to_dict()],
            }
        
        # Get configured accounts
        accounts = frappe.get_all(
            "Email Account",
            filters={"enable_outgoing": 1, "enabled": 1},
            fields=["name", "email_id", "default_outgoing", "smtp_server"],
        )
        
        # Check email queue status
        queued_emails = frappe.db.count("Email Queue", {"status": "Pending"})
        failed_emails = frappe.db.count("Email Queue", {"status": "Error"})
        
        return {
            "ready": True,
            "status": HealthStatus.HEALTHY,
            "message": "Email system is ready",
            "configured_accounts": len(accounts),
            "accounts": [
                {
                    "name": a.name,
                    "email": a.email_id,
                    "is_default": bool(a.default_outgoing),
                    "smtp_server": a.smtp_server,
                }
                for a in accounts
            ],
            "queue_status": {
                "pending": queued_emails,
                "failed": failed_emails,
            },
        }
    except Exception as e:
        return {
            "ready": False,
            "status": HealthStatus.UNKNOWN,
            "message": f"Could not validate email readiness: {str(e)}",
            "error": str(e),
        }


def validate_queue_readiness() -> Dict[str, Any]:
    """
    Validate queue system readiness.
    
    Returns:
        Dict with queue readiness status
    """
    try:
        redis_check = check_redis_queue()
        
        if redis_check.status != HealthStatus.HEALTHY:
            return {
                "ready": False,
                "status": redis_check.status,
                "message": redis_check.message,
                "checks": [redis_check.to_dict()],
            }
        
        # Get queue stats
        pending_jobs = 0
        failed_jobs = 0
        
        try:
            # CheckRQ queue if available
            from frappe.utils.background_jobs import get_queue
            queue = get_queue("default")
            if queue:
                # Basic stats
                pending_jobs = getattr(queue, 'get_job_ids', lambda: [])().__len__() if hasattr(queue, 'get_job_ids') else 0
        except Exception:
            pass
        
        return {
            "ready": True,
            "status": HealthStatus.HEALTHY,
            "message": "Queue system is ready",
            "redis": {
                "host": redis_check.details.get("host"),
                "port": redis_check.details.get("port"),
            },
            "job_stats": {
                "pending": pending_jobs,
                "failed": failed_jobs,
            },
        }
    except Exception as e:
        return {
            "ready": False,
            "status": HealthStatus.UNKNOWN,
            "message": f"Could not validate queue readiness: {str(e)}",
            "error": str(e),
        }


def get_quick_health_check() -> Dict[str, Any]:
    """
    Get a quick health check for monitoring.
    
    This is a lightweight check suitable for frequent monitoring.
    
    Returns:
        Dict with basic health status
    """
    try:
        # Quick DB check
        frappe.db.sql("SELECT 1")
        
        # Quick Redis check
        redis_check = check_redis_connection()
        
        if redis_check.status == HealthStatus.HEALTHY:
            return {
                "status": "healthy",
                "timestamp": str(now_datetime()),
            }
        else:
            return {
                "status": "degraded",
                "timestamp": str(now_datetime()),
                "reason": "redis_unavailable",
            }
    except Exception:
        return {
            "status": "unhealthy",
            "timestamp": str(now_datetime()),
            "reason": "database_unavailable",
        }
