"""
Stock Service - Business logic for QR tag stock management and validation.

This module provides functions for:
- Getting stock summary statistics
- Validating tag eligibility for activation
- Managing stock lifecycle states
- Tracking stock by location/status
"""

import frappe
from frappe import _
from frappe.utils import now_datetime, cint
from typing import Optional, List, Dict, Any


# Valid tag statuses
VALID_TAG_STATUSES = ["Generated", "Printed", "In Stock", "Assigned", "Activated", "Suspended", "Retired"]


def get_stock_summary(batch_name: Optional[str] = None) -> Dict[str, Any]:
	"""Get stock summary for QR tags.

	Provides counts by status and optionally filtered by batch.

	Args:
	    batch_name: Optional QR Batch to filter by

	Returns:
	    Dict with stock summary statistics
	"""
	filters = {}
	if batch_name:
		filters["batch"] = batch_name

	# Get count by status
	status_counts = {}
	for status in VALID_TAG_STATUSES:
		count = frappe.db.count("QR Code Tag", {**filters, "status": status})
		status_counts[status] = count

	# Get total
	total = sum(status_counts.values())

	# Get batch info if specified
	batch_info = None
	if batch_name:
		batch = frappe.db.get_value(
			"QR Batch",
			batch_name,
			["name", "batch_name", "batch_size", "status"],
			as_dict=True,
		)
		if batch:
			batch_info = {
				"name": batch.name,
				"batch_name": batch.batch_name,
				"expected_size": batch.batch_size,
				"batch_status": batch.status,
			}

	return {
		"batch": batch_name,
		"batch_info": batch_info,
		"total_tags": total,
		"status_counts": status_counts,
		"generated": status_counts.get("Generated", 0),
		"printed": status_counts.get("Printed", 0),
		"in_stock": status_counts.get("In Stock", 0),
		"assigned": status_counts.get("Assigned", 0),
		"activated": status_counts.get("Activated", 0),
		"suspended": status_counts.get("Suspended", 0),
		"retired": status_counts.get("Retired", 0),
	}


def get_tags_by_status(
	status: str,
	batch_name: Optional[str] = None,
	limit: int = 50,
) -> List[Dict[str, Any]]:
	"""Get QR tags by status.

	Args:
	    status: Tag status to filter by
	    batch_name: Optional QR Batch to filter by
	    limit: Maximum number of tags to return

	Returns:
	    List of QR tag dictionaries
	"""
	if status not in VALID_TAG_STATUSES:
		frappe.throw(_("Invalid status: {0}").format(status))

	filters = {"status": status}
	if batch_name:
		filters["batch"] = batch_name

	tags = frappe.db.get_all(
		"QR Code Tag",
		filters=filters,
		fields=[
			"name",
			"qr_uid",
			"qr_token",
			"qr_url",
			"batch",
			"status",
			"print_job",
			"distribution_record",
			"registered_item",
			"stock_location",
			"assigned_on",
			"created_on",
		],
		order_by="creation desc",
		limit=cint(limit),
	)

	return tags


def validate_tag_can_be_activated(tag_name: str) -> Dict[str, Any]:
	"""Validate if a tag can be activated.

	A tag can be activated if:
	- It exists
	- It is in 'In Stock' or 'Assigned' status (ready for activation)
	- It is not already activated
	- It is not suspended or retired

	Note: The actual activation is handled by the items API.
	This function checks stock-state eligibility only.

	Args:
	    tag_name: QR Code Tag name

	Returns:
	    Dict with validation result and reason
	"""
	tag = frappe.db.get_value(
		"QR Code Tag",
		tag_name,
		[
			"name",
			"qr_uid",
			"qr_token",
			"status",
			"registered_item",
			"batch",
		],
		as_dict=True,
	)

	if not tag:
		return {
			"can_activate": False,
			"reason": "Tag not found",
			"qr_uid": None,
		}

	# Already activated
	if tag.status == "Activated":
		return {
			"can_activate": False,
			"reason": "Tag is already activated",
			"qr_uid": tag.qr_uid,
			"registered_item": tag.registered_item,
		}

	# Suspended or retired tags cannot be activated
	if tag.status in ["Suspended", "Retired"]:
		return {
			"can_activate": False,
			"reason": f"Tag status is {tag.status} and cannot be activated",
			"qr_uid": tag.qr_uid,
			"current_status": tag.status,
		}

	# Generated tags need to be printed first
	if tag.status == "Generated":
		return {
			"can_activate": False,
			"reason": "Tag must be printed and in stock before activation",
			"qr_uid": tag.qr_uid,
			"current_status": tag.status,
		}

	# Printed tags can be activated if in stock
	if tag.status == "Printed":
		return {
			"can_activate": True,
			"reason": "Tag is printed and ready for activation",
			"qr_uid": tag.qr_uid,
			"current_status": tag.status,
		}

	# In Stock or Assigned tags can be activated
	if tag.status in ["In Stock", "Assigned"]:
		return {
			"can_activate": True,
			"reason": "Tag is available for activation",
			"qr_uid": tag.qr_uid,
			"current_status": tag.status,
		}

	# Default: cannot activate
	return {
		"can_activate": False,
		"reason": f"Tag status {tag.status} does not allow activation",
		"qr_uid": tag.qr_uid,
		"current_status": tag.status,
	}


def update_tag_stock_location(tag_name: str, location: str) -> Dict[str, Any]:
	"""Update the stock location of a QR tag.

	Args:
	    tag_name: QR Code Tag name
	    location: New stock location

	Returns:
	    Dict with update result
	"""
	if not frappe.db.exists("QR Code Tag", tag_name):
		frappe.throw(_("Tag {0} not found").format(tag_name))

	frappe.db.set_value("QR Code Tag", tag_name, "stock_location", location)
	frappe.db.commit()

	return {
		"tag": tag_name,
		"stock_location": location,
		"updated": True,
	}


def get_stock_by_location(location: Optional[str] = None) -> Dict[str, Any]:
	"""Get stock summary by location.

	Args:
	    location: Optional location to filter by

	Returns:
	    Dict with stock by location
	"""
	if location:
		tags = frappe.db.get_all(
			"QR Code Tag",
			filters={"stock_location": location},
			fields=["status", "count(*) as count"],
			group_by="status",
		)
		return {
			"location": location,
			"status_breakdown": {tag.status: tag.count for tag in tags},
		}

	# Get all locations with counts
	locations = frappe.db.get_all(
		"QR Code Tag",
		fields=["stock_location", "count(*) as count"],
		group_by="stock_location",
	)

	result = {}
	for loc in locations:
		if loc.stock_location:
			result[loc.stock_location] = loc.count

	return {
		"locations": result,
	}


def get_print_ready_batches() -> List[Dict[str, Any]]:
	"""Get batches that are ready for printing.

	A batch is ready for printing if:
	- Status is 'Generated' (QR codes have been created)
	- Has tags in 'Generated' status

	Returns:
	    List of batch dictionaries with print readiness info
	"""
	batches = frappe.db.get_all(
		"QR Batch",
		filters={"status": "Generated"},
		fields=["name", "batch_name", "batch_prefix", "batch_size", "created_by", "created_on"],
		order_by="creation desc",
	)

	result = []
	for batch in batches:
		# Count tags in Generated status
		generated_count = frappe.db.count(
			"QR Code Tag",
			{"batch": batch.name, "status": "Generated"},
		)

		# Count total tags
		total_count = frappe.db.count("QR Code Tag", {"batch": batch.name})

		result.append(
			{
				"name": batch.name,
				"batch_name": batch.batch_name,
				"batch_prefix": batch.batch_prefix,
				"total_tags": total_count,
				"print_ready_tags": generated_count,
				"created_by": batch.created_by,
				"created_on": str(batch.created_on),
			}
		)

	return result


def get_distribution_ready_tags(batch_name: str) -> List[Dict[str, Any]]:
	"""Get tags that are ready for distribution from a batch.

	Tags are ready for distribution if:
	- Status is 'Printed' or 'In Stock'

	Args:
	    batch_name: QR Batch name

	Returns:
	    List of tag dictionaries
	"""
	tags = frappe.db.get_all(
		"QR Code Tag",
		filters={
			"batch": batch_name,
			"status": ["in", ["Printed", "In Stock"]],
		},
		fields=[
			"name",
			"qr_uid",
			"qr_token",
			"status",
			"print_job",
			"stock_location",
			"created_on",
		],
		order_by="creation asc",
	)

	return tags
