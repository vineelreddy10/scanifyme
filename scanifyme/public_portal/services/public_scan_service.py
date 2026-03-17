"""
Public Scan Service - Service layer for public scan portal.

This module provides the business logic for resolving public QR tokens
and retrieving safe public item context.
"""

import frappe
from frappe.utils import cint
import hashlib


def resolve_public_token(token: str) -> dict:
	"""
	Resolve a public QR token and return the associated QR tag and item.

	This function validates the token and returns only what's needed for
	the public scan portal. It never exposes private owner information.

	Args:
	    token: The QR token from the URL

	Returns:
	    dict with:
	    - error: Error message if invalid
	    - qr_tag: QR tag document dict (minimal fields)
	    - registered_item: Registered item document dict (minimal fields)
	"""
	if not token:
		return {"error": "Token is required", "qr_tag": None, "registered_item": None}

	# Find QR tag by token
	qr_tag = frappe.db.get_value(
		"QR Code Tag",
		{"qr_token": token},
		["name", "qr_uid", "qr_token", "status", "registered_item"],
		as_dict=True,
	)

	if not qr_tag:
		return {"error": "Invalid token", "qr_tag": None, "registered_item": None}

	# Check if QR tag is in a usable state
	valid_statuses = ["Activated", "Assigned"]
	if qr_tag.status not in valid_statuses:
		return {"error": f"QR code is {qr_tag.status.lower()}", "qr_tag": qr_tag, "registered_item": None}

	# Get registered item if linked
	registered_item = None
	if qr_tag.registered_item:
		registered_item = frappe.db.get_value(
			"Registered Item",
			{"name": qr_tag.registered_item},
			[
				"name",
				"item_name",
				"owner_profile",
				"item_category",
				"public_label",
				"recovery_note",
				"reward_note",
				"status",
			],
			as_dict=True,
		)

		if not registered_item:
			return {"error": "Item not found", "qr_tag": qr_tag, "registered_item": None}

		# Check item status
		if registered_item.status not in ["Active"]:
			return {
				"error": f"Item is {registered_item.status.lower()}",
				"qr_tag": qr_tag,
				"registered_item": registered_item,
			}

	return {
		"error": None,
		"qr_tag": qr_tag,
		"registered_item": registered_item,
	}


def get_public_item_context(registered_item: dict) -> dict:
	"""
	Get public-safe item context for display on the public scan page.

	This function filters out all private owner information and returns
	only what should be visible to the public.

	Args:
	    registered_item: Registered item document dict

	Returns:
	    dict with only public-safe fields
	"""
	# Return only safe public fields - NEVER expose owner info
	return {
		"name": registered_item.get("name"),
		"item_name": registered_item.get("item_name"),
		"public_label": registered_item.get("public_label") or registered_item.get("item_name"),
		"recovery_note": registered_item.get("recovery_note"),
		"reward_note": registered_item.get("reward_note"),
		"status": registered_item.get("status"),
		"item_category": registered_item.get("item_category"),
	}


def hash_ip(ip_address: str) -> str:
	"""
	Hash an IP address for privacy-safe storage.

	Args:
	    ip_address: Raw IP address

	Returns:
	    Hashed IP address (SHA256, first 16 characters)
	"""
	if not ip_address:
		return None

	# Use a salt-like prefix for additional privacy
	salt = "scanifyme_"
	hashed = hashlib.sha256(f"{salt}{ip_address}".encode()).hexdigest()
	return hashed[:16]


def create_scan_event(
	token: str,
	status: str,
	qr_tag: str = None,
	item: str = None,
) -> str:
	"""
	Create a scan event for analytics and recovery history.

	Args:
	    token: The QR token that was scanned
	    status: Scan status (Valid, Invalid, Unavailable, Recovery Initiated)
	    qr_tag: QR Code Tag name (optional)
	    item: Registered Item name (optional)

	Returns:
	    Scan Event name
	"""
	# Get request info
	ip_address = frappe.local.request.remote_addr if hasattr(frappe.local, "request") else None
	user_agent = frappe.local.request.headers.get("User-Agent") if hasattr(frappe.local, "request") else None
	route = frappe.local.request.path if hasattr(frappe.local, "request") else None

	# Hash the IP
	ip_hash = hash_ip(ip_address)

	scan_event = frappe.get_doc(
		{
			"doctype": "Scan Event",
			"token": token,
			"status": status,
			"qr_code_tag": qr_tag,
			"registered_item": item,
			"scanned_on": frappe.utils.now(),
			"ip_hash": ip_hash,
			"user_agent": user_agent[:500] if user_agent else None,  # Limit length
			"route": route,
		}
	)

	scan_event.insert(ignore_permissions=True)
	frappe.db.commit()

	return scan_event.name


def get_public_item_context_api(token: str) -> dict:
	"""
	API wrapper for getting public item context.

	This is the public API that returns safe item information
	for a given token.

	Args:
	    token: QR token

	Returns:
	    dict with item data or error
	"""
	if not token:
		return {"success": False, "error": "Token is required"}

	result = resolve_public_token(token)

	if result.get("error"):
		# Log the invalid scan attempt
		create_scan_event(token=token, status="Invalid")
		return {"success": False, "error": result["error"]}

	registered_item = result.get("registered_item")
	qr_tag = result.get("qr_tag")

	if not registered_item:
		create_scan_event(token=token, status="Unavailable", qr_tag=qr_tag.get("name") if qr_tag else None)
		return {"success": False, "error": "No item linked to this QR code"}

	# Log valid scan
	create_scan_event(
		token=token,
		status="Valid",
		qr_tag=qr_tag.get("name"),
		item=registered_item.get("name"),
	)

	# Return safe public context
	public_context = get_public_item_context(registered_item)

	# Add QR tag name to context (needed for location sharing)
	public_context["qr_tag_name"] = qr_tag.get("name") if qr_tag else None
	public_context["owner_profile_name"] = registered_item.get("owner_profile")

	return {
		"success": True,
		"item": public_context,
	}
