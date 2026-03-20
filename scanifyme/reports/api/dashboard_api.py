"""
Dashboard API - Whitelisted API methods for dashboard and reporting.

This module provides API endpoints for owner and admin dashboard views.
All endpoints enforce authentication and permission checks.
"""

import frappe
from scanifyme.reports.services import dashboard_service
from scanifyme.reports.services import recovery_metrics_service
from scanifyme.reports.services import stock_metrics_service
from scanifyme.utils.permissions import get_owner_profile_for_user, is_scanifyme_admin


def _get_auth_context() -> dict:
	"""
	Get authentication context for the current user.

	Returns:
	    Dict with owner_profile, is_admin flags
	"""
	owner_profile = get_owner_profile_for_user()
	if not owner_profile:
		frappe.throw("Authentication required", frappe.PermissionError)

	is_admin = is_scanifyme_admin()
	return {
		"owner_profile": owner_profile,
		"is_admin": is_admin,
	}


# ==============================================================================
# OWNER DASHBOARD APIs
# ==============================================================================


@frappe.whitelist()
def get_owner_dashboard_summary() -> dict:
	"""
	Get dashboard summary metrics for the current owner.

	Returns:
	    Dict with items, recovery cases, QR tags, rewards, notifications counts
	"""
	ctx = _get_auth_context()
	return dashboard_service.get_owner_dashboard_summary(ctx["owner_profile"])


@frappe.whitelist()
def get_owner_recent_activity(limit: int = 10) -> dict:
	"""
	Get recent activity for the owner dashboard.

	Args:
	    limit: Maximum items per category (default 10)

	Returns:
	    Dict with recent_cases, recent_notifications, recent_scans, recent_locations
	"""
	ctx = _get_auth_context()
	return dashboard_service.get_owner_recent_activity(ctx["owner_profile"], limit=limit)


# ==============================================================================
# ADMIN / OPERATIONS DASHBOARD APIs
# ==============================================================================


@frappe.whitelist()
def get_admin_operational_summary() -> dict:
	"""
	Get system-wide operational summary for admin.

	Admin-only: returns all system metrics.

	Returns:
	    Dict with all system-wide counts and breakdowns
	"""
	ctx = _get_auth_context()
	if not ctx["is_admin"]:
		frappe.throw("Admin access required", frappe.PermissionError)

	return dashboard_service.get_admin_operational_summary()


# ==============================================================================
# RECOVERY METRICS APIs
# ==============================================================================


@frappe.whitelist()
def get_recovery_metrics(
	status: str = None,
	date_from: str = None,
	date_to: str = None,
	limit: int = 100,
) -> list:
	"""
	Get recovery case metrics with filters.

	Admin sees all cases. Owners see only their own.

	Args:
	    status: Filter by case status (optional)
	    date_from: Filter by opened_on >= date_from (optional)
	    date_to: Filter by opened_on <= date_to (optional)
	    limit: Maximum rows (default 100)

	Returns:
	    List of recovery case metric rows
	"""
	ctx = _get_auth_context()
	owner_profile = None if ctx["is_admin"] else ctx["owner_profile"]

	return recovery_metrics_service.get_recovery_metrics(
		owner_profile=owner_profile,
		status=status,
		date_from=date_from,
		date_to=date_to,
		limit=limit,
	)


@frappe.whitelist()
def get_scan_metrics(
	status: str = None,
	date_from: str = None,
	date_to: str = None,
	limit: int = 100,
) -> list:
	"""
	Get scan event metrics with filters.

	Admin-only endpoint.

	Args:
	    status: Filter by scan status (optional)
	    date_from: Filter by scanned_on >= date_from (optional)
	    date_to: Filter by scanned_on <= date_to (optional)
	    limit: Maximum rows (default 100)

	Returns:
	    List of scan event metric rows
	"""
	ctx = _get_auth_context()
	if not ctx["is_admin"]:
		frappe.throw("Admin access required", frappe.PermissionError)

	return recovery_metrics_service.get_scan_metrics(
		status=status,
		date_from=date_from,
		date_to=date_to,
		limit=limit,
	)


@frappe.whitelist()
def get_notification_metrics(
	channel: str = None,
	status: str = None,
	date_from: str = None,
	date_to: str = None,
	limit: int = 100,
) -> list:
	"""
	Get notification event log metrics with filters.

	Admin sees all. Owners see only their own.

	Args:
	    channel: Filter by channel - In App, Email, System (optional)
	    status: Filter by status - Queued, Sent, Failed, Skipped (optional)
	    date_from: Filter by triggered_on >= date_from (optional)
	    date_to: Filter by triggered_on <= date_to (optional)
	    limit: Maximum rows (default 100)

	Returns:
	    List of notification event rows
	"""
	ctx = _get_auth_context()
	owner_profile = None if ctx["is_admin"] else ctx["owner_profile"]

	return recovery_metrics_service.get_notification_metrics(
		owner_profile=owner_profile,
		channel=channel,
		status=status,
		date_from=date_from,
		date_to=date_to,
		limit=limit,
	)


# ==============================================================================
# STOCK METRICS APIs
# ==============================================================================


@frappe.whitelist()
def get_stock_metrics(
	batch: str = None,
	status: str = None,
	limit: int = 100,
) -> list:
	"""
	Get QR tag stock metrics with filters.

	Admin-only endpoint.

	Args:
	    batch: Filter by QR batch (optional)
	    status: Filter by tag status (optional)
	    limit: Maximum rows (default 100)

	Returns:
	    List of QR tag rows with enrichment
	"""
	ctx = _get_auth_context()
	if not ctx["is_admin"]:
		frappe.throw("Admin access required", frappe.PermissionError)

	return stock_metrics_service.get_stock_metrics(
		batch=batch,
		status=status,
		limit=limit,
	)


@frappe.whitelist()
def get_qr_stock_summary(batch: str = None) -> dict:
	"""
	Get QR stock summary aggregated by status.

	Admin-only endpoint.

	Args:
	    batch: Specific batch to summarize (optional)

	Returns:
	    Dict with total counts, per-status breakdown, by-batch summary
	"""
	ctx = _get_auth_context()
	if not ctx["is_admin"]:
		frappe.throw("Admin access required", frappe.PermissionError)

	return stock_metrics_service.get_qr_stock_summary(batch=batch)


@frappe.whitelist()
def get_registered_items_report(
	status: str = None,
	category: str = None,
	batch: str = None,
	limit: int = 100,
) -> list:
	"""
	Get registered items report with filters.

	Admin sees all. Owners see only their own.

	Args:
	    status: Filter by item status (optional)
	    category: Filter by item category (optional)
	    batch: Filter by QR batch (optional)
	    limit: Maximum rows (default 100)

	Returns:
	    List of registered item rows with enrichment
	"""
	ctx = _get_auth_context()
	owner_profile = None if ctx["is_admin"] else ctx["owner_profile"]

	return stock_metrics_service.get_registered_items_report(
		owner_profile=owner_profile,
		status=status,
		category=category,
		batch=batch,
		limit=limit,
	)


# ==============================================================================
# REPORT FILTER METADATA API
# ==============================================================================


@frappe.whitelist()
def get_report_filter_metadata(doctype: str = None) -> dict:
	"""
	Get available filter values for report dropdowns.

	Admin-only endpoint.

	Args:
	    doctype: DocType to get filters for (optional)

	Returns:
	    Dict with filter options for various doctypes
	"""
	ctx = _get_auth_context()
	if not ctx["is_admin"]:
		frappe.throw("Admin access required", frappe.PermissionError)

	metadata: dict = {}

	# QR Batch options
	metadata["qr_batches"] = frappe.get_list(
		"QR Batch",
		fields=["name", "batch_name", "status"],
		order_by="creation desc",
		limit=50,
	)

	# Item Category options
	metadata["item_categories"] = frappe.get_list(
		"Item Category",
		fields=["name", "category_name", "icon"],
		filters={"is_active": 1},
		order_by="category_name asc",
	)

	# QR Tag status options
	metadata["qr_tag_statuses"] = [
		"Generated",
		"Printed",
		"In Stock",
		"Assigned",
		"Activated",
		"Suspended",
		"Retired",
	]

	# Item status options
	metadata["item_statuses"] = ["Draft", "Active", "Lost", "Recovered", "Archived"]

	# Recovery Case status options
	metadata["case_statuses"] = [
		"Open",
		"Owner Responded",
		"Return Planned",
		"Recovered",
		"Closed",
		"Invalid",
		"Spam",
	]

	# Scan status options
	metadata["scan_statuses"] = ["Valid", "Invalid", "Unavailable", "Recovery Initiated"]

	# Notification channel options
	metadata["notification_channels"] = ["In App", "Email", "System"]

	# Notification status options
	metadata["notification_statuses"] = ["Queued", "Sent", "Failed", "Skipped"]

	# Owner profiles (for admin filtering)
	metadata["owner_profiles"] = frappe.get_list(
		"Owner Profile",
		fields=["name", "display_name", "user"],
		order_by="display_name asc",
		limit=50,
	)

	return metadata
