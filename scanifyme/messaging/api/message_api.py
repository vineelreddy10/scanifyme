"""
Messaging API - Whitelisted API methods for messaging between finders and owners.

This module provides:
- Public API for finders to submit messages
- Protected APIs for owners to view and manage messages
"""

import frappe
from scanifyme.messaging.services import message_service
from scanifyme.utils.permissions import is_scanifyme_admin


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


@frappe.whitelist(allow_guest=True)
def submit_finder_message(
	token: str,
	message: str,
	finder_name: str = None,
	contact_hint: str = None,
) -> dict:
	"""
	Submit a message from a finder to an item owner.

	This is a public API that allows finders to contact owners
	without authentication.

	Args:
	    token: QR code token
	    message: Message content (required)
	    finder_name: Finder's name (optional)
	    contact_hint: Contact information (optional)

	Returns:
	    dict with success status and message
	"""
	return message_service.submit_finder_message(
		token=token,
		message=message,
		finder_name=finder_name,
		contact_hint=contact_hint,
	)


@frappe.whitelist()
def get_recovery_case_messages(case_id: str) -> list:
	"""
	Get messages for a recovery case.

	This is a protected API that requires authentication.

	Args:
	    case_id: Recovery Case name

	Returns:
	    List of message dicts
	"""
	owner_profile = get_owner_profile_for_user()

	# Administrator can access all cases
	if not owner_profile or owner_profile == "Administrator":
		# Allow admin to proceed
		pass
	elif not owner_profile:
		frappe.throw("Permission denied", frappe.PermissionError)

	return message_service.get_recovery_case_messages(case_id, current_user=frappe.session.user)


@frappe.whitelist()
def send_owner_message(
	case_id: str,
	message: str,
	attachment: str = None,
) -> dict:
	"""
	Send a message from the owner to the finder.

	This is a protected API that requires authentication.

	Args:
	    case_id: Recovery Case name
	    message: Message content (required)
	    attachment: Attachment file path (optional)

	Returns:
	    dict with success status
	"""
	owner_profile = get_owner_profile_for_user()

	if not owner_profile:
		frappe.throw("Permission denied", frappe.PermissionError)

	# Handle Administrator case - use special sender name
	if owner_profile == "Administrator":
		sender_name = "Administrator"
	else:
		# Get owner profile for sender name
		owner = frappe.get_doc("Owner Profile", owner_profile)
		sender_name = owner.display_name

	return message_service.send_owner_message(
		case_id=case_id,
		message=message,
		sender_name=sender_name,
		attachment=attachment,
	)
