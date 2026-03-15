# Copyright (c) 2024, ScanifyMe and contributors
import frappe


def has_app_permission():
	"""Check if user has access to ScanifyMe app.

	Returns:
	    bool: True if user has access
	"""
	return frappe.session.user != "Guest"


def get_user_role():
	"""Get current user's ScanifyMe role.

	Returns:
	    str: Role name or None
	"""
	user = frappe.session.user
	if user == "Guest":
		return None

	roles = frappe.get_roles(user)

	role_priority = {
		"ScanifyMe Admin": 4,
		"ScanifyMe Support": 3,
		"ScanifyMe Operations": 2,
		"ScanifyMe User": 1,
	}

	user_role = None
	max_priority = 0

	for role in roles:
		if role in role_priority and role_priority[role] > max_priority:
			user_role = role
			max_priority = role_priority[role]

	return user_role
