"""
Location Service - Service layer for location sharing functionality.

This module provides business logic for validating and storing location
shares from finders in recovery cases.
"""

import frappe
from frappe.utils import now_datetime
import json


def validate_coordinates(latitude: float, longitude: float) -> bool:
	"""
	Validate that coordinates are within valid ranges.

	Args:
	    latitude: Latitude value
	    longitude: Longitude value

	Returns:
	    True if valid, False otherwise
	"""
	if latitude is None or longitude is None:
		return False

	# Valid latitude range: -90 to 90
	if latitude < -90 or latitude > 90:
		return False

	# Valid longitude range: -180 to 180
	if longitude < -180 or longitude > 180:
		return False

	return True


def submit_location_share(
	token: str,
	latitude: float,
	longitude: float,
	accuracy_meters: float = None,
	note: str = None,
	source: str = "Browser Geolocation",
) -> dict:
	"""
	Submit a location share from a finder for a recovery case.

	Args:
	    token: QR code token
	    latitude: Latitude coordinate
	    longitude: Longitude coordinate
	    accuracy_meters: Accuracy in meters (optional)
	    note: Optional note from finder (optional)
	    source: Source of location (Browser Geolocation, Manual, System)

	Returns:
	    Dict with success status and location share info or error
	"""
	# Validate coordinates
	if not validate_coordinates(latitude, longitude):
		return {
			"success": False,
			"error": "Invalid coordinates. Please provide valid latitude and longitude values.",
		}

	# Get the QR tag and item context
	from scanifyme.public_portal.services import public_scan_service

	context = public_scan_service.get_public_item_context_api(token)
	if not context.get("success"):
		return {
			"success": False,
			"error": context.get("error", "Invalid token"),
		}

	item_data = context.get("item", {})
	qr_tag_name = item_data.get("qr_tag_name")
	registered_item_name = item_data.get("name")
	owner_profile_name = item_data.get("owner_profile_name")

	if not qr_tag_name or not registered_item_name:
		return {
			"success": False,
			"error": "QR tag or item not found",
		}

	# Get or create recovery case for this finder session
	# Find the latest open recovery case for this item
	recovery_case = frappe.db.get_value(
		"Recovery Case",
		{
			"qr_code_tag": qr_tag_name,
			"status": ["in", ["Open", "Owner Responded", "Return Planned"]],
		},
		"name",
		order_by="opened_on desc",
	)

	# Get finder session if available
	finder_session = frappe.db.get_value(
		"Finder Session",
		{"qr_code_tag": qr_tag_name, "status": "Active"},
		"name",
		order_by="started_on desc",
	)

	# Mark previous locations as not latest
	if recovery_case:
		frappe.db.sql(
			"UPDATE `tabLocation Share` SET is_latest = 0 WHERE recovery_case = %s",
			(recovery_case,),
		)

	# Create location share
	location_share = frappe.get_doc(
		{
			"doctype": "Location Share",
			"recovery_case": recovery_case,
			"qr_code_tag": qr_tag_name,
			"registered_item": registered_item_name,
			"finder_session": finder_session,
			"latitude": latitude,
			"longitude": longitude,
			"accuracy_meters": accuracy_meters,
			"source": source,
			"shared_on": now_datetime(),
			"note": note,
			"is_latest": 1,
		}
	)

	location_share.insert(ignore_permissions=True)
	frappe.db.commit()

	# Update recovery case with latest location summary
	if recovery_case:
		location_summary = f"{latitude:.6f}, {longitude:.6f}"
		if accuracy_meters:
			location_summary += f" (±{int(accuracy_meters)}m)"
		frappe.db.set_value(
			"Recovery Case",
			recovery_case,
			{
				"latest_location_summary": location_summary,
				"last_activity_on": now_datetime(),
			},
		)
		frappe.db.commit()

		# Auto-update handover status to Location Shared if not already past that stage
		current_handover_status = frappe.db.get_value("Recovery Case", recovery_case, "handover_status")
		if current_handover_status in [None, "", "Not Started", "Finder Contacted"]:
			frappe.db.set_value("Recovery Case", recovery_case, "handover_status", "Location Shared")
			frappe.db.commit()

		# Create timeline event
		from scanifyme.recovery.services import timeline_service

		timeline_service.create_timeline_event(
			recovery_case=recovery_case,
			event_type="Location Shared",
			event_label="Finder shared location",
			actor_type="Finder",
			actor_reference=finder_session,
			summary=f"Finder shared location: {latitude:.6f}, {longitude:.6f}"
			+ (f" (±{int(accuracy_meters)}m)" if accuracy_meters else ""),
			reference_doctype="Location Share",
			reference_name=location_share.name,
		)

	return {
		"success": True,
		"message": "Location shared successfully",
		"location_share": {
			"name": location_share.name,
			"latitude": latitude,
			"longitude": longitude,
			"shared_on": str(location_share.shared_on),
		},
	}


def get_latest_case_location(recovery_case: str) -> dict | None:
	"""
	Get the latest location share for a recovery case.

	Args:
	    recovery_case: Recovery Case name

	Returns:
	    Dict with location data or empty dict if none
	"""
	location = frappe.db.get_value(
		"Location Share",
		{"recovery_case": recovery_case, "is_latest": 1},
		[
			"name",
			"latitude",
			"longitude",
			"accuracy_meters",
			"source",
			"shared_on",
			"note",
			"is_latest",
		],
		as_dict=True,
	)

	if not location:
		# Try to get any location for this case
		location = frappe.db.get_value(
			"Location Share",
			{"recovery_case": recovery_case},
			[
				"name",
				"latitude",
				"longitude",
				"accuracy_meters",
				"source",
				"shared_on",
				"note",
				"is_latest",
			],
			as_dict=True,
			order_by="shared_on desc",
		)

	if location:
		return {
			"name": location.name,
			"latitude": location.latitude,
			"longitude": location.longitude,
			"accuracy_meters": location.accuracy_meters,
			"source": location.source,
			"shared_on": str(location.shared_on) if location.shared_on else None,
			"note": location.note,
			"is_latest": location.is_latest,
			"maps_url": f"https://www.openstreetmap.org/?mlat={location.latitude}&mlon={location.longitude}#map=15/{location.latitude}/{location.longitude}",
		}

	return None


def get_case_location_history(recovery_case: str) -> list:
	"""
	Get all location shares for a recovery case.

	Args:
	    recovery_case: Recovery Case name

	Returns:
	    List of location share dicts ordered by shared_on desc
	"""
	locations = frappe.get_list(
		"Location Share",
		filters={"recovery_case": recovery_case},
		fields=[
			"name",
			"latitude",
			"longitude",
			"accuracy_meters",
			"source",
			"shared_on",
			"note",
			"is_latest",
		],
		order_by="shared_on desc",
		ignore_permissions=True,
	)

	result = []
	for loc in locations:
		result.append(
			{
				"name": loc.name,
				"latitude": loc.latitude,
				"longitude": loc.longitude,
				"accuracy_meters": loc.accuracy_meters,
				"source": loc.source,
				"shared_on": str(loc.shared_on) if loc.shared_on else None,
				"note": loc.note,
				"is_latest": loc.is_latest,
				"maps_url": f"https://www.openstreetmap.org/?mlat={loc.latitude}&mlon={loc.longitude}#map=15/{loc.latitude}/{loc.longitude}",
			}
		)

	return result


def summarize_latest_location(recovery_case: str) -> str:
	"""
	Get a summary string of the latest location for a recovery case.

	Args:
	    recovery_case: Recovery Case name

	Returns:
	    Summary string or empty string if none
	"""
	location = get_latest_case_location(recovery_case)

	if not location:
		return ""

	summary = f"{location.get('latitude', 0):.6f}, {location.get('longitude', 0):.6f}"
	if location.get("accuracy_meters"):
		summary += f" (±{int(location.get('accuracy_meters'))}m)"

	return summary
