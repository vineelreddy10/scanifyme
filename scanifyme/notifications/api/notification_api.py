"""
Notification API - Whitelisted API methods for notification preferences.

This module provides API endpoints for owners to manage their notification preferences.
"""

import frappe
from scanifyme.notifications.services import notification_service


def get_owner_profile_for_user() -> str:
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
