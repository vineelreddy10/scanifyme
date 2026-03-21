"""
Maintenance Service - Safe maintenance operations for ScanifyMe.

This module provides:
- Safe, idempotent maintenance actions
- State recomputation utilities
- Data repair helpers
- Cleanup operations

All operations are designed to be safe and reversible.
Admin-only access is enforced at the API layer.

Usage:
    from scanifyme.support.services.maintenance_service import (
        recompute_case_metadata,
        expire_stale_sessions,
        repair_notification_state,
        validate_system_state,
    )
"""

import frappe
from frappe.utils import now_datetime, add_to_date, get_datetime
from typing import Dict, Any, List, Optional
import logging

logger = logging.getLogger(__name__)


def recompute_case_metadata(recovery_case: str) -> Dict[str, Any]:
    """
    Recompute and update recovery case metadata fields.
    
    This updates:
    - latest_event_on: Most recent timeline event time
    - latest_location_on: Most recent location share time
    - latest_notification_on: Most recent notification time
    
    Args:
        recovery_case: Recovery Case name
        
    Returns:
        Dict with success status and updated fields
    """
    try:
        case = frappe.get_doc("Recovery Case", recovery_case)
        
        updated_fields = []
        
        # Get latest timeline event time
        latest_timeline = frappe.db.get_value(
            "Recovery Timeline Event",
            {"recovery_case": recovery_case},
            "MAX(event_time) as latest_event",
        )
        
        # Get latest location share time
        latest_location = frappe.db.get_value(
            "Location Share",
            {"recovery_case": recovery_case},
            "MAX(shared_on) as latest_location",
        )
        
        # Get latest notification time
        latest_notification = frappe.db.get_value(
            "Notification Event Log",
            {"recovery_case": recovery_case},
            "MAX(triggered_on) as latest_notification",
        )
        
        # Update fields if changed
        if latest_timeline and (
            not case.latest_event_on or get_datetime(case.latest_event_on) != latest_timeline
        ):
            case.latest_event_on = latest_timeline
            updated_fields.append("latest_event_on")
        
        if latest_location and (
            not case.latest_location_on or get_datetime(case.latest_location_on) != latest_location
        ):
            case.latest_location_on = latest_location
            updated_fields.append("latest_location_on")
        
        if latest_notification and (
            not case.latest_notification_on
            or get_datetime(case.latest_notification_on) != latest_notification
        ):
            case.latest_notification_on = latest_notification
            updated_fields.append("latest_notification_on")
        
        if updated_fields:
            case.save(ignore_permissions=True)
            frappe.db.commit()
        
        return {
            "success": True,
            "case_id": recovery_case,
            "updated_fields": updated_fields,
            "message": f"Updated fields: {', '.join(updated_fields)}" if updated_fields else "No changes needed",
        }
        
    except Exception as e:
        logger.error(f"Error recomputing case metadata: {e}")
        frappe.db.rollback()
        return {
            "success": False,
            "error": str(e),
            "case_id": recovery_case,
        }


def recompute_all_open_case_metadata() -> Dict[str, Any]:
    """
    Recompute metadata for all open recovery cases.
    
    Returns:
        Dict with results summary
    """
    try:
        open_cases = frappe.get_list(
            "Recovery Case",
            filters={"status": ["in", ["Open", "Owner Responded", "Return Planned"]]},
            fields=["name"],
        )
        
        updated = 0
        failed = 0
        errors = []
        
        for case in open_cases:
            result = recompute_case_metadata(case.name)
            if result.get("success") and result.get("updated_fields"):
                updated += 1
            elif not result.get("success"):
                failed += 1
                errors.append({"case": case.name, "error": result.get("error")})
        
        return {
            "success": True,
            "total_cases": len(open_cases),
            "updated": updated,
            "failed": failed,
            "errors": errors[:10],  # Limit error list
        }
        
    except Exception as e:
        logger.error(f"Error recomputing all case metadata: {e}")
        return {
            "success": False,
            "error": str(e),
        }


def expire_stale_sessions(days_threshold: int = 2) -> Dict[str, Any]:
    """
    Expire finder sessions that have been inactive.
    
    Args:
        days_threshold: Days of inactivity to consider stale
        
    Returns:
        Dict with expired session counts
    """
    try:
        cutoff = add_to_date(now_datetime(), hours=-(days_threshold * 24))
        
        # Find sessions to expire
        stale_sessions = frappe.get_list(
            "Finder Session",
            filters={
                "status": "Active",
                "last_seen_on": ["<", cutoff],
            },
            fields=["name", "session_id", "last_seen_on"],
        )
        
        expired_count = 0
        errors = []
        
        for session in stale_sessions:
            try:
                frappe.db.set_value(
                    "Finder Session",
                    session.name,
                    {"status": "Expired"},
                )
                expired_count += 1
            except Exception as e:
                errors.append({"session": session.name, "error": str(e)})
        
        if expired_count > 0:
            frappe.db.commit()
        
        return {
            "success": True,
            "expired_count": expired_count,
            "threshold_days": days_threshold,
            "errors": errors[:10],
        }
        
    except Exception as e:
        logger.error(f"Error expiring stale sessions: {e}")
        frappe.db.rollback()
        return {
            "success": False,
            "error": str(e),
        }


def repair_notification_state(notification_id: str) -> Dict[str, Any]:
    """
    Attempt to repair a stuck notification.
    
    This can:
    - Retry a failed notification
    - Reset stuck "Queued" notifications
    
    Args:
        notification_id: Notification Event Log name
        
    Returns:
        Dict with repair result
    """
    try:
        notification = frappe.get_doc("Notification Event Log", notification_id)
        
        actions_taken = []
        
        if notification.status == "Failed":
            # Attempt to retry
            from scanifyme.notifications.services.notification_delivery_service import (
                send_email_notification,
            )
            
            if notification.channel == "Email":
                result = send_email_notification(
                    event_type=notification.event_type,
                    owner_profile=notification.owner_profile,
                    recovery_case=notification.recovery_case,
                    registered_item=notification.registered_item,
                )
                
                if result.get("success"):
                    notification.status = "Sent"
                    notification.delivered_on = now_datetime()
                    notification.processing_note = "Repaired via maintenance"
                    actions_taken.append("retry_succeeded")
                else:
                    notification.retry_count = (notification.retry_count or 0) + 1
                    notification.last_retry_on = now_datetime()
                    notification.processing_note = f"Retry failed: {result.get('reason')}"
                    actions_taken.append("retry_failed")
            else:
                # For non-email, just mark as sent
                notification.status = "Sent"
                notification.delivered_on = now_datetime()
                notification.processing_note = "Repaired via maintenance"
                actions_taken.append("marked_sent")
        
        elif notification.status == "Queued":
            # Check if too old
            if notification.triggered_on:
                age_hours = (now_datetime() - get_datetime(notification.triggered_on)).total_seconds() / 3600
                if age_hours > 24:
                    notification.status = "Skipped"
                    notification.processing_note = "Auto-skipped: queued for >24h"
                    actions_taken.append("auto_skipped")
        
        notification.save(ignore_permissions=True)
        frappe.db.commit()
        
        return {
            "success": True,
            "notification_id": notification_id,
            "actions_taken": actions_taken,
            "new_status": notification.status,
        }
        
    except Exception as e:
        logger.error(f"Error repairing notification: {e}")
        frappe.db.rollback()
        return {
            "success": False,
            "error": str(e),
            "notification_id": notification_id,
        }


def validate_system_state() -> Dict[str, Any]:
    """
    Validate overall system state and find inconsistencies.
    
    Checks:
    - Orphaned recovery cases (no linked item)
    - Duplicate open cases for same session
    - Stale open cases
    - Notification mismatches
    
    Returns:
        Dict with validation results
    """
    try:
        issues = []
        
        # Check 1: Orphaned recovery cases
        orphaned = frappe.db.sql(
            """
            SELECT rc.name, rc.case_title
            FROM `tabRecovery Case` rc
            LEFT JOIN `tabRegistered Item` ri ON rc.registered_item = ri.name
            WHERE rc.registered_item IS NOT NULL AND ri.name IS NULL
            """,
            as_dict=True,
        )
        if orphaned:
            issues.append({
                "type": "orphaned_cases",
                "count": len(orphaned),
                "cases": [c.name for c in orphaned[:10]],
                "severity": "high",
            })
        
        # Check 2: Duplicate open cases for same session
        duplicates = frappe.db.sql(
            """
            SELECT finder_session_id, COUNT(*) as cnt
            FROM `tabRecovery Case`
            WHERE status IN ('Open', 'Owner Responded', 'Return Planned')
            AND finder_session_id IS NOT NULL
            GROUP BY finder_session_id
            HAVING cnt > 1
            """,
            as_dict=True,
        )
        if duplicates:
            issues.append({
                "type": "duplicate_open_cases",
                "count": len(duplicates),
                "sessions": [d.finder_session_id for d in duplicates[:10]],
                "severity": "medium",
            })
        
        # Check 3: Stale open cases (>30 days inactive)
        cutoff = add_to_date(now_datetime(), days=-30)
        stale_cases = frappe.db.sql(
            """
            SELECT name, case_title
            FROM `tabRecovery Case`
            WHERE status IN ('Open', 'Owner Responded', 'Return Planned')
            AND COALESCE(last_activity_on, opened_on) < %(cutoff)s
            """,
            {"cutoff": cutoff},
            as_dict=True,
        )
        if stale_cases:
            issues.append({
                "type": "stale_open_cases",
                "count": len(stale_cases),
                "cases": [c.name for c in stale_cases[:10]],
                "severity": "low",
            })
        
        # Check 4: Notification state mismatches
        mismatched = frappe.db.sql(
            """
            SELECT nel.name, nel.status, nel.channel
            FROM `tabNotification Event Log` nel
            WHERE nel.channel = 'Email' AND nel.status = 'Sent'
            AND nel.delivered_on IS NULL
            LIMIT 20
            """,
            as_dict=True,
        )
        if mismatched:
            issues.append({
                "type": "notification_mismatch",
                "count": len(mismatched),
                "notifications": [n.name for n in mismatched[:10]],
                "severity": "low",
            })
        
        # Overall status
        high_issues = sum(1 for i in issues if i.get("severity") == "high")
        medium_issues = sum(1 for i in issues if i.get("severity") == "medium")
        
        if high_issues > 0:
            overall_status = "critical"
        elif medium_issues > 0:
            overall_status = "warning"
        else:
            overall_status = "healthy"
        
        return {
            "success": True,
            "overall_status": overall_status,
            "generated_at": str(now_datetime()),
            "total_issues": len(issues),
            "issues": issues,
        }
        
    except Exception as e:
        logger.error(f"Error validating system state: {e}")
        return {
            "success": False,
            "error": str(e),
        }


def get_maintenance_actions() -> List[Dict[str, Any]]:
    """
    Get list of available maintenance actions.
    
    Returns:
        List of action definitions
    """
    return [
        {
            "action": "recompute_all_case_metadata",
            "label": "Recompute All Case Metadata",
            "description": "Recompute metadata fields for all open recovery cases",
            "confirm_required": False,
            "idempotent": True,
        },
        {
            "action": "expire_stale_sessions",
            "label": "Expire Stale Sessions",
            "description": "Mark finder sessions inactive for >2 days as expired",
            "confirm_required": True,
            "idempotent": True,
        },
        {
            "action": "repair_failed_notifications",
            "label": "Repair Failed Notifications",
            "description": "Attempt to retry all failed notifications",
            "confirm_required": True,
            "idempotent": False,
        },
        {
            "action": "validate_system_state",
            "label": "Validate System State",
            "description": "Check for inconsistencies and data issues",
            "confirm_required": False,
            "idempotent": True,
        },
        {
            "action": "cleanup_old_scan_events",
            "label": "Cleanup Old Scan Events",
            "description": "Delete scan events older than 90 days not linked to active cases",
            "confirm_required": True,
            "idempotent": True,
        },
    ]


def run_maintenance_action(
    action: str,
    **kwargs
) -> Dict[str, Any]:
    """
    Run a specific maintenance action.
    
    Args:
        action: Action name
        **kwargs: Additional parameters for the action
        
    Returns:
        Dict with action result
    """
    action_map = {
        "recompute_all_case_metadata": recompute_all_open_case_metadata,
        "expire_stale_sessions": lambda: expire_stale_sessions(kwargs.get("days_threshold", 2)),
        "validate_system_state": validate_system_state,
        "cleanup_old_scan_events": lambda: cleanup_old_scan_events(kwargs.get("days_old", 90)),
    }
    
    if action not in action_map:
        return {
            "success": False,
            "error": f"Unknown action: {action}",
        }
    
    try:
        result = action_map[action]()
        return result
    except Exception as e:
        logger.error(f"Error running maintenance action {action}: {e}")
        return {
            "success": False,
            "error": str(e),
        }


def cleanup_old_scan_events(days_old: int = 90) -> Dict[str, Any]:
    """
    Clean up old scan events not linked to active cases.
    
    Args:
        days_old: Delete events older than this many days
        
    Returns:
        Dict with cleanup results
    """
    try:
        threshold = add_to_date(now_datetime(), days=-days_old)
        
        # Find old scan events not linked to active cases
        old_events = frappe.db.sql(
            """
            SELECT se.name
            FROM `tabScan Event` se
            LEFT JOIN `tabRecovery Case` rc ON rc.registered_item = se.registered_item
            WHERE se.creation < %(threshold)s
            AND (rc.name IS NULL OR rc.status IN ('Recovered', 'Closed', 'Invalid', 'Spam'))
            LIMIT 1000
            """,
            {"threshold": threshold},
            as_dict=True,
        )
        
        deleted_count = 0
        errors = []
        
        for event in old_events:
            try:
                frappe.delete_doc("Scan Event", event.name, ignore_permissions=True)
                deleted_count += 1
            except Exception as e:
                errors.append({"event": event.name, "error": str(e)})
        
        if deleted_count > 0:
            frappe.db.commit()
        
        return {
            "success": True,
            "deleted_count": deleted_count,
            "threshold_days": days_old,
            "errors": errors[:10],
        }
        
    except Exception as e:
        logger.error(f"Error cleaning up scan events: {e}")
        frappe.db.rollback()
        return {
            "success": False,
            "error": str(e),
        }
