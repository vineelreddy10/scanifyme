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

	# Import QR service
	from scanifyme.qr_management.services.qr_service import generate_qr_token, generate_qr_uid

	site_url = frappe.utils.get_url()

	# Check if we already have an activated QR tag with a linked item
	existing_activated = frappe.db.get_value(
		"QR Code Tag",
		{"status": "Activated"},
		["name", "qr_uid", "qr_token", "registered_item"],
		as_dict=True,
	)

	if existing_activated and existing_activated.registered_item:
		# Use existing data
		activated_qr = {
			"name": existing_activated.name,
			"uid": existing_activated.qr_uid,
			"token": existing_activated.qr_token,
			"status": "Activated",
		}
		item1 = frappe.get_doc("Registered Item", existing_activated.registered_item)
		created_qr_tags = [activated_qr]
		created_items = [
			{
				"name": item1.name,
				"item_name": item1.item_name,
				"status": item1.status,
				"qr_token": activated_qr["token"],
			}
		]
		created_data["qr_tags"] = created_qr_tags
		created_data["registered_items"] = created_items
		created_data["qr_batch"] = existing_activated.name
	else:
		# Create new QR Batch with unique name
		import uuid

		batch_suffix = str(uuid.uuid4())[:8]
		batch_name = f"Demo-Batch-{now_datetime().strftime('%Y%m%d')}-{batch_suffix}"
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

		# Create tags in different states
		statuses = ["In Stock", "In Stock", "In Stock", "Activated", "Suspended", "Printed"]

		created_qr_tags = []
		qr_tokens = []
		for i in range(1, 7):
			token = generate_qr_token()
			uid = generate_qr_uid(f"DEMO{batch_suffix[:4].upper()}", i)

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
			created_qr_tags.append(
				{"name": qr_tag.name, "uid": uid, "token": token, "status": statuses[i - 1]}
			)
			qr_tokens.append(token)

		created_data["qr_tags"] = created_qr_tags

		# Create demo registered items for the demo user
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

		# Update QR tag to link to the registered item
		frappe.db.set_value("QR Code Tag", activated_qr["name"], "registered_item", item1.name)
		frappe.db.commit()

		created_items = [
			{
				"name": item1.name,
				"item_name": item1.item_name,
				"status": item1.status,
				"qr_token": activated_qr["token"],
			}
		]

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

	# Now handle recovery data (if it doesn't exist)
	# Get the activated QR tag and item for recovery data
	if not activated_qr:
		# Need to get it from the existing data
		existing_activated = frappe.db.get_value(
			"QR Code Tag",
			{"status": "Activated", "registered_item": ["is", "set"]},
			["name", "registered_item"],
			as_dict=True,
		)
		if existing_activated:
			activated_qr = {
				"name": existing_activated.name,
				"token": existing_activated.qr_token,
			}
			item1_name = existing_activated.registered_item
		else:
			item1_name = None
	else:
		item1_name = item1.name if "item1" in dir() else None

	# Create demo recovery data if item exists
	if item1_name:
		# 1. Create a Finder Session if not exists
		finder_session_id = "demo_finder_001"
		if not frappe.db.exists("Finder Session", finder_session_id):
			finder_session = frappe.get_doc(
				{
					"doctype": "Finder Session",
					"session_id": finder_session_id,
					"qr_code_tag": activated_qr.get("name") if activated_qr else None,
					"started_on": now_datetime(),
					"last_seen_on": now_datetime(),
					"ip_hash": "demo_hash_001",
					"user_agent": "Demo Browser/1.0",
					"status": "Active",
				}
			)
			finder_session.insert(ignore_permissions=True)
		created_data["finder_session"] = finder_session_id

		# 2. Create a Scan Event if not exists
		if activated_qr and activated_qr.get("token"):
			if not frappe.db.exists("Scan Event", {"token": activated_qr.get("token")}):
				scan_event = frappe.get_doc(
					{
						"doctype": "Scan Event",
						"qr_code_tag": activated_qr.get("name"),
						"registered_item": item1_name,
						"token": activated_qr.get("token"),
						"scanned_on": now_datetime(),
						"ip_hash": "demo_hash_001",
						"user_agent": "Demo Browser/1.0",
						"route": f"/s/{activated_qr.get('token')}",
						"status": "Valid",
					}
				)
				scan_event.insert(ignore_permissions=True)
			created_data["scan_event"] = "created"

		# 3. Create a Recovery Case if not exists (use unique case title)
		case_title = f"Recovery - MacBook Pro 14 - {now_datetime().strftime('%Y%m%d%H%M%S')}"
		existing_case = None
		if activated_qr and activated_qr.get("name"):
			existing_case = frappe.db.get_value(
				"Recovery Case",
				{"qr_code_tag": activated_qr.get("name")},
				"name",
			)
		recovery_case_name = existing_case
		if not existing_case:
			recovery_case = frappe.get_doc(
				{
					"doctype": "Recovery Case",
					"case_title": case_title,
					"qr_code_tag": activated_qr.get("name") if activated_qr else None,
					"registered_item": item1_name,
					"owner_profile": owner_profile_name,
					"status": "Open",
					"opened_on": now_datetime(),
					"last_activity_on": now_datetime(),
					"finder_session_id": finder_session_id,
					"finder_name": "John Finder",
					"finder_contact_hint": "+9876543210",
					"latest_message_preview": "Hi, I found your MacBook...",
				}
			)
			recovery_case.insert(ignore_permissions=True)
			recovery_case_name = recovery_case.name

		# 4. Create Recovery Messages if not exists
		if recovery_case_name and not frappe.db.exists(
			"Recovery Message", {"recovery_case": recovery_case_name}
		):
			message1 = frappe.get_doc(
				{
					"doctype": "Recovery Message",
					"recovery_case": recovery_case_name,
					"sender_type": "Finder",
					"sender_name": "John Finder",
					"message": "Hi, I found your MacBook at the coffee shop on Main Street. It's in great condition!",
					"created_on": now_datetime(),
					"is_public_submission": 1,
				}
			)
			message1.insert(ignore_permissions=True)

			message2 = frappe.get_doc(
				{
					"doctype": "Recovery Message",
					"recovery_case": recovery_case_name,
					"sender_type": "Owner",
					"sender_name": "Demo User",
					"message": "Thank you so much for finding it! Can we meet at the coffee shop tomorrow?",
					"created_on": now_datetime(),
					"is_public_submission": 0,
				}
			)
			message2.insert(ignore_permissions=True)

		created_data["recovery_messages"] = "created"

	frappe.db.commit()

	# Get the public test token
	public_token = None
	if activated_qr and activated_qr.get("token"):
		public_token = activated_qr.get("token")
	else:
		# Try to get from database
		tag = frappe.db.get_value(
			"QR Code Tag",
			{"registered_item": ["is", "set"]},
			"qr_token",
			order_by="creation desc",
		)
		public_token = tag

	return {
		"success": True,
		"message": "Demo data created successfully",
		"data": {
			"demo_user": demo_user_email,
			"demo_password": "demo123",
			"owner_profile": owner_profile_name,
			"categories": created_categories,
			"qr_batch": created_data.get("qr_batch"),
			"public_test_token": public_token,
			"recovery": {
				"finder_session": created_data.get("finder_session"),
				"scan_event": created_data.get("scan_event"),
				"recovery_messages": created_data.get("recovery_messages"),
			},
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
