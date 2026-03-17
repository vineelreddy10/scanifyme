"""
Notification API - Whitelisted API methods for notification preferences.

This module provides API endpoints for owners to manage their notification preferences.
"""

import frappe
from typing import Optional
from scanifyme.notifications.services import notification_service


def get_owner_profile_for_user() -> Optional[str]:
	"""
	Get the owner profile for the current user.

	Returns:
	    Owner Profile name or None
	    Returns "Administrator" if user is Administrator (for admin access)
	"""
	user = frappe.session.user
	if user == "Guest":
		return None

	# Administrator can access all
	if user == "Administrator":
		return "Administrator"

	owner_profile = frappe.db.get_value(
		"Owner Profile",
		{"user": user},
		"name",
	)
	return owner_profile


@frappe.whitelist()
def get_notification_preferences() -> dict:
	"""
	Get notification preferences for the current user.

	Returns:
	    Dict with notification preferences
	"""
	owner_profile = get_owner_profile_for_user()

	# Administrator can access but has no preferences, return defaults
	if not owner_profile:
		frappe.throw("Permission denied", frappe.PermissionError)

	if owner_profile == "Administrator":
		return {"success": True, "preferences": None, "is_admin": True}

	preferences = notification_service.get_owner_notification_preferences(owner_profile)

	if preferences:
		return {"success": True, "preferences": preferences}

	# Create default preferences if none exist
	notification_service.create_default_notification_preferences(owner_profile)
	preferences = notification_service.get_owner_notification_preferences(owner_profile)

	return {"success": True, "preferences": preferences}


@frappe.whitelist()
def save_notification_preferences(
	enable_in_app_notifications: int = 1,
	enable_email_notifications: int = 1,
	notify_on_new_finder_message: int = 1,
	notify_on_case_opened: int = 1,
	notify_on_case_status_change: int = 1,
) -> dict:
	"""
	Save notification preferences for the current user.

	Args:
	    enable_in_app_notifications: Enable in-app notifications (0 or 1)
	    enable_email_notifications: Enable email notifications (0 or 1)
	    notify_on_new_finder_message: Notify on new finder message (0 or 1)
	    notify_on_case_opened: Notify on case opened (0 or 1)
	    notify_on_case_status_change: Notify on case status change (0 or 1)

	Returns:
	    Dict with success status
	"""
	owner_profile = get_owner_profile_for_user()

	# Administrator cannot save preferences
	if not owner_profile:
		frappe.throw("Permission denied", frappe.PermissionError)

	if owner_profile == "Administrator":
		return {"success": False, "message": "Administrator cannot save preferences"}

	return notification_service.save_notification_preferences(
		owner_profile=owner_profile,
		enable_in_app_notifications=bool(enable_in_app_notifications),
		enable_email_notifications=bool(enable_email_notifications),
		notify_on_new_finder_message=bool(notify_on_new_finder_message),
		notify_on_case_opened=bool(notify_on_case_opened),
		notify_on_case_status_change=bool(notify_on_case_status_change),
	)


@frappe.whitelist()
def get_owner_notifications(is_read: Optional[int] = None, limit: int = 50) -> dict:
	"""
	Get notifications for the current user.

	Args:
	    is_read: Filter by read status (0 for unread, 1 for read, None for all)
	    limit: Maximum number of notifications to return

	Returns:
	    Dict with success status and list of notifications
	"""
	owner_profile = get_owner_profile_for_user()

	# Administrator can view all notifications
	if not owner_profile:
		frappe.throw("Permission denied", frappe.PermissionError)

	# Build filters
	filters = None
	if is_read is not None:
		filters = {"is_read": is_read}

	# Administrator sees all notifications
	if owner_profile == "Administrator":
		notifications = frappe.get_list(
			"Notification Event Log",
			filters=filters,
			fields=[
				"name",
				"title",
				"message",
				"event_type",
				"route",
				"priority",
				"is_read",
				"read_on",
				"creation",
			],
			order_by="creation desc",
			limit=limit,
		)
		return {"success": True, "notifications": notifications, "is_admin": True}

	notifications = notification_service.get_owner_notifications(
		owner_profile=owner_profile,
		filters=filters,
		limit=limit,
	)

	return {"success": True, "notifications": notifications}


@frappe.whitelist()
def get_unread_notification_count() -> dict:
	"""
	Get the count of unread notifications for the current user.

	Returns:
	    Dict with success status and count
	"""
	owner_profile = get_owner_profile_for_user()

	if not owner_profile:
		frappe.throw("Permission denied", frappe.PermissionError)

	# Administrator sees all unread
	if owner_profile == "Administrator":
		count = frappe.db.count("Notification Event Log", {"is_read": 0})
		return {"success": True, "count": count, "is_admin": True}

	count = notification_service.get_unread_notification_count(owner_profile)

	return {"success": True, "count": count}


@frappe.whitelist()
def mark_notification_read(notification_id: str) -> dict:
	"""
	Mark a single notification as read.

	Args:
	    notification_id: Notification Event Log name

	Returns:
	    Dict with success status
	"""
	owner_profile = get_owner_profile_for_user()

	if not owner_profile:
		frappe.throw("Permission denied", frappe.PermissionError)

	# Administrator can mark any as read
	if owner_profile == "Administrator":
		frappe.db.set_value("Notification Event Log", notification_id, "is_read", 1)
		frappe.db.set_value("Notification Event Log", notification_id, "read_on", frappe.utils.now_datetime())
		frappe.db.commit()
		return {"success": True}

	return notification_service.mark_notification_read(notification_id, owner_profile)


@frappe.whitelist()
def mark_all_notifications_read() -> dict:
	"""
	Mark all notifications as read for the current user.

	Returns:
	    Dict with success status and count of updated notifications
	"""
	owner_profile = get_owner_profile_for_user()

	if not owner_profile:
		frappe.throw("Permission denied", frappe.PermissionError)

	# Administrator marks all as read
	if owner_profile == "Administrator":
		frappe.db.sql(
			"""
			update `tabNotification Event Log`
			set is_read = 1, read_on = %(now)s
			where is_read = 0
		""",
			{"now": frappe.utils.now_datetime()},
		)
		frappe.db.commit()
		count = frappe.db.count("Notification Event Log", {"is_read": 0})
		# Return original count before marking
		return {"success": True, "count": 0, "message": "All notifications marked as read", "is_admin": True}

	return notification_service.mark_all_notifications_read(owner_profile)
