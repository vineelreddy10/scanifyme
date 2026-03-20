"""
Onboarding Service - Service layer for owner onboarding state management.

This module provides business logic for:
- Deriving onboarding state from real system data
- Persisting onboarding state to DocType
- Providing next action CTAs for owners
- Admin reporting on onboarding status

NAMING RULES (to prevent recursion bugs):
- Service functions use compute_*, persist_*, build_* prefixes
- Never reuse the same name as the API layer function they serve
- Internal helpers use _ prefix
"""

import frappe
from frappe.utils import now_datetime
from typing import Optional, Dict, Any, List


def compute_onboarding_state(owner_profile: str) -> Dict[str, Any]:
	"""
	Derive onboarding state from real system data.

	This is a READ/derived function - it computes state based on actual
	database records, not persisted state.

	Args:
	    owner_profile: Owner Profile name, or "Administrator" for admin users

	Returns:
	    Dict with onboarding state:
	    - account_created: bool
	    - profile_completed: bool
	    - qr_activated: bool
	    - item_registered: bool
	    - recovery_note_added: bool
	    - notifications_configured: bool
	    - reward_reviewed: bool
	    - onboarding_completed: bool
	    - completion_percent: float (0-100)
	"""
	# Admin users bypass onboarding
	if owner_profile == "Administrator":
		return {
			"account_created": True,
			"profile_completed": True,
			"qr_activated": True,
			"item_registered": True,
			"recovery_note_added": True,
			"notifications_configured": True,
			"reward_reviewed": True,
			"onboarding_completed": True,
			"completion_percent": 100.0,
		}

	# Get owner profile document
	try:
		profile = frappe.get_doc("Owner Profile", owner_profile)
	except frappe.DoesNotExistError:
		return _empty_onboarding_state()

	# 1. Account Created - user exists
	account_created = bool(profile.user and frappe.db.exists("User", profile.user))

	# 2. Profile Completed - has display_name and phone
	profile_completed = bool(profile.display_name and profile.phone)

	# 3. QR Activated - owner has registered items with QR tags in "Activated" status
	# Get registered items that have a QR code tag assigned
	registered_items = frappe.get_all(
		"Registered Item",
		filters={
			"owner_profile": owner_profile,
			"qr_code_tag": ["is", "set"],
		},
		pluck="qr_code_tag",
		limit=100,
	)
	if registered_items:
		qr_activated = frappe.db.exists("QR Code Tag", {"name": registered_items[0], "status": "Activated"})
		if not qr_activated and len(registered_items) > 1:
			qr_activated = any(
				frappe.db.exists("QR Code Tag", {"name": tag, "status": "Activated"})
				for tag in registered_items[1:]
			)
	else:
		qr_activated = False

	# 4. Item Registered - owner has Registered Items
	item_count = frappe.db.count(
		"Registered Item",
		{"owner_profile": owner_profile},
	)
	item_registered = item_count > 0

	# 5. Recovery Note Added - owner has items with recovery_note set
	recovery_note_count = frappe.db.count(
		"Registered Item",
		{
			"owner_profile": owner_profile,
			"recovery_note": ["is", "set"],
		},
	)
	recovery_note_added = recovery_note_count > 0

	# 6. Notifications Configured - owner has Notification Preference enabled
	notification_pref = frappe.db.get_value(
		"Notification Preference",
		{"owner_profile": owner_profile, "enable_in_app_notifications": 1},
		"name",
	)
	notifications_configured = bool(notification_pref)

	# 7. Reward Reviewed - owner has items (simplified: any registered items)
	reward_reviewed = item_count > 0

	# Calculate completion
	steps = [
		account_created,
		profile_completed,
		qr_activated,
		item_registered,
		recovery_note_added,
		notifications_configured,
		reward_reviewed,
	]

	completed_count = sum(1 for step in steps if step)
	total_count = len(steps)

	# Safe float calculation with bounds
	calculated_percent = (completed_count / total_count * 100) if total_count > 0 else 0.0
	completion_percent = max(0.0, min(100.0, calculated_percent))

	# Onboarding completed if >= 75%
	onboarding_completed = completion_percent >= 75.0

	return {
		"account_created": account_created,
		"profile_completed": profile_completed,
		"qr_activated": qr_activated,
		"item_registered": item_registered,
		"recovery_note_added": recovery_note_added,
		"notifications_configured": notifications_configured,
		"reward_reviewed": reward_reviewed,
		"onboarding_completed": onboarding_completed,
		"completion_percent": completion_percent,
	}


def persist_onboarding_state(owner_profile: str) -> Dict[str, Any]:
	"""
	Persist onboarding state to DocType (create or update).

	This is a WRITE/persist function that updates the database.

	Args:
	    owner_profile: Owner Profile name, or "Administrator" for admin users

	Returns:
	    Dict with:
	    - success: bool
	    - message: str
	    - state: dict of the persisted state
	"""
	# Admin users — no DocType needed
	if owner_profile == "Administrator":
		state = compute_onboarding_state(owner_profile)
		return {
			"success": True,
			"message": "Admin user — state not persisted",
			"state": state,
		}

	# Check if owner profile actually exists before trying to persist
	if not frappe.db.exists("Owner Profile", owner_profile):
		frappe.throw(
			f"Owner Profile '{owner_profile}' does not exist.",
			frappe.DoesNotExistError,
		)

	# Get derived state from real data
	state = compute_onboarding_state(owner_profile)

	# Check if doc exists
	existing = frappe.db.exists("Owner Onboarding State", owner_profile)

	if existing:
		# Update existing doc
		doc = frappe.get_doc("Owner Onboarding State", owner_profile)
		doc.account_created = 1 if state["account_created"] else 0
		doc.profile_completed = 1 if state["profile_completed"] else 0
		doc.qr_activated = 1 if state["qr_activated"] else 0
		doc.item_registered = 1 if state["item_registered"] else 0
		doc.recovery_note_added = 1 if state["recovery_note_added"] else 0
		doc.notifications_configured = 1 if state["notifications_configured"] else 0
		doc.reward_reviewed = 1 if state["reward_reviewed"] else 0
		doc.onboarding_completed = 1 if state["onboarding_completed"] else 0
		doc.completion_percent = state["completion_percent"]
		doc.last_updated_on = now_datetime()
		doc.save(ignore_permissions=True)
		message = "Onboarding state updated"
	else:
		# Create new doc
		doc = frappe.get_doc(
			{
				"doctype": "Owner Onboarding State",
				"owner_profile": owner_profile,
				"account_created": 1 if state["account_created"] else 0,
				"profile_completed": 1 if state["profile_completed"] else 0,
				"qr_activated": 1 if state["qr_activated"] else 0,
				"item_registered": 1 if state["item_registered"] else 0,
				"recovery_note_added": 1 if state["recovery_note_added"] else 0,
				"notifications_configured": 1 if state["notifications_configured"] else 0,
				"reward_reviewed": 1 if state["reward_reviewed"] else 0,
				"onboarding_completed": 1 if state["onboarding_completed"] else 0,
				"completion_percent": state["completion_percent"],
				"last_updated_on": now_datetime(),
			}
		)
		doc.insert(ignore_permissions=True)
		message = "Onboarding state created"

	frappe.db.commit()

	return {
		"success": True,
		"message": message,
		"state": state,
	}


def compute_owner_next_actions(owner_profile: str) -> List[Dict[str, Any]]:
	"""
	Build next CTA steps for owner onboarding.

	Returns incomplete onboarding steps with actions to complete them.

	Args:
	    owner_profile: Owner Profile name, or "Administrator" for admin users

	Returns:
	    List of action dicts:
	    - action_key: str (step identifier)
	    - title: str (short title)
	    - description: str (helpful description)
	    - route: str (frontend route)
	    - priority: int (lower = more important)
	"""
	# Admin users have no actions needed
	if owner_profile == "Administrator":
		return []

	# Get current state
	state = compute_onboarding_state(owner_profile)

	actions = []

	# Priority order (lower number = higher priority)
	priority_map = {
		"qr_activated": 1,
		"item_registered": 2,
		"recovery_note_added": 3,
		"notifications_configured": 4,
		"reward_reviewed": 5,
		"profile_completed": 6,
	}

	# Check each step and add action if incomplete
	if not state["qr_activated"]:
		actions.append(
			{
				"action_key": "qr_activated",
				"title": "Activate your first QR code",
				"description": "Get a QR code tag and activate it to start registering items",
				"route": "/frontend/activate-qr",
				"priority": priority_map.get("qr_activated", 99),
			}
		)

	if not state["item_registered"]:
		actions.append(
			{
				"action_key": "item_registered",
				"title": "Register your first item",
				"description": "Link an item to your QR code to start protecting it",
				"route": "/frontend/activate-qr",
				"priority": priority_map.get("item_registered", 99),
			}
		)

	if not state["recovery_note_added"]:
		# Find an item that needs recovery note
		items_without_note = frappe.get_list(
			"Registered Item",
			filters={
				"owner_profile": owner_profile,
				"recovery_note": ["is", "not set"],
			},
			fields=["name"],
			limit=1,
		)
		item_id = items_without_note[0].name if items_without_note else None
		route = f"/frontend/items/{item_id}" if item_id else "/frontend/items"

		actions.append(
			{
				"action_key": "recovery_note_added",
				"title": "Add a recovery note",
				"description": "Help finders return your item by adding instructions",
				"route": route,
				"priority": priority_map.get("recovery_note_added", 99),
			}
		)

	if not state["notifications_configured"]:
		actions.append(
			{
				"action_key": "notifications_configured",
				"title": "Configure notifications",
				"description": "Set up how you want to be notified about your items",
				"route": "/frontend/settings/notifications",
				"priority": priority_map.get("notifications_configured", 99),
			}
		)

	if not state["reward_reviewed"]:
		# Find an item to review rewards
		items = frappe.get_list(
			"Registered Item",
			filters={"owner_profile": owner_profile},
			fields=["name"],
			limit=1,
		)
		item_id = items[0].name if items else None
		route = f"/frontend/items/{item_id}" if item_id else "/frontend/items"

		actions.append(
			{
				"action_key": "reward_reviewed",
				"title": "Review reward settings",
				"description": "Consider offering a reward to encourage item returns",
				"route": route,
				"priority": priority_map.get("reward_reviewed", 99),
			}
		)

	if not state["profile_completed"]:
		actions.append(
			{
				"action_key": "profile_completed",
				"title": "Complete your profile",
				"description": "Add your phone number so finders can contact you",
				"route": "/frontend/settings/profile",
				"priority": priority_map.get("profile_completed", 99),
			}
		)

	# Sort by priority
	actions.sort(key=lambda x: x["priority"])

	return actions


def get_incomplete_onboarding_summary(filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
	"""
	Admin-only: Get summary of owners with incomplete onboarding.

	Args:
	    filters: Optional dict with filter criteria:
	        - min_percent: Only owners with completion <= this value
	        - max_percent: Only owners with completion >= this value
	        - onboarding_completed: Filter by completed status

	Returns:
	    List of dicts with:
	    - owner_profile: Owner Profile name
	    - owner_display_name: Display name
	    - completion_percent: float
	    - onboarding_completed: bool
	    - missing_steps: list of incomplete step keys
	"""
	# Get all onboarding state records
	fields = [
		"name as owner_profile",
		"completion_percent",
		"onboarding_completed",
		"account_created",
		"profile_completed",
		"qr_activated",
		"item_registered",
		"recovery_note_added",
		"notifications_configured",
		"reward_reviewed",
	]

	records = frappe.get_list(
		"Owner Onboarding State",
		filters={},
		fields=fields,
		ignore_permissions=True,
	)

	results = []

	for record in records:
		# Apply filters
		if filters:
			if filters.get("min_percent") and record.completion_percent > filters["min_percent"]:
				continue
			if filters.get("max_percent") and record.completion_percent < filters["max_percent"]:
				continue
			if filters.get("onboarding_completed") is not None:
				if record.onboarding_completed != filters["onboarding_completed"]:
					continue

		# Get owner display name
		owner_display_name = frappe.db.get_value(
			"Owner Profile",
			record.owner_profile,
			"display_name",
		)

		# Build missing steps list
		missing_steps = []
		step_fields = [
			"account_created",
			"profile_completed",
			"qr_activated",
			"item_registered",
			"recovery_note_added",
			"notifications_configured",
			"reward_reviewed",
		]

		for step in step_fields:
			if not record.get(step):
				missing_steps.append(step)

		results.append(
			{
				"owner_profile": record.owner_profile,
				"owner_display_name": owner_display_name,
				"completion_percent": record.completion_percent,
				"onboarding_completed": bool(record.onboarding_completed),
				"missing_steps": missing_steps,
			}
		)

	# Sort by completion percent (lowest first)
	results.sort(key=lambda x: x["completion_percent"])

	return results


def _empty_onboarding_state() -> Dict[str, Any]:
	"""
	Return empty onboarding state for invalid/missing profiles.

	Returns:
	    Dict with all False values and 0% completion
	"""
	return {
		"account_created": False,
		"profile_completed": False,
		"qr_activated": False,
		"item_registered": False,
		"recovery_note_added": False,
		"notifications_configured": False,
		"reward_reviewed": False,
		"onboarding_completed": False,
		"completion_percent": 0.0,
	}


def trigger_onboarding_recompute(owner_profile: str) -> None:
	"""
	Trigger a recompute of onboarding state.

	This is a convenience function that can be called after
	significant actions (item creation, profile update, etc.)
	to ensure onboarding state is fresh.

	Args:
	    owner_profile: Owner Profile name
	"""
	if owner_profile and owner_profile != "Administrator":
		persist_onboarding_state(owner_profile)
