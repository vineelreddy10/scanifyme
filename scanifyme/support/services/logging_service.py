"""
Logging Service - Structured logging and event tracking for ScanifyMe.

This module provides:
- log_scanifyme_event(): Log important workflow events
- log_scanifyme_error(): Log errors with structured context
- Event category constants
- Sensitive data sanitization

Usage:
    from scanifyme.support.services.logging_service import (
        log_scanifyme_event,
        log_scanifyme_error,
        EventCategory,
    )
"""

import frappe
import logging
from frappe.utils import now_datetime
from typing import Optional, Dict, Any, List
from datetime import datetime

logger = logging.getLogger(__name__)


class EventCategory:
    """Event category constants for classification."""
    QR_ACTIVATION = "qr_activation"
    PUBLIC_SCAN = "public_scan"
    FINDER_MESSAGE = "finder_message"
    LOCATION_SHARE = "location_share"
    RECOVERY_STATUS = "recovery_status"
    OWNER_REPLY = "owner_reply"
    NOTIFICATION = "notification"
    EMAIL_QUEUE = "email_queue"
    CRUD_OPERATION = "crud_operation"
    MAINTENANCE = "maintenance"
    SYSTEM = "system"


class EventSeverity:
    """Event severity levels."""
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


# Fields that should never be logged
SENSITIVE_FIELDS = frozenset([
    "password",
    "pwd",
    "secret",
    "token",
    "api_key",
    "api_secret",
    "access_token",
    "refresh_token",
    "session_key",
    "authorization",
    "cookie",
    "csrf_token",
    "credit_card",
    "card_number",
    "ssn",
])


def sanitize_dict(data: Dict[str, Any], max_length: int = 500) -> Dict[str, Any]:
    """
    Remove or mask sensitive fields from a dictionary.
    
    Args:
        data: Dictionary to sanitize
        max_length: Maximum length for string values
        
    Returns:
        Sanitized dictionary safe for logging
    """
    if not data:
        return {}
    
    result = {}
    for key, value in data.items():
        key_lower = key.lower()
        
        # Skip sensitive fields
        if any(s in key_lower for s in SENSITIVE_FIELDS):
            result[key] = "[REDACTED]"
            continue
        
        # Handle nested dicts
        if isinstance(value, dict):
            result[key] = sanitize_dict(value, max_length)
        # Handle lists
        elif isinstance(value, list):
            result[key] = [
                sanitize_dict(item, max_length) if isinstance(item, dict) else item
                for item in value[:10]  # Limit list size
            ]
        # Handle strings - truncate
        elif isinstance(value, str) and len(value) > max_length:
            result[key] = value[:max_length] + "..."
        else:
            result[key] = value
    
    return result


def log_scanifyme_event(
    category: str,
    action: str,
    doctype: Optional[str] = None,
    docname: Optional[str] = None,
    actor_type: str = "System",
    actor_id: Optional[str] = None,
    severity: str = EventSeverity.INFO,
    context: Optional[Dict[str, Any]] = None,
    metadata: Optional[Dict[str, Any]] = None,
) -> str:
    """
    Log an important ScanifyMe workflow event.
    
    This function provides structured logging for important business events,
    making it easy to trace what happened in the system.
    
    Args:
        category: Event category (use EventCategory constants)
        action: What happened (e.g., "activated", "submitted", "updated")
        doctype: Related DocType (optional)
        docname: Related document name (optional)
        actor_type: Who triggered this (System, Owner, Finder, Admin)
        actor_id: Identifier for the actor (optional)
        severity: Event severity (default: INFO)
        context: Additional context dict (will be sanitized)
        metadata: Metadata that won't be sanitized (use carefully)
        
    Returns:
        Event tracking ID (for correlation)
    """
    # Sanitize context to remove sensitive data
    safe_context = sanitize_dict(context or {})
    
    # Build log message
    log_parts = [
        f"[ScanifyMe:{category}]",
        f"{action}",
    ]
    
    if doctype and docname:
        log_parts.append(f"on {doctype}:{docname}")
    
    if actor_type:
        log_parts.append(f"by {actor_type}")
        if actor_id:
            log_parts.append(f"({actor_id})")
    
    log_message = " ".join(log_parts)
    
    # Log to Python logger
    log_level = getattr(logging, severity.upper(), logging.INFO)
    logger.log(log_level, log_message, extra={
        "scanifyme_category": category,
        "scanifyme_action": action,
        "scanifyme_doctype": doctype,
        "scanifyme_docname": docname,
        "scanifyme_actor_type": actor_type,
        "scanifyme_actor_id": actor_id,
        "scanifyme_context": safe_context,
    })
    
    # Also log to Frappe's error log for important events
    if severity in (EventSeverity.WARNING, EventSeverity.ERROR, EventSeverity.CRITICAL):
        frappe.logger().warning(log_message)
    
    # Return tracking ID for correlation
    return f"{category}:{action}:{now_datetime().strftime('%Y%m%d%H%M%S')}"


def log_scanifyme_error(
    error: Exception,
    category: str,
    action: str,
    doctype: Optional[str] = None,
    docname: Optional[str] = None,
    context: Optional[Dict[str, Any]] = None,
    reraise: bool = False,
) -> str:
    """
    Log an error with structured context for debugging.
    
    Args:
        error: The exception that occurred
        category: Error category (use EventCategory constants)
        action: What was being attempted
        doctype: Related DocType (optional)
        docname: Related document name (optional)
        context: Additional context dict (will be sanitized)
        reraise: Whether to re-raise the exception after logging
        
    Returns:
        Error tracking ID
        
    Raises:
        The original exception if reraise is True
    """
    # Sanitize context
    safe_context = sanitize_dict(context or {})
    
    # Build error message
    error_type = type(error).__name__
    error_message = str(error)
    
    log_parts = [
        f"[ScanifyMe:ERROR:{category}]",
        f"{action}",
        f"failed with {error_type}: {error_message}",
    ]
    
    if doctype and docname:
        log_parts.append(f"on {doctype}:{docname}")
    
    log_message = " ".join(log_parts)
    
    # Log to Python logger
    logger.error(log_message, extra={
        "scanifyme_category": category,
        "scanifyme_action": action,
        "scanifyme_doctype": doctype,
        "scanifyme_docname": docname,
        "scanifyme_error_type": error_type,
        "scanifyme_context": safe_context,
        "scanifyme_traceback": frappe.get_traceback() if hasattr(frappe, 'get_traceback') else None,
    })
    
    # Log to Frappe's error log
    frappe.log_error(
        title=f"ScanifyMe Error: {category}/{action}",
        message=f"""
Category: {category}
Action: {action}
Doctype: {doctype}
Docname: {docname}
Error Type: {error_type}
Error Message: {error_message}

Context:
{frappe.as_json(safe_context) if safe_context else 'None'}

Traceback:
{frappe.get_traceback() if hasattr(frappe, 'get_traceback') else 'N/A'}
        """.strip()
    )
    
    # Return tracking ID
    tracking_id = f"ERR:{category}:{error_type}:{now_datetime().strftime('%Y%m%d%H%M%S')}"
    
    if reraise:
        raise
    
    return tracking_id


def log_workflow_event(
    workflow_name: str,
    step: str,
    status: str,
    input_data: Optional[Dict[str, Any]] = None,
    output_data: Optional[Dict[str, Any]] = None,
    error: Optional[str] = None,
) -> str:
    """
    Log a multi-step workflow event.
    
    Args:
        workflow_name: Name of the workflow
        step: Current step in the workflow
        status: Status (started, completed, failed)
        input_data: Input data (will be sanitized)
        output_data: Output data (will be sanitized)
        error: Error message if failed
        
    Returns:
        Event tracking ID
    """
    safe_input = sanitize_dict(input_data or {})
    safe_output = sanitize_dict(output_data or {})
    
    log_message = f"[Workflow:{workflow_name}] Step '{step}' {status}"
    if error:
        log_message += f" - Error: {error}"
    
    logger.info(log_message, extra={
        "workflow_name": workflow_name,
        "workflow_step": step,
        "workflow_status": status,
        "workflow_input": safe_input,
        "workflow_output": safe_output,
    })
    
    return f"WF:{workflow_name}:{step}:{status}:{now_datetime().strftime('%Y%m%d%H%M%S')}"


def get_recent_events(
    category: Optional[str] = None,
    hours: int = 24,
    limit: int = 100,
) -> List[Dict[str, Any]]:
    """
    Get recent error log entries for ScanifyMe.
    
    Args:
        category: Filter by category (optional)
        hours: Look back period in hours
        limit: Maximum number of entries
        
    Returns:
        List of recent error entries
    """
    # Get recent error logs
    filters = {
        "creation": [">=", frappe.utils.add_to_date(now_datetime(), hours=-hours)],
    }
    
    if category:
        filters["title"] = ["like", f"%{category}%"]
    
    # This would query the Error Log doctype
    # For now, return empty list as this is advisory
    try:
        errors = frappe.get_list(
            "Error Log",
            filters=filters,
            fields=["name", "title", "error", "creation", "modified"],
            order_by="creation desc",
            limit=limit,
        )
        
        result = []
        for err in errors:
            result.append({
                "id": err.name,
                "title": err.title,
                "error": err.error[:500] if err.error else None,
                "created_on": err.creation,
                "modified_on": err.modified,
            })
        
        return result
    except Exception:
        return []


# Convenience functions for common event types

def log_qr_activation(token: str, user: str, success: bool, item_id: str = None) -> str:
    """Log a QR activation event."""
    return log_scanifyme_event(
        category=EventCategory.QR_ACTIVATION,
        action="activated" if success else "activation_failed",
        doctype="QR Code Tag",
        docname=token,
        actor_type="Owner",
        actor_id=user,
        severity=EventSeverity.INFO if success else EventSeverity.WARNING,
        context={
            "token": token,
            "user": user,
            "item_created": item_id is not None,
        },
    )


def log_finder_message(
    token: str,
    case_id: str,
    finder_name: str = None,
    success: bool = True,
) -> str:
    """Log a finder message submission."""
    return log_scanifyme_event(
        category=EventCategory.FINDER_MESSAGE,
        action="submitted" if success else "submission_failed",
        doctype="Recovery Message",
        docname=case_id,
        actor_type="Finder",
        actor_id=finder_name,
        severity=EventSeverity.INFO if success else EventSeverity.WARNING,
        context={
            "token": token,
            "case_id": case_id,
            "finder_name": finder_name,
        },
    )


def log_recovery_status_change(
    case_id: str,
    old_status: str,
    new_status: str,
    actor_type: str = "Owner",
    actor_id: str = None,
) -> str:
    """Log a recovery case status change."""
    return log_scanifyme_event(
        category=EventCategory.RECOVERY_STATUS,
        action="status_updated",
        doctype="Recovery Case",
        docname=case_id,
        actor_type=actor_type,
        actor_id=actor_id,
        severity=EventSeverity.INFO,
        context={
            "case_id": case_id,
            "old_status": old_status,
            "new_status": new_status,
        },
    )


def log_notification_event(
    event_type: str,
    notification_id: str,
    status: str,
    channel: str = "In App",
    error: str = None,
) -> str:
    """Log a notification event."""
    return log_scanifyme_event(
        category=EventCategory.NOTIFICATION,
        action=event_type,
        doctype="Notification Event Log",
        docname=notification_id,
        actor_type="System",
        severity=EventSeverity.ERROR if status == "Failed" else EventSeverity.INFO,
        context={
            "event_type": event_type,
            "notification_id": notification_id,
            "status": status,
            "channel": channel,
            "error": error,
        },
    )


def log_email_queue_event(
    notification_id: str,
    email_account: str,
    status: str,
    error: str = None,
) -> str:
    """Log an email queue event."""
    return log_scanifyme_event(
        category=EventCategory.EMAIL_QUEUE,
        action="email_queued",
        doctype="Notification Event Log",
        docname=notification_id,
        actor_type="System",
        severity=EventSeverity.ERROR if status == "Failed" else EventSeverity.INFO,
        context={
            "notification_id": notification_id,
            "email_account": email_account,
            "status": status,
            "error": error,
        },
    )
