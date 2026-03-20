"""
Operational Health API - Admin/Operations API endpoints.

This module provides whitelisted APIs for operational visibility:
- get_operational_health_summary
- get_failed_notification_events
- retry_failed_notification_event
- get_stale_finder_sessions
- run_maintenance_job

All endpoints require admin/operations permissions.
"""

import frappe
from frappe import _
import json
from typing import Dict, Any


@frappe.whitelist()
def get_operational_health_summary() -> Dict[str, Any]:
	"""
	Get a comprehensive operational health summary.

	Returns aggregated health metrics including:
	- Notification backlog status
	- Finder session counts
	- Recovery case counts
	- Overall health status

	Returns:
	    Dict with health status and metrics
	"""
	# Check permissions - must be System Manager or ScanifyMe Admin
	if not (
		frappe.has_permission("Recovery Case", "read")
		or frappe.has_permission("Notification Event Log", "read")
	):
		frappe.throw(_("Insufficient permissions"), frappe.PermissionError)

	from scanifyme.recovery.services.cleanup_service import (
		get_operational_health_summary as cleanup_health_summary,
	)

	result = cleanup_health_summary()

	# Add additional metrics
	if result.get("success"):
		# Get database stats
		try:
			result["database"] = {
				"total_recovery_cases": frappe.db.count("Recovery Case"),
				"total_finder_sessions": frappe.db.count("Finder Session"),
				"total_notification_events": frappe.db.count("Notification Event Log"),
			}
		except Exception:
			pass

	return result


@frappe.whitelist()
def get_failed_notification_events(
	limit: int = 50,
) -> Dict[str, Any]:
	"""
	Get failed notification events for review.

	Args:
	    limit: Maximum number of events to return (default 50)

	Returns:
	    Dict with failed notification events
	"""
	# Check permissions
	if not frappe.has_permission("Notification Event Log", "read"):
		frappe.throw(_("Insufficient permissions"), frappe.PermissionError)

	try:
		events = frappe.get_list(
			"Notification Event Log",
			filters={"status": "Failed"},
			fields=[
				"name",
				"event_type",
				"owner_profile",
				"recovery_case",
				"error_message",
				"triggered_on",
				"retry_count",
				"last_retry_on",
			],
			order_by="triggered_on desc",
			limit=limit,
		)

		return {
			"success": True,
			"events": events,
			"count": len(events),
		}

	except Exception as e:
		frappe.log_error(f"Error getting failed notifications: {e}")
		return {
			"success": False,
			"error": str(e),
			"events": [],
		}


@frappe.whitelist()
def retry_failed_notification_event(
	notification_id: str,
) -> Dict[str, Any]:
	"""
	Retry a specific failed notification event.

	Args:
	    notification_id: Notification Event Log name

	Returns:
	    Dict with retry result
	"""
	# Check permissions
	if not frappe.has_permission("Notification Event Log", "write"):
		frappe.throw(_("Insufficient permissions"), frappe.PermissionError)

	try:
		# Get the notification
		notification = frappe.get_doc("Notification Event Log", notification_id)

		if notification.status != "Failed":
			return {
				"success": False,
				"error": "Notification is not in Failed status",
			}

		# Increment retry count
		retry_count = (notification.retry_count or 0) + 1
		frappe.db.set_value(
			"Notification Event Log",
			notification_id,
			{
				"retry_count": retry_count,
				"last_retry_on": frappe.utils.now_datetime(),
			},
		)

		# Attempt to resend email if applicable
		if notification.channel == "Email":
			from scanifyme.notifications.services.notification_delivery_service import (
				send_email_notification,
			)

			result = send_email_notification(
				event_type=notification.event_type,
				owner_profile=notification.owner_profile,
				recovery_case=notification.recovery_case,
				registered_item=notification.registered_item,
			)

			if result.get("success"):
				frappe.db.set_value(
					"Notification Event Log",
					notification_id,
					{
						"status": "Sent",
						"delivered_on": frappe.utils.now_datetime(),
						"processing_note": f"Retry {retry_count} succeeded",
					},
				)
			else:
				frappe.db.set_value(
					"Notification Event Log",
					notification_id,
					{
						"processing_note": f"Retry {retry_count} failed: {result.get('reason')}",
					},
				)
				return {
					"success": False,
					"error": result.get("reason", "Retry failed"),
				}

		frappe.db.commit()

		return {
			"success": True,
			"message": f"Notification retry initiated (attempt {retry_count})",
		}

	except Exception as e:
		frappe.log_error(f"Error retrying notification {notification_id}: {e}")
		frappe.db.rollback()
		return {
			"success": False,
			"error": str(e),
		}


@frappe.whitelist()
def get_stale_finder_sessions(
	status: str = "Expired",
	limit: int = 50,
) -> Dict[str, Any]:
	"""
	Get stale finder sessions for review.

	Args:
	    status: Session status to filter (default: Expired)
	    limit: Maximum number of sessions to return

	Returns:
	    Dict with finder sessions
	"""
	# Check permissions
	if not frappe.has_permission("Finder Session", "read"):
		frappe.throw(_("Insufficient permissions"), frappe.PermissionError)

	try:
		sessions = frappe.get_list(
			"Finder Session",
			filters={"status": status},
			fields=[
				"name",
				"session_id",
				"qr_code_tag",
				"started_on",
				"last_seen_on",
				"status",
			],
			order_by="started_on desc",
			limit=limit,
		)

		return {
			"success": True,
			"sessions": sessions,
			"count": len(sessions),
		}

	except Exception as e:
		return {
			"success": False,
			"error": str(e),
			"sessions": [],
		}


@frappe.whitelist()
def run_maintenance_job(
	job_name: str,
) -> Dict[str, Any]:
	"""
	Run a maintenance job manually.

	Args:
	    job_name: Name of the maintenance job to run

	Returns:
	    Dict with job execution result
	"""
	# Check permissions - must be System Manager
	if not frappe.has_permission("System Manager"):
		frappe.throw(_("Insufficient permissions"), frappe.PermissionError)

	try:
		if job_name == "expire_stale_finder_sessions":
			from scanifyme.recovery.services.cleanup_service import (
				expire_stale_finder_sessions,
			)

			result = expire_stale_finder_sessions()

		elif job_name == "close_completed_sessions":
			from scanifyme.recovery.services.cleanup_service import (
				close_completed_sessions,
			)

			result = close_completed_sessions()

		elif job_name == "recompute_case_metadata":
			from scanifyme.recovery.services.cleanup_service import (
				recompute_case_latest_metadata,
			)

			result = recompute_case_latest_metadata()

		elif job_name == "cleanup_scan_events":
			from scanifyme.recovery.services.cleanup_service import (
				cleanup_old_scan_events,
			)

			result = cleanup_old_scan_events()

		elif job_name == "health_check_notifications":
			from scanifyme.recovery.services.cleanup_service import (
				health_check_notification_backlog,
			)

			result = health_check_notification_backlog()

		elif job_name == "process_failed_notifications":
			from scanifyme.notifications.services.reliability_service import (
				process_failed_notifications,
			)

			result = process_failed_notifications()

		else:
			return {
				"success": False,
				"error": f"Unknown maintenance job: {job_name}",
			}

		return result

	except Exception as e:
		frappe.log_error(f"Error running maintenance job {job_name}: {e}")
		return {
			"success": False,
			"error": str(e),
		}


@frappe.whitelist()
def recompute_recovery_case_metadata(
	case_id: str,
) -> Dict[str, Any]:
	"""
	Recompute metadata for a specific recovery case.

	Args:
	    case_id: Recovery Case name

	Returns:
	    Dict with recomputation result
	"""
	# Check permissions
	if not frappe.has_permission("Recovery Case", "write"):
		frappe.throw(_("Insufficient permissions"), frappe.PermissionError)

	try:
		from scanifyme.notifications.services.reliability_service import (
			update_case_metadata,
		)

		result = update_case_metadata(case_id)
		return result

	except Exception as e:
		return {
			"success": False,
			"error": str(e),
		}


@frappe.whitelist()
def get_notification_queue_status() -> Dict[str, Any]:
	"""
	Get the current notification queue status.

	Returns:
	    Dict with queue statistics
	"""
	# Check permissions
	if not frappe.has_permission("Notification Event Log", "read"):
		frappe.throw(_("Insufficient permissions"), frappe.PermissionError)

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
