"""
Public Location API - Whitelisted API methods for location sharing from public portal.

This module provides a public-safe API for finders to share their location.
"""

import frappe
from scanifyme.recovery.services import location_service


@frappe.whitelist(allow_guest=True)
def submit_finder_location(
	token: str,
	latitude: float,
	longitude: float,
	accuracy_meters: float = None,
	note: str = None,
	source: str = "Browser Geolocation",
) -> dict:
	"""
	Submit a location share from a finder for a recovery case.

	This is a public API that allows finders to share their location
	when they have a valid QR token.

	Args:
	    token: QR code token
	    latitude: Latitude coordinate
	    longitude: Longitude coordinate
	    accuracy_meters: Accuracy in meters (optional)
	    note: Optional note from finder (optional)
	    source: Source of location (Browser Geolocation, Manual, System)

	Returns:
	    dict with success status and location share info or error
	"""
	# Validate required arguments
	if not token:
		return {"success": False, "error": "Token is required"}

	if latitude is None or longitude is None:
		return {"success": False, "error": "Latitude and longitude are required"}

	# Convert to float if string
	try:
		latitude = float(latitude)
		longitude = float(longitude)
	except (ValueError, TypeError):
		return {"success": False, "error": "Invalid latitude or longitude format"}

	if accuracy_meters is not None:
		try:
			accuracy_meters = float(accuracy_meters)
		except (ValueError, TypeError):
			accuracy_meters = None

	# Validate source
	if source not in ["Browser Geolocation", "Manual", "System"]:
		source = "Browser Geolocation"

	return location_service.submit_location_share(
		token=token,
		latitude=latitude,
		longitude=longitude,
		accuracy_meters=accuracy_meters,
		note=note,
		source=source,
	)
