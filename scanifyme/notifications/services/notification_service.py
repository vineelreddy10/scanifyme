"""
Notification Service - Service layer for notification management.

This module provides business logic for:
- Logging notification events
- Managing owner notification preferences
- Determining when to send notifications
- Email notification delivery
"""

import frappe
from frappe.utils import now_datetime
from typing import Optional


def log_notification_event(
	event_type: str,
	owner_profile: str,
	channel: str = "In App",
	status: str = "Queued",
	recovery_case: Optional[str] = None,
	registered_item: Optional[str] = None,
	qr_code_tag: Optional[str] = None,
	message_summary: Optional[str] = None,
	error_message: Optional[str] = None,
	reference_doctype: Optional[str] = None,
	reference_name: Optional[str] = None,
	deliver: bool = True,
	title: Optional[str] = None,
	route: Optional[str] = None,
	priority: str = "Normal",
) -> str:
	"""
	Log a notification event.

	Args:
	    event_type: Type of event (Finder Message Received, Recovery Case Opened, etc.)
	    owner_profile: Owner Profile name
	    channel: Notification channel (In App, Email, System)
	    status: Notification status (Queued, Sent, Failed, Skipped)
	    recovery_case: Recovery Case name (optional)
	    registered_item: Registered Item name (optional)
	    qr_code_tag: QR Code Tag name (optional)
	    message_summary: Summary of the message (optional)
	    error_message: Error message if status is Failed (optional)
	    reference_doctype: Reference DocType (optional)
	    reference_name: Reference DocName (optional)
	    deliver: Whether to attempt delivery (default True)
	    title: Notification title (optional)
	    route: Route to navigate to (optional)
	    priority: Priority level (Low, Normal, High) (default Normal)

	Returns:
	    Notification Event Log name
	"""
	# Determine status based on whether we should deliver
	if not deliver:
		status = "Skipped"

	notification_log = frappe.get_doc(
		{
			"doctype": "Notification Event Log",
			"event_type": event_type,
			"owner_profile": owner_profile,
			"recovery_case": recovery_case,
			"registered_item": registered_item,
			"qr_code_tag": qr_code_tag,
			"message_summary": message_summary,
			"channel": channel,
			"status": status,
			"triggered_on": now_datetime(),
			"error_message": error_message,
			"reference_doctype": reference_doctype,
			"reference_name": reference_name,
			"title": title,
			"route": route,
			"priority": priority,
			"is_read": 0,
		}
	)

	notification_log.insert(ignore_permissions=True)

	# Simulate delivery for in-app notifications
	if deliver and channel == "In App" and status == "Queued":
		notification_log.status = "Sent"
		notification_log.delivered_on = now_datetime()
		notification_log.save(ignore_permissions=True)

	frappe.db.commit()

	return notification_log.name


def get_owner_notification_preferences(owner_profile: str) -> Optional[dict]:
	"""
	Get notification preferences for an owner.

	Args:
	    owner_profile: Owner Profile name

	Returns:
	    Dict with notification preferences or None
	"""
	preference = frappe.db.get_value(
		"Notification Preference",
		{"owner_profile": owner_profile},
		[
			"name",
			"owner_profile",
			"enable_in_app_notifications",
			"enable_email_notifications",
			"notify_on_new_finder_message",
			"notify_on_case_opened",
			"notify_on_case_status_change",
			"is_default",
		],
		as_dict=True,
	)

	if preference:
		return {
			"name": preference.name,
			"owner_profile": preference.owner_profile,
			"enable_in_app_notifications": bool(preference.enable_in_app_notifications),
			"enable_email_notifications": bool(preference.enable_email_notifications),
			"notify_on_new_finder_message": bool(preference.notify_on_new_finder_message),
			"notify_on_case_opened": bool(preference.notify_on_case_opened),
			"notify_on_case_status_change": bool(preference.notify_on_case_status_change),
			"is_default": bool(preference.is_default),
		}

	return None


def create_default_notification_preferences(owner_profile: str) -> str:
	"""
	Create default notification preferences for an owner.

	Args:
	    owner_profile: Owner Profile name

	Returns:
	    Notification Preference name
	"""
	# Check if preferences already exist
	existing = frappe.db.get_value(
		"Notification Preference",
		{"owner_profile": owner_profile},
		"name",
	)

	if existing:
		return existing

	preference = frappe.get_doc(
		{
			"doctype": "Notification Preference",
			"owner_profile": owner_profile,
			"enable_in_app_notifications": 1,
			"enable_email_notifications": 1,
			"notify_on_new_finder_message": 1,
			"notify_on_case_opened": 1,
			"notify_on_case_status_change": 1,
			"is_default": 1,
		}
	)

	preference.insert(ignore_permissions=True)
	frappe.db.commit()

	return preference.name


def should_notify_owner(event_type: str, preferences: Optional[dict]) -> bool:
	"""
	Determine if owner should be notified based on event type and preferences.

	Args:
	    event_type: Type of event
	    preferences: Owner notification preferences

	Returns:
	    True if owner should be notified, False otherwise
	"""
	# If no preferences exist, allow notification (default behavior)
	if not preferences:
		return True

	# Check if in-app notifications are enabled
	if not preferences.get("enable_in_app_notifications"):
		return False

	# Check specific event type preferences
	event_preference_map = {
		"Finder Message Received": "notify_on_new_finder_message",
		"Recovery Case Opened": "notify_on_case_opened",
		"Case Status Updated": "notify_on_case_status_change",
	}

	pref_field = event_preference_map.get(event_type)
	if pref_field and not preferences.get(pref_field):
		return False

	return True


def save_notification_preferences(
	owner_profile: str,
	enable_in_app_notifications: bool = True,
	enable_email_notifications: bool = True,
	notify_on_new_finder_message: bool = True,
	notify_on_case_opened: bool = True,
	notify_on_case_status_change: bool = True,
) -> dict:
	"""
	Save notification preferences for an owner.

	Args:
	    owner_profile: Owner Profile name
	    enable_in_app_notifications: Enable in-app notifications
	    enable_email_notifications: Enable email notifications
	    notify_on_new_finder_message: Notify on new finder message
	    notify_on_case_opened: Notify on case opened
	    notify_on_case_status_change: Notify on case status change

	Returns:
	    Dict with success status
	"""
	# Check for existing preferences
	existing = frappe.db.get_value(
		"Notification Preference",
		{"owner_profile": owner_profile},
		"name",
	)

	if existing:
		# Update existing
		preference = frappe.get_doc("Notification Preference", existing)
		preference.enable_in_app_notifications = 1 if enable_in_app_notifications else 0
		preference.enable_email_notifications = 1 if enable_email_notifications else 0
		preference.notify_on_new_finder_message = 1 if notify_on_new_finder_message else 0
		preference.notify_on_case_opened = 1 if notify_on_case_opened else 0
		preference.notify_on_case_status_change = 1 if notify_on_case_status_change else 0
		preference.save(ignore_permissions=True)
		frappe.db.commit()
		return {"success": True, "message": "Preferences updated", "name": existing}
	else:
		# Create new
		preference = frappe.get_doc(
			{
				"doctype": "Notification Preference",
				"owner_profile": owner_profile,
				"enable_in_app_notifications": 1 if enable_in_app_notifications else 0,
				"enable_email_notifications": 1 if enable_email_notifications else 0,
				"notify_on_new_finder_message": 1 if notify_on_new_finder_message else 0,
				"notify_on_case_opened": 1 if notify_on_case_opened else 0,
				"notify_on_case_status_change": 1 if notify_on_case_status_change else 0,
				"is_default": 1,
			}
		)
		preference.insert(ignore_permissions=True)
		frappe.db.commit()
		return {"success": True, "message": "Preferences created", "name": preference.name}


def notify_finder_message_received(
	owner_profile: str,
	recovery_case: str,
	message_summary: str,
	priority: str = "Normal",
	send_email: bool = True,
) -> Optional[str]:
	"""
	Notify owner that a finder message was received.

	Args:
	    owner_profile: Owner Profile name
	    recovery_case: Recovery Case name
	    message_summary: Summary of the message
	    priority: Priority level (Low, Normal, High)
	    send_email: Whether to send email notification (default True)

	Returns:
	    Notification Event Log name or None
	"""
	preferences = get_owner_notification_preferences(owner_profile)

	if not should_notify_owner("Finder Message Received", preferences):
		return None

	# Get item name from recovery case
	item_name = frappe.db.get_value("Recovery Case", recovery_case, "registered_item")
	if item_name:
		item_name = frappe.db.get_value("Registered Item", item_name, "item_name")

	title = f"New message for {item_name or 'your item'}"
	route = f"/frontend/recovery/{recovery_case}"

	notification_id = log_notification_event(
		event_type="Finder Message Received",
		owner_profile=owner_profile,
		recovery_case=recovery_case,
		message_summary=message_summary,
		channel="In App",
		status="Queued",
		title=title,
		route=route,
		priority=priority,
	)

	# Send email notification if enabled
	if send_email and preferences and preferences.get("enable_email_notifications"):
		from scanifyme.notifications.services.notification_delivery_service import (
			send_email_notification,
		)

		email_result = send_email_notification(
			event_type="Finder Message Received",
			owner_profile=owner_profile,
			recovery_case=recovery_case,
			message_summary=message_summary,
		)

		# Update notification log with email status
		if notification_id:
			if email_result.get("success"):
				frappe.db.set_value(
					"Notification Event Log",
					notification_id,
					{"status": "Sent", "delivered_on": now_datetime()},
				)
			else:
				frappe.db.set_value(
					"Notification Event Log",
					notification_id,
					{"status": "Failed", "error_message": email_result.get("reason", "Email failed")},
				)
			frappe.db.commit()

	return notification_id


def notify_recovery_case_opened(
	owner_profile: str,
	recovery_case: str,
	registered_item: str,
	qr_code_tag: str,
	priority: str = "High",
	send_email: bool = True,
) -> Optional[str]:
	"""
	Notify owner that a recovery case was opened.

	Args:
	    owner_profile: Owner Profile name
	    recovery_case: Recovery Case name
	    registered_item: Registered Item name
	    qr_code_tag: QR Code Tag name
	    priority: Priority level (Low, Normal, High)
	    send_email: Whether to send email notification (default True)

	Returns:
	    Notification Event Log name or None
	"""
	preferences = get_owner_notification_preferences(owner_profile)

	if not should_notify_owner("Recovery Case Opened", preferences):
		return None

	# Get item name for summary
	item_name = frappe.db.get_value("Registered Item", registered_item, "item_name")

	title = f"New recovery case: {item_name}"
	route = f"/frontend/recovery/{recovery_case}"

	notification_id = log_notification_event(
		event_type="Recovery Case Opened",
		owner_profile=owner_profile,
		recovery_case=recovery_case,
		registered_item=registered_item,
		qr_code_tag=qr_code_tag,
		message_summary=f"New recovery case opened for {item_name}",
		channel="In App",
		status="Queued",
		title=title,
		route=route,
		priority=priority,
	)

	# Send email notification if enabled
	if send_email and preferences and preferences.get("enable_email_notifications"):
		from scanifyme.notifications.services.notification_delivery_service import (
			send_email_notification,
		)

		email_result = send_email_notification(
			event_type="Recovery Case Opened",
			owner_profile=owner_profile,
			recovery_case=recovery_case,
			registered_item=registered_item,
		)

		# Update notification log with email status
		if notification_id:
			if email_result.get("success"):
				frappe.db.set_value(
					"Notification Event Log",
					notification_id,
					{"status": "Sent", "delivered_on": now_datetime()},
				)
			else:
				frappe.db.set_value(
					"Notification Event Log",
					notification_id,
					{"status": "Failed", "error_message": email_result.get("reason", "Email failed")},
				)
			frappe.db.commit()

	return notification_id


def notify_owner_reply_sent(
	owner_profile: str,
	recovery_case: str,
	message_summary: str,
) -> Optional[str]:
	"""
	Notify that an owner reply was sent.

	Args:
	    owner_profile: Owner Profile name
	    recovery_case: Recovery Case name
	    message_summary: Summary of the message

	Returns:
	    Notification Event Log name or None
	"""
	return log_notification_event(
		event_type="Owner Reply Sent",
		owner_profile=owner_profile,
		recovery_case=recovery_case,
		message_summary=message_summary,
		channel="System",
		status="Sent",
	)


def notify_case_status_updated(
	owner_profile: str,
	recovery_case: str,
	old_status: str,
	new_status: str,
	priority: str = "Normal",
	send_email: bool = True,
) -> Optional[str]:
	"""
	Notify that a case status was updated.

	Args:
	    owner_profile: Owner Profile name
	    recovery_case: Recovery Case name
	    old_status: Previous status
	    new_status: New status
	    priority: Priority level (Low, Normal, High)
	    send_email: Whether to send email notification (default True)

	Returns:
	    Notification Event Log name or None
	"""
	preferences = get_owner_notification_preferences(owner_profile)

	if not should_notify_owner("Case Status Updated", preferences):
		return None

	# Get item name from recovery case
	item_name = frappe.db.get_value("Recovery Case", recovery_case, "registered_item")
	if item_name:
		item_name = frappe.db.get_value("Registered Item", item_name, "item_name")

	title = f"Case status updated: {item_name or 'Recovery'}"
	route = f"/frontend/recovery/{recovery_case}"

	notification_id = log_notification_event(
		event_type="Case Status Updated",
		owner_profile=owner_profile,
		recovery_case=recovery_case,
		message_summary=f"Case status changed from {old_status} to {new_status}",
		channel="In App",
		status="Sent",
		title=title,
		route=route,
		priority=priority,
	)

	# Send email notification if enabled
	if send_email and preferences and preferences.get("enable_email_notifications"):
		from scanifyme.notifications.services.notification_delivery_service import (
			send_email_notification,
		)

		email_result = send_email_notification(
			event_type="Case Status Updated",
			owner_profile=owner_profile,
			recovery_case=recovery_case,
			old_status=old_status,
			new_status=new_status,
		)

		# Update notification log with email status if email was sent
		if notification_id and email_result.get("success"):
			frappe.db.set_value(
				"Notification Event Log",
				notification_id,
				{"status": "Sent", "delivered_on": now_datetime()},
			)
			frappe.db.commit()

	return notification_id


# =============================================================================
# Notification Query Service Functions
# =============================================================================


def get_owner_notifications(
	owner_profile: str,
	filters: Optional[dict] = None,
	limit: int = 50,
) -> list:
	"""
	Get notifications for an owner.

	Args:
	    owner_profile: Owner Profile name
	    filters: Optional filters dict (e.g., {"is_read": 0})
	    limit: Maximum number of notifications to return

	Returns:
	    List of notification dicts
	"""
	# Build filters
	query_filters = {"owner_profile": owner_profile}
	if filters:
		query_filters.update(filters)

	notifications = frappe.get_list(
		"Notification Event Log",
		filters=query_filters,
		fields=[
			"name",
			"title",
			"event_type",
			"message_summary",
			"priority",
			"is_read",
			"read_on",
			"triggered_on",
			"route",
			"recovery_case",
			"registered_item",
			"status",
		],
		order_by="triggered_on desc",
		limit=limit,
		ignore_permissions=True,
	)

	return notifications


def get_unread_notification_count(owner_profile: str) -> int:
	"""
	Get the count of unread notifications for an owner.

	Args:
	    owner_profile: Owner Profile name

	Returns:
	    Number of unread notifications
	"""
	count = frappe.db.count(
		"Notification Event Log",
		{"owner_profile": owner_profile, "is_read": 0},
	)

	return count or 0


def mark_notification_read(notification_id: str, owner_profile: str) -> dict:
	"""
	Mark a single notification as read.

	Args:
	    notification_id: Notification Event Log name
	    owner_profile: Owner Profile name (for ownership validation)

	Returns:
	    Dict with success status
	"""
	# Verify ownership
	notification_owner = frappe.db.get_value(
		"Notification Event Log",
		notification_id,
		"owner_profile",
	)

	if not notification_owner:
		return {"success": False, "error": "Notification not found"}

	# Administrator can mark any as read
	if owner_profile != "Administrator" and notification_owner != owner_profile:
		frappe.throw("Permission denied", frappe.PermissionError)

	# Mark as read
	frappe.db.set_value(
		"Notification Event Log",
		notification_id,
		{
			"is_read": 1,
			"read_on": now_datetime(),
		},
	)

	frappe.db.commit()

	return {"success": True, "message": "Notification marked as read"}


def mark_all_notifications_read(owner_profile: str) -> dict:
	"""
	Mark all notifications as read for an owner.

	Args:
	    owner_profile: Owner Profile name

	Returns:
	    Dict with success status and count of updated notifications
	"""
	# Get count of unread notifications
	unread_count = get_unread_notification_count(owner_profile)

	if unread_count == 0:
		return {"success": True, "message": "No unread notifications", "count": 0}

	# Update all unread notifications
	frappe.db.sql(
		"""
		UPDATE `tabNotification Event Log`
		SET is_read = 1, read_on = %(now)s
		WHERE owner_profile = %(owner_profile)s AND is_read = 0
		""",
		{"owner_profile": owner_profile, "now": now_datetime()},
	)

	frappe.db.commit()

	return {
		"success": True,
		"message": f"Marked {unread_count} notifications as read",
		"count": unread_count,
	}


def build_notification_route(notification: dict) -> str:
	"""
	Build the frontend route for a notification.

	Args:
	    notification: Notification dict

	Returns:
	    Frontend route string
	"""
	# If route is already set, use it
	if notification.get("route"):
		return notification["route"]

	# Build route based on event type and linked document
	if notification.get("recovery_case"):
		return f"/frontend/recovery/{notification['recovery_case']}"

	if notification.get("registered_item"):
		return f"/frontend/items/{notification['registered_item']}"

	# Default to recovery list
	return "/frontend/recovery"
