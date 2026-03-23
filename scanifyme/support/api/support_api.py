"""
Support API - Admin/Operations API endpoints for diagnostics and maintenance.

This module provides whitelisted APIs for operational visibility:
- get_environment_health_summary - Infrastructure health checks
- get_operational_health_summary - Business-level health metrics
- get_case_diagnostic_bundle - Comprehensive case diagnostics
- get_system_state_snapshot - System state overview
- get_stale_cases_report - Stale open cases report
- get_queue_failure_report - Queue/notification failure report
- validate_scanifyme_setup - Full setup validation
- run_safe_maintenance_action - Execute safe maintenance operations
- get_maintenance_actions - List available actions
- get_quick_health_check - Lightweight health check

All endpoints require admin/operations permissions.
"""

import frappe
from frappe import _
from typing import Dict, Any


def _check_admin_or_operations():
    """Check if current user has admin or operations role."""
    roles = frappe.get_roles()
    admin_roles = {"Administrator", "System Manager", "ScanifyMe Admin", "ScanifyMe Operations"}
    if not any(r in roles for r in admin_roles):
        frappe.throw(_("Insufficient permissions"), frappe.PermissionError)


@frappe.whitelist()
def get_environment_health_summary() -> Dict[str, Any]:
    """
    Get comprehensive environment health summary.
    
    Checks infrastructure dependencies:
    - Redis cache
    - Redis queue
    - Database
    - Web worker
    - Scheduler
    - Email account
    
    Returns:
        Dict with overall status and detailed checks
    """
    _check_admin_or_operations()
    
    from scanifyme.support.services.health_service import (
        get_environment_health_summary as _get_health,
    )
    
    return _get_health()


@frappe.whitelist()
def get_operational_health_summary() -> Dict[str, Any]:
    """
    Get operational health summary.
    
    Aggregates business-level health metrics:
    - Notification backlog
    - Recovery case stats
    - Finder session stats
    - Recent failures
    
    Returns:
        Dict with operational health status
    """
    _check_admin_or_operations()
    
    from scanifyme.support.services.health_service import (
        get_operational_health_summary as _get_op_health,
    )
    
    return _get_op_health()


@frappe.whitelist()
def get_quick_health_check() -> Dict[str, Any]:
    """
    Get a quick lightweight health check for monitoring.
    
    Returns:
        Dict with basic health status (healthy/degraded/unhealthy)
    """
    _check_admin_or_operations()
    
    from scanifyme.support.services.health_service import (
        get_quick_health_check as _quick_check,
    )
    
    return _quick_check()


@frappe.whitelist()
def validate_email_readiness() -> Dict[str, Any]:
    """
    Validate email system readiness.
    
    Returns:
        Dict with email readiness status
    """
    _check_admin_or_operations()
    
    from scanifyme.support.services.health_service import (
        validate_email_readiness as _validate_email,
    )
    
    return _validate_email()


@frappe.whitelist()
def validate_queue_readiness() -> Dict[str, Any]:
    """
    Validate queue system readiness.
    
    Returns:
        Dict with queue readiness status
    """
    _check_admin_or_operations()
    
    from scanifyme.support.services.health_service import (
        validate_queue_readiness as _validate_queue,
    )
    
    return _validate_queue()


@frappe.whitelist()
def validate_scanifyme_setup() -> Dict[str, Any]:
    """
    Validate complete ScanifyMe setup.
    
    Combines:
    - Environment health
    - Email readiness
    - Queue readiness
    - System state validation
    
    Returns:
        Dict with complete validation results
    """
    _check_admin_or_operations()
    
    from scanifyme.support.services.health_service import get_environment_health_summary
    from scanifyme.support.services.health_service import validate_email_readiness
    from scanifyme.support.services.health_service import validate_queue_readiness
    from scanifyme.support.services.maintenance_service import validate_system_state
    
    env_health = get_environment_health_summary()
    email_ready = validate_email_readiness()
    queue_ready = validate_queue_readiness()
    sys_state = validate_system_state()
    
    # Determine overall setup status
    all_healthy = (
        env_health.get("overall_status") == "healthy"
        and email_ready.get("ready", False)
        and queue_ready.get("ready", False)
        and sys_state.get("overall_status") == "healthy"
    )
    
    has_warnings = (
        env_health.get("overall_status") == "warning"
        or email_ready.get("status") == "warning"
        or queue_ready.get("status") == "warning"
        or sys_state.get("overall_status") == "warning"
    )
    
    if all_healthy:
        setup_status = "ready"
    elif has_warnings:
        setup_status = "warning"
    else:
        setup_status = "not_ready"
    
    return {
        "success": True,
        "setup_status": setup_status,
        "timestamp": str(frappe.utils.now_datetime()),
        "environment": env_health,
        "email": email_ready,
        "queue": queue_ready,
        "system_state": sys_state,
    }


@frappe.whitelist()
def get_case_diagnostic_bundle(case_id: str) -> Dict[str, Any]:
    """
    Get comprehensive diagnostic bundle for a recovery case.
    
    Bundles together:
    - Recovery case details
    - Timeline events
    - Messages
    - Notifications
    - Scan events
    - Finder sessions
    - Email queue entries
    
    Args:
        case_id: Recovery Case name
        
    Returns:
        Dict with all related diagnostic data
    """
    _check_admin_or_operations()
    
    if not case_id:
        return {"success": False, "error": "case_id is required"}
    
    from scanifyme.support.services.diagnostics_service import (
        get_case_diagnostic_bundle as _get_bundle,
    )
    
    return _get_bundle(case_id)


@frappe.whitelist()
def get_notification_diagnostic_info(notification_id: str) -> Dict[str, Any]:
    """
    Get diagnostic information for a specific notification.
    
    Args:
        notification_id: Notification Event Log name
        
    Returns:
        Dict with notification and related data
    """
    _check_admin_or_operations()
    
    if not notification_id:
        return {"success": False, "error": "notification_id is required"}
    
    from scanifyme.support.services.diagnostics_service import (
        get_notification_diagnostic_info as _get_info,
    )
    
    return _get_info(notification_id)


@frappe.whitelist()
def get_system_state_snapshot(hours: int = 24) -> Dict[str, Any]:
    """
    Get a snapshot of system state for debugging.
    
    Args:
        hours: Look back period for recent activity (default: 24)
        
    Returns:
        Dict with system state snapshot
    """
    _check_admin_or_operations()
    
    from scanifyme.support.services.diagnostics_service import (
        get_system_state_snapshot as _get_snapshot,
    )
    
    return _get_snapshot(hours)


@frappe.whitelist()
def get_stale_cases_report(days_threshold: int = 7) -> Dict[str, Any]:
    """
    Get report of stale open recovery cases.
    
    Args:
        days_threshold: Days of inactivity to consider stale (default: 7)
        
    Returns:
        Dict with stale case information
    """
    _check_admin_or_operations()
    
    from scanifyme.support.services.diagnostics_service import (
        get_stale_cases_report as _get_stale,
    )
    
    return _get_stale(days_threshold)


@frappe.whitelist()
def get_queue_failure_report() -> Dict[str, Any]:
    """
    Get report of queue/notification failures.
    
    Returns:
        Dict with failure information
    """
    _check_admin_or_operations()
    
    from scanifyme.support.services.diagnostics_service import (
        get_queue_failure_report as _get_report,
    )
    
    return _get_report()


@frappe.whitelist()
def get_maintenance_actions() -> list:
    """
    Get list of available maintenance actions.
    
    Returns:
        List of action definitions
    """
    _check_admin_or_operations()
    
    from scanifyme.support.services.maintenance_service import (
        get_maintenance_actions as _get_actions,
    )
    
    return _get_actions()


@frappe.whitelist()
def run_safe_maintenance_action(action: str, **kwargs) -> Dict[str, Any]:
    """
    Run a specific safe maintenance action.
    
    Available actions:
    - recompute_all_case_metadata
    - expire_stale_sessions
    - validate_system_state
    - cleanup_old_scan_events
    
    Args:
        action: Action name
        **kwargs: Additional parameters
        
    Returns:
        Dict with action result
    """
    _check_admin_or_operations()
    
    if not action:
        return {"success": False, "error": "action is required"}
    
    from scanifyme.support.services.maintenance_service import (
        run_maintenance_action as _run_action,
    )
    
    return _run_action(action, **kwargs)


@frappe.whitelist()
def recompute_case_metadata(case_id: str) -> Dict[str, Any]:
    """
    Recompute metadata for a specific recovery case.
    
    Args:
        case_id: Recovery Case name
        
    Returns:
        Dict with recomputation result
    """
    _check_admin_or_operations()
    
    if not case_id:
        return {"success": False, "error": "case_id is required"}
    
    from scanifyme.support.services.maintenance_service import (
        recompute_case_metadata as _recompute,
    )
    
    return _recompute(case_id)


@frappe.whitelist()
def repair_notification(notification_id: str) -> Dict[str, Any]:
    """
    Attempt to repair a stuck notification.
    
    Args:
        notification_id: Notification Event Log name
        
    Returns:
        Dict with repair result
    """
    _check_admin_or_operations()
    
    if not notification_id:
        return {"success": False, "error": "notification_id is required"}
    
    from scanifyme.support.services.maintenance_service import (
        repair_notification_state as _repair,
    )
    
    return _repair(notification_id)


@frappe.whitelist()
def get_recent_errors(hours: int = 24, limit: int = 50) -> list:
    """
    Get recent error log entries for ScanifyMe.
    
    Args:
        hours: Look back period (default: 24)
        limit: Maximum entries (default: 50)
        
    Returns:
        List of recent errors
    """
    _check_admin_or_operations()
    
    from scanifyme.support.services.logging_service import get_recent_events
    
    return get_recent_events(hours=hours, limit=limit)


@frappe.whitelist()
def get_notification_queue_status() -> Dict[str, Any]:
    """
    Get the current notification queue status.
    
    Returns:
        Dict with queue statistics
    """
    _check_admin_or_operations()
    
    try:
        # Get counts by status
        queued = frappe.db.count(
            "Notification Event Log",
            {"status": "Queued"},
        )
        
        sent = frappe.db.count(
            "Notification Event Log",
            {"status": "Sent"},
        )
        
        failed = frappe.db.count(
            "Notification Event Log",
            {"status": "Failed"},
        )
        
        skipped = frappe.db.count(
            "Notification Event Log",
            {"status": "Skipped"},
        )
        
        # Get today's stats
        today = frappe.utils.today()
        sent_today = frappe.db.count(
            "Notification Event Log",
            {"status": "Sent", "triggered_on": [">=", today]},
        )
        
        failed_today = frappe.db.count(
            "Notification Event Log",
            {"status": "Failed", "triggered_on": [">=", today]},
        )
        
        return {
            "success": True,
            "queue": {
                "queued": queued,
                "sent": sent,
                "failed": failed,
                "skipped": skipped,
                "total": queued + sent + failed + skipped,
            },
            "today": {
                "sent": sent_today,
                "failed": failed_today,
            },
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
        }
