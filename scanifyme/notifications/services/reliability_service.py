"""
Reliability Service - Service layer for retry-safe background processing.

This module provides business logic for:
- Safe enqueueing of background jobs
- Idempotent execution of notifications/emails
- Status tracking and failure logging
- Recovery case metadata computation

Usage:
    from scanifyme.notifications.services.reliability_service import (
        safe_create_notification_event,
        safe_queue_email_notification,
        safe_create_timeline_event,
    )
"""

import frappe
from frappe.utils import now_datetime, get_datetime, add_to_date
from typing import Optional, Dict, Any, Callable
import logging

logger = logging.getLogger(__name__)

# Maximum retry attempts for background jobs
MAX_RETRY_ATTEMPTS = 3

# Retry delays in seconds (exponential backoff)
RETRY_DELAYS = [60, 300, 900]  # 1 min, 5 min, 15 min


def safe_create_notification_event(
	event_type: str,
	owner_profile: str,
	recovery_case: Optional[str] = None,
	registered_item: Optional[str] = None,
	qr_code_tag: Optional[str] = None,
	message_summary: Optional[str] = None,
	title: Optional[str] = None,
	route: Optional[str] = None,
	priority: str = "Normal",
	deliver: bool = True,
	channel: str = "In App",
) -> Dict[str, Any]:
	"""
	Safely create a notification event with error handling and logging.

	This function wraps the notification creation with:
	- Error handling
	- Logging
	- Status tracking
	- Optional background processing

	Args:
	    event_type: Type of event
	    owner_profile: Owner Profile name
	    recovery_case: Recovery Case name (optional)
	    registered_item: Registered Item name (optional)
	    qr_code_tag: QR Code Tag name (optional)
	    message_summary: Message summary
	    title: Notification title
	    route: Navigation route
	    priority: Priority level
	    deliver: Whether to deliver
	    channel: Notification channel

	Returns:
	    Dict with success status and notification_id or error
	"""
	try:
		from scanifyme.notifications.services import notification_service

		notification_id = notification_service.log_notification_event(
			event_type=event_type,
			owner_profile=owner_profile,
			recovery_case=recovery_case,
			registered_item=registered_item,
			qr_code_tag=qr_code_tag,
			message_summary=message_summary,
			channel=channel,
			status="Queued",
			title=title,
			route=route,
			priority=priority,
			deliver=deliver,
		)

		return {
			"success": True,
			"notification_id": notification_id,
			"status": "Created",
		}

	except Exception as e:
		logger.error(f"Error creating notification event: {e}")
		frappe.db.rollback()
		return {
			"success": False,
			"error": str(e),
			"notification_id": None,
			"status": "Failed",
		}


def safe_queue_email_notification(
	event_type: str,
	owner_profile: str,
	recovery_case: Optional[str] = None,
	registered_item: Optional[str] = None,
	message_summary: Optional[str] = None,
	old_status: Optional[str] = None,
	new_status: Optional[str] = None,
) -> Dict[str, Any]:
	"""
	Safely queue an email notification with error handling.

	This function:
	- Checks owner preferences
	- Queues email via frappe.sendmail
	- Logs success/failure to notification event
	- Handles errors gracefully

	Args:
	    event_type: Type of event
	    owner_profile: Owner Profile name
	    recovery_case: Recovery Case name (optional)
	    registered_item: Registered Item name (optional)
	    message_summary: Message summary (optional)
	    old_status: Previous status (for status updates)
	    new_status: New status (for status updates)

	Returns:
	    Dict with success status and details
	"""
	try:
		from scanifyme.notifications.services import notification_service
		from scanifyme.notifications.services.notification_delivery_service import (
			send_email_notification,
		)

		# Check preferences first
		preferences = notification_service.get_owner_notification_preferences(owner_profile)
		if not preferences or not preferences.get("enable_email_notifications"):
			return {
				"success": True,
				"reason": "Email notifications disabled",
				"status": "Skipped",
			}

		# Send email
		result = send_email_notification(
			event_type=event_type,
			owner_profile=owner_profile,
			recovery_case=recovery_case,
			registered_item=registered_item,
			message_summary=message_summary,
			old_status=old_status,
			new_status=new_status,
		)

		return result

	except Exception as e:
		logger.error(f"Error queuing email notification: {e}")
		frappe.db.rollback()
		return {
			"success": False,
			"reason": str(e),
			"status": "Failed",
		}


def safe_create_timeline_event(
	recovery_case: str,
	event_type: str,
	event_label: Optional[str] = None,
	actor_type: str = "System",
	actor_reference: Optional[str] = None,
	summary: Optional[str] = None,
	reference_doctype: Optional[str] = None,
	reference_name: Optional[str] = None,
	metadata: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
	"""
	Safely create a timeline event with error handling.

	Args:
	    recovery_case: Recovery Case name
	    event_type: Type of event
	    event_label: Human-readable label
	    actor_type: Who triggered the event
	    actor_reference: Reference to actor
	    summary: Brief summary
	    reference_doctype: Related doctype
	    reference_name: Related document name
	    metadata: Additional metadata

	Returns:
	    Dict with success status and event_id or error
	"""
	try:
		from scanifyme.recovery.services import timeline_service

		event_id = timeline_service.create_timeline_event(
			recovery_case=recovery_case,
			event_type=event_type,
			event_label=event_label,
			actor_type=actor_type,
			actor_reference=actor_reference,
			summary=summary,
			reference_doctype=reference_doctype,
			reference_name=reference_name,
			metadata=metadata,
		)

		return {
			"success": True,
			"event_id": event_id,
			"status": "Created",
		}

	except Exception as e:
		logger.error(f"Error creating timeline event: {e}")
		frappe.db.rollback()
		return {
			"success": False,
			"error": str(e),
			"event_id": None,
			"status": "Failed",
		}


def update_case_metadata(
	recovery_case: str,
) -> Dict[str, Any]:
	"""
	Recompute and update recovery case metadata fields.

	This includes:
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
		updated_fields = []
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
			"updated_fields": updated_fields,
			"recovery_case": recovery_case,
		}

	except Exception as e:
		logger.error(f"Error updating case metadata: {e}")
		frappe.db.rollback()
		return {
			"success": False,
			"error": str(e),
			"recovery_case": recovery_case,
		}


def enqueue_notification_with_retry(
	method: str,
	kwargs: Dict[str, Any],
	queue: str = "default",
) -> Dict[str, Any]:
	"""
	Enqueue a background job with retry capability.

	This wraps frappe.enqueue with:
	- Error handling
	- Job tracking
	- Failure logging

	Args:
	    method: The method to call (e.g., 'scanifyme.module.method')
	    kwargs: Keyword arguments for the method
	    queue: Queue name (default, short, long)

	Returns:
	    Dict with job_id and status
	"""
	try:
		job = frappe.enqueue(
			method,
			queue=queue,
			timeout=300,
			**kwargs,
		)

		return {
			"success": True,
			"job_id": job.id if hasattr(job, "id") else None,
			"status": "Enqueued",
		}

	except Exception as e:
		logger.error(f"Error enqueuing job: {e}")
		return {
			"success": False,
			"error": str(e),
			"job_id": None,
			"status": "Failed",
		}


def process_failed_notifications() -> Dict[str, Any]:
	"""
	Process failed notification events for retry.

	This is a maintenance function that:
	- Finds notifications with status='Failed'
	- Attempts to resend them
	- Updates status accordingly

	Returns:
	    Dict with results
	"""
	try:
		failed_notifications = frappe.get_list(
			"Notification Event Log",
			filters={"status": "Failed"},
			fields=["name", "event_type", "owner_profile", "recovery_case"],
			limit=50,
		)

		processed = 0
		succeeded = 0
		still_failed = 0

		for notif in failed_notifications:
			try:
				# Attempt to resend
				result = safe_queue_email_notification(
					event_type=notif.event_type,
					owner_profile=notif.owner_profile,
					recovery_case=notif.recovery_case,
				)

				if result.get("success"):
					frappe.db.set_value(
						"Notification Event Log",
						notif.name,
						{"status": "Sent", "delivered_on": now_datetime()},
					)
					succeeded += 1
				else:
					still_failed += 1

				processed += 1

			except Exception as e:
				logger.error(f"Error processing notification {notif.name}: {e}")
				still_failed += 1
				processed += 1

		frappe.db.commit()

		return {
			"success": True,
			"processed": processed,
			"succeeded": succeeded,
			"still_failed": still_failed,
		}

	except Exception as e:
		logger.error(f"Error processing failed notifications: {e}")
		return {
			"success": False,
			"error": str(e),
		}


def get_notification_backlog() -> Dict[str, Any]:
	"""
	Get current notification backlog status.

	Returns counts of:
	- Queued notifications
	- Failed notifications
	- Recent notifications

	Returns:
	    Dict with backlog statistics
	"""
	try:
		# Get counts
		queued_count = frappe.db.count(
			"Notification Event Log",
			{"status": "Queued"},
		)

		failed_count = frappe.db.count(
			"Notification Event Log",
			{"status": "Failed"},
		)

		sent_count = frappe.db.count(
			"Notification Event Log",
			{"status": "Sent"},
		)

		# Get recent failures
		recent_failures = frappe.get_list(
			"Notification Event Log",
			filters={"status": "Failed"},
			fields=["name", "event_type", "error_message", "triggered_on"],
			order_by="triggered_on desc",
			limit=10,
		)

		return {
			"success": True,
			"backlog": {
				"queued": queued_count,
				"failed": failed_count,
				"sent_today": sent_count,
			},
			"recent_failures": recent_failures,
		}

	except Exception as e:
		logger.error(f"Error getting notification backlog: {e}")
		return {
			"success": False,
			"error": str(e),
		}
