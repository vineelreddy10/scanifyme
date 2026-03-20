import frappe
from frappe import _
from frappe.utils import cint
from scanifyme.qr_management.services.qr_service import generate_qr_batch, get_public_qr, generate_qr_image
from scanifyme.qr_management.services import print_service, distribution_service, stock_service


def has_qr_role():
	"""Check if user has QR management role or is admin."""
	user = frappe.session.user

	# Admin always has access
	if user in ["Administrator", "admin"]:
		return True

	roles = frappe.get_roles()
	# Check for ScanifyMe roles and System Manager
	return "ScanifyMe Admin" in roles or "ScanifyMe Operations" in roles or "System Manager" in roles


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


# ==================== PRINT JOB APIs ====================


@frappe.whitelist()
def create_qr_print_job(
	print_job_name: str,
	qr_batch: str = None,
	template_name: str = None,
	notes: str = None,
) -> str:
	"""Create a new QR print job.

	Args:
	    print_job_name: Name for the print job
	    qr_batch: Optional QR Batch to print
	    template_name: Optional template name
	    notes: Optional notes

	Returns:
	    QR Print Job name
	"""
	if not has_qr_role():
		frappe.throw(_("Permission denied"), frappe.PermissionError)

	return print_service.create_print_job(
		print_job_name=print_job_name,
		qr_batch=qr_batch,
		template_name=template_name,
		notes=notes,
	)


@frappe.whitelist()
def get_qr_print_jobs(filters: str = None, limit: int = 20) -> list:
	"""Get list of QR print jobs.

	Args:
	    filters: JSON string of filters
	    limit: Maximum number of records

	Returns:
	    List of QR Print Job documents
	"""
	if not has_qr_role():
		frappe.throw(_("Permission denied"), frappe.PermissionError)

	return frappe.db.get_all(
		"QR Print Job",
		filters=frappe.parse_json(filters) if filters else {},
		fields=[
			"name",
			"print_job_name",
			"qr_batch",
			"status",
			"item_count",
			"generated_on",
			"printed_on",
			"created_by",
		],
		order_by="creation desc",
		limit=cint(limit),
	)


@frappe.whitelist()
def get_qr_print_job_detail(print_job_name: str) -> dict:
	"""Get detailed information about a print job.

	Args:
	    print_job_name: QR Print Job name

	Returns:
	    Dict with print job details and tags
	"""
	if not has_qr_role():
		frappe.throw(_("Permission denied"), frappe.PermissionError)

	return print_service.get_print_job_detail(print_job_name)


@frappe.whitelist()
def generate_qr_print_output(print_job_name: str, output_format: str = "html") -> dict:
	"""Generate print output for a QR print job.

	Args:
	    print_job_name: QR Print Job name
	    output_format: Output format (html or pdf)

	Returns:
	    Dict with output file URL and metadata
	"""
	if not has_qr_role():
		frappe.throw(_("Permission denied"), frappe.PermissionError)

	return print_service.generate_print_output(print_job_name, output_format)


@frappe.whitelist()
def mark_qr_print_job_printed(print_job_name: str) -> dict:
	"""Mark QR tags as printed and update their status.

	Args:
	    print_job_name: QR Print Job name

	Returns:
	    Dict with update summary
	"""
	if not has_qr_role():
		frappe.throw(_("Permission denied"), frappe.PermissionError)

	return print_service.mark_tags_printed(print_job_name)


# ==================== DISTRIBUTION APIs ====================


@frappe.whitelist()
def create_qr_distribution_record(
	distribution_name: str,
	distributed_to_type: str,
	distributed_to_name: str,
	qr_batch: str = None,
	quantity: int = 0,
	notes: str = None,
) -> str:
	"""Create a new QR distribution record.

	Args:
	    distribution_name: Name for the distribution
	    distributed_to_type: Type of destination (Customer, Reseller, Internal Stock, Demo, Test)
	    distributed_to_name: Name of the destination
	    qr_batch: Optional QR Batch to distribute
	    quantity: Number of tags to distribute
	    notes: Optional notes

	Returns:
	    QR Distribution Record name
	"""
	if not has_qr_role():
		frappe.throw(_("Permission denied"), frappe.PermissionError)

	return distribution_service.create_distribution_record(
		distribution_name=distribution_name,
		distributed_to_type=distributed_to_type,
		distributed_to_name=distributed_to_name,
		qr_batch=qr_batch,
		quantity=quantity,
		notes=notes,
	)


@frappe.whitelist()
def get_qr_distribution_records(filters: str = None, limit: int = 20) -> list:
	"""Get list of QR distribution records.

	Args:
	    filters: JSON string of filters
	    limit: Maximum number of records

	Returns:
	    List of QR Distribution Record documents
	"""
	if not has_qr_role():
		frappe.throw(_("Permission denied"), frappe.PermissionError)

	return frappe.db.get_all(
		"QR Distribution Record",
		filters=frappe.parse_json(filters) if filters else {},
		fields=[
			"name",
			"distribution_name",
			"qr_batch",
			"status",
			"distributed_to_type",
			"distributed_to_name",
			"quantity",
			"distributed_on",
			"created_by",
		],
		order_by="creation desc",
		limit=cint(limit),
	)


@frappe.whitelist()
def get_qr_distribution_detail(distribution_name: str) -> dict:
	"""Get detailed information about a distribution record.

	Args:
	    distribution_name: QR Distribution Record name

	Returns:
	    Dict with distribution details and tags
	"""
	if not has_qr_role():
		frappe.throw(_("Permission denied"), frappe.PermissionError)

	return distribution_service.get_distribution_detail(distribution_name)


@frappe.whitelist()
def update_qr_distribution_status(distribution_name: str, new_status: str) -> dict:
	"""Update the status of a distribution record.

	Args:
	    distribution_name: QR Distribution Record name
	    new_status: New status (Draft, Packed, Dispatched, Delivered, Cancelled)

	Returns:
	    Dict with update summary
	"""
	if not has_qr_role():
		frappe.throw(_("Permission denied"), frappe.PermissionError)

	return distribution_service.update_distribution_status(distribution_name, new_status)


@frappe.whitelist()
def assign_tags_to_distribution(
	distribution_name: str,
	tag_names: str = None,
	update_status: bool = False,
) -> dict:
	"""Assign QR tags to a distribution record.

	Args:
	    distribution_name: QR Distribution Record name
	    tag_names: Optional JSON list of specific tag names to assign
	    update_status: If True, update tag status to 'Assigned'

	Returns:
	    Dict with assignment summary
	"""
	if not has_qr_role():
		frappe.throw(_("Permission denied"), frappe.PermissionError)

	tag_list = frappe.parse_json(tag_names) if tag_names else None
	return distribution_service.assign_tags_to_distribution(
		distribution_name=distribution_name,
		tag_names=tag_list,
		update_status=update_status,
	)


# ==================== STOCK APIs ====================


@frappe.whitelist()
def get_qr_stock_summary(batch: str = None) -> dict:
	"""Get stock summary for QR tags.

	Args:
	    batch: Optional QR Batch to filter by

	Returns:
	    Dict with stock summary statistics
	"""
	if not has_qr_role():
		frappe.throw(_("Permission denied"), frappe.PermissionError)

	return stock_service.get_stock_summary(batch)


@frappe.whitelist()
def validate_tag_activation_eligibility(tag_name: str) -> dict:
	"""Validate if a tag can be activated.

	Args:
	    tag_name: QR Code Tag name

	Returns:
	    Dict with validation result
	"""
	if not has_qr_role():
		frappe.throw(_("Permission denied"), frappe.PermissionError)

	return stock_service.validate_tag_can_be_activated(tag_name)


@frappe.whitelist()
def get_print_ready_batches() -> list:
	"""Get batches that are ready for printing.

	Returns:
	    List of batch dictionaries with print readiness info
	"""
	if not has_qr_role():
		frappe.throw(_("Permission denied"), frappe.PermissionError)

	return stock_service.get_print_ready_batches()


@frappe.whitelist()
def get_distribution_ready_tags(batch_name: str) -> list:
	"""Get tags that are ready for distribution from a batch.

	Args:
	    batch_name: QR Batch name

	Returns:
	    List of tag dictionaries
	"""
	if not has_qr_role():
		frappe.throw(_("Permission denied"), frappe.PermissionError)

	return stock_service.get_distribution_ready_tags(batch_name)
