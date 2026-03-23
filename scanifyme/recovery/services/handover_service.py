"""
Handover Service - Service layer for recovery handover workflow.

This module provides business logic for managing handover status
and related operations for recovery cases.
"""

import frappe
from frappe.utils import now_datetime


# Valid handover statuses
VALID_HANDOVER_STATUSES = [
	"Not Started",
	"Finder Contacted",
	"Location Shared",
	"Return Planned",
	"Handover Scheduled",
	"Recovered",
	"Closed",
	"Failed",
]


def update_handover_status(
	case_id: str,
	handover_status: str,
	handover_note: str = None,
	owner_profile: str = None,
) -> dict:
	"""
	Update the handover status of a recovery case.

	Args:
	    case_id: Recovery Case name
	    handover_status: New handover status
	    handover_note: Optional note for the handover
	    owner_profile: Owner Profile name (for permission check, optional)

	Returns:
	    Dict with success status and message
	"""
	# Permission check - Administrator can access all cases
	if owner_profile and owner_profile != "Administrator":
		case_owner = frappe.db.get_value("Recovery Case", case_id, "owner_profile")
		if case_owner != owner_profile:
			frappe.throw("Permission denied", frappe.PermissionError)

	# Validate handover_status
	if handover_status not in VALID_HANDOVER_STATUSES:
		frappe.throw(f"Invalid handover_status. Must be one of: {', '.join(VALID_HANDOVER_STATUSES)}")

	# Get current status
	case = frappe.get_doc("Recovery Case", case_id)
	old_handover_status = case.handover_status or "Not Started"

	# Update case
	case.handover_status = handover_status
	case.last_activity_on = now_datetime()

	if handover_note:
		case.handover_note = handover_note

	case.save(ignore_permissions=True)
	frappe.db.commit()

	# Create timeline event for status change
	from scanifyme.recovery.services import timeline_service

	timeline_service.create_timeline_event(
		recovery_case=case_id,
		event_type="Status Updated",
		event_label=f"Handover Status: {handover_status}",
		actor_type="Owner",
		actor_reference=owner_profile,
		summary=f"Handover status changed from '{old_handover_status}' to '{handover_status}'"
		+ (f". Note: {handover_note}" if handover_note else ""),
	)

	# If handover status indicates recovery is complete, update main status too
	if handover_status == "Recovered":
		if case.status not in ["Recovered", "Closed"]:
			case.status = "Recovered"
			case.closed_on = now_datetime()
			case.save(ignore_permissions=True)
			frappe.db.commit()

			# Also log this in timeline
			timeline_service.create_timeline_event(
				recovery_case=case_id,
				event_type="Case Closed",
				event_label="Case Recovered",
				actor_type="Owner",
				actor_reference=owner_profile,
				summary="Recovery case marked as recovered via handover workflow",
			)

	elif handover_status == "Failed":
		if case.status not in ["Closed", "Recovered"]:
			case.status = "Closed"
			case.closed_on = now_datetime()
			case.save(ignore_permissions=True)
			frappe.db.commit()

			timeline_service.create_timeline_event(
				recovery_case=case_id,
				event_type="Case Closed",
				event_label="Recovery Failed",
				actor_type="Owner",
				actor_reference=owner_profile,
				summary="Recovery case marked as failed via handover workflow",
			)

	elif handover_status == "Closed":
		if case.status not in ["Closed", "Recovered"]:
			case.status = "Closed"
			case.closed_on = now_datetime()
			case.save(ignore_permissions=True)
			frappe.db.commit()

			timeline_service.create_timeline_event(
				recovery_case=case_id,
				event_type="Case Closed",
				event_label="Case Closed",
				actor_type="Owner",
				actor_reference=owner_profile,
				summary="Recovery case closed via handover workflow",
			)

	return {
		"success": True,
		"message": f"Handover status updated from '{old_handover_status}' to '{handover_status}'",
		"old_status": old_handover_status,
		"new_status": handover_status,
	}


def get_handover_status_options() -> list:
	"""
	Get the list of valid handover status options.

	Returns:
	    List of handover status strings
	"""
	return VALID_HANDOVER_STATUSES


def auto_update_handover_on_finder_message(case_id: str) -> None:
	"""
	Automatically update handover status when a finder sends a message.

	Args:
	    case_id: Recovery Case name
	"""
	current_status = frappe.db.get_value("Recovery Case", case_id, "handover_status")

	# Only update if not yet past "Finder Contacted"
	if current_status in [None, "", "Not Started"]:
		frappe.db.set_value(
			"Recovery Case",
			case_id,
			"handover_status",
			"Finder Contacted",
		)
		frappe.db.commit()

		# Create timeline event
		from scanifyme.recovery.services import timeline_service

		timeline_service.create_timeline_event(
			recovery_case=case_id,
			event_type="Status Updated",
			event_label="Handover: Finder Contacted",
			actor_type="System",
			summary="Handover status auto-updated to 'Finder Contacted' after finder message",
		)


def get_case_handover_details(case_id: str, owner_profile: str = None) -> dict:
	"""
	Get detailed handover information for a recovery case.

	Args:
	    case_id: Recovery Case name
	    owner_profile: Owner Profile name (for permission check, optional)
	                  Pass "Administrator" to bypass ownership check

	Returns:
	    Dict with handover details
	"""
	# Permission check - Administrator can access all cases
	if owner_profile and owner_profile != "Administrator":
		case_owner = frappe.db.get_value("Recovery Case", case_id, "owner_profile")
		if case_owner != owner_profile:
			frappe.throw("Permission denied", frappe.PermissionError)

	case = frappe.get_doc("Recovery Case", case_id)

	return {
		"case_id": case.name,
		"handover_status": case.handover_status or "Not Started",
		"handover_note": case.handover_note,
		"latest_location_summary": case.latest_location_summary,
		"valid_statuses": VALID_HANDOVER_STATUSES,
	}
