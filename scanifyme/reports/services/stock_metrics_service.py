"""
Stock Metrics Service - QR and item stock reporting.

This module provides service functions for QR stock and registered item reports.
"""

import frappe
from typing import Optional, Dict, Any, List


def get_stock_metrics(
	batch: Optional[str] = None,
	status: Optional[str] = None,
	limit: int = 100,
) -> List[Dict[str, Any]]:
	"""
	Get QR tag stock metrics with optional filters.

	Args:
	    batch: Filter by QR batch (optional)
	    status: Filter by tag status (optional)
	    limit: Maximum rows to return

	Returns:
	    List of QR tag rows with enrichment data
	"""
	filters: Dict[str, Any] = {}

	if batch:
		filters["batch"] = batch

	if status:
		filters["status"] = status

	rows = frappe.get_list(
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
			"assigned_on",
			"assigned_to_user",
			"stock_location",
			"created_on",
		],
		order_by="created_on desc",
		limit=limit,
		ignore_permissions=True,
	)

	# Enrich with batch info and item info
	for row in rows:
		if row.batch:
			batch_info = frappe.db.get_value(
				"QR Batch",
				row.batch,
				["batch_name", "batch_prefix", "batch_size", "status"],
				as_dict=True,
			)
			if batch_info:
				row["batch_name"] = batch_info.batch_name
				row["batch_prefix"] = batch_info.batch_prefix
				row["batch_size"] = batch_info.batch_size
				row["batch_status"] = batch_info.status
			else:
				row["batch_name"] = None
				row["batch_prefix"] = None
				row["batch_size"] = None
				row["batch_status"] = None
		else:
			row["batch_name"] = None
			row["batch_prefix"] = None
			row["batch_size"] = None
			row["batch_status"] = None

		if row.registered_item:
			item_info = frappe.db.get_value(
				"Registered Item",
				row.registered_item,
				["item_name", "owner_profile", "status", "activation_date"],
				as_dict=True,
			)
			if item_info:
				row["item_name"] = item_info.item_name
				row["item_status"] = item_info.status
				row["activation_date"] = item_info.activation_date
				owner_name = frappe.db.get_value(
					"Owner Profile",
					item_info.owner_profile,
					"display_name",
				)
				row["owner_name"] = owner_name
			else:
				row["item_name"] = None
				row["item_status"] = None
				row["activation_date"] = None
				row["owner_name"] = None
		else:
			row["item_name"] = None
			row["item_status"] = None
			row["activation_date"] = None
			row["owner_name"] = None

	return rows


def get_qr_stock_summary(
	batch: Optional[str] = None,
) -> Dict[str, Any]:
	"""
	Get QR stock summary aggregated by status for a batch (or all batches).

	Args:
	    batch: Specific batch to summarize (optional, all if None)

	Returns:
	    Dict with total counts and per-status breakdown
	"""
	filters = {}
	if batch:
		filters["batch"] = batch

	total = frappe.db.count("QR Code Tag", filters=filters)

	by_status: Dict[str, int] = {}
	for status in ["Generated", "Printed", "In Stock", "Assigned", "Activated", "Suspended", "Retired"]:
		status_filters = {**filters, "status": status}
		by_status[status.lower().replace(" ", "_")] = frappe.db.count("QR Code Tag", filters=status_filters)

	# Items linked
	linked_filters = {**filters, "registered_item": ["is", "set"]}
	linked_count = frappe.db.count("QR Code Tag", filters=linked_filters)

	# Items activated
	activated_filters = {**filters, "status": "Activated"}
	activated_count = frappe.db.count("QR Code Tag", filters=activated_filters)

	# By batch summary (if not filtering by specific batch)
	by_batch: List[Dict[str, Any]] = []
	if not batch:
		batches = frappe.get_list(
			"QR Batch",
			fields=["name", "batch_name", "batch_size", "status"],
			order_by="creation desc",
			limit=20,
		)
		for b in batches:
			batch_total = frappe.db.count("QR Code Tag", filters={"batch": b.name})
			batch_statuses = {}
			for status in [
				"Generated",
				"Printed",
				"In Stock",
				"Assigned",
				"Activated",
				"Suspended",
				"Retired",
			]:
				batch_status_filters = {"batch": b.name, "status": status}
				batch_statuses[status.lower().replace(" ", "_")] = frappe.db.count(
					"QR Code Tag", filters=batch_status_filters
				)
			by_batch.append(
				{
					"batch": b.name,
					"batch_name": b.batch_name,
					"batch_size": b.batch_size,
					"batch_status": b.status,
					"total_tags": batch_total,
					"by_status": batch_statuses,
				}
			)

	return {
		"total_tags": total,
		"by_status": by_status,
		"linked_items": linked_count,
		"activated": activated_count,
		"by_batch": by_batch,
	}


def get_registered_items_report(
	owner_profile: Optional[str] = None,
	status: Optional[str] = None,
	category: Optional[str] = None,
	batch: Optional[str] = None,
	limit: int = 100,
) -> List[Dict[str, Any]]:
	"""
	Get registered items report with optional filters.

	Args:
	    owner_profile: Filter by owner (optional, admin sees all if None)
	    status: Filter by item status (optional)
	    category: Filter by item category (optional)
	    batch: Filter by QR batch (optional)
	    limit: Maximum rows to return

	Returns:
	    List of registered item rows with enrichment
	"""
	filters: Dict[str, Any] = {}

	if owner_profile and owner_profile != "Administrator":
		filters["owner_profile"] = owner_profile

	if status:
		filters["status"] = status

	if category:
		filters["item_category"] = category

	if batch:
		filters["batch"] = batch

	rows = frappe.get_list(
		"Registered Item",
		filters=filters,
		fields=[
			"name",
			"item_name",
			"status",
			"public_label",
			"owner_profile",
			"qr_code_tag",
			"item_category",
			"activation_date",
			"last_scan_at",
			"reward_enabled",
			"reward_amount_text",
			"reward_visibility",
		],
		order_by="creation desc",
		limit=limit,
		ignore_permissions=True,
	)

	# Enrich with category, QR, and owner info
	for row in rows:
		if row.item_category:
			cat_info = frappe.db.get_value(
				"Item Category",
				row.item_category,
				["category_name", "icon"],
				as_dict=True,
			)
			row["category_name"] = cat_info.category_name if cat_info else row.item_category
			row["category_icon"] = cat_info.icon if cat_info else None
		else:
			row["category_name"] = None
			row["category_icon"] = None

		if row.qr_code_tag:
			qr_info = frappe.db.get_value(
				"QR Code Tag",
				row.qr_code_tag,
				["qr_uid", "batch", "status"],
				as_dict=True,
			)
			if qr_info:
				row["qr_uid"] = qr_info.qr_uid
				row["batch"] = qr_info.batch
				row["qr_status"] = qr_info.status
			else:
				row["qr_uid"] = None
				row["batch"] = None
				row["qr_status"] = None
		else:
			row["qr_uid"] = None
			row["batch"] = None
			row["qr_status"] = None

		if row.owner_profile:
			owner_info = frappe.db.get_value(
				"Owner Profile",
				row.owner_profile,
				["display_name", "user"],
				as_dict=True,
			)
			if owner_info:
				row["owner_name"] = owner_info.display_name
				row["owner_email"] = owner_info.user
			else:
				row["owner_name"] = None
				row["owner_email"] = None
		else:
			row["owner_name"] = None
			row["owner_email"] = None

		# Count open cases for this item
		if row.name:
			open_cases = frappe.db.count(
				"Recovery Case",
				filters={
					"registered_item": row.name,
					"status": ["in", ["Open", "Owner Responded", "Return Planned"]],
				},
			)
			row["open_cases"] = open_cases
		else:
			row["open_cases"] = 0

		# Count total scans
		if row.name:
			total_scans = frappe.db.count(
				"Scan Event",
				filters={"registered_item": row.name},
			)
			row["total_scans"] = total_scans
		else:
			row["total_scans"] = 0

	return rows
