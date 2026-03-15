import frappe
from frappe import _
from frappe.utils import cint
from scanifyme.qr_management.services.qr_service import generate_qr_batch, get_public_qr, generate_qr_image


def has_qr_role():
	"""Check if user has QR management role."""
	roles = frappe.get_roles()
	return "ScanifyMe Admin" in roles or "ScanifyMe Operations" in roles


@frappe.whitelist()
def create_qr_batch(batch_name: str, batch_size: int, batch_prefix: str = None) -> str:
	"""Create a new QR batch.

	Args:
	    batch_name: Name for the batch
	    batch_size: Number of QR codes to generate
	    batch_prefix: Optional prefix for QR UIDs

	Returns:
	    QR Batch name
	"""
	if not has_qr_role():
		frappe.throw(_("Permission denied"), frappe.PermissionError)

	if not batch_name:
		frappe.throw(_("Batch name is required"))

	batch_size = cint(batch_size)
	if batch_size <= 0:
		frappe.throw(_("Batch size must be greater than 0"))

	return generate_qr_batch(batch_name, batch_size, batch_prefix)


@frappe.whitelist()
def get_qr_batches(filters: str = None, fields: str = None, limit: int = 20) -> list:
	"""Get list of QR batches.

	Args:
	    filters: JSON string of filters
	    fields: JSON string of fields to return
	    limit: Maximum number of records

	Returns:
	    List of QR Batch documents
	"""
	if not has_qr_role():
		frappe.throw(_("Permission denied"), frappe.PermissionError)

	if not fields:
		fields = ["name", "batch_name", "batch_prefix", "batch_size", "status", "created_by", "created_on"]

	return frappe.db.get_all(
		"QR Batch",
		filters=frappe.parse_json(filters) if filters else {},
		fields=fields,
		order_by="creation desc",
		limit=cint(limit),
	)


@frappe.whitelist()
def get_qr_tags(batch: str = None, status: str = None, limit: int = 20) -> list:
	"""Get list of QR code tags.

	Args:
	    batch: Filter by batch name
	    status: Filter by status
	    limit: Maximum number of records

	Returns:
	    List of QR Code Tag documents
	"""
	if not has_qr_role():
		frappe.throw(_("Permission denied"), frappe.PermissionError)

	filters = {}
	if batch:
		filters["batch"] = batch
	if status:
		filters["status"] = status

	return frappe.db.get_all(
		"QR Code Tag",
		filters=filters,
		fields=["name", "qr_uid", "qr_token", "qr_url", "batch", "status", "registered_item", "created_on"],
		order_by="creation desc",
		limit=cint(limit),
	)


@frappe.whitelist()
def get_qr_preview(token: str) -> dict:
	"""Get preview information for a QR token.

	Args:
	    token: QR token

	Returns:
	    Dict with QR preview information
	"""
	if not has_qr_role():
		frappe.throw(_("Permission denied"), frappe.PermissionError)

	qr_tag = frappe.db.get_value(
		"QR Code Tag",
		{"qr_token": token},
		["name", "qr_uid", "qr_token", "qr_url", "batch", "status", "registered_item", "created_on"],
		as_dict=True,
	)

	if not qr_tag:
		frappe.throw(_("QR code not found"), frappe.DoesNotExistError)

	return qr_tag
