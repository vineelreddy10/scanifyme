"""
Admin Onboarding API - Admin-only endpoints for onboarding oversight.

All endpoints require System Manager or ScanifyMe Admin role.

RBAC:
- Only admin (System Manager or ScanifyMe Admin) can access these endpoints
- Operations/Support role is NOT granted access (business rule: only full admins)
- No owner_profile filtering — admin sees all owners
"""

import frappe
from typing import Optional, Dict, Any, List

from scanifyme.utils.permissions import has_admin_role
from scanifyme.items.services.readiness_service import get_owner_items_readiness


def _check_admin() -> None:
	"""Raise PermissionError if current user is not an admin."""
	if not has_admin_role():
		frappe.throw(
			"Permission denied. Admin role required.",
			frappe.PermissionError,
		)


@frappe.whitelist()
def get_onboarding_overview() -> Dict[str, Any]:
	"""
	Get a high-level overview of onboarding status across all owners.

	Returns:
	    Dict with total_owners, completed, in_progress, avg_completion_percent,
	    and a breakdown of owners by completion bucket.
	"""
	_check_admin()

	# Get all persisted onboarding state records
	records = frappe.get_all(
		"Owner Onboarding State",
		fields=[
			"name",
			"completion_percent",
			"onboarding_completed",
		],
		ignore_permissions=True,
	)

	total = len(records)
	if total == 0:
		return {
			"total_owners": 0,
			"completed": 0,
			"in_progress": 0,
			"avg_completion_percent": 0.0,
			"breakdown": {
				"not_started": 0,
				"getting_started": 0,
				"halfway": 0,
				"almost_done": 0,
			},
		}

	completed = sum(1 for r in records if r.onboarding_completed)
	in_progress = total - completed

	total_pct = sum(float(r.completion_percent or 0) for r in records)
	avg_pct = round(total_pct / total, 1)

	breakdown = {
		"not_started": sum(1 for r in records if (r.completion_percent or 0) == 0),
		"getting_started": sum(1 for r in records if 0 < (r.completion_percent or 0) <= 25),
		"halfway": sum(1 for r in records if 25 < (r.completion_percent or 0) <= 75),
		"almost_done": sum(1 for r in records if 75 < (r.completion_percent or 0) < 100),
	}

	return {
		"total_owners": total,
		"completed": completed,
		"in_progress": in_progress,
		"avg_completion_percent": avg_pct,
		"breakdown": breakdown,
	}


@frappe.whitelist()
def get_incomplete_onboarding_summary(
	min_completion: Optional[float] = None,
	max_completion: Optional[float] = None,
	limit: int = 50,
) -> List[Dict[str, Any]]:
	"""
	Get a summary of owners with incomplete onboarding, optionally filtered.

	Args:
	    min_completion: Only owners with completion <= this value (0-100).
	    max_completion: Only owners with completion >= this value (0-100).
	    limit: Maximum number of records to return (default 50).

	Returns:
	    List of dicts with owner_profile, completion_percent, missing_steps, etc.
	"""
	_check_admin()

	# Recompute onboarding state for each owner on the fly for accuracy
	# and sort by completion percent
	owner_profiles = frappe.get_all(
		"Owner Profile",
		pluck="name",
		ignore_permissions=True,
	)

	results = []
	for op in owner_profiles:
		from scanifyme.onboarding.services.onboarding_service import compute_onboarding_state

		state = compute_onboarding_state(op)
		if state.get("onboarding_completed"):
			continue

		# Apply filters
		pct = state.get("completion_percent", 0)
		if min_completion is not None and pct > min_completion:
			continue
		if max_completion is not None and pct < max_completion:
			continue

		missing = [
			k
			for k in [
				"account_created",
				"profile_completed",
				"qr_activated",
				"item_registered",
				"recovery_note_added",
				"notifications_configured",
				"reward_reviewed",
			]
			if not state.get(k)
		]

		owner_display_name = frappe.db.get_value("Owner Profile", op, "display_name", cache=True) or op

		results.append(
			{
				"owner_profile": op,
				"owner_display_name": owner_display_name,
				"completion_percent": pct,
				"onboarding_completed": bool(state.get("onboarding_completed")),
				"missing_steps": missing,
				"last_updated_on": None,
			}
		)

	# Sort by completion percent ascending
	results.sort(key=lambda x: x["completion_percent"])

	return results[:limit]
