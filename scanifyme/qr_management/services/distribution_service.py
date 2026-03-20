"""
Distribution Service - Business logic for QR tag distribution and assignment.

This module provides functions for:
- Creating distribution records
- Assigning tags to distribution
- Updating distribution status
- Validating tag eligibility for distribution
- Tracking tag distribution lifecycle
"""

import frappe
from frappe import _
from frappe.utils import now_datetime
from typing import Optional, List, Dict, Any


# Valid distribution destination types
VALID_DISTRIBUTION_TYPES = ["Customer", "Reseller", "Internal Stock", "Demo", "Test"]

# Valid status transitions for distribution
VALID_STATUS_TRANSITIONS = {
	"Draft": ["Packed", "Cancelled"],
	"Packed": ["Dispatched", "Cancelled"],
	"Dispatched": ["Delivered", "Cancelled"],
	"Delivered": [],
	"Cancelled": [],
}


def create_distribution_record(
	distribution_name: str,
	distributed_to_type: str,
	distributed_to_name: str,
	qr_batch: Optional[str] = None,
	quantity: int = 0,
	notes: Optional[str] = None,
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

	Raises:
	    frappe.PermissionError: If user doesn't have permission
	    frappe.ValidationError: If validation fails
	"""
	frappe.has_permission("QR Distribution Record", "create", throw=True)

	if not distribution_name:
		frappe.throw(_("Distribution name is required"))

	if distributed_to_type not in VALID_DISTRIBUTION_TYPES:
		frappe.throw(
			_("Invalid distribution type. Must be one of: {0}").format(", ".join(VALID_DISTRIBUTION_TYPES))
		)

	if not distributed_to_name:
		frappe.throw(_("Distribution destination name is required"))

	# Count tags in batch if provided
	if qr_batch:
		if not frappe.db.exists("QR Batch", qr_batch):
			frappe.throw(_("QR Batch {0} not found").format(qr_batch))

		# Count eligible tags (Printed or In Stock)
		quantity = frappe.db.count(
			"QR Code Tag",
			{"batch": qr_batch, "status": ["in", ["Printed", "In Stock"]]},
		)

	# Create the distribution record
	distribution = frappe.get_doc(
		{
			"doctype": "QR Distribution Record",
			"distribution_name": distribution_name,
			"qr_batch": qr_batch,
			"distributed_to_type": distributed_to_type,
			"distributed_to_name": distributed_to_name,
			"status": "Draft",
			"quantity": quantity,
			"notes": notes,
			"created_by": frappe.session.user,
		}
	)
	distribution.insert()

	frappe.db.commit()
	return distribution.name


def assign_tags_to_distribution(
	distribution_name: str,
	tag_names: Optional[List[str]] = None,
	update_status: bool = False,
) -> Dict[str, Any]:
	"""Assign QR tags to a distribution record.

	Tags must be in Printed or In Stock status to be distributed.
	Activated tags cannot be redistributed as fresh stock.

	Args:
	    distribution_name: QR Distribution Record name
	    tag_names: Optional list of specific tag names to assign
	    update_status: If True, update tag status to 'Assigned'

	Returns:
	    Dict with assignment summary

	Raises:
	    frappe.ValidationError: If tags are not eligible for distribution
	"""
	if not frappe.db.exists("QR Distribution Record", distribution_name):
		frappe.throw(_("Distribution record {0} not found").format(distribution_name))

	distribution = frappe.get_doc("QR Distribution Record", distribution_name)

	# Get tags to assign
	if tag_names:
		# Validate specified tags
		eligible_tags = []
		for tag_name in tag_names:
			tag = frappe.db.get_value(
				"QR Code Tag",
				tag_name,
				["name", "status", "registered_item"],
				as_dict=True,
			)
			if tag:
				if tag.status in ["Activated"]:
					# Activated tags should not be redistributed
					frappe.throw(
						_(
							"Tag {0} is activated and cannot be redistributed. "
							"It is already linked to a registered item."
						).format(tag_name)
					)
				eligible_tags.append(tag_name)
	elif distribution.qr_batch:
		# Get all eligible tags from batch
		eligible_tags = frappe.db.get_all(
			"QR Code Tag",
			filters={
				"batch": distribution.qr_batch,
				"status": ["in", ["Printed", "In Stock"]],
			},
			pluck="name",
		)
	else:
		frappe.throw(_("No tags specified and no batch linked to distribution"))

	if not eligible_tags:
		frappe.throw(_("No eligible tags found for distribution"))

	# Assign tags to distribution
	assigned_count = 0
	for tag_name in eligible_tags:
		frappe.db.set_value(
			"QR Code Tag",
			tag_name,
			{
				"distribution_record": distribution_name,
			},
		)
		if update_status:
			frappe.db.set_value(
				"QR Code Tag",
				tag_name,
				{
					"status": "Assigned",
				},
			)
		assigned_count += 1

	# Update distribution quantity
	distribution.quantity = assigned_count
	distribution.save()

	# Update batch status if distributed
	if distribution.qr_batch and update_status:
		frappe.db.set_value("QR Batch", distribution.qr_batch, "status", "Distributed")

	frappe.db.commit()

	return {
		"distribution": distribution_name,
		"tags_assigned": assigned_count,
		"status_updated": update_status,
	}


def update_distribution_status(
	distribution_name: str,
	new_status: str,
) -> Dict[str, Any]:
	"""Update the status of a distribution record.

	Valid transitions:
	- Draft -> Packed, Cancelled
	- Packed -> Dispatched, Cancelled
	- Dispatched -> Delivered, Cancelled
	- Delivered -> (none)
	- Cancelled -> (none)

	Args:
	    distribution_name: QR Distribution Record name
	    new_status: New status to set

	Returns:
	    Dict with update summary

	Raises:
	    frappe.ValidationError: If status transition is invalid
	"""
	if not frappe.db.exists("QR Distribution Record", distribution_name):
		frappe.throw(_("Distribution record {0} not found").format(distribution_name))

	distribution = frappe.get_doc("QR Distribution Record", distribution_name)

	current_status = distribution.status

	# Validate status transition
	if new_status not in VALID_STATUS_TRANSITIONS.get(current_status, []):
		frappe.throw(
			_("Invalid status transition from {0} to {1}. Valid transitions: {2}").format(
				current_status,
				new_status,
				", ".join(VALID_STATUS_TRANSITIONS.get(current_status, [])) or "none",
			)
		)

	# Update distribution status
	distribution.status = new_status
	if new_status == "Delivered":
		distribution.distributed_on = now_datetime()
	distribution.save()

	# Update associated tag statuses based on distribution status
	if new_status == "Delivered":
		# Get all tags assigned to this distribution
		tags = frappe.db.get_all(
			"QR Code Tag",
			filters={"distribution_record": distribution_name},
			fields=["name", "status"],
		)

		for tag in tags:
			# Move tags from Assigned to In Stock when delivered
			# (they become available for activation by end customer)
			if tag.status == "Assigned":
				frappe.db.set_value("QR Code Tag", tag.name, "status", "In Stock")

	frappe.db.commit()

	return {
		"distribution": distribution_name,
		"previous_status": current_status,
		"new_status": new_status,
	}


def get_distribution_detail(distribution_name: str) -> Dict[str, Any]:
	"""Get detailed information about a distribution record.

	Args:
	    distribution_name: QR Distribution Record name

	Returns:
	    Dict with distribution details and tags
	"""
	if not frappe.db.exists("QR Distribution Record", distribution_name):
		frappe.throw(_("Distribution record {0} not found").format(distribution_name))

	distribution = frappe.get_doc("QR Distribution Record", distribution_name)

	# Get tags
	tags = frappe.db.get_all(
		"QR Code Tag",
		filters={"distribution_record": distribution_name},
		fields=["name", "qr_uid", "qr_token", "status", "stock_location", "assigned_on"],
	)

	return {
		"name": distribution.name,
		"distribution_name": distribution.distribution_name,
		"qr_batch": distribution.qr_batch,
		"status": distribution.status,
		"distributed_to_type": distribution.distributed_to_type,
		"distributed_to_name": distribution.distributed_to_name,
		"distributed_on": str(distribution.distributed_on) if distribution.distributed_on else None,
		"quantity": distribution.quantity,
		"created_by": distribution.created_by,
		"notes": distribution.notes,
		"tags": tags,
	}


def can_tag_be_distributed(tag_name: str) -> Dict[str, Any]:
	"""Check if a tag can be distributed.

	A tag cannot be distributed if:
	- It is already Activated (linked to a registered item)
	- It is Suspended or Retired

	Args:
	    tag_name: QR Code Tag name

	Returns:
	    Dict with eligibility status and reason
	"""
	tag = frappe.db.get_value(
		"QR Code Tag",
		tag_name,
		["name", "status", "registered_item", "qr_uid"],
		as_dict=True,
	)

	if not tag:
		return {
			"eligible": False,
			"reason": "Tag not found",
		}

	# Check if activated
	if tag.status == "Activated":
		return {
			"eligible": False,
			"reason": "Tag is already activated and linked to a registered item",
			"qr_uid": tag.qr_uid,
			"current_status": tag.status,
		}

	# Check if suspended/retired
	if tag.status in ["Suspended", "Retired"]:
		return {
			"eligible": False,
			"reason": f"Tag status is {tag.status}",
			"qr_uid": tag.qr_uid,
			"current_status": tag.status,
		}

	return {
		"eligible": True,
		"reason": "Tag is eligible for distribution",
		"qr_uid": tag.qr_uid,
		"current_status": tag.status,
	}


def get_distributions_by_batch(batch_name: str) -> List[Dict[str, Any]]:
	"""Get all distribution records for a QR batch.

	Args:
	    batch_name: QR Batch name

	Returns:
	    List of distribution records
	"""
	distributions = frappe.db.get_all(
		"QR Distribution Record",
		filters={"qr_batch": batch_name},
		fields=[
			"name",
			"distribution_name",
			"status",
			"distributed_to_type",
			"distributed_to_name",
			"quantity",
			"distributed_on",
			"created_by",
		],
		order_by="creation desc",
	)

	return distributions
