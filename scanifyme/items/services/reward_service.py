"""
Reward Service - Business logic for reward management.

This module provides functions for:
- Validating reward configuration
- Applying reward settings to items
- Managing reward status on recovery cases
- Creating reward timeline events
"""

import frappe
from frappe.utils import now_datetime
from typing import Optional, Dict, Any, List
from scanifyme.utils.permissions import is_scanifyme_admin


# Valid reward visibility options
REWARD_VISIBILITY_OPTIONS = ["Public", "Private Mention On Contact", "Disabled"]

# Valid reward status options for recovery cases
REWARD_STATUS_OPTIONS = [
	"Not Applicable",
	"Offered",
	"Mentioned To Finder",
	"Return Completed",
	"Closed Without Reward",
	"Cancelled",
]


def validate_reward_configuration(
	reward_enabled: bool,
	reward_amount_text: Optional[str] = None,
	reward_visibility: Optional[str] = None,
) -> Dict[str, Any]:
	"""
	Validate reward configuration settings.

	Args:
	    reward_enabled: Whether reward is enabled
	    reward_amount_text: Display text for reward amount
	    reward_visibility: Visibility setting

	Returns:
	    Dict with validation result

	Raises:
	    frappe.ValidationError: If validation fails
	"""
	errors = []

	if reward_enabled:
		if not reward_amount_text or not reward_amount_text.strip():
			errors.append("Reward amount is required when reward is enabled")

		if reward_visibility not in REWARD_VISIBILITY_OPTIONS:
			errors.append(
				f"Invalid reward visibility. Must be one of: {', '.join(REWARD_VISIBILITY_OPTIONS)}"
			)

	if errors:
		frappe.throw("\n".join(errors))

	return {"valid": True, "message": "Reward configuration is valid"}


def apply_reward_to_item(
	item: str,
	reward_enabled: bool,
	reward_amount_text: Optional[str] = None,
	reward_note: Optional[str] = None,
	reward_terms: Optional[str] = None,
	reward_visibility: str = "Public",
	user: Optional[str] = None,
) -> Dict[str, Any]:
	"""
	Apply reward settings to a registered item.

	Args:
	    item: Registered Item name
	    reward_enabled: Whether reward is enabled
	    reward_amount_text: Display text for reward amount
	    reward_note: Note about the reward
	    reward_terms: Terms and conditions
	    reward_visibility: Visibility setting
	    user: User making the change

	Returns:
	    Dict with success status

	Raises:
	    frappe.ValidationError: If validation fails or permission denied
	"""
	if not user:
		user = frappe.session.user

	# Get item
	try:
		item_doc = frappe.get_doc("Registered Item", item)
	except frappe.DoesNotExistError:
		frappe.throw("Item not found")

	# Check permission - admin can update any item
	is_admin = is_scanifyme_admin(user)

	if not is_admin:
		# Get owner profile
		owner_profile = frappe.db.get_value("Owner Profile", {"user": user}, "name")
		if not owner_profile or item_doc.owner_profile != owner_profile:
			frappe.throw("Permission denied. You can only update your own items.")

	# Validate configuration if enabling reward
	if reward_enabled:
		validate_reward_configuration(
			reward_enabled=reward_enabled,
			reward_amount_text=reward_amount_text,
			reward_visibility=reward_visibility,
		)

	# Get old reward state for timeline
	old_reward_enabled = item_doc.reward_enabled
	old_reward_status = (
		"Disabled"
		if not old_reward_enabled
		else (item_doc.reward_visibility if item_doc.reward_visibility else "Public")
	)

	# Update item
	item_doc.reward_enabled = 1 if reward_enabled else 0
	item_doc.reward_amount_text = reward_amount_text if reward_enabled else None
	item_doc.reward_note = reward_note if reward_enabled else None
	item_doc.reward_terms = reward_terms if reward_enabled else None
	item_doc.reward_visibility = reward_visibility if reward_enabled else None

	item_doc.save()

	# Create timeline event if reward was just enabled
	if reward_enabled and not old_reward_enabled:
		create_reward_timeline_event(
			recovery_case=None,
			event_type="Reward Enabled",
			event_label="Reward Enabled",
			actor_type="Owner" if not is_admin else "Admin",
			actor_reference=user,
			summary=f"Reward of {reward_amount_text or 'unspecified amount'} enabled for this item",
		)

	frappe.db.commit()

	return {
		"success": True,
		"message": f"Reward settings updated for item '{item_doc.item_name}'",
		"item": item,
		"reward_enabled": reward_enabled,
	}


def derive_case_reward_context(item: str, case: str, user: Optional[str] = None) -> Dict[str, Any]:
	"""
	Derive reward context from item when creating a recovery case.

	Args:
	    item: Registered Item name
	    case: Recovery Case name
	    user: User performing the action

	Returns:
	    Dict with reward context
	"""
	if not user:
		user = frappe.session.user

	# Get item
	try:
		item_doc = frappe.get_doc("Registered Item", item)
	except frappe.DoesNotExistError:
		return {"reward_offered": 0}

	# Get recovery case
	try:
		case_doc = frappe.get_doc("Recovery Case", case)
	except frappe.DoesNotExistError:
		return {"reward_offered": 0}

	# Copy reward context if item has reward enabled
	if item_doc.reward_enabled:
		case_doc.reward_offered = 1
		case_doc.reward_display_text = item_doc.reward_amount_text
		case_doc.reward_status = "Offered"
		case_doc.reward_last_updated_on = now_datetime()
		case_doc.save()

		# Create timeline event
		create_reward_timeline_event(
			recovery_case=case,
			event_type="Reward Enabled",
			event_label="Reward Offered",
			actor_type="System",
			actor_reference="System",
			summary=f"Reward of {item_doc.reward_amount_text or 'unspecified'} derived from item",
		)

		frappe.db.commit()

		return {
			"reward_offered": 1,
			"reward_display_text": item_doc.reward_amount_text,
			"reward_status": "Offered",
		}

	return {"reward_offered": 0}


def update_reward_status(
	case: str,
	reward_status: str,
	reward_internal_note: Optional[str] = None,
	user: Optional[str] = None,
) -> Dict[str, Any]:
	"""
	Update the reward status on a recovery case.

	Args:
	    case: Recovery Case name
	    reward_status: New reward status
	    reward_internal_note: Optional internal note
	    user: User making the change

	Returns:
	    Dict with success status

	Raises:
	    frappe.ValidationError: If validation fails or permission denied
	"""
	if not user:
		user = frappe.session.user

	# Validate reward status
	if reward_status not in REWARD_STATUS_OPTIONS:
		frappe.throw(f"Invalid reward status. Must be one of: {', '.join(REWARD_STATUS_OPTIONS)}")

	# Get case
	try:
		case_doc = frappe.get_doc("Recovery Case", case)
	except frappe.DoesNotExistError:
		frappe.throw("Recovery case not found")

	# Check permission - admin can update any case
	is_admin = is_scanifyme_admin(user)

	if not is_admin:
		# Get owner profile
		owner_profile = frappe.db.get_value("Owner Profile", {"user": user}, "name")
		if not owner_profile or case_doc.owner_profile != owner_profile:
			frappe.throw("Permission denied. You can only update your own recovery cases.")

	# Get old status for timeline
	old_status = case_doc.reward_status

	# Update case
	case_doc.reward_status = reward_status
	case_doc.reward_internal_note = reward_internal_note
	case_doc.reward_last_updated_on = now_datetime()
	case_doc.save()

	# Create timeline event
	create_reward_timeline_event(
		recovery_case=case,
		event_type="Reward Status Updated",
		event_label=f"Reward Status: {reward_status}",
		actor_type="Owner" if not is_admin else "Admin",
		actor_reference=user,
		summary=f"Reward status changed from '{old_status or 'Not Applicable'}' to '{reward_status}'"
		+ (f". Note: {reward_internal_note}" if reward_internal_note else ""),
	)

	frappe.db.commit()

	return {
		"success": True,
		"message": f"Reward status updated to '{reward_status}'",
		"case": case,
		"old_status": old_status,
		"new_status": reward_status,
	}


def get_public_reward_context(item: str) -> Dict[str, Any]:
	"""
	Get public-safe reward context for an item.

	This function returns only the reward information that should be
	visible to the public based on visibility settings.

	Args:
	    item: Registered Item name

	Returns:
	    Dict with public reward context
	"""
	# Get item
	try:
		item_doc = frappe.get_doc("Registered Item", item)
	except frappe.DoesNotExistError:
		return {"has_reward": False}

	# Check if reward is enabled
	if not item_doc.reward_enabled:
		return {"has_reward": False}

	# Check visibility
	visibility = item_doc.reward_visibility or "Public"

	if visibility == "Disabled":
		return {"has_reward": False}

	if visibility == "Public":
		# Return full public reward info
		return {
			"has_reward": True,
			"reward_amount_text": item_doc.reward_amount_text,
			"reward_note": item_doc.reward_note,
			"reward_terms": item_doc.reward_terms,
			"visibility": "Public",
		}

	if visibility == "Private Mention On Contact":
		# Only show that reward exists, not details
		return {
			"has_reward": True,
			"reward_amount_text": None,
			"reward_note": None,
			"reward_terms": None,
			"visibility": "Private Mention On Contact",
			"reward_available": True,
		}

	return {"has_reward": False}


def create_reward_timeline_event(
	recovery_case: Optional[str],
	event_type: str,
	event_label: str,
	actor_type: str,
	actor_reference: str,
	summary: str,
) -> str:
	"""
	Create a reward-related timeline event.

	Args:
	    recovery_case: Recovery Case name (optional)
	    event_type: Type of event
	    event_label: Label for the event
	    actor_type: Type of actor (Finder, Owner, System, Admin)
	    actor_reference: Reference to the actor
	    summary: Summary description

	Returns:
	    Timeline event name
	"""
	if not recovery_case:
		return None

	timeline_event = frappe.get_doc(
		{
			"doctype": "Recovery Timeline Event",
			"recovery_case": recovery_case,
			"event_type": event_type,
			"event_label": event_label,
			"actor_type": actor_type,
			"actor_reference": actor_reference,
			"event_time": now_datetime(),
			"summary": summary,
		}
	)

	timeline_event.insert(ignore_permissions=True)
	frappe.db.commit()

	return timeline_event.name


def get_item_reward_settings(item: str, user: Optional[str] = None) -> Dict[str, Any]:
	"""
	Get reward settings for an item.

	Args:
	    item: Registered Item name
	    user: User requesting the settings

	Returns:
	    Dict with reward settings
	"""
	if not user:
		user = frappe.session.user

	# Check if user is admin
	is_admin = is_scanifyme_admin(user)

	# Get item
	try:
		item_doc = frappe.get_doc("Registered Item", item)
	except frappe.DoesNotExistError:
		frappe.throw("Item not found")

	# Check permission
	if not is_admin:
		owner_profile = frappe.db.get_value("Owner Profile", {"user": user}, "name")
		if not owner_profile or item_doc.owner_profile != owner_profile:
			frappe.throw("Permission denied. You can only view your own items.")

	return {
		"item": item,
		"reward_enabled": bool(item_doc.reward_enabled),
		"reward_amount_text": item_doc.reward_amount_text,
		"reward_note": item_doc.reward_note,
		"reward_terms": item_doc.reward_terms,
		"reward_visibility": item_doc.reward_visibility,
	}


def get_case_reward_status(case: str, user: Optional[str] = None) -> Dict[str, Any]:
	"""
	Get reward status for a recovery case.

	Args:
	    case: Recovery Case name
	    user: User requesting the status

	Returns:
	    Dict with reward status
	"""
	if not user:
		user = frappe.session.user

	# Check if user is admin
	is_admin = is_scanifyme_admin(user)

	# Get case
	try:
		case_doc = frappe.get_doc("Recovery Case", case)
	except frappe.DoesNotExistError:
		frappe.throw("Recovery case not found")

	# Check permission
	if not is_admin:
		owner_profile = frappe.db.get_value("Owner Profile", {"user": user}, "name")
		if not owner_profile or case_doc.owner_profile != owner_profile:
			frappe.throw("Permission denied. You can only view your own recovery cases.")

	return {
		"case": case,
		"reward_offered": bool(case_doc.reward_offered),
		"reward_display_text": case_doc.reward_display_text,
		"reward_status": case_doc.reward_status,
		"reward_internal_note": case_doc.reward_internal_note,
		"reward_last_updated_on": case_doc.reward_last_updated_on,
	}
