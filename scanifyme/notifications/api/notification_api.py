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
	"""
	user = frappe.session.user
	if user == "Guest":
		return None

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

	if not owner_profile:
		frappe.throw("Permission denied", frappe.PermissionError)

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

	if not owner_profile:
		frappe.throw("Permission denied", frappe.PermissionError)

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

	if not owner_profile:
		frappe.throw("Permission denied", frappe.PermissionError)

	# Build filters
	filters = None
	if is_read is not None:
		filters = {"is_read": is_read}

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

	return notification_service.mark_all_notifications_read(owner_profile)
