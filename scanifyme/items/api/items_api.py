"""
Items API - Whitelisted API methods for React frontend.

This module provides the API endpoints that the React frontend uses
to interact with the items module.
"""

import frappe
from frappe.utils import cint
from scanifyme.items.services import item_service


@frappe.whitelist()
def activate_qr(token: str) -> dict:
	"""
	Activate a QR code for item registration.

	Args:
	    token: QR code token to activate

	Returns:
	    Dict with activation result:
	    - success: bool
	    - message: str
	    - qr_tag: dict (QR tag info)
	    - needs_item_creation: bool
	    - linked_item: str (if already linked)
	"""
	if not token:
		frappe.throw("QR token is required")

	return item_service.activate_qr(token)


@frappe.whitelist()
def create_item(
	item_name: str,
	qr_code_tag: str,
	item_category: str = None,
	public_label: str = None,
	recovery_note: str = None,
	reward_note: str = None,
	photos: str = None,
) -> str:
	"""
	Create a new registered item.

	Args:
	    item_name: Name of the item (required)
	    qr_code_tag: QR Code Tag name (required)
	    item_category: Item Category name (optional)
	    public_label: Public-facing label (optional)
	    recovery_note: Recovery instructions (optional)
	    reward_note: Reward information (optional)
	    photos: JSON string of photo list (optional)

	Returns:
	    Registered Item name
	"""
	# Validate required fields
	if not item_name:
		frappe.throw("Item name is required")

	if not qr_code_tag:
		frappe.throw("QR Code Tag is required")

	# Parse photos if provided
	photo_list = None
	if photos:
		try:
			photo_list = frappe.parse_json(photos)
		except Exception:
			frappe.throw("Invalid photos format")

	item_data = {
		"item_name": item_name,
		"qr_code_tag": qr_code_tag,
		"item_category": item_category,
		"public_label": public_label,
		"recovery_note": recovery_note,
		"reward_note": reward_note,
		"photos": photo_list,
	}

	return item_service.create_item(item_data)


@frappe.whitelist()
def get_user_items(status: str = None, limit: int = 20) -> list:
	"""
	Get items for the current user.

	Args:
	    status: Filter by status (optional)
	    limit: Maximum items to return (default 20)

	Returns:
	    List of user items with safe fields
	"""
	return item_service.get_user_items(status=status, limit=cint(limit))


@frappe.whitelist()
def get_item_details(item: str) -> dict:
	"""
	Get detailed information about an item.

	Args:
	    item: Registered Item name

	Returns:
	    Item details dict or None
	"""
	if not item:
		frappe.throw("Item ID is required")

	return item_service.get_item_details(item)


@frappe.whitelist()
def update_item_status(item: str, status: str) -> dict:
	"""
	Update the status of a registered item.

	Args:
	    item: Registered Item name
	    status: New status (Draft, Active, Lost, Recovered, Archived)

	Returns:
	    Dict with success status
	"""
	if not item:
		frappe.throw("Item ID is required")

	if not status:
		frappe.throw("Status is required")

	return item_service.update_item_status(item, status)


@frappe.whitelist()
def link_item_to_qr(item: str, qr_tag: str) -> dict:
	"""
	Link an existing item to a QR code tag.

	Args:
	    item: Registered Item name
	    qr_tag: QR Code Tag name

	Returns:
	    Dict with success status
	"""
	if not item:
		frappe.throw("Item ID is required")

	if not qr_tag:
		frappe.throw("QR Code Tag is required")

	return item_service.link_item_to_qr(item, qr_tag)


@frappe.whitelist(allow_guest=True)
def get_item_categories() -> list:
	"""
	Get all active item categories.

	Returns:
	    List of category dictionaries
	"""
	categories = frappe.get_list(
		"Item Category",
		filters={"is_active": 1},
		fields=["name", "category_name", "category_code", "description", "icon"],
		order_by="category_name",
		ignore_permissions=True,
	)
	return categories
