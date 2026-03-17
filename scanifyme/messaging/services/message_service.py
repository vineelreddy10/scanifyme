"""
Message Service - Service layer for messaging between finders and owners.

This module provides business logic for submitting finder messages and
managing the messaging workflow.
"""

import frappe
from frappe.utils import now_datetime
import uuid

from scanifyme.recovery.services import recovery_service
from scanifyme.public_portal.services import public_scan_service
from scanifyme.notifications.services import notification_service


def generate_finder_session_id() -> str:
	"""
	Generate a unique finder session ID.

	Returns:
	    Unique session ID string
	"""
	return uuid.uuid4().hex[:16]


def create_finder_session(
	qr_tag: str,
	ip_hash: str = None,
	user_agent: str = None,
) -> str:
	"""
	Create a new finder session.

	Args:
	    qr_tag: QR Code Tag name
	    ip_hash: Hashed IP address
	    user_agent: User agent string

	Returns:
	    Finder Session name
	"""
	session_id = generate_finder_session_id()

	finder_session = frappe.get_doc(
		{
			"doctype": "Finder Session",
			"session_id": session_id,
			"qr_code_tag": qr_tag,
			"started_on": now_datetime(),
			"last_seen_on": now_datetime(),
			"ip_hash": ip_hash,
			"user_agent": user_agent[:500] if user_agent else None,
			"status": "Active",
		}
	)

	finder_session.insert(ignore_permissions=True)
	frappe.db.commit()

	return session_id


def get_or_create_finder_session(
	qr_tag: str,
	ip_hash: str = None,
	user_agent: str = None,
) -> str:
	"""
	Get an active finder session for this QR tag or create a new one.

	Args:
	    qr_tag: QR Code Tag name
	    ip_hash: Hashed IP address
	    user_agent: User agent string

	Returns:
	    Finder Session ID
	"""
	# Check for existing active session for this QR tag
	existing = frappe.db.get_value(
		"Finder Session",
		{
			"qr_code_tag": qr_tag,
			"status": "Active",
		},
		"session_id",
		order_by="last_seen_on desc",
	)

	if existing:
		# Update last seen
		frappe.db.set_value("Finder Session", {"session_id": existing}, "last_seen_on", now_datetime())
		frappe.db.commit()
		return existing

	# Create new session
	return create_finder_session(qr_tag, ip_hash, user_agent)


def submit_finder_message(
	token: str,
	message: str,
	finder_name: str = None,
	contact_hint: str = None,
) -> dict:
	"""
	Submit a message from a finder to an item owner.

	This is the main entry point for finder communications.
	It creates or updates a finder session, creates a recovery case if needed,
	and stores the message.

	Args:
	    token: QR token
	    message: Message content
	    finder_name: Finder's name (optional)
	    contact_hint: Contact information (optional)

	Returns:
	    dict with success status and message
	"""
	# Validate required fields
	if not token:
		return {"success": False, "error": "Token is required"}

	if not message:
		return {"success": False, "error": "Message is required"}

	# Resolve the token
	result = public_scan_service.resolve_public_token(token)

	if result.get("error"):
		return {"success": False, "error": result["error"]}

	qr_tag = result.get("qr_tag")
	registered_item = result.get("registered_item")

	if not qr_tag or not registered_item:
		return {"success": False, "error": "No item found for this token"}

	# Get or create finder session
	ip_address = frappe.local.request.remote_addr if hasattr(frappe.local, "request") else None
	ip_hash = public_scan_service.hash_ip(ip_address)
	user_agent = frappe.local.request.headers.get("User-Agent") if hasattr(frappe.local, "request") else None

	session_id = get_or_create_finder_session(
		qr_tag.get("name"),
		ip_hash=ip_hash,
		user_agent=user_agent,
	)

	# Get owner profile from the item
	owner_profile = registered_item.get("owner_profile")

	# Create or get recovery case
	case_was_new = False
	existing_case = frappe.db.get_value(
		"Recovery Case",
		{"finder_session_id": session_id, "status": ["in", ["Open", "Owner Responded", "Return Planned"]]},
		"name",
	)
	if not existing_case:
		case_was_new = True

	case_id = recovery_service.create_or_get_recovery_case(
		qr_tag=qr_tag.get("name"),
		registered_item=registered_item.get("name"),
		owner_profile=owner_profile,
		finder_session_id=session_id,
		finder_name=finder_name,
		finder_contact_hint=contact_hint,
	)

	# Create the message
	recovery_message = frappe.get_doc(
		{
			"doctype": "Recovery Message",
			"recovery_case": case_id,
			"sender_type": "Finder",
			"sender_name": finder_name,
			"message": message,
			"created_on": now_datetime(),
			"is_public_submission": 1,
		}
	)

	recovery_message.insert(ignore_permissions=True)

	# Update recovery case with latest message preview
	message_preview = message[:100] + "..." if len(message) > 100 else message
	frappe.db.set_value("Recovery Case", case_id, "latest_message_preview", message_preview)
	frappe.db.set_value("Recovery Case", case_id, "last_activity_on", now_datetime())

	# Create/update scan event to mark recovery initiated
	public_scan_service.create_scan_event(
		token=token,
		status="Recovery Initiated",
		qr_tag=qr_tag.get("name"),
		item=registered_item.get("name"),
	)

	# Create notification event for the owner
	message_summary = f"New message from {finder_name or 'a finder'}: {message_preview}"
	if case_was_new:
		# This is a new case - notify that a case was opened
		notification_service.notify_recovery_case_opened(
			owner_profile=owner_profile,
			recovery_case=case_id,
			registered_item=registered_item.get("name"),
			qr_code_tag=qr_tag.get("name"),
		)
	else:
		# Existing case - notify about new message
		notification_service.notify_finder_message_received(
			owner_profile=owner_profile,
			recovery_case=case_id,
			message_summary=message_summary,
		)

	frappe.db.commit()

	return {
		"success": True,
		"message": "Your message has been sent to the owner",
		"case_id": case_id,
		"session_id": session_id,
	}


def get_recovery_case_messages(case_id: str, current_user: str = None) -> list:
	"""
	Get messages for a recovery case.

	Args:
	    case_id: Recovery Case name
	    current_user: Current user email (for permission check)

	Returns:
	    List of message dicts
	"""
	# Get case to verify access
	case = frappe.get_doc("Recovery Case", case_id)

	# Check if user has access (owner or system)
	if current_user and current_user != "Guest":
		owner_profile = frappe.db.get_value(
			"Owner Profile",
			{"user": current_user},
			"name",
		)
		if owner_profile and case.owner_profile != owner_profile:
			frappe.throw("Permission denied", frappe.PermissionError)

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

	return messages


def send_owner_message(
	case_id: str,
	message: str,
	sender_name: str = None,
	attachment: str = None,
) -> dict:
	"""
	Send a message from the owner to the finder.

	Args:
	    case_id: Recovery Case name
	    message: Message content
	    sender_name: Sender's name (usually from owner profile)
	    attachment: Attachment file path (optional)

	Returns:
	    dict with success status
	"""
	if not message:
		return {"success": False, "error": "Message is required"}

	# Verify the case exists
	case = frappe.get_doc("Recovery Case", case_id)

	# Create message
	recovery_message = frappe.get_doc(
		{
			"doctype": "Recovery Message",
			"recovery_case": case_id,
			"sender_type": "Owner",
			"sender_name": sender_name,
			"message": message,
			"attachment": attachment,
			"created_on": now_datetime(),
			"is_public_submission": 0,
		}
	)

	recovery_message.insert(ignore_permissions=True)

	# Update case status
	case.last_activity_on = now_datetime()
	if case.status == "Open":
		case.status = "Owner Responded"
	case.save(ignore_permissions=True)

	# Log notification event for owner reply sent
	message_preview = message[:100] + "..." if len(message) > 100 else message
	notification_service.notify_owner_reply_sent(
		owner_profile=case.owner_profile,
		recovery_case=case_id,
		message_summary=f"You replied: {message_preview}",
	)

	frappe.db.commit()

	return {
		"success": True,
		"message": "Message sent successfully",
	}
