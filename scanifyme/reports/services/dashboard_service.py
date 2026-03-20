"""
Dashboard Service - Service layer for owner and admin dashboard metrics.

This module provides business logic for aggregating dashboard data.
All functions follow the pattern: admin gets all data, owner gets own data.
"""

import frappe
from frappe.utils import now_datetime
from typing import Optional, Dict, Any, List


def get_owner_dashboard_summary(owner_profile: str) -> Dict[str, Any]:
	"""
	Get dashboard summary metrics for an owner.

	Args:
	    owner_profile: Owner Profile name, or "Administrator" for admin access

	Returns:
	    Dict with summary metrics for the owner dashboard
	"""
	# Admin can see all data
	is_admin = owner_profile == "Administrator"

	# Build filters
	owner_filter = {} if is_admin else {"owner_profile": owner_profile}

	# Count registered items by status
	items_total = frappe.db.count("Registered Item", filters=owner_filter)
	items_active = frappe.db.count("Registered Item", filters={**owner_filter, "status": "Active"})
	items_lost = frappe.db.count("Registered Item", filters={**owner_filter, "status": "Lost"})
	items_recovered = frappe.db.count("Registered Item", filters={**owner_filter, "status": "Recovered"})
	items_draft = frappe.db.count("Registered Item", filters={**owner_filter, "status": "Draft"})

	# Count recovery cases by status
	cases_total = frappe.db.count("Recovery Case", filters=owner_filter)
	cases_open = frappe.db.count("Recovery Case", filters={**owner_filter, "status": "Open"})
	cases_responded = frappe.db.count("Recovery Case", filters={**owner_filter, "status": "Owner Responded"})
	cases_return_planned = frappe.db.count(
		"Recovery Case", filters={**owner_filter, "status": "Return Planned"}
	)
	cases_recovered = frappe.db.count("Recovery Case", filters={**owner_filter, "status": "Recovered"})
	cases_closed = frappe.db.count("Recovery Case", filters={**owner_filter, "status": "Closed"})

	# Count open cases (active recovery workflow)
	cases_open_count = frappe.db.count(
		"Recovery Case",
		filters={**owner_filter, "status": ["in", ["Open", "Owner Responded", "Return Planned"]]},
	)

	# Count reward-enabled items
	reward_enabled_items = frappe.db.count("Registered Item", filters={**owner_filter, "reward_enabled": 1})

	# Count unread notifications
	unread_notifications = frappe.db.count(
		"Notification Event Log",
		filters={**owner_filter, "is_read": 0},
	)

	# Count activated QR tags
	activated_qr_count = 0
	if is_admin:
		activated_qr_count = frappe.db.count("QR Code Tag", filters={"status": "Activated"})
	else:
		# Owner: count activated tags linked to their items
		activated_qr_count = frappe.db.count(
			"QR Code Tag",
			filters={
				"status": "Activated",
				"registered_item": ["is", "set"],
			},
		)
		# Filter to only owner's items
		owner_items = frappe.get_list(
			"Registered Item",
			filters=owner_filter,
			pluck="name",
		)
		if owner_items:
			activated_qr_count = frappe.db.count(
				"QR Code Tag",
				filters={
					"status": "Activated",
					"registered_item": ["in", owner_items],
				},
			)

	return {
		"items": {
			"total": items_total,
			"active": items_active,
			"lost": items_lost,
			"recovered": items_recovered,
			"draft": items_draft,
		},
		"recovery_cases": {
			"total": cases_total,
			"open": cases_open,
			"responded": cases_responded,
			"return_planned": cases_return_planned,
			"recovered": cases_recovered,
			"closed": cases_closed,
			"active_workflow": cases_open_count,
		},
		"qr_tags": {
			"activated": activated_qr_count,
		},
		"rewards": {
			"enabled_items": reward_enabled_items,
		},
		"notifications": {
			"unread": unread_notifications,
		},
	}


def get_owner_recent_activity(
	owner_profile: str,
	limit: int = 10,
) -> Dict[str, Any]:
	"""
	Get recent activity for an owner's dashboard.

	Args:
	    owner_profile: Owner Profile name, or "Administrator" for admin access
	    limit: Maximum number of items per category

	Returns:
	    Dict with recent recovery cases, notifications, and scans
	"""
	is_admin = owner_profile == "Administrator"
	owner_filter = {} if is_admin else {"owner_profile": owner_profile}

	# Recent recovery cases
	recent_cases = frappe.get_list(
		"Recovery Case",
		filters=owner_filter,
		fields=[
			"name",
			"case_title",
			"status",
			"opened_on",
			"last_activity_on",
			"finder_name",
			"handover_status",
		],
		order_by="last_activity_on desc",
		limit=limit,
	)

	# Recent notifications (last 10)
	recent_notifications = frappe.get_list(
		"Notification Event Log",
		filters=owner_filter,
		fields=[
			"name",
			"title",
			"event_type",
			"is_read",
			"triggered_on",
			"route",
			"recovery_case",
		],
		order_by="triggered_on desc",
		limit=limit,
	)

	# Recent scans for owner's items
	owner_item_filter = {}
	if not is_admin:
		owner_item_filter = {"registered_item": ["is", "set"]}
		owner_items = frappe.get_list(
			"Registered Item",
			filters=owner_filter,
			pluck="name",
		)
		if owner_items:
			owner_item_filter = {"registered_item": ["in", owner_items]}
		else:
			owner_item_filter = {"registered_item": "-----non-existent-----"}
	else:
		owner_item_filter = {"registered_item": ["is", "set"]}

	recent_scans = frappe.get_list(
		"Scan Event",
		filters=owner_item_filter,
		fields=[
			"name",
			"token",
			"scanned_on",
			"status",
			"registered_item",
			"recovery_case",
		],
		order_by="scanned_on desc",
		limit=limit,
	)

	# Recent location shares for owner's cases
	owner_case_filter = {}
	if not is_admin:
		owner_case_filter = {"owner_profile": owner_profile}

	case_ids = []
	if not is_admin:
		cases = frappe.get_list(
			"Recovery Case",
			filters=owner_filter,
			pluck="name",
		)
		if cases:
			case_ids = cases

	recent_locations = []
	if case_ids:
		recent_locations = frappe.get_list(
			"Location Share",
			filters={"recovery_case": ["in", case_ids]},
			fields=[
				"name",
				"recovery_case",
				"latitude",
				"longitude",
				"shared_on",
				"note",
			],
			order_by="shared_on desc",
			limit=5,
		)

	return {
		"recent_cases": recent_cases or [],
		"recent_notifications": recent_notifications or [],
		"recent_scans": recent_scans or [],
		"recent_locations": recent_locations or [],
	}


def get_admin_operational_summary() -> Dict[str, Any]:
	"""
	Get system-wide operational summary for admin/operations dashboard.

	Returns:
	    Dict with system-wide metrics
	"""
	# QR Batch counts
	batches_total = frappe.db.count("QR Batch")
	batches_by_status = {}
	for status in ["Draft", "Generated", "Printed", "Distributed", "Closed"]:
		batches_by_status[status.lower().replace(" ", "_")] = frappe.db.count(
			"QR Batch", filters={"status": status}
		)

	# QR Tag counts by status
	tags_total = frappe.db.count("QR Code Tag")
	tags_by_status = {}
	for status in ["Generated", "Printed", "In Stock", "Assigned", "Activated", "Suspended", "Retired"]:
		tags_by_status[status.lower().replace(" ", "_")] = frappe.db.count(
			"QR Code Tag", filters={"status": status}
		)

	# Registered Item counts by status
	items_total = frappe.db.count("Registered Item")
	items_by_status = {}
	for status in ["Draft", "Active", "Lost", "Recovered", "Archived"]:
		items_by_status[status.lower()] = frappe.db.count("Registered Item", filters={"status": status})

	# Recovery Case counts by status
	cases_total = frappe.db.count("Recovery Case")
	cases_by_status = {}
	for status in ["Open", "Owner Responded", "Return Planned", "Recovered", "Closed", "Invalid", "Spam"]:
		key = status.lower().replace(" ", "_")
		cases_by_status[key] = frappe.db.count("Recovery Case", filters={"status": status})

	# Active workflow cases (open, responded, return planned)
	cases_active = frappe.db.count(
		"Recovery Case",
		filters={"status": ["in", ["Open", "Owner Responded", "Return Planned"]]},
	)

	# Scan Event counts
	scans_total = frappe.db.count("Scan Event")
	scans_valid = frappe.db.count("Scan Event", filters={"status": "Valid"})
	scans_invalid = frappe.db.count("Scan Event", filters={"status": "Invalid"})
	scans_recovery_initiated = frappe.db.count("Scan Event", filters={"status": "Recovery Initiated"})

	# Notification Event counts
	notifications_total = frappe.db.count("Notification Event Log")
	notifications_unread = frappe.db.count("Notification Event Log", filters={"is_read": 0})
	notifications_by_channel = {}
	for channel in ["In App", "Email", "System"]:
		notifications_by_channel[channel.lower().replace(" ", "_")] = frappe.db.count(
			"Notification Event Log", filters={"channel": channel}
		)
	notifications_by_status = {}
	for status in ["Queued", "Sent", "Failed", "Skipped"]:
		notifications_by_status[status.lower()] = frappe.db.count(
			"Notification Event Log", filters={"status": status}
		)

	# Location Shares count
	location_shares_total = frappe.db.count("Location Share")

	# Handover status breakdown
	handover_by_status = {}
	for status in [
		"Not Started",
		"Finder Contacted",
		"Location Shared",
		"Return Planned",
		"Handover Scheduled",
		"Recovered",
		"Closed",
		"Failed",
	]:
		key = status.lower().replace(" ", "_")
		handover_by_status[key] = frappe.db.count("Recovery Case", filters={"handover_status": status})

	# Reward stats
	reward_enabled_items = frappe.db.count("Registered Item", filters={"reward_enabled": 1})
	cases_with_rewards = frappe.db.count("Recovery Case", filters={"reward_offered": 1})

	# Owner profile count
	owner_profiles_total = frappe.db.count("Owner Profile")

	# Finder sessions
	sessions_active = frappe.db.count("Finder Session", filters={"status": "Active"})
	sessions_expired = frappe.db.count("Finder Session", filters={"status": "Expired"})

	return {
		"qr_batches": {
			"total": batches_total,
			"by_status": batches_by_status,
		},
		"qr_tags": {
			"total": tags_total,
			"by_status": tags_by_status,
		},
		"registered_items": {
			"total": items_total,
			"by_status": items_by_status,
		},
		"recovery_cases": {
			"total": cases_total,
			"by_status": cases_by_status,
			"active_workflow": cases_active,
		},
		"scans": {
			"total": scans_total,
			"valid": scans_valid,
			"invalid": scans_invalid,
			"recovery_initiated": scans_recovery_initiated,
		},
		"notifications": {
			"total": notifications_total,
			"unread": notifications_unread,
			"by_channel": notifications_by_channel,
			"by_status": notifications_by_status,
		},
		"location_shares": {
			"total": location_shares_total,
		},
		"handover": {
			"by_status": handover_by_status,
		},
		"rewards": {
			"enabled_items": reward_enabled_items,
			"cases_with_rewards": cases_with_rewards,
		},
		"owner_profiles": {
			"total": owner_profiles_total,
		},
		"finder_sessions": {
			"active": sessions_active,
			"expired": sessions_expired,
		},
	}
