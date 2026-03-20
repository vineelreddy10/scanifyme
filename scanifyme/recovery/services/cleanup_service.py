"""
Cleanup and Maintenance Service - Service layer for scheduled cleanup jobs.

This module provides business logic for:
- Expiring stale finder sessions
- Cleaning up old duplicate suppression cache
- Recomputing case metadata
- Health check notifications

Usage:
    from scanifyme.recovery.services.cleanup_service import (
        expire_stale_finder_sessions,
        cleanup_duplicate_suppression_cache,
        recompute_case_latest_metadata,
        health_check_notification_backlog,
    )
"""

import frappe
from frappe.utils import now_datetime, add_to_date, get_datetime
from typing import Dict, Any, List
import logging

logger = logging.getLogger(__name__)

# Finder session expiration settings
FINDER_SESSION_EXPIRY_HOURS = 24  # Sessions older than 24 hours are stale
FINDER_SESSION_INACTIVE_HOURS = 2  # Inactive sessions older than 2 hours


def expire_stale_finder_sessions() -> Dict[str, Any]:
	"""
	Expire finder sessions that are stale or inactive.

	A session is considered stale if:
	- It has been inactive for more than FINDER_SESSION_INACTIVE_HOURS
	- It has been active but not updated in FINDER_SESSION_EXPIRY_HOURS

	This does NOT delete the sessions, just marks them as Expired.

	Returns:
	    Dict with success status and counts
	"""
	try:
		now = now_datetime()

		# Calculate thresholds
		inactive_threshold = add_to_date(now, hours=-FINDER_SESSION_INACTIVE_HOURS, as_datetime=True)
		expiry_threshold = add_to_date(now, hours=-FINDER_SESSION_EXPIRY_HOURS, as_datetime=True)

		# Find sessions to expire
		# 1. Active sessions that haven't been seen in 2 hours
		inactive_sessions = frappe.get_list(
			"Finder Session",
			filters={
				"status": "Active",
				"last_seen_on": ["<", inactive_threshold],
			},
			fields=["name", "session_id", "last_seen_on"],
		)

		# 2. Active sessions that were started but never updated in 24 hours
		old_sessions = frappe.get_list(
			"Finder Session",
			filters={
				"status": "Active",
				"started_on": ["<", expiry_threshold],
			},
			fields=["name", "session_id", "started_on"],
		)

		# Combine unique session names
		session_names = set([s.name for s in inactive_sessions] + [s.name for s in old_sessions])

		expired_count = 0
		for session_name in session_names:
			try:
				frappe.db.set_value(
					"Finder Session",
					session_name,
					{"status": "Expired", "last_seen_on": now},
				)
				expired_count += 1
			except Exception as e:
				logger.error(f"Error expiring session {session_name}: {e}")

		if expired_count > 0:
			frappe.db.commit()

		return {
			"success": True,
			"expired_count": expired_count,
			"inactive_count": len(inactive_sessions),
			"old_count": len(old_sessions),
			"message": f"Expired {expired_count} stale finder sessions",
		}

	except Exception as e:
		logger.error(f"Error expiring stale finder sessions: {e}")
		frappe.db.rollback()
		return {
			"success": False,
			"error": str(e),
		}


def close_completed_sessions() -> Dict[str, Any]:
	"""
	Close finder sessions associated with completed recovery cases.

	When a recovery case is closed (Recovered, Closed, Invalid, Spam),
	the associated finder session can be marked as Closed.

	Returns:
	    Dict with success status and counts
	"""
	try:
		# Find active sessions with closed cases
		closed_case_sessions = frappe.db.sql(
			"""
            SELECT fs.name, fs.session_id
            FROM `tabFinder Session` fs
            INNER JOIN `tabRecovery Case` rc ON rc.finder_session_id = fs.session_id
            WHERE fs.status = 'Active'
            AND rc.status IN ('Recovered', 'Closed', 'Invalid', 'Spam')
            """,
			as_dict=True,
		)

		closed_count = 0
		for session in closed_case_sessions:
			try:
				frappe.db.set_value(
					"Finder Session",
					session.name,
					{"status": "Closed"},
				)
				closed_count += 1
			except Exception as e:
				logger.error(f"Error closing session {session.name}: {e}")

		if closed_count > 0:
			frappe.db.commit()

		return {
			"success": True,
			"closed_count": closed_count,
			"message": f"Closed {closed_count} finder sessions for completed cases",
		}

	except Exception as e:
		logger.error(f"Error closing completed sessions: {e}")
		frappe.db.rollback()
		return {
			"success": False,
			"error": str(e),
		}


def cleanup_duplicate_suppression_cache() -> Dict[str, Any]:
	"""
	Clean up old duplicate suppression cache entries.

	This is a placeholder for future cache-based deduplication.
	Currently, deduplication is done via time-window queries,
	so no cache cleanup is needed.

	Returns:
	    Dict with success status
	"""
	# Currently, we use time-window based deduplication which doesn't
	# require explicit cache cleanup. This function is a placeholder
	# for future cache-based approaches.
	return {
		"success": True,
		"cleaned": 0,
		"message": "No cache cleanup needed - using time-window deduplication",
	}


def recompute_case_latest_metadata(
	recovery_case: Optional[str] = None,
) -> Dict[str, Any]:
	"""
	Recompute latest metadata fields for recovery cases.

	This updates:
	- latest_event_on: Most recent timeline event time
	- latest_location_on: Most recent location share time
	- latest_notification_on: Most recent notification time

	Args:
	    recovery_case: Specific case to recompute (optional, processes all if None)

	Returns:
	    Dict with success status and counts
	"""
	try:
		from scanifyme.notifications.services.reliability_service import (
			update_case_metadata,
		)

		# Get cases to update
		if recovery_case:
			cases = [{"name": recovery_case}]
		else:
			cases = frappe.get_list(
				"Recovery Case",
				filters={"status": ["in", ["Open", "Owner Responded", "Return Planned"]]},
				fields=["name"],
			)

		updated_count = 0
		failed_count = 0

		for case in cases:
			try:
				result = update_case_metadata(case.name)
				if result.get("success"):
					updated_count += 1
				else:
					failed_count += 1
			except Exception as e:
				logger.error(f"Error updating metadata for {case.name}: {e}")
				failed_count += 1

		return {
			"success": True,
			"total_cases": len(cases),
			"updated": updated_count,
			"failed": failed_count,
			"message": f"Recomputed metadata for {updated_count} cases",
		}

	except Exception as e:
		logger.error(f"Error recomputing case metadata: {e}")
		return {
			"success": False,
			"error": str(e),
		}


def health_check_notification_backlog() -> Dict[str, Any]:
	"""
	Perform health check on notification backlog.

	Returns:
	    Dict with health status and statistics
	"""
	try:
		from scanifyme.notifications.services.reliability_service import (
			get_notification_backlog,
		)

		backlog = get_notification_backlog()

		if not backlog.get("success"):
			return backlog

		# Determine health status
		failed_count = backlog.get("backlog", {}).get("failed", 0)
		queued_count = backlog.get("backlog", {}).get("queued", 0)

		health_status = "healthy"
		issues = []

		if failed_count > 10:
			health_status = "critical"
			issues.append(f"{failed_count} failed notifications need attention")
		elif failed_count > 5:
			health_status = "warning"
			issues.append(f"{failed_count} failed notifications")

		if queued_count > 100:
			health_status = "warning" if health_status == "healthy" else health_status
			issues.append(f"{queued_count} queued notifications")

		return {
			"success": True,
			"health_status": health_status,
			"issues": issues,
			"backlog": backlog.get("backlog"),
			"recent_failures": backlog.get("recent_failures"),
		}

	except Exception as e:
		logger.error(f"Error checking notification backlog: {e}")
		return {
			"success": False,
			"error": str(e),
		}


def cleanup_old_scan_events(days_old: int = 90) -> Dict[str, Any]:
	"""
	Clean up old scan events that are no longer needed.

	Only deletes scan events that:
	- Are older than specified days
	- Are not linked to active recovery cases

	Args:
	    days_old: Delete events older than this many days

	Returns:
	    Dict with success status and counts
	"""
	try:
		threshold_date = add_to_date(now_datetime(), days=-days_old, as_datetime=True)

		# Find old scan events not linked to active cases
		old_events = frappe.db.sql(
			"""
            SELECT se.name
            FROM `tabScan Event` se
            LEFT JOIN `tabRecovery Case` rc ON rc.name = se.registered_item
            WHERE se.creation < %(threshold)s
            AND (rc.status IS NULL OR rc.status NOT IN ('Open', 'Owner Responded', 'Return Planned'))
            LIMIT 1000
            """,
			{"threshold": threshold_date},
			as_dict=True,
		)

		deleted_count = 0
		for event in old_events:
			try:
				frappe.delete_doc("Scan Event", event.name, ignore_permissions=True)
				deleted_count += 1
			except Exception as e:
				logger.error(f"Error deleting scan event {event.name}: {e}")

		if deleted_count > 0:
			frappe.db.commit()

		return {
			"success": True,
			"deleted_count": deleted_count,
			"message": f"Deleted {deleted_count} old scan events",
		}

	except Exception as e:
		logger.error(f"Error cleaning up scan events: {e}")
		frappe.db.rollback()
		return {
			"success": False,
			"error": str(e),
		}


def get_operational_health_summary() -> Dict[str, Any]:
	"""
	Get a comprehensive operational health summary.

	This aggregates multiple health checks:
	- Notification backlog
	- Finder sessions
	- Recovery cases

	Returns:
	    Dict with overall health status and details
	"""
	try:
		# Get notification backlog health
		notification_health = health_check_notification_backlog()

		# Get finder session stats
		active_sessions = frappe.db.count(
			"Finder Session",
			{"status": "Active"},
		)

		expired_sessions = frappe.db.count(
			"Finder Session",
			{"status": "Expired"},
		)

		# Get recovery case stats
		open_cases = frappe.db.count(
			"Recovery Case",
			{"status": ["in", ["Open", "Owner Responded", "Return Planned"]]},
		)

		closed_cases = frappe.db.count(
			"Recovery Case",
			{"status": ["in", ["Recovered", "Closed", "Invalid", "Spam"]]},
		)

		# Determine overall health
		overall_status = "healthy"
		issues = []

		if notification_health.get("health_status") == "critical":
			overall_status = "critical"
			issues.extend(notification_health.get("issues", []))
		elif notification_health.get("health_status") == "warning":
			overall_status = "warning"
			issues.extend(notification_health.get("issues", []))

		return {
			"success": True,
			"overall_status": overall_status,
			"issues": issues,
			"notifications": notification_health.get("backlog"),
			"finder_sessions": {
				"active": active_sessions,
				"expired": expired_sessions,
			},
			"recovery_cases": {
				"open": open_cases,
				"closed": closed_cases,
			},
		}

	except Exception as e:
		logger.error(f"Error getting operational health summary: {e}")
		return {
			"success": False,
			"error": str(e),
		}


# Import Optional for type hint
from typing import Optional
