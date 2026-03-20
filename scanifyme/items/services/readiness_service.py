"""
Readiness Service - Computes item recovery readiness scores.

Provides per-item and per-owner recovery readiness assessments
to guide owners toward better item protection setup.
"""

import frappe
from typing import Dict, Any, List, Optional


def get_item_recovery_readiness(item_id: str, owner_profile: str) -> Dict[str, Any]:
	"""
	Compute recovery readiness for a single registered item.

	Args:
	    item_id: Registered Item document name.
	    owner_profile: Owner Profile document name.

	Returns:
	    Dict containing:
	    - item: str (item name)
	    - item_name: str
	    - is_ready: bool
	    - readiness_percent: float (0-100)
	    - checks: list of per-factor dicts with check_key, label, passed, message
	    - missing: list of missing factor keys
	    - next_action: dict with action details or None
	"""
	# Validate item exists and belongs to owner
	item_data = frappe.db.get_value(
		"Registered Item",
		{"name": item_id, "owner_profile": owner_profile},
		["name", "item_name", "qr_code_tag", "recovery_note"],
		as_dict=True,
	)

	if not item_data:
		return {
			"item": item_id,
			"item_name": "",
			"is_ready": False,
			"readiness_percent": 0.0,
			"checks": [],
			"missing": [],
			"next_action": None,
			"error": "Item not found or access denied.",
		}

	# --- Factor 1: Has QR tag assigned ---
	has_qr_tag = bool(item_data.qr_code_tag)

	# --- Factor 2: QR is activated ---
	qr_is_activated = False
	if item_data.qr_code_tag:
		qr_status = frappe.db.get_value("QR Code Tag", item_data.qr_code_tag, "status", cache=True)
		qr_is_activated = qr_status == "Activated"

	# --- Factor 3: Has recovery note ---
	recovery_note_val = item_data.recovery_note or ""
	has_recovery_note = bool(recovery_note_val.strip())

	# --- Factor 4: Owner has valid phone ---
	owner_phone = frappe.db.get_value("Owner Profile", owner_profile, "phone", cache=True)
	has_valid_phone = bool(owner_phone and owner_phone.strip())

	# --- Factor 5: Notifications enabled ---
	notif_pref = frappe.db.get_value(
		"Notification Preference",
		{"owner_profile": owner_profile},
		["enable_in_app_notifications", "enable_email_notifications"],
		as_dict=True,
	)
	has_notification_enabled = bool(
		notif_pref
		and (notif_pref.get("enable_in_app_notifications") or notif_pref.get("enable_email_notifications"))
	)

	# Build checks list
	checks = [
		{
			"check_key": "has_qr_tag",
			"label": "QR Code Assigned",
			"passed": has_qr_tag,
			"message": "A QR code is linked to this item."
			if has_qr_tag
			else "Link a QR code tag to this item.",
		},
		{
			"check_key": "qr_is_activated",
			"label": "QR Code Activated",
			"passed": qr_is_activated,
			"message": "The QR code is active and scannable."
			if qr_is_activated
			else "The QR code needs to be activated first.",
		},
		{
			"check_key": "has_recovery_note",
			"label": "Recovery Note Added",
			"passed": has_recovery_note,
			"message": "A recovery note helps finders return the item."
			if has_recovery_note
			else "Add instructions to help finders contact you.",
		},
		{
			"check_key": "has_valid_phone",
			"label": "Phone Number Set",
			"passed": has_valid_phone,
			"message": "Your phone number is on file."
			if has_valid_phone
			else "Add your phone number to your profile.",
		},
		{
			"check_key": "has_notification_enabled",
			"label": "Notifications Enabled",
			"passed": has_notification_enabled,
			"message": "You'll receive alerts about your item."
			if has_notification_enabled
			else "Enable notifications to stay updated.",
		},
	]

	# Weighted score (max 3.4 points)
	weights = {
		"has_qr_tag": 1.0,
		"qr_is_activated": 0.8,
		"has_recovery_note": 0.7,
		"has_valid_phone": 0.5,
		"has_notification_enabled": 0.4,
	}
	score = 0.0
	for check in checks:
		if check["passed"]:
			score += weights.get(check["check_key"], 0.0)

	readiness_percent = round(min(100.0, (score / 3.4) * 100), 1)
	is_ready = readiness_percent >= 80.0

	missing = [c["check_key"] for c in checks if not c["passed"]]

	# Determine next action (first missing factor)
	next_action_map = {
		"has_qr_tag": {
			"action_key": "has_qr_tag",
			"title": "Assign a QR code",
			"description": "Link a QR code tag to start protecting your item.",
			"route": "/frontend/activate-qr",
		},
		"qr_is_activated": {
			"action_key": "qr_is_activated",
			"title": "Activate your QR code",
			"description": "Scan the QR code to activate it.",
			"route": "/frontend/activate-qr",
		},
		"has_recovery_note": {
			"action_key": "has_recovery_note",
			"title": "Add a recovery note",
			"description": "Help finders return your item by adding instructions.",
			"route": f"/frontend/items/{item_id}",
		},
		"has_valid_phone": {
			"action_key": "has_valid_phone",
			"title": "Set your phone number",
			"description": "Add a phone number so finders can contact you.",
			"route": "/frontend/settings/profile",
		},
		"has_notification_enabled": {
			"action_key": "has_notification_enabled",
			"title": "Enable notifications",
			"description": "Turn on notifications to receive alerts.",
			"route": "/frontend/settings/notifications",
		},
	}

	next_action = next_action_map.get(missing[0]) if missing else None

	return {
		"item": item_id,
		"item_name": item_data.item_name or "",
		"is_ready": is_ready,
		"readiness_percent": readiness_percent,
		"checks": checks,
		"missing": missing,
		"next_action": next_action,
	}


def get_owner_items_readiness(owner_profile: str) -> Dict[str, Any]:
	"""
	Compute aggregate recovery readiness across all items for an owner.

	Args:
	    owner_profile: Owner Profile document name.

	Returns:
	    Dict containing:
	    - total_items: int
	    - high_readiness_count: int
	    - medium_readiness_count: int
	    - low_readiness_count: int
	    - avg_readiness_score: float
	    - coverage_percent: float (% with QR tags)
	    - full_recovery_ready_count: int
	    - overall_readiness_level: str ("high"/"medium"/"low")
	    - item_breakdown: list of per-item readiness dicts (max 20)
	"""
	# Get all registered items for owner
	items = frappe.get_all(
		"Registered Item",
		filters={"owner_profile": owner_profile},
		fields=["name", "item_name", "qr_code_tag", "recovery_note"],
		limit=100,
	)

	total_items = len(items)
	if total_items == 0:
		return {
			"total_items": 0,
			"high_readiness_count": 0,
			"medium_readiness_count": 0,
			"low_readiness_count": 0,
			"avg_readiness_score": 0.0,
			"coverage_percent": 0.0,
			"full_recovery_ready_count": 0,
			"overall_readiness_level": "low",
			"item_breakdown": [],
		}

	item_readiness_list = []
	high_count = 0
	medium_count = 0
	low_count = 0
	total_score = 0.0
	coverage = 0

	for item in items:
		readiness = get_item_recovery_readiness(item.name, owner_profile)
		item_readiness_list.append(readiness)
		total_score += readiness["readiness_percent"]
		coverage += 1 if readiness["checks"][0]["passed"] else 0

		level = "high"
		pct = readiness["readiness_percent"]
		if pct < 50:
			level = "low"
		elif pct < 80:
			level = "medium"

		if level == "high":
			high_count += 1
		elif level == "medium":
			medium_count += 1
		else:
			low_count += 1

	avg_score = round(total_score / total_items, 1)
	coverage_percent = round((coverage / total_items) * 100, 1)

	# Overall level based on avg score
	if avg_score >= 80:
		overall_level = "high"
	elif avg_score >= 50:
		overall_level = "medium"
	else:
		overall_level = "low"

	full_ready = high_count

	# Limit breakdown to 20 items for performance
	item_breakdown = item_readiness_list[:20]

	return {
		"total_items": total_items,
		"high_readiness_count": high_count,
		"medium_readiness_count": medium_count,
		"low_readiness_count": low_count,
		"avg_readiness_score": avg_score,
		"coverage_percent": coverage_percent,
		"full_recovery_ready_count": full_ready,
		"overall_readiness_level": overall_level,
		"item_breakdown": item_breakdown,
	}
