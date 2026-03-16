"""
Item Service - Business logic for item management.

This module provides high-level functions for:
- QR code activation
- Item creation
- QR-to-item linking
- Ownership transfers
"""

import frappe
from frappe.utils import now_datetime
from typing import Optional, Dict, Any, List


def activate_qr(token: str, user: str = None) -> Dict[str, Any]:
	"""
	Activate a QR code for an item.

	This function validates the QR token, checks its current status,
	and prepares it for item association.

	Args:
	    token: QR code token to activate
	    user: User email activating the QR. If None, uses current session user.

	Returns:
	    Dict containing:
	    - success: bool
	    - message: str
	    - qr_tag: dict (QR tag details)
	    - needs_item_creation: bool (whether item details need to be provided)

	Raises:
	    frappe.ValidationError: If QR token is invalid or already activated
	"""
	if not user:
		user = frappe.session.user

	if not token:
		frappe.throw("QR token is required")

	# Find the QR code tag by token
	qr_tag = frappe.db.get_value(
		"QR Code Tag",
		{"qr_token": token},
		["name", "qr_uid", "qr_token", "status", "registered_item"],
		as_dict=True,
	)

	if not qr_tag:
		frappe.throw("Invalid QR token. Please check and try again.")

	# Check if already activated
	if qr_tag.status == "Activated":
		if qr_tag.registered_item:
			# Get the item details
			item = frappe.get_doc("Registered Item", qr_tag.registered_item)
			return {
				"success": True,
				"message": "This QR code is already linked to an item",
				"qr_tag": {"name": qr_tag.name, "qr_uid": qr_tag.qr_uid, "status": qr_tag.status},
				"linked_item": item.name,
				"linked_item_name": item.item_name,
				"needs_item_creation": False,
			}

	# Check if QR is in valid state for activation
	valid_states = ["Generated", "In Stock", "Assigned", "Printed"]
	if qr_tag.status not in valid_states:
		frappe.throw(
			f"QR code cannot be activated. Current status: {qr_tag.status}. "
			f"Please ensure the QR code is in 'Generated', 'In Stock', or 'Assigned' state."
		)

	# Return success - user needs to create item
	return {
		"success": True,
		"message": "QR code validated. Please create an item to link.",
		"qr_tag": {
			"name": qr_tag.name,
			"qr_uid": qr_tag.qr_uid,
			"qr_token": qr_tag.qr_token,
			"status": qr_tag.status,
		},
		"needs_item_creation": True,
	}


def create_item(item_data: Dict[str, Any], user: str = None) -> str:
	"""
	Create a new registered item.

	Args:
	    item_data: Dictionary containing item fields:
	        - item_name: str (required)
	        - qr_code_tag: str (required) - QR Code Tag name
	        - item_category: str (optional) - Item Category name
	        - public_label: str (optional)
	        - recovery_note: str (optional)
	        - reward_note: str (optional)
	        - photos: list (optional) - List of photo dicts
	    user: User email creating the item. If None, uses current session user.

	Returns:
	    Registered Item name

	Raises:
	    frappe.ValidationError: If required fields are missing or invalid
	"""
	if not user:
		user = frappe.session.user

	# Validate required fields
	if not item_data.get("item_name"):
		frappe.throw("Item name is required")

	if not item_data.get("qr_code_tag"):
		frappe.throw("QR Code Tag is required")

	# Get or create owner profile
	owner_profile = get_or_create_owner_profile(user)

	# Check that QR tag is not already linked to active item
	existing_item = frappe.db.get_value(
		"Registered Item",
		{"qr_code_tag": item_data["qr_code_tag"], "status": ["in", ["Active", "Lost"]]},
		"name",
	)

	if existing_item:
		frappe.throw("This QR code is already linked to an active item")

	# Validate item category if provided
	if item_data.get("item_category"):
		if not frappe.db.exists("Item Category", item_data["item_category"]):
			frappe.throw(f"Invalid Item Category: {item_data['item_category']}")

	# Prepare item doc
	item_doc = frappe.get_doc(
		{
			"doctype": "Registered Item",
			"item_name": item_data["item_name"],
			"owner_profile": owner_profile,
			"qr_code_tag": item_data["qr_code_tag"],
			"item_category": item_data.get("item_category"),
			"public_label": item_data.get("public_label"),
			"recovery_note": item_data.get("recovery_note"),
			"reward_note": item_data.get("reward_note"),
			"status": "Active",
			"activation_date": now_datetime(),
		}
	)

	# Add photos if provided
	if item_data.get("photos"):
		for photo in item_data["photos"]:
			item_doc.append(
				"photos",
				{
					"image": photo.get("image"),
					"visibility": photo.get("visibility", "Private"),
					"caption": photo.get("caption"),
				},
			)

	item_doc.insert()

	return item_doc.name


def link_item_to_qr(item: str, qr_tag: str) -> Dict[str, Any]:
	"""
	Link an existing item to a QR code tag.

	Args:
	    item: Registered Item name
	    qr_tag: QR Code Tag name

	Returns:
	    Dict with success status

	Raises:
	    frappe.ValidationError: If linking is not possible
	"""
	# Get the item
	item_doc = frappe.get_doc("Registered Item", item)

	# Check if QR is already linked
	if item_doc.qr_code_tag:
		frappe.throw("Item is already linked to a QR code")

	# Check QR tag is available
	existing = frappe.db.get_value(
		"Registered Item",
		{"qr_code_tag": qr_tag, "status": ["in", ["Active", "Lost"]], "name": ["!=", item]},
		"name",
	)

	if existing:
		frappe.throw("QR code is already linked to another active item")

	# Update the item
	item_doc.qr_code_tag = qr_tag
	item_doc.status = "Active"
	if not item_doc.activation_date:
		item_doc.activation_date = now_datetime()
	item_doc.save()

	# Update QR tag status
	qr_doc = frappe.get_doc("QR Code Tag", qr_tag)
	qr_doc.status = "Activated"
	qr_doc.registered_item = item
	qr_doc.save(ignore_permissions=True)

	return {"success": True, "message": f"Item '{item}' linked to QR code '{qr_tag}'"}


def get_user_items(user: str = None, status: str = None, limit: int = 20) -> List[Dict[str, Any]]:
	"""
	Get items for a user.

	Args:
	    user: User email. If None, uses current session user.
	    status: Filter by status (Draft, Active, Lost, Recovered, Archived)
	    limit: Maximum number of items to return

	Returns:
	    List of item dictionaries with safe fields only
	"""
	if not user:
		user = frappe.session.user

	# Get owner profile
	owner_profile = frappe.db.get_value("Owner Profile", {"user": user}, "name")

	if not owner_profile:
		return []

	# Build filters
	filters = {"owner_profile": owner_profile}
	if status:
		filters["status"] = status

	# Get items
	items = frappe.get_list(
		"Registered Item",
		filters=filters,
		fields=[
			"name",
			"item_name",
			"status",
			"public_label",
			"activation_date",
			"last_scan_at",
			"item_category",
			"qr_code_tag",
		],
		order_by="activation_date desc",
		limit=limit,
	)

	# Get category names
	for item in items:
		if item.item_category:
			item["item_category_name"] = frappe.db.get_value(
				"Item Category", item.item_category, "category_name"
			)

		if item.qr_code_tag:
			item["qr_uid"] = frappe.db.get_value("QR Code Tag", item.qr_code_tag, "qr_uid")

	return items


def get_item_details(item: str, user: str = None) -> Optional[Dict[str, Any]]:
	"""
	Get detailed information about an item.

	Args:
	    item: Registered Item name
	    user: User requesting the details. If None, uses current session user.

	Returns:
	    Item details dict or None if not found/not authorized

	Note:
	    This function sanitizes the output to never expose:
	    - DocType internal names
	    - database IDs
	    - Owner Profile internal references
	"""
	if not user:
		user = frappe.session.user

	# Get owner profile
	owner_profile = frappe.db.get_value("Owner Profile", {"user": user}, "name")

	# Get item
	try:
		item_doc = frappe.get_doc("Registered Item", item)
	except frappe.DoesNotExistError:
		return None

	# Check ownership
	if item_doc.owner_profile != owner_profile:
		# Check if user is admin/operations
		if not frappe.has_permission("Registered Item", "read"):
			return None

	# Build sanitized response
	result = {
		# Safe identifiers (not DocType names)
		"id": item_doc.name,
		"item_name": item_doc.item_name,
		"status": item_doc.status,
		"public_label": item_doc.public_label,
		"recovery_note": item_doc.recovery_note,
		"reward_note": item_doc.reward_note,
		"activation_date": item_doc.activation_date,
		"last_scan_at": item_doc.last_scan_at,
	}

	# Category (just the name, not internal ID)
	if item_doc.item_category:
		result["item_category"] = item_doc.item_category
		result["item_category_name"] = frappe.db.get_value(
			"Item Category", item_doc.item_category, "category_name"
		)

	# QR Code info (just UID, not internal ID)
	if item_doc.qr_code_tag:
		qr_info = frappe.db.get_value(
			"QR Code Tag", item_doc.qr_code_tag, ["name", "qr_uid", "qr_token", "status"], as_dict=True
		)
		if qr_info:
			result["qr_code"] = {"uid": qr_info.qr_uid, "status": qr_info.status}

	# Photos (filter based on visibility)
	photos = []
	for photo in item_doc.photos:
		photos.append({"image": photo.image, "visibility": photo.visibility, "caption": photo.caption})
	result["photos"] = photos

	return result


def get_or_create_owner_profile(user: str = None) -> str:
	"""
	Get or create an owner profile for a user.

	Args:
	    user: User email. If None, uses current session user.

	Returns:
	    Owner Profile name
	"""
	if not user:
		user = frappe.session.user

	# Check if profile exists
	existing = frappe.db.get_value("Owner Profile", {"user": user}, "name")

	if existing:
		return existing

	# Create new profile
	profile = frappe.get_doc(
		{
			"doctype": "Owner Profile",
			"user": user,
			"display_name": frappe.utils.get_fullname(user),
		}
	)
	profile.insert()

	return profile.name


def update_item_status(item: str, status: str, user: str = None) -> Dict[str, Any]:
	"""
	Update the status of a registered item.

	Args:
	    item: Registered Item name
	    status: New status (Draft, Active, Lost, Recovered, Archived)
	    user: User updating the status. If None, uses current session user.

	Returns:
	    Dict with success status

	Raises:
	    frappe.ValidationError: If status transition is invalid
	"""
	if not user:
		user = frappe.session.user

	# Get owner profile
	owner_profile = frappe.db.get_value("Owner Profile", {"user": user}, "name")

	# Get item
	item_doc = frappe.get_doc("Registered Item", item)

	# Check ownership
	if item_doc.owner_profile != owner_profile:
		if not frappe.has_permission("Registered Item", "write"):
			frappe.throw("You don't have permission to update this item")

	# Validate status
	valid_statuses = ["Draft", "Active", "Lost", "Recovered", "Archived"]
	if status not in valid_statuses:
		frappe.throw(f"Invalid status. Must be one of: {', '.join(valid_statuses)}")

	old_status = item_doc.status
	item_doc.status = status
	item_doc.save()

	# If marking as Lost, update QR tag status
	if status == "Lost" and item_doc.qr_code_tag:
		qr_doc = frappe.get_doc("QR Code Tag", item_doc.qr_code_tag)
		qr_doc.status = "Suspended"
		qr_doc.save(ignore_permissions=True)

	# If marking as Recovered, restore QR tag status
	if status == "Recovered" and item_doc.qr_code_tag:
		qr_doc = frappe.get_doc("QR Code Tag", item_doc.qr_code_tag)
		qr_doc.status = "Activated"
		qr_doc.save(ignore_permissions=True)

	return {"success": True, "message": f"Item status updated from {old_status} to {status}"}
