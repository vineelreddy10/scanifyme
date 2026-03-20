"""
Onboarding API - Owner-facing endpoints for onboarding state and recovery readiness.

All endpoints require authentication (owner-only).

NAMING RULES:
- API functions use the names exposed via @frappe.whitelist() (required by the route system)
- Service calls use compute_*, persist_* prefixes to avoid shadowing
- RBAC: owners can only access their own data; admin bypasses owner checks
"""

import frappe
from typing import Optional, Dict, Any, List

from scanifyme.utils.permissions import get_owner_profile_for_user, has_admin_role
from scanifyme.onboarding.services.onboarding_service import (
	compute_onboarding_state,
	persist_onboarding_state,
	compute_owner_next_actions,
)
from scanifyme.items.services.readiness_service import get_item_recovery_readiness


@frappe.whitelist()
def get_owner_onboarding_state(user: Optional[str] = None) -> Dict[str, Any]:
	"""
	Get the onboarding state for the current owner.

	Args:
	    user: Optional user email. Defaults to current session user.

	Returns:
	    Dict with onboarding step completion flags and completion percent.
	"""
	owner_profile = get_owner_profile_for_user(user or frappe.session.user)
	if not owner_profile:
		frappe.throw("Owner profile not found.", frappe.PermissionError)
	return compute_onboarding_state(owner_profile)


@frappe.whitelist()
def recompute_onboarding_state(user: Optional[str] = None) -> Dict[str, Any]:
	"""
	Recompute and persist the onboarding state for the current owner.

	Args:
	    user: Optional user email. Defaults to current session user.

	Returns:
	    Dict with success status, message, and the computed state.
	"""
	owner_profile = get_owner_profile_for_user(user or frappe.session.user)
	if not owner_profile:
		frappe.throw("Owner profile not found.", frappe.PermissionError)
	return persist_onboarding_state(owner_profile)


@frappe.whitelist()
def get_owner_next_actions(user: Optional[str] = None) -> List[Dict[str, Any]]:
	"""
	Get the next action CTAs for the current owner's onboarding.

	Args:
	    user: Optional user email. Defaults to current session user.

	Returns:
	    List of action dicts with action_key, title, description, route, priority.
	"""
	owner_profile = get_owner_profile_for_user(user or frappe.session.user)
	if not owner_profile:
		frappe.throw("Owner profile not found.", frappe.PermissionError)
	return compute_owner_next_actions(owner_profile)


@frappe.whitelist()
def get_item_recovery_readiness(item_id: str, user: Optional[str] = None) -> Dict[str, Any]:
	"""
	Get the recovery readiness score for a specific item.

	Args:
	    item_id: The Registered Item name.
	    user: Optional user email. Defaults to current session user.

	Returns:
	    Dict with readiness checks, score, level, missing factors, and next action.
	"""
	owner_profile = get_owner_profile_for_user(user or frappe.session.user)
	if not owner_profile:
		frappe.throw("Owner profile not found.", frappe.PermissionError)
	return get_item_recovery_readiness(item_id, owner_profile)
