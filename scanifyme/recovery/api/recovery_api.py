"""
Recovery API - Whitelisted API methods for recovery case management.

This module provides API endpoints for owners to manage recovery cases.
"""

import frappe
from scanifyme.recovery.services import recovery_service
from scanifyme.messaging.services import message_service
from scanifyme.utils.permissions import is_scanifyme_admin, user_can_access_recovery_case


def get_owner_profile_for_user() -> str:
	"""
	Get the owner profile for the current user.

	Returns:
	    Owner Profile name or None
	    Returns "Administrator" if user is Administrator (for admin access)
	"""
	user = frappe.session.user
	if user == "Guest":
		return None

	# Check if user is admin using centralized permission helper
	if is_scanifyme_admin(user):
		return "Administrator"

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

	# Verify the case belongs to the owner (admin can access all)
	if owner_profile != "Administrator":
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
		ignore_permissions=True,
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

	# Verify the case belongs to the owner (admin can access all)
	if owner_profile != "Administrator":
		case = frappe.get_doc("Recovery Case", case_id)
		if case.owner_profile != owner_profile:
			frappe.throw("Permission denied", frappe.PermissionError)
		# Get owner profile for sender name
		owner = frappe.get_doc("Owner Profile", owner_profile)
		sender_name = owner.display_name
	else:
		# Admin user - use special sender name
		sender_name = "Administrator"

	return message_service.send_owner_message(
		case_id=case_id,
		message=message,
		sender_name=sender_name,
		attachment=attachment,
	)


# Import the new services
from scanifyme.recovery.services import location_service, timeline_service, handover_service


@frappe.whitelist()
def get_recovery_case_timeline(case_id: str, limit: int = 50) -> list:
	"""
	Get timeline events for a recovery case.

	Args:
	    case_id: Recovery Case name
	    limit: Maximum number of events to return

	Returns:
	    List of timeline event dicts
	"""
	owner_profile = get_owner_profile_for_user()

	if not owner_profile:
		frappe.throw("Permission denied", frappe.PermissionError)

	return timeline_service.get_case_timeline(case_id, owner_profile, limit=limit)


@frappe.whitelist()
def get_latest_case_location(case_id: str) -> dict | None:
	"""
	Get the latest location share for a recovery case.

	Args:
	    case_id: Recovery Case name

	Returns:
	    Dict with location data or None if no location shared
	"""
	owner_profile = get_owner_profile_for_user()

	# Administrator can access all cases
	if owner_profile != "Administrator":
		if not owner_profile:
			frappe.throw("Permission denied", frappe.PermissionError)

		# Verify the case belongs to the owner
		case = frappe.get_doc("Recovery Case", case_id)
		if case.owner_profile != owner_profile:
			frappe.throw("Permission denied", frappe.PermissionError)

	result = location_service.get_latest_case_location(case_id)
	# Return None explicitly so frontend gets null, not {}
	if not result:
		return None
	return result


@frappe.whitelist()
def get_case_location_history(case_id: str) -> list:
	"""
	Get location history for a recovery case.

	Args:
	    case_id: Recovery Case name

	Returns:
	    List of location share dicts
	"""
	owner_profile = get_owner_profile_for_user()

	# Administrator can access all cases
	if owner_profile != "Administrator":
		if not owner_profile:
			frappe.throw("Permission denied", frappe.PermissionError)

		# Verify the case belongs to the owner
		case = frappe.get_doc("Recovery Case", case_id)
		if case.owner_profile != owner_profile:
			frappe.throw("Permission denied", frappe.PermissionError)

	return location_service.get_case_location_history(case_id)


@frappe.whitelist()
def update_handover_status(case_id: str, handover_status: str, handover_note: str = None) -> dict:
	"""
	Update the handover status of a recovery case.

	Args:
	    case_id: Recovery Case name
	    handover_status: New handover status
	    handover_note: Optional note for the handover

	Returns:
	    Dict with success status
	"""
	owner_profile = get_owner_profile_for_user()

	if not owner_profile:
		frappe.throw("Permission denied", frappe.PermissionError)

	return handover_service.update_handover_status(
		case_id=case_id,
		handover_status=handover_status,
		handover_note=handover_note,
		owner_profile=owner_profile,
	)


@frappe.whitelist()
def get_case_handover_details(case_id: str) -> dict:
	"""
	Get detailed handover information for a recovery case.

	Args:
	    case_id: Recovery Case name

	Returns:
	    Dict with handover details
	"""
	owner_profile = get_owner_profile_for_user()

	if not owner_profile:
		frappe.throw("Permission denied", frappe.PermissionError)

	return handover_service.get_case_handover_details(case_id, owner_profile)


# ============== REWARD APIS ==============

# Import reward service
from scanifyme.items.services import reward_service as reward_svc


@frappe.whitelist()
def get_case_reward_status(case_id: str) -> dict:
	"""
	Get reward status for a recovery case.

	Args:
	    case_id: Recovery Case name

	Returns:
	    Dict with reward status
	"""
	if not case_id:
		frappe.throw("Case ID is required")

	return reward_svc.get_case_reward_status(case_id)


@frappe.whitelist()
def update_recovery_case_reward_status(
	case_id: str,
	reward_status: str,
	reward_internal_note: str = None,
) -> dict:
	"""
	Update the reward status on a recovery case.

	Args:
	    case_id: Recovery Case name
	    reward_status: New reward status
	    reward_internal_note: Optional internal note

	Returns:
	    Dict with success status
	"""
	if not case_id:
		frappe.throw("Case ID is required")

	if not reward_status:
		frappe.throw("Reward status is required")

	return reward_svc.update_reward_status(
		case=case_id,
		reward_status=reward_status,
		reward_internal_note=reward_internal_note,
	)
