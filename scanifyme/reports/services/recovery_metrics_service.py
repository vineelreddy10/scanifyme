"""
Recovery Metrics Service - Aggregation queries for recovery and scan reporting.

This module provides service functions for recovery and scan metric reports.
"""

import frappe
from typing import Optional, Dict, Any, List


def get_recovery_metrics(
	owner_profile: Optional[str] = None,
	status: Optional[str] = None,
	batch: Optional[str] = None,
	date_from: Optional[str] = None,
	date_to: Optional[str] = None,
	limit: int = 100,
) -> List[Dict[str, Any]]:
	"""
	Get recovery case metrics with optional filters.

	Args:
	    owner_profile: Filter by owner (optional, admin sees all if None)
	    status: Filter by case status (optional)
	    batch: Filter by QR batch (optional)
	    date_from: Filter by opened_on >= date_from (optional)
	    date_to: Filter by opened_on <= date_to (optional)
	    limit: Maximum rows to return

	Returns:
	    List of recovery case metric rows
	"""
	filters: Dict[str, Any] = {}

	if owner_profile and owner_profile != "Administrator":
		filters["owner_profile"] = owner_profile

	if status:
		filters["status"] = status

	if date_from and date_to:
		filters["opened_on"] = ["between", [date_from, date_to]]
	elif date_from:
		filters["opened_on"] = [">=", date_from]
	elif date_to:
		filters["opened_on"] = ["<=", date_to]

	# If batch filter, join through QR Code Tag
	if batch:
		filters["batch"] = batch

	rows = frappe.get_list(
		"Recovery Case",
		filters=filters,
		fields=[
			"name",
			"case_title",
			"status",
			"opened_on",
			"last_activity_on",
			"closed_on",
			"owner_profile",
			"registered_item",
			"qr_code_tag",
			"finder_name",
			"handover_status",
			"handover_note",
			"reward_offered",
			"reward_display_text",
			"reward_status",
			"latest_location_summary",
		],
		order_by="last_activity_on desc",
		limit=limit,
		ignore_permissions=True,
	)

	# Add computed fields
	for row in rows:
		# Compute case age in hours
		if row.opened_on:
			opened = frappe.utils.get_datetime(row.opened_on)
			now = frappe.utils.get_datetime()
			age_hours = (now - opened).total_seconds() / 3600
			row["age_hours"] = round(age_hours, 1)
		else:
			row["age_hours"] = None

		# Compute resolution time if closed
		if row.closed_on and row.opened_on:
			opened = frappe.utils.get_datetime(row.opened_on)
			closed = frappe.utils.get_datetime(row.closed_on)
			resolution_hours = (closed - opened).total_seconds() / 3600
			row["resolution_hours"] = round(resolution_hours, 1)
		else:
			row["resolution_hours"] = None

		# Get item category
		if row.registered_item:
			item_cat = frappe.db.get_value(
				"Registered Item",
				row.registered_item,
				"item_category",
			)
			row["item_category"] = item_cat
		else:
			row["item_category"] = None

		# Get owner display name
		if row.owner_profile:
			owner_name = frappe.db.get_value(
				"Owner Profile",
				row.owner_profile,
				"display_name",
			)
			row["owner_name"] = owner_name
		else:
			row["owner_name"] = None

	return rows


def get_scan_metrics(
	status: Optional[str] = None,
	date_from: Optional[str] = None,
	date_to: Optional[str] = None,
	limit: int = 100,
) -> List[Dict[str, Any]]:
	"""
	Get scan event metrics with optional filters.

	Args:
	    status: Filter by scan status (optional)
	    date_from: Filter by scanned_on >= date_from (optional)
	    date_to: Filter by scanned_on <= date_to (optional)
	    limit: Maximum rows to return

	Returns:
	    List of scan event metric rows
	"""
	filters: Dict[str, Any] = {}

	if status:
		filters["status"] = status

	if date_from and date_to:
		filters["scanned_on"] = ["between", [date_from, date_to]]
	elif date_from:
		filters["scanned_on"] = [">=", date_from]
	elif date_to:
		filters["scanned_on"] = ["<=", date_to]

	rows = frappe.get_list(
		"Scan Event",
		filters=filters,
		fields=[
			"name",
			"token",
			"qr_code_tag",
			"registered_item",
			"scanned_on",
			"status",
			"ip_hash",
			"route",
			"recovery_case",
		],
		order_by="scanned_on desc",
		limit=limit,
		ignore_permissions=True,
	)

	# Enrich with item and QR info
	for row in rows:
		if row.registered_item:
			item_info = frappe.db.get_value(
				"Registered Item",
				row.registered_item,
				["item_name", "item_category", "status", "owner_profile"],
				as_dict=True,
			)
			if item_info:
				row["item_name"] = item_info.item_name
				row["item_category"] = item_info.item_category
				row["item_status"] = item_info.status
				# Get owner display name
				owner_name = frappe.db.get_value(
					"Owner Profile",
					item_info.owner_profile,
					"display_name",
				)
				row["owner_name"] = owner_name
			else:
				row["item_name"] = None
				row["item_category"] = None
				row["item_status"] = None
				row["owner_name"] = None
		else:
			row["item_name"] = None
			row["item_category"] = None
			row["item_status"] = None
			row["owner_name"] = None

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

	return rows


def get_notification_metrics(
	owner_profile: Optional[str] = None,
	channel: Optional[str] = None,
	status: Optional[str] = None,
	date_from: Optional[str] = None,
	date_to: Optional[str] = None,
	limit: int = 100,
) -> List[Dict[str, Any]]:
	"""
	Get notification event log metrics with optional filters.

	Args:
	    owner_profile: Filter by owner (optional, admin sees all if None)
	    channel: Filter by channel (optional)
	    status: Filter by notification status (optional)
	    date_from: Filter by triggered_on >= date_from (optional)
	    date_to: Filter by triggered_on <= date_to (optional)
	    limit: Maximum rows to return

	Returns:
	    List of notification event metric rows
	"""
	filters: Dict[str, Any] = {}

	if owner_profile and owner_profile != "Administrator":
		filters["owner_profile"] = owner_profile

	if channel:
		filters["channel"] = channel

	if status:
		filters["status"] = status

	if date_from and date_to:
		filters["triggered_on"] = ["between", [date_from, date_to]]
	elif date_from:
		filters["triggered_on"] = [">=", date_from]
	elif date_to:
		filters["triggered_on"] = ["<=", date_to]

	rows = frappe.get_list(
		"Notification Event Log",
		filters=filters,
		fields=[
			"name",
			"title",
			"event_type",
			"channel",
			"status",
			"priority",
			"is_read",
			"triggered_on",
			"delivered_on",
			"owner_profile",
			"recovery_case",
			"registered_item",
			"route",
			"error_message",
		],
		order_by="triggered_on desc",
		limit=limit,
		ignore_permissions=True,
	)

	# Enrich with owner display name
	for row in rows:
		if row.owner_profile:
			owner_name = frappe.db.get_value(
				"Owner Profile",
				row.owner_profile,
				"display_name",
			)
			row["owner_name"] = owner_name
		else:
			row["owner_name"] = None

	return rows
