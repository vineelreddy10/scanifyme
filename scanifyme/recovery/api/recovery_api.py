"""
Recovery API - Whitelisted API methods for recovery case management.

This module provides API endpoints for owners to manage recovery cases.
"""

import frappe
from scanifyme.recovery.services import recovery_service
from scanifyme.messaging.services import message_service


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
def get_owner_recovery_cases(status: str = None) -> list:
	"""
	Get recovery cases for the current user.

	Args:
	    status: Filter by status (optional)

	Returns:
	    List of recovery case dicts
	"""
	owner_profile = get_owner_profile_for_user()

	if not owner_profile:
		frappe.throw("Permission denied", frappe.PermissionError)

	return recovery_service.get_owner_recovery_cases(owner_profile, status=status)


@frappe.whitelist()
def get_recovery_case_details(case_id: str) -> dict:
	"""
	Get detailed information about a recovery case.

	Args:
	    case_id: Recovery Case name

	Returns:
	    Recovery case dict
	"""
	owner_profile = get_owner_profile_for_user()

	if not owner_profile:
		frappe.throw("Permission denied", frappe.PermissionError)

	return recovery_service.get_recovery_case_details(case_id, owner_profile)


@frappe.whitelist()
def get_recovery_case_messages(case_id: str) -> list:
	"""
	Get messages for a recovery case.

	Args:
	    case_id: Recovery Case name

	Returns:
	    List of message dicts
	"""
	owner_profile = get_owner_profile_for_user()

	if not owner_profile:
		frappe.throw("Permission denied", frappe.PermissionError)

	# Verify the case belongs to the owner
	case = frappe.get_doc("Recovery Case", case_id)
	if case.owner_profile != owner_profile:
		frappe.throw("Permission denied", frappe.PermissionError)

	# Get messages
	messages = frappe.get_list(
		"Recovery Message",
		filters={"recovery_case": case_id},
		fields=[
			"name",
			"sender_type",
			"sender_name",
			"message",
			"attachment",
			"created_on",
			"is_read_by_owner",
		],
		order_by="created_on asc",
	)

	# Mark messages as read
	for msg in messages:
		if not msg.is_read_by_owner and msg.sender_type == "Finder":
			frappe.db.set_value("Recovery Message", msg.name, "is_read_by_owner", 1)

	frappe.db.commit()

	return messages


@frappe.whitelist()
def mark_recovery_case_status(case_id: str, status: str) -> dict:
	"""
	Update the status of a recovery case.

	Args:
	    case_id: Recovery Case name
	    status: New status

	Returns:
	    Dict with success status
	"""
	owner_profile = get_owner_profile_for_user()

	if not owner_profile:
		frappe.throw("Permission denied", frappe.PermissionError)

	return recovery_service.update_recovery_case_status(case_id, status, owner_profile)


@frappe.whitelist()
def send_owner_reply(case_id: str, message: str, attachment: str = None) -> dict:
	"""
	Send a reply message from the owner to the finder.

	Args:
	    case_id: Recovery Case name
	    message: Message content
	    attachment: Attachment file path (optional)

	Returns:
	    Dict with success status
	"""
	owner_profile = get_owner_profile_for_user()

	if not owner_profile:
		frappe.throw("Permission denied", frappe.PermissionError)

	# Verify the case belongs to the owner
	case = frappe.get_doc("Recovery Case", case_id)
	if case.owner_profile != owner_profile:
		frappe.throw("Permission denied", frappe.PermissionError)

	# Get owner profile for sender name
	owner = frappe.get_doc("Owner Profile", owner_profile)
	sender_name = owner.display_name

	return message_service.send_owner_message(
		case_id=case_id,
		message=message,
		sender_name=sender_name,
		attachment=attachment,
	)
