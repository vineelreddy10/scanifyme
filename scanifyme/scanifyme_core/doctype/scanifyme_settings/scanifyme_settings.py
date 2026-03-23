# Copyright (c) 2024, ScanifyMe and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class ScanifyMeSettings(Document):
	"""Singleton pattern for ScanifyMe Settings.

	This ensures only one instance of settings exists.
	"""

	def validate(self):
		"""Validate settings before saving."""
		self.validate_limits()

	def validate_limits(self):
		"""Validate numeric limits."""
		if self.max_messages_per_hour < 1:
			frappe.throw("Max messages per hour must be at least 1")

		if self.max_scans_per_minute < 1:
			frappe.throw("Max scans per minute must be at least 1")


def get_settings() -> "ScanifyMeSettings":
	"""Get the singleton ScanifyMe Settings instance.

	Returns:
	    ScanifyMeSettings: The settings document

	Raises:
	    frappe.DoesNotExistError: If settings don't exist
	"""
	settings = frappe.get_single("ScanifyMe Settings")
	return settings


def get_settings_or_create() -> "ScanifyMeSettings":
	"""Get the singleton ScanifyMe Settings instance or create default.

	Returns:
	    ScanifyMeSettings: The settings document
	"""
	try:
		return get_settings()
	except frappe.DoesNotExistError:
		return create_default_settings()


def create_default_settings() -> "ScanifyMeSettings":
	"""Create default ScanifyMe Settings.

	Returns:
	    ScanifyMeSettings: The newly created settings document
	"""
	settings = frappe.get_doc(
		{
			"doctype": "ScanifyMe Settings",
			"site_name": "ScanifyMe",
			"default_privacy_level": "High",
			"allow_anonymous_messages": 1,
			"allow_location_sharing": 1,
			"default_reward_message": "Thank you for finding this item! Please contact the owner to arrange a return.",
			"max_messages_per_hour": 10,
			"max_scans_per_minute": 5,
		}
	)
	settings.insert(ignore_permissions=True)
	return settings


@frappe.whitelist()
def get_public_settings() -> dict:
	"""Get public settings that can be accessed by guests.

	Returns:
	    dict: Public settings (sanitized)
	"""
	try:
		settings = get_settings()
		return {
			"site_name": settings.site_name,
			"allow_anonymous_messages": settings.allow_anonymous_messages,
			"allow_location_sharing": settings.allow_location_sharing,
			"default_reward_message": settings.default_reward_message,
			"default_privacy_level": settings.default_privacy_level,
		}
	except frappe.DoesNotExistError:
		return {
			"site_name": "ScanifyMe",
			"allow_anonymous_messages": 1,
			"allow_location_sharing": 1,
			"default_reward_message": "Thank you for finding this item!",
			"default_privacy_level": "High",
		}


@frappe.whitelist()
def update_settings(**kwargs) -> "ScanifyMeSettings":
	"""Update ScanifyMe Settings.

	Args:
	    **kwargs: Fields to update

	Returns:
	    ScanifyMeSettings: The updated settings document
	"""
	frappe.only_for("System Manager", "ScanifyMe Admin")

	settings = get_settings()

	for key, value in kwargs.items():
		if hasattr(settings, key):
			setattr(settings, key, value)

	settings.save(ignore_permissions=True)
	return settings
