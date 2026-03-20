"""
Public Scan Portal - Page handler for /s/<token>

This module handles the public scan portal page that finders see when they scan
a QR code. It provides a safe, public-facing view of item information and
allows finders to contact owners.
"""

import frappe
from scanifyme.public_portal.services.public_scan_service import (
	resolve_public_token,
	get_public_item_context,
	create_scan_event,
)

no_cache = 1


def get_context():
	"""
	Get context for the public scan page.

	Returns:
	    dict: Context for rendering the template
	"""
	context = frappe._dict()

	# Get token from URL path
	token = frappe.local.request.path.strip("/").split("/")[-1]

	if not token:
		context.err_msg = "No token provided"
		context.item = None
		return context

	# Resolve the token
	result = resolve_public_token(token)

	if result.get("error"):
		# Handle invalid token - create scan event for analytics
		create_scan_event(
			token=token,
			status="Invalid",
			qr_tag=None,
			item=None,
		)
		context.err_msg = result.get("error")
		context.item = None
		return context

	# Get the QR tag and registered item
	qr_tag = result.get("qr_tag")
	registered_item = result.get("registered_item")

	if not qr_tag or not registered_item:
		# Create scan event for unavailable item
		create_scan_event(
			token=token,
			status="Unavailable",
			qr_tag=qr_tag.get("name") if qr_tag else None,
			item=None,
		)
		context.err_msg = "This item is currently unavailable."
		context.item = None
		return context

	# Check if item is in a usable state
	item_status = registered_item.get("status")
	if item_status not in ["Active"]:
		create_scan_event(
			token=token,
			status="Unavailable",
			qr_tag=qr_tag.get("name"),
			item=registered_item.get("name"),
		)
		context.err_msg = f"This item is currently marked as {item_status}."
		context.item = None
		return context

	# Get public-safe item context
	public_context = get_public_item_context(registered_item)

	# Create scan event for valid scan
	create_scan_event(
		token=token,
		status="Valid",
		qr_tag=qr_tag.get("name"),
		item=registered_item.get("name"),
	)

	context.item = public_context
	context.token = token
	context.csrf_token = frappe.sessions.get_csrf_token()

	return context
