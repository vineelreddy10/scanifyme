"""
Demo Data Generator - Development-only utility for creating test data.

This module provides a whitelisted method to generate demo data for testing.
It is ONLY available in development mode and requires admin privileges.

WARNING: This is for development/testing only. Do not use in production.
"""

import frappe
from frappe.utils import now_datetime
import random


def has_admin_role():
	"""Check if user has admin role."""
	roles = frappe.get_roles()
	return "Administrator" in roles or "ScanifyMe Admin" in roles


@frappe.whitelist()
def create_demo_data():
	"""
	Create demo data for testing purposes.

	This method is admin-only and should only be used in development.

	Returns:
	    dict with created demo data info
	"""
	# Security: Only allow in development
	if frappe.flags.in_import or frappe.flags.in_patch:
		pass  # Allow in bench context
	elif not has_admin_role():
		frappe.throw("Permission denied. Admin role required.", frappe.PermissionError)

	created_data = {}

	# Create demo user if not exists
	demo_user_email = "demo@scanifyme.app"
	if not frappe.db.exists("User", demo_user_email):
		user = frappe.get_doc(
			{
				"doctype": "User",
				"email": demo_user_email,
				"first_name": "Demo",
				"last_name": "User",
				"send_welcome_email": 0,
				"user_type": "Website User",
				"enabled": 1,
			}
		)
		user.insert(ignore_permissions=True)
		created_data["user"] = demo_user_email
	else:
		created_data["user"] = demo_user_email

	# Create owner profile for demo user
	owner_profile_name = None
	if frappe.db.exists("Owner Profile", {"user": demo_user_email}):
		owner_profile_name = frappe.db.get_value("Owner Profile", {"user": demo_user_email}, "name")
	else:
		owner_profile = frappe.get_doc(
			{
				"doctype": "Owner Profile",
				"user": demo_user_email,
				"display_name": "Demo User",
				"phone": "+1234567890",
				"address": "123 Demo Street, Demo City, DC 12345",
				"is_verified": 1,
			}
		)
		owner_profile.insert(ignore_permissions=True)
		owner_profile_name = owner_profile.name
		created_data["owner_profile"] = owner_profile_name

	# Create item categories
	categories = [
		{"category_name": "Keys", "category_code": "KEYS", "description": "Keys and keychains", "icon": "🔑"},
		{"category_name": "Bag", "category_code": "BAG", "description": "Bags and luggage", "icon": "👜"},
		{
			"category_name": "Wallet",
			"category_code": "WALLET",
			"description": "Wallets and purses",
			"icon": "👛",
		},
		{
			"category_name": "Laptop",
			"category_code": "LAPTOP",
			"description": "Laptops and electronics",
			"icon": "💻",
		},
		{"category_name": "Pet", "category_code": "PET", "description": "Pet accessories", "icon": "🐕"},
	]

	created_categories = []
	for cat in categories:
		if not frappe.db.exists("Item Category", {"category_code": cat["category_code"]}):
			category = frappe.get_doc(
				{
					"doctype": "Item Category",
					"category_name": cat["category_name"],
					"category_code": cat["category_code"],
					"description": cat["description"],
					"icon": cat["icon"],
					"is_active": 1,
				}
			)
			category.insert(ignore_permissions=True)
			created_categories.append(category.name)
		else:
			created_categories.append(cat["category_name"])
	created_data["categories"] = created_categories

	# Create QR Batch
	batch_name = f"Demo-Batch-{now_datetime().strftime('%Y%m%d')}"
	batch = frappe.get_doc(
		{
			"doctype": "QR Batch",
			"batch_name": batch_name,
			"batch_prefix": "DEMO",
			"batch_size": 10,
			"status": "Generated",
			"naming_series": "QRB-.YYYY.-",
		}
	)
	batch.insert(ignore_permissions=True)
	created_data["qr_batch"] = batch.name

	# Create QR Code Tags
	qr_tokens = []
	from scanifyme.qr_management.services.qr_service import generate_qr_token, generate_qr_uid

	site_url = frappe.utils.get_url()

	# Create tags in different states
	statuses = ["In Stock", "In Stock", "In Stock", "Activated", "Suspended", "Printed"]

	created_qr_tags = []
	for i in range(1, 7):
		token = generate_qr_token()
		uid = generate_qr_uid("DEMO", i)

		qr_tag = frappe.get_doc(
			{
				"doctype": "QR Code Tag",
				"qr_uid": uid,
				"qr_token": token,
				"qr_url": f"{site_url}/s/{token}",
				"batch": batch.name,
				"status": statuses[i - 1],
			}
		)
		qr_tag.insert(ignore_permissions=True)
		created_qr_tags.append({"name": qr_tag.name, "uid": uid, "token": token, "status": statuses[i - 1]})
		qr_tokens.append(token)

	created_data["qr_tags"] = created_qr_tags

	# Create demo registered items for the demo user
	# Find available QR tags (not already linked)
	available_qr_tags = [tag["name"] for tag in created_qr_tags if tag["status"] == "In Stock"]

	created_items = []

	# Item 1: With activated QR
	activated_qr = created_qr_tags[3]  # The "Activated" one
	item1 = frappe.get_doc(
		{
			"doctype": "Registered Item",
			"item_name": "MacBook Pro 14",
			"owner_profile": owner_profile_name,
			"qr_code_tag": activated_qr["name"],
			"item_category": "Laptop",
			"public_label": "MacBook",
			"recovery_note": "Please contact me at demo@scanifyme.app or call +1234567890",
			"reward_note": "Reward: $50 for safe return",
			"status": "Active",
			"activation_date": now_datetime(),
		}
	)
	item1.insert(ignore_permissions=True)
	created_items.append(
		{
			"name": item1.name,
			"item_name": item1.item_name,
			"status": item1.status,
			"qr_token": activated_qr["token"],
		}
	)

	# Item 2: Without QR (draft)
	item2 = frappe.get_doc(
		{
			"doctype": "Registered Item",
			"item_name": "My House Keys",
			"owner_profile": owner_profile_name,
			"item_category": "Keys",
			"public_label": "House Keys",
			"recovery_note": "These are my house keys. Please return!",
			"status": "Draft",
		}
	)
	item2.insert(ignore_permissions=True)
	created_items.append(
		{"name": item2.name, "item_name": item2.item_name, "status": item2.status, "qr_token": None}
	)

	created_data["registered_items"] = created_items

	frappe.db.commit()

	return {
		"success": True,
		"message": "Demo data created successfully",
		"data": {
			"demo_user": demo_user_email,
			"demo_password": "demo123",  # Note: In real setup, this would be set properly
			"owner_profile": owner_profile_name,
			"categories": created_categories,
			"qr_batch": batch.name,
			"qr_tags": [
				{"uid": tag["uid"], "token": tag["token"], "status": tag["status"]} for tag in created_qr_tags
			],
			"items": [
				{
					"name": item["name"],
					"item_name": item["item_name"],
					"status": item["status"],
					"qr_token": item.get("qr_token"),
				}
				for item in created_items
			],
		},
	}


@frappe.whitelist()
def get_demo_tokens():
	"""
	Get list of available demo QR tokens.

	Returns:
	    List of demo tokens with their status
	"""
	# Security: Only allow in development
	if not has_admin_role():
		frappe.throw("Permission denied. Admin role required.", frappe.PermissionError)

	demo_batch = frappe.db.get_value(
		"QR Batch", {"batch_name": ["like", "Demo-Batch%"]}, "name", order_by="creation desc"
	)

	if not demo_batch:
		return {"message": "No demo data found. Run create_demo_data first."}

	qr_tags = frappe.get_list(
		"QR Code Tag",
		filters={"batch": demo_batch},
		fields=["name", "qr_uid", "qr_token", "status", "registered_item"],
		order_by="creation asc",
	)

	return {"batch": demo_batch, "tags": qr_tags}
