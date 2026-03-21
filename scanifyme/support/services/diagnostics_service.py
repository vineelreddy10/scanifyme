"""
Diagnostics Service - Diagnostic helpers for debugging ScanifyMe issues.

This module provides:
- Case diagnostic bundles (correlation of related data)
- Error investigation helpers
- System state snapshots
- Troubleshooting guidance

Usage:
    from scanifyme.support.services.diagnostics_service import (
        get_case_diagnostic_bundle,
        get_notification_diagnostic_info,
        get_system_state_snapshot,
    )
"""

import frappe
from frappe.utils import now_datetime, get_datetime, add_to_date
from typing import Dict, Any, List, Optional
import logging

logger = logging.getLogger(__name__)


def get_case_diagnostic_bundle(case_id: str) -> Dict[str, Any]:
    """
    Get a comprehensive diagnostic bundle for a recovery case.
    
    This bundles together all related data for debugging:
    - Recovery case details
    - Timeline events
    - Messages
    - Notifications
    - Scan events
    - Finder sessions
    - Related email queue entries
    
    Args:
        case_id: Recovery Case name
        
    Returns:
        Dict with all related diagnostic data
    """
    try:
        # Get case details
        case = frappe.get_doc("Recovery Case", case_id)
        
        bundle = {
            "success": True,
            "case_id": case_id,
            "generated_at": str(now_datetime()),
            "recovery_case": {
                "name": case.name,
                "case_title": case.case_title,
                "status": case.status,
                "opened_on": str(case.opened_on) if case.opened_on else None,
                "last_activity_on": str(case.last_activity_on) if case.last_activity_on else None,
                "closed_on": str(case.closed_on) if case.closed_on else None,
                "finder_session_id": case.finder_session_id,
                "finder_name": case.finder_name,
                "finder_contact_hint": case.finder_contact_hint,
                "latest_message_preview": case.latest_message_preview,
                "handover_status": case.handover_status,
                "notes_internal": case.notes_internal,
            },
        }
        
        # Get timeline events
        try:
            timeline = frappe.get_list(
                "Recovery Timeline Event",
                filters={"recovery_case": case_id},
                fields=["name", "event_type", "event_label", "actor_type", "event_time", "summary"],
                order_by="event_time desc",
                limit=50,
            )
            bundle["timeline_events"] = [
                {
                    "id": e.name,
                    "type": e.event_type,
                    "label": e.event_label,
                    "actor": e.actor_type,
                    "time": str(e.event_time),
                    "summary": e.summary,
                }
                for e in timeline
            ]
        except Exception as e:
            bundle["timeline_events"] = {"error": str(e)}
        
        # Get messages
        try:
            messages = frappe.get_list(
                "Recovery Message",
                filters={"recovery_case": case_id},
                fields=["name", "sender_type", "sender_name", "message", "created_on"],
                order_by="created_on asc",
            )
            bundle["messages"] = [
                {
                    "id": m.name,
                    "sender": m.sender_type,
                    "sender_name": m.sender_name,
                    "message_preview": m.message[:100] + "..." if len(m.message) > 100 else m.message,
                    "created_on": str(m.created_on),
                }
                for m in messages
            ]
        except Exception as e:
            bundle["messages"] = {"error": str(e)}
        
        # Get notifications
        try:
            notifications = frappe.get_list(
                "Notification Event Log",
                filters={"recovery_case": case_id},
                fields=[
                    "name", "event_type", "channel", "status", "triggered_on",
                    "delivered_on", "error_message", "retry_count"
                ],
                order_by="triggered_on desc",
            )
            bundle["notifications"] = [
                {
                    "id": n.name,
                    "event_type": n.event_type,
                    "channel": n.channel,
                    "status": n.status,
                    "triggered_on": str(n.triggered_on),
                    "delivered_on": str(n.delivered_on) if n.delivered_on else None,
                    "error": n.error_message,
                    "retry_count": n.retry_count,
                }
                for n in notifications
            ]
        except Exception as e:
            bundle["notifications"] = {"error": str(e)}
        
        # Get scan events
        try:
            scans = frappe.get_list(
                "Scan Event",
                filters={"registered_item": case.registered_item},
                fields=["name", "status", "creation", "ip_hash"],
                order_by="creation desc",
                limit=20,
            )
            bundle["scan_events"] = [
                {
                    "id": s.name,
                    "status": s.status,
                    "created_on": str(s.creation),
                }
                for s in scans
            ]
        except Exception as e:
            bundle["scan_events"] = {"error": str(e)}
        
        # Get finder session
        if case.finder_session_id:
            try:
                sessions = frappe.get_list(
                    "Finder Session",
                    filters={"session_id": case.finder_session_id},
                    fields=["name", "status", "started_on", "last_seen_on", "ip_hash"],
                    limit=1,
                )
                if sessions:
                    s = sessions[0]
                    bundle["finder_session"] = {
                        "id": s.name,
                        "session_id": case.finder_session_id,
                        "status": s.status,
                        "started_on": str(s.started_on),
                        "last_seen_on": str(s.last_seen_on) if s.last_seen_on else None,
                    }
            except Exception as e:
                bundle["finder_session"] = {"error": str(e)}
        
        # Get registered item info
        if case.registered_item:
            try:
                item = frappe.get_doc("Registered Item", case.registered_item)
                bundle["registered_item"] = {
                    "name": item.name,
                    "item_name": item.item_name,
                    "status": item.status,
                    "activation_date": str(item.activation_date) if item.activation_date else None,
                }
            except Exception as e:
                bundle["registered_item"] = {"error": str(e)}
        
        # Get email queue entries for related notifications
        try:
            email_entries = frappe.get_list(
                "Email Queue",
                filters={"reference_name": case_id},
                fields=["name", "subject", "status", "creation", "executed"],
                order_by="creation desc",
                limit=10,
            )
            bundle["email_queue"] = [
                {
                    "id": e.name,
                    "subject": e.subject,
                    "status": e.status,
                    "queued_on": str(e.creation),
                    "executed_on": str(e.executed) if e.executed else None,
                }
                for e in email_entries
            ]
        except Exception as e:
            bundle["email_queue"] = {"error": str(e)}
        
        return bundle
        
    except frappe.DoesNotExistError:
        return {
            "success": False,
            "error": f"Recovery case {case_id} not found",
        }
    except Exception as e:
        logger.error(f"Error generating diagnostic bundle for {case_id}: {e}")
        return {
            "success": False,
            "error": str(e),
        }


def get_notification_diagnostic_info(notification_id: str) -> Dict[str, Any]:
    """
    Get diagnostic information for a specific notification.
    
    Args:
        notification_id: Notification Event Log name
        
    Returns:
        Dict with notification and related data
    """
    try:
        notification = frappe.get_doc("Notification Event Log", notification_id)
        
        info = {
            "success": True,
            "notification_id": notification_id,
            "generated_at": str(now_datetime()),
            "notification": {
                "name": notification.name,
                "event_type": notification.event_type,
                "channel": notification.channel,
                "status": notification.status,
                "priority": notification.priority,
                "triggered_on": str(notification.triggered_on) if notification.triggered_on else None,
                "delivered_on": str(notification.delivered_on) if notification.delivered_on else None,
                "error_message": notification.error_message,
                "retry_count": notification.retry_count,
                "last_retry_on": str(notification.last_retry_on) if notification.last_retry_on else None,
                "processing_note": notification.processing_note,
            },
        }
        
        # Get email queue entry if email channel
        if notification.channel == "Email" and notification.recovery_case:
            try:
                email_entries = frappe.get_list(
                    "Email Queue",
                    filters={"reference_name": notification.recovery_case},
                    fields=["name", "subject", "recipient", "status", "creation", "executed", "error"],
                    order_by="creation desc",
                    limit=5,
                )
                info["email_queue_entries"] = [
                    {
                        "id": e.name,
                        "subject": e.subject,
                        "recipient": e.recipient,
                        "status": e.status,
                        "queued_on": str(e.creation),
                        "executed_on": str(e.executed) if e.executed else None,
                        "error": e.error,
                    }
                    for e in email_entries
                ]
            except Exception:
                info["email_queue_entries"] = []
        
        # Get owner profile info
        if notification.owner_profile:
            try:
                owner = frappe.get_doc("Owner Profile", notification.owner_profile)
                info["owner_profile"] = {
                    "name": owner.name,
                    "user": owner.user,
                    "display_name": owner.display_name,
                }
                
                # Get notification preferences
                prefs = frappe.get_value(
                    "Notification Preference",
                    {"owner_profile": notification.owner_profile},
                    ["enable_in_app_notifications", "enable_email_notifications"],
                    as_dict=True,
                )
                if prefs:
                    info["notification_preferences"] = {
                        "in_app_enabled": bool(prefs.enable_in_app_notifications),
                        "email_enabled": bool(prefs.enable_email_notifications),
                    }
            except Exception:
                pass
        
        return info
        
    except frappe.DoesNotExistError:
        return {
            "success": False,
            "error": f"Notification {notification_id} not found",
        }
    except Exception as e:
        logger.error(f"Error getting notification diagnostics: {e}")
        return {
            "success": False,
            "error": str(e),
        }


def get_system_state_snapshot(hours: int = 24) -> Dict[str, Any]:
    """
    Get a snapshot of system state for debugging.
    
    Args:
        hours: Look back period for recent activity
        
    Returns:
        Dict with system state snapshot
    """
    try:
        cutoff = add_to_date(now_datetime(), hours=-hours)
        
        snapshot = {
            "success": True,
            "generated_at": str(now_datetime()),
            "period_hours": hours,
            "cutoff_time": str(cutoff),
        }
        
        # Count totals
        snapshot["totals"] = {
            "recovery_cases": frappe.db.count("Recovery Case"),
            "open_cases": frappe.db.count(
                "Recovery Case",
                {"status": ["in", ["Open", "Owner Responded", "Return Planned"]]}
            ),
            "notification_events": frappe.db.count("Notification Event Log"),
            "scan_events": frappe.db.count("Scan Event"),
            "finder_sessions": frappe.db.count("Finder Session"),
            "active_sessions": frappe.db.count("Finder Session", {"status": "Active"}),
            "registered_items": frappe.db.count("Registered Item"),
            "qr_batches": frappe.db.count("QR Batch"),
            "qr_tags": frappe.db.count("QR Code Tag"),
        }
        
        # Recent notifications by status
        for status in ["Sent", "Failed", "Queued", "Skipped"]:
            count = frappe.db.count(
                "Notification Event Log",
                {"status": status, "triggered_on": [">=", cutoff]}
            )
            snapshot["totals"][f"notifications_{status.lower()}"] = count
        
        # Recent activity
        snapshot["recent_activity"] = {}
        
        # Recent recovery cases
        recent_cases = frappe.get_list(
            "Recovery Case",
            filters={"modified": [">=", cutoff]},
            fields=["name", "status", "modified"],
            order_by="modified desc",
            limit=10,
        )
        snapshot["recent_activity"]["recovery_cases"] = [
            {"name": c.name, "status": c.status, "modified": str(c.modified)}
            for c in recent_cases
        ]
        
        # Recent notifications
        recent_notifs = frappe.get_list(
            "Notification Event Log",
            filters={"triggered_on": [">=", cutoff]},
            fields=["name", "event_type", "status", "triggered_on"],
            order_by="triggered_on desc",
            limit=10,
        )
        snapshot["recent_activity"]["notifications"] = [
            {"name": n.name, "event_type": n.event_type, "status": n.status, "triggered_on": str(n.triggered_on)}
            for n in recent_notifs
        ]
        
        # Failed notifications
        failed = frappe.get_list(
            "Notification Event Log",
            filters={"status": "Failed", "triggered_on": [">=", cutoff]},
            fields=["name", "event_type", "error_message", "triggered_on"],
            order_by="triggered_on desc",
            limit=10,
        )
        snapshot["recent_activity"]["failed_notifications"] = [
            {"name": f.name, "event_type": f.event_type, "error": f.error_message, "triggered_on": str(f.triggered_on)}
            for f in failed
        ]
        
        # Environment info
        try:
            from scanifyme.support.services.health_service import get_environment_health_summary
            env_health = get_environment_health_summary()
            snapshot["environment"] = {
                "overall_status": env_health.get("overall_status"),
                "checks_summary": env_health.get("summary"),
            }
        except Exception:
            snapshot["environment"] = {"error": "Could not get environment health"}
        
        return snapshot
        
    except Exception as e:
        logger.error(f"Error generating system state snapshot: {e}")
        return {
            "success": False,
            "error": str(e),
        }


def get_stale_cases_report(days_threshold: int = 7) -> Dict[str, Any]:
    """
    Get report of stale open recovery cases.
    
    A stale case is one that has been open but has had no activity
    for more than the specified threshold.
    
    Args:
        days_threshold: Days of inactivity to consider stale
        
    Returns:
        Dict with stale case information
    """
    try:
        cutoff = add_to_date(now_datetime(), days=-days_threshold)
        
        # Find open cases with no recent activity
        stale_cases = frappe.db.sql(
            """
            SELECT 
                rc.name,
                rc.case_title,
                rc.status,
                rc.opened_on,
                rc.last_activity_on,
                DATEDIFF(NOW(), COALESCE(rc.last_activity_on, rc.opened_on)) as days_inactive
            FROM `tabRecovery Case` rc
            WHERE rc.status IN ('Open', 'Owner Responded', 'Return Planned')
            AND COALESCE(rc.last_activity_on, rc.opened_on) < %(cutoff)s
            ORDER BY days_inactive DESC
            """,
            {"cutoff": cutoff},
            as_dict=True,
        )
        
        return {
            "success": True,
            "generated_at": str(now_datetime()),
            "days_threshold": days_threshold,
            "stale_count": len(stale_cases),
            "cases": [
                {
                    "name": c.name,
                    "case_title": c.case_title,
                    "status": c.status,
                    "opened_on": str(c.opened_on),
                    "last_activity_on": str(c.last_activity_on),
                    "days_inactive": c.days_inactive,
                }
                for c in stale_cases
            ],
        }
        
    except Exception as e:
        logger.error(f"Error generating stale cases report: {e}")
        return {
            "success": False,
            "error": str(e),
        }


def get_queue_failure_report() -> Dict[str, Any]:
    """
    Get report of queue/notification failures.
    
    Returns:
        Dict with failure information
    """
    try:
        # Get failed notifications
        failed_notifications = frappe.get_list(
            "Notification Event Log",
            filters={"status": "Failed"},
            fields=[
                "name", "event_type", "channel", "owner_profile",
                "recovery_case", "error_message", "triggered_on", "retry_count"
            ],
            order_by="triggered_on desc",
        )
        
        # Group by event type
        by_event_type = {}
        for n in failed_notifications:
            event_type = n.event_type
            if event_type not in by_event_type:
                by_event_type[event_type] = []
            by_event_type[event_type].append({
                "id": n.name,
                "channel": n.channel,
                "owner_profile": n.owner_profile,
                "case_id": n.recovery_case,
                "error": n.error_message,
                "triggered_on": str(n.triggered_on),
                "retry_count": n.retry_count,
            })
        
        # Get failed email queue entries
        failed_emails = frappe.get_list(
            "Email Queue",
            filters={"status": "Error"},
            fields=["name", "subject", "recipient", "error", "creation"],
            order_by="creation desc",
            limit=20,
        )
        
        return {
            "success": True,
            "generated_at": str(now_datetime()),
            "summary": {
                "total_failed_notifications": len(failed_notifications),
                "total_failed_emails": len(failed_emails),
                "event_types_with_failures": list(by_event_type.keys()),
            },
            "notifications_by_type": by_event_type,
            "failed_emails": [
                {
                    "id": e.name,
                    "subject": e.subject,
                    "recipient": e.recipient,
                    "error": e.error,
                    "queued_on": str(e.creation),
                }
                for e in failed_emails
            ],
        }
        
    except Exception as e:
        logger.error(f"Error generating queue failure report: {e}")
        return {
            "success": False,
            "error": str(e),
        }
