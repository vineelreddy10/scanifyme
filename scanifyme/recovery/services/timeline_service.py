"""
Timeline Service - Service layer for recovery timeline/activity log.

This module provides business logic for creating and retrieving timeline
events for recovery cases.
"""

import frappe
from frappe.utils import now_datetime
import json


def create_timeline_event(
	recovery_case: str,
	event_type: str,
	event_label: str = None,
	actor_type: str = "System",
	actor_reference: str = None,
	summary: str = None,
	reference_doctype: str = None,
	reference_name: str = None,
	metadata: dict = None,
) -> str:
	"""
	Create a timeline event for a recovery case.

	Args:
	    recovery_case: Recovery Case name
	    event_type: Type of event (from event_type options)
	    event_label: Human-readable label for the event
	    actor_type: Who triggered the event (Finder, Owner, System, Admin)
	    actor_reference: Reference to the actor (optional)
	    summary: Brief summary of the event
	    reference_doctype: Related doctype (optional)
	    reference_name: Related document name (optional)
	    metadata: Additional metadata as dict (optional)

	Returns:
	    Timeline event name
	"""
	# Validate event_type
	valid_event_types = [
		"Scan Detected",
		"Finder Message",
		"Location Shared",
		"Owner Reply",
		"Status Updated",
		"Notification Created",
		"Email Queued",
		"Case Closed",
	]
	if event_type not in valid_event_types:
		frappe.throw(f"Invalid event_type. Must be one of: {', '.join(valid_event_types)}")

	# Validate actor_type
	valid_actor_types = ["Finder", "Owner", "System", "Admin"]
	if actor_type not in valid_actor_types:
		frappe.throw(f"Invalid actor_type. Must be one of: {', '.join(valid_actor_types)}")

	# Convert metadata to JSON if provided
	metadata_json = None
	if metadata:
		metadata_json = json.dumps(metadata)

	timeline_event = frappe.get_doc(
		{
			"doctype": "Recovery Timeline Event",
			"recovery_case": recovery_case,
			"event_type": event_type,
			"event_label": event_label,
			"actor_type": actor_type,
			"actor_reference": actor_reference,
			"event_time": now_datetime(),
			"summary": summary,
			"reference_doctype": reference_doctype,
			"reference_name": reference_name,
			"metadata_json": metadata_json,
		}
	)

	timeline_event.insert(ignore_permissions=True)
	frappe.db.commit()

	return timeline_event.name


def get_case_timeline(
	recovery_case: str,
	owner_profile: str = None,
	limit: int = 50,
) -> list:
	"""
	Get timeline events for a recovery case.

	Args:
	    recovery_case: Recovery Case name
	    owner_profile: Owner Profile name (for permission check, optional)
	    limit: Maximum number of events to return

	Returns:
	    List of timeline event dicts ordered by event_time desc
	"""
	# Permission check - Administrator can access all cases
	if owner_profile and owner_profile != "Administrator":
		case_owner = frappe.db.get_value("Recovery Case", recovery_case, "owner_profile")
		if case_owner != owner_profile:
			frappe.throw("Permission denied", frappe.PermissionError)

	events = frappe.get_list(
		"Recovery Timeline Event",
		filters={"recovery_case": recovery_case},
		fields=[
			"name",
			"event_type",
			"event_label",
			"actor_type",
			"actor_reference",
			"event_time",
			"summary",
			"reference_doctype",
			"reference_name",
			"metadata_json",
		],
		order_by="event_time desc",
		limit=limit,
	)

	result = []
	for event in events:
		# Parse metadata JSON if present
		metadata = None
		if event.metadata_json:
			try:
				metadata = json.loads(event.metadata_json)
			except (json.JSONDecodeError, TypeError):
				pass

		result.append(
			{
				"name": event.name,
				"event_type": event.event_type,
				"event_label": event.event_label,
				"actor_type": event.actor_type,
				"actor_reference": event.actor_reference,
				"event_time": str(event.event_time) if event.event_time else None,
				"summary": event.summary,
				"reference_doctype": event.reference_doctype,
				"reference_name": event.reference_name,
				"metadata": metadata,
			}
		)

	return result


def get_case_timeline_count(recovery_case: str) -> int:
	"""
	Get the count of timeline events for a recovery case.

	Args:
	    recovery_case: Recovery Case name

	Returns:
	    Number of timeline events
	"""
	return frappe.db.count("Recovery Timeline Event", {"recovery_case": recovery_case})
