"""
Recovery Service - Service layer for recovery case management.

This module provides business logic for managing recovery cases.
"""

import frappe
from frappe.utils import now_datetime

from scanifyme.notifications.services import notification_service


def create_or_get_recovery_case(
	qr_tag: str,
	registered_item: str,
	owner_profile: str,
	finder_session_id: str = None,
	finder_name: str = None,
	finder_contact_hint: str = None,
) -> str:
	"""
	Create a new recovery case or get an existing open one.

	If there's an existing open recovery case for the same QR tag and
	finder session, it returns that case instead of creating a new one.

	Args:
	    qr_tag: QR Code Tag name
	    registered_item: Registered Item name
	    owner_profile: Owner Profile name
	    finder_session_id: Finder session ID (optional)
	    finder_name: Finder's name (optional)
	    finder_contact_hint: Contact hint from finder (optional)

	Returns:
	    Recovery Case name
	"""
	# Check for existing open case for this finder session
	if finder_session_id:
		existing_case = frappe.db.get_value(
			"Recovery Case",
			{
				"finder_session_id": finder_session_id,
				"status": ["in", ["Open", "Owner Responded", "Return Planned"]],
			},
			"name",
		)
		if existing_case:
			# Update finder info if provided
			if finder_name or finder_contact_hint:
				case = frappe.get_doc("Recovery Case", existing_case)
				if finder_name:
					case.finder_name = finder_name
				if finder_contact_hint:
					case.finder_contact_hint = finder_contact_hint
				case.last_activity_on = now_datetime()
				case.save(ignore_permissions=True)
				frappe.db.commit()
			return existing_case

	# Create new recovery case
	case_title = f"Recovery - {registered_item}"

	recovery_case = frappe.get_doc(
		{
			"doctype": "Recovery Case",
			"case_title": case_title,
			"qr_code_tag": qr_tag,
			"registered_item": registered_item,
			"owner_profile": owner_profile,
			"status": "Open",
			"opened_on": now_datetime(),
			"last_activity_on": now_datetime(),
			"finder_session_id": finder_session_id,
			"finder_name": finder_name,
			"finder_contact_hint": finder_contact_hint,
		}
	)

	recovery_case.insert(ignore_permissions=True)
	frappe.db.commit()

	return recovery_case.name


def get_owner_recovery_cases(owner_profile: str, status: str = None) -> list:
	"""
	Get recovery cases for an owner.

	Args:
	    owner_profile: Owner Profile name, or "Administrator" for admin access
	    status: Filter by status (optional)

	Returns:
	    List of recovery case dicts
	"""
	# Admin can see all cases
	if owner_profile == "Administrator":
		filters = {}
	else:
		filters = {"owner_profile": owner_profile}

	if status:
		filters["status"] = status

	cases = frappe.get_list(
		"Recovery Case",
		filters=filters,
		fields=[
			"name",
			"case_title",
			"status",
			"opened_on",
			"last_activity_on",
			"registered_item",
			"finder_name",
			"finder_contact_hint",
			"latest_message_preview",
		],
		order_by="last_activity_on desc",
		ignore_permissions=True,
	)

	return cases


def get_recovery_case_details(case_id: str, owner_profile: str = None) -> dict:
	"""
	Get detailed information about a recovery case.

	Args:
	    case_id: Recovery Case name
	    owner_profile: Owner Profile name (for permission check)

	Returns:
	    Recovery case dict or None
	"""
	# Get the case
	case = frappe.get_doc("Recovery Case", case_id)

	# Permission check - Administrator can access all cases
	if owner_profile and owner_profile != "Administrator" and case.owner_profile != owner_profile:
		frappe.throw("Permission denied", frappe.PermissionError)

	# Get item info
	item = frappe.db.get_value(
		"Registered Item",
		case.registered_item,
		["name", "item_name", "public_label", "qr_code_tag"],
		as_dict=True,
	)

	# Get QR tag info
	qr_tag = frappe.db.get_value(
		"QR Code Tag",
		case.qr_code_tag,
		["name", "qr_token"],
		as_dict=True,
	)

	return {
		"name": case.name,
		"case_title": case.case_title,
		"status": case.status,
		"opened_on": case.opened_on,
		"last_activity_on": case.last_activity_on,
		"closed_on": case.closed_on,
		"finder_name": case.finder_name,
		"finder_contact_hint": case.finder_contact_hint,
		"notes_internal": case.notes_internal,
		"registered_item": item,
		"qr_tag": qr_tag,
	}


def update_recovery_case_status(case_id: str, status: str, owner_profile: str = None) -> dict:
	"""
	Update the status of a recovery case.

	Args:
	    case_id: Recovery Case name
	    status: New status
	    owner_profile: Owner Profile name (for permission check)

	Returns:
	    Dict with success status
	"""
	case = frappe.get_doc("Recovery Case", case_id)

	# Permission check - Administrator can access all cases
	if owner_profile and owner_profile != "Administrator" and case.owner_profile != owner_profile:
		frappe.throw("Permission denied", frappe.PermissionError)

	# Validate status
	valid_statuses = ["Open", "Owner Responded", "Return Planned", "Recovered", "Closed", "Invalid", "Spam"]
	if status not in valid_statuses:
		frappe.throw(f"Invalid status. Must be one of: {', '.join(valid_statuses)}")

	old_status = case.status
	case.status = status
	case.last_activity_on = now_datetime()

	if status in ["Closed", "Recovered", "Invalid", "Spam"]:
		case.closed_on = now_datetime()

	case.save(ignore_permissions=True)

	# Log notification event for status change
	notification_service.notify_case_status_updated(
		owner_profile=case.owner_profile,
		recovery_case=case_id,
		old_status=old_status,
		new_status=status,
	)

	frappe.db.commit()

	return {
		"success": True,
		"message": f"Case status updated from {old_status} to {status}",
	}
