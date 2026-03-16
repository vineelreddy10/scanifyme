"""
Public Portal API - Whitelisted API methods for public scan portal.

This module provides public-safe API endpoints that can be accessed without
authentication. All responses are sanitized to never expose private owner information.
"""

import frappe
from scanifyme.public_portal.services import public_scan_service


@frappe.whitelist(allow_guest=True)
def get_public_item_context(token: str) -> dict:
	"""
	Get public-safe item context for a QR token.

	This is a public API that returns only safe, non-private information
	about an item associated with a QR token.

	Args:
	    token: QR code token

	Returns:
	    dict with success status and item data or error
	"""
	if not token:
		return {"success": False, "error": "Token is required"}

	return public_scan_service.get_public_item_context_api(token)
