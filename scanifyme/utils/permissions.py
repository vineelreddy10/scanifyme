"""
Permissions Helper Module - Centralized permission checking for ScanifyMe.

This module provides helper functions for checking user permissions
across the ScanifyMe application. It enforces the following rules:

1. Admin (Administrator, System Manager, ScanifyMe Admin) can access all
2. Owner users can access only their own records
3. Guest users can only access explicitly public APIs
4. Operations/Support follow intended business rules
"""

import frappe
from frappe.utils import cint
from typing import Optional, List, Dict, Any


def is_scanifyme_admin(user: Optional[str] = None) -> bool:
	"""
	Check if user is a ScanifyMe admin or system admin.

	Args:
	    user: User email. If None, uses current session user.

	Returns:
	    True if user is Administrator, System Manager, or has ScanifyMe Admin role
	"""
	if not user:
		user = frappe.session.user

	if user == "Guest" or not user:
		return False

	# Check for special admin users
	if user in ["Administrator", "admin"]:
		return True

	# Get user roles
	roles = frappe.get_roles(user)

	# Check for admin roles
	admin_roles = ["System Manager", "ScanifyMe Admin", "Admin"]
	return any(role in roles for role in admin_roles)


def is_system_admin(user: Optional[str] = None) -> bool:
	"""
	Check if user is a system-level administrator.

	Args:
	    user: User email. If None, uses current session user.

	Returns:
	    True if user is Administrator or has System Manager role
	"""
	if not user:
		user = frappe.session.user

	if user == "Guest" or not user:
		return False

	if user in ["Administrator", "admin"]:
		return True

	roles = frappe.get_roles(user)
	return "System Manager" in roles


def is_owner_user(user: Optional[str] = None) -> bool:
	"""
	Check if user has an owner profile.

	Args:
	    user: User email. If None, uses current session user.

	Returns:
	    True if user has an Owner Profile
	"""
	if not user:
		user = frappe.session.user

	if user == "Guest" or not user:
		return False

	return bool(frappe.db.get_value("Owner Profile", {"user": user}, "name"))


def get_owner_profile_for_user(user: Optional[str] = None) -> Optional[str]:
	"""
	Get the owner profile for the current user.

	This function returns:
	- None for Guest users
	- "Administrator" for admin users (special marker for admin access)
	- The Owner Profile name for regular owners

	Args:
	    user: User email. If None, uses current session user.

	Returns:
	    Owner Profile name, "Administrator", or None
	"""
	if not user:
		user = frappe.session.user

	if user == "Guest" or not user:
		return None

	# Check if user is admin - return special marker
	if is_scanifyme_admin(user):
		return "Administrator"

	# Get owner profile
	owner_profile = frappe.db.get_value(
		"Owner Profile",
		{"user": user},
		"name",
	)
	return owner_profile


def get_owner_profile_for_user_detailed(user: Optional[str] = None) -> Dict[str, Any]:
	"""
	Get detailed owner profile info including admin flag.

	Args:
	    user: User email. If None, uses current session user.

	Returns:
	    Dict with owner_profile, is_admin flags
	"""
	if not user:
		user = frappe.session.user

	result = {
		"user": user,
		"owner_profile": None,
		"is_scanifyme_admin": is_scanifyme_admin(user),
		"is_system_admin": is_system_admin(user),
	}

	if user == "Guest" or not user:
		return result

	if result["is_scanifyme_admin"]:
		result["owner_profile"] = "Administrator"
	else:
		result["owner_profile"] = frappe.db.get_value(
			"Owner Profile",
			{"user": user},
			"name",
		)

	return result


def can_access_owner_record(user: str, owner_profile: str) -> bool:
	"""
	Check if user can access a record belonging to an owner.

	Admin users can access all records.
	Non-admin users can only access their own records.

	Args:
	    user: User email trying to access the record
	    owner_profile: Owner Profile that owns the record

	Returns:
	    True if access is allowed
	"""
	if not user or user == "Guest":
		return False

	# Admin can access all
	if is_scanifyme_admin(user):
		return True

	# Get user's owner profile
	user_profile = get_owner_profile_for_user(user)

	# Owner can access their own records
	if user_profile == owner_profile:
		return True

	return False


def user_can_access_registered_item(user: str, item_name: str) -> bool:
	"""
	Check if user can access a specific registered item.

	Args:
	    user: User email trying to access the item
	    item_name: Registered Item name

	Returns:
	    True if access is allowed
	"""
	if not user or user == "Guest":
		return False

	# Admin can access all items
	if is_scanifyme_admin(user):
		return True

	# Get item's owner
	try:
		item_owner = frappe.db.get_value(
			"Registered Item",
			item_name,
			"owner_profile",
		)
	except Exception:
		return False

	if not item_owner:
		return False

	# Check if user owns the item
	user_profile = get_owner_profile_for_user(user)
	return user_profile == item_owner


def user_can_access_recovery_case(user: str, case_name: str) -> bool:
	"""
	Check if user can access a specific recovery case.

	Args:
	    user: User email trying to access the case
	    case_name: Recovery Case name

	Returns:
	    True if access is allowed
	"""
	if not user or user == "Guest":
		return False

	# Admin can access all cases
	if is_scanifyme_admin(user):
		return True

	# Get case owner
	try:
		case_owner = frappe.db.get_value(
			"Recovery Case",
			case_name,
			"owner_profile",
		)
	except Exception:
		return False

	if not case_owner:
		return False

	# Check if user owns the case
	user_profile = get_owner_profile_for_user(user)
	return user_profile == case_owner


def user_can_access_notification(user: str, notification_name: str) -> bool:
	"""
	Check if user can access a specific notification.

	Args:
	    user: User email trying to access the notification
	    notification_name: Notification Event Log name

	Returns:
	    True if access is allowed
	"""
	if not user or user == "Guest":
		return False

	# Admin can access all notifications
	if is_scanifyme_admin(user):
		return True

	# Get notification owner
	try:
		notification_owner = frappe.db.get_value(
			"Notification Event Log",
			notification_name,
			"owner_profile",
		)
	except Exception:
		return False

	if not notification_owner:
		return False

	# Check if user owns the notification
	user_profile = get_owner_profile_for_user(user)
	return user_profile == notification_owner


def user_can_access_location_share(user: str, location_name: str) -> bool:
	"""
	Check if user can access a specific location share.

	Args:
	    user: User email trying to access the location
	    location_name: Location Share name

	Returns:
	    True if access is allowed
	"""
	if not user or user == "Guest":
		return False

	# Admin can access all locations
	if is_scanifyme_admin(user):
		return True

	# Get location's recovery case owner
	try:
		case_name = frappe.db.get_value(
			"Location Share",
			location_name,
			"recovery_case",
		)
	except Exception:
		return False

	if not case_name:
		return False

	return user_can_access_recovery_case(user, case_name)


def has_qr_management_role(user: Optional[str] = None) -> bool:
	"""
	Check if user has QR management role.

	Args:
	    user: User email. If None, uses current session user.

	Returns:
	    True if user has ScanifyMe Admin or ScanifyMe Operations role
	"""
	if not user:
		user = frappe.session.user

	if user == "Guest" or not user:
		return False

	# Admin always has access
	if is_scanifyme_admin(user):
		return True

	roles = frappe.get_roles(user)
	return "ScanifyMe Operations" in roles or "ScanifyMe Admin" in roles


def check_api_permission(resource: str, ptype: str = "read") -> bool:
	"""
	Check if current user has permission for a resource.

	Args:
	    resource: DocType name
	    ptype: Permission type (read, write, create, delete)

	Returns:
	    True if user has permission
	"""
	return frappe.has_permission(resource, ptype)


def require_authentication():
	"""
	Ensure the request is from an authenticated user.

	Raises:
	    frappe.PermissionError if user is Guest
	"""
	user = frappe.session.user
	if user == "Guest":
		frappe.throw("Authentication required", frappe.PermissionError)


def require_admin():
	"""
	Ensure the request is from an admin user.

	Raises:
	    frappe.PermissionError if user is not admin
	"""
	if not is_scanifyme_admin():
		frappe.throw("Admin access required", frappe.PermissionError)


def require_owner_profile():
	"""
	Ensure the user has an owner profile.

	Raises:
	    frappe.PermissionError if user doesn't have owner profile
	"""
	profile = get_owner_profile_for_user()
	if not profile or profile == "Administrator":
		frappe.throw("Owner profile required", frappe.PermissionError)


def has_admin_role() -> bool:
	"""
	Check if the current user has admin privileges.

	Returns:
	    True if user is Administrator or has ScanifyMe Admin role.
	"""
	roles = frappe.get_roles()
	return "Administrator" in roles or "ScanifyMe Admin" in roles
