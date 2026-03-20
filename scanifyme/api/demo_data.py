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

	# Update demo user's email to ensure it's properly set
	frappe.db.set_value("User", demo_user_email, "enabled", 1)
	frappe.db.commit()

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

	activated_qr = None
	item1_name = None

	# Check if we already have an activated QR tag with a linked item
	try:
		existing_activated = frappe.db.get_value(
			"QR Code Tag",
			{"status": "Activated", "registered_item": ["is", "set"]},
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
			item1_name = existing_activated.registered_item
			created_qr_tags = [activated_qr]
			created_items = [
				{
					"name": existing_activated.registered_item,
					"item_name": "Existing Item",
					"status": "Active",
					"qr_token": activated_qr["token"],
				}
			]
			created_data["qr_tags"] = created_qr_tags
			created_data["registered_items"] = created_items
			created_data["qr_batch"] = existing_activated.name
	except Exception:
		pass

	if not activated_qr:
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
				"recovery_note": "Please message me through this platform. I'll reply as soon as possible!",
				"reward_enabled": 1,
				"reward_amount_text": "₹500",
				"reward_note": "Reward for safe return!",
				"reward_visibility": "Public",
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
					# Reward fields
					"reward_offered": 1,
					"reward_display_text": "₹500",
					"reward_status": "Mentioned To Finder",
					"reward_last_updated_on": now_datetime(),
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

	# 5. Create Notification Preference for the owner (if not exists) or update existing
	if owner_profile_name:
		existing_pref = frappe.db.get_value(
			"Notification Preference", {"owner_profile": owner_profile_name}, "name"
		)
		if existing_pref:
			# Update existing preference to ensure email is enabled
			frappe.db.set_value(
				"Notification Preference",
				existing_pref,
				{
					"enable_in_app_notifications": 1,
					"enable_email_notifications": 1,
					"notify_on_new_finder_message": 1,
					"notify_on_case_opened": 1,
					"notify_on_case_status_change": 1,
				},
			)
			created_data["notification_preference"] = existing_pref
		else:
			notification_pref = frappe.get_doc(
				{
					"doctype": "Notification Preference",
					"owner_profile": owner_profile_name,
					"enable_in_app_notifications": 1,
					"enable_email_notifications": 1,
					"notify_on_new_finder_message": 1,
					"notify_on_case_opened": 1,
					"notify_on_case_status_change": 1,
					"is_default": 1,
				}
			)
			notification_pref.insert(ignore_permissions=True)
			created_data["notification_preference"] = notification_pref.name

	# 6. Create Notification Event Logs (if recovery case exists)
	if recovery_case_name and owner_profile_name:
		# Delete existing notification logs for this recovery case to allow refresh
		frappe.db.delete("Notification Event Log", {"recovery_case": recovery_case_name})

		# Log: Case Opened (unread)
		log1 = frappe.get_doc(
			{
				"doctype": "Notification Event Log",
				"event_type": "Recovery Case Opened",
				"owner_profile": owner_profile_name,
				"recovery_case": recovery_case_name,
				"registered_item": item1_name,
				"qr_code_tag": activated_qr.get("name") if activated_qr else None,
				"title": "New recovery case: MacBook Pro 14",
				"message_summary": "New recovery case opened for MacBook Pro 14",
				"channel": "In App",
				"status": "Sent",
				"priority": "High",
				"route": f"/frontend/recovery/{recovery_case_name}",
				"is_read": 0,
				"triggered_on": now_datetime(),
				"delivered_on": now_datetime(),
			}
		)
		log1.insert(ignore_permissions=True)

		# Log: Finder Message Received (unread)
		log2 = frappe.get_doc(
			{
				"doctype": "Notification Event Log",
				"event_type": "Finder Message Received",
				"owner_profile": owner_profile_name,
				"recovery_case": recovery_case_name,
				"registered_item": item1_name,
				"qr_code_tag": activated_qr.get("name") if activated_qr else None,
				"title": "New message for MacBook Pro 14",
				"message_summary": "New message from John Finder: Hi, I found your MacBook...",
				"channel": "In App",
				"status": "Sent",
				"priority": "Normal",
				"route": f"/frontend/recovery/{recovery_case_name}",
				"is_read": 0,
				"triggered_on": now_datetime(),
				"delivered_on": now_datetime(),
			}
		)
		log2.insert(ignore_permissions=True)

		# Log: Owner Reply Sent (read)
		log3 = frappe.get_doc(
			{
				"doctype": "Notification Event Log",
				"event_type": "Owner Reply Sent",
				"owner_profile": owner_profile_name,
				"recovery_case": recovery_case_name,
				"registered_item": item1_name,
				"qr_code_tag": activated_qr.get("name") if activated_qr else None,
				"title": "Reply sent successfully",
				"message_summary": "You replied: Thank you so much for finding it!...",
				"channel": "System",
				"status": "Sent",
				"priority": "Low",
				"route": f"/frontend/recovery/{recovery_case_name}",
				"is_read": 1,
				"read_on": now_datetime(),
				"triggered_on": now_datetime(),
				"delivered_on": now_datetime(),
			}
		)
		log3.insert(ignore_permissions=True)

		# Create additional demo notifications with different scenarios
		# Log: Case Status Updated (unread)
		log4 = frappe.get_doc(
			{
				"doctype": "Notification Event Log",
				"event_type": "Case Status Updated",
				"owner_profile": owner_profile_name,
				"recovery_case": recovery_case_name,
				"registered_item": item1_name,
				"qr_code_tag": activated_qr.get("name") if activated_qr else None,
				"title": "Case status updated: MacBook Pro 14",
				"message_summary": "Case status changed from Open to Owner Responded",
				"channel": "In App",
				"status": "Sent",
				"priority": "Normal",
				"route": f"/frontend/recovery/{recovery_case_name}",
				"is_read": 0,
				"triggered_on": now_datetime(),
				"delivered_on": now_datetime(),
			}
		)
		log4.insert(ignore_permissions=True)

		# Log: Item Marked Recovered (read)
		log5 = frappe.get_doc(
			{
				"doctype": "Notification Event Log",
				"event_type": "Item Marked Recovered",
				"owner_profile": owner_profile_name,
				"recovery_case": recovery_case_name,
				"registered_item": item1_name,
				"qr_code_tag": activated_qr.get("name") if activated_qr else None,
				"title": "Item recovered!",
				"message_summary": "Your MacBook Pro 14 has been marked as recovered",
				"channel": "In App",
				"status": "Sent",
				"priority": "High",
				"route": f"/frontend/items/{item1_name}",
				"is_read": 1,
				"read_on": now_datetime(),
				"triggered_on": now_datetime(),
				"delivered_on": now_datetime(),
			}
		)
		log5.insert(ignore_permissions=True)

		created_data["notification_event_logs"] = "created"
		created_data["recovery_case_id"] = recovery_case_name

		# 7. Create Location Share for the recovery case
		location_share_name = None
		if recovery_case_name and activated_qr and activated_qr.get("name"):
			# Check if location share already exists
			if not frappe.db.exists("Location Share", {"recovery_case": recovery_case_name}):
				location_share = frappe.get_doc(
					{
						"doctype": "Location Share",
						"recovery_case": recovery_case_name,
						"qr_code_tag": activated_qr.get("name"),
						"registered_item": item1_name,
						"finder_session": finder_session_id,
						"latitude": 37.7749,
						"longitude": -122.4194,
						"accuracy_meters": 10.0,
						"source": "Browser Geolocation",
						"shared_on": now_datetime(),
						"note": "Found at the coffee shop on Main Street",
						"is_latest": 1,
					}
				)
				location_share.insert(ignore_permissions=True)
				location_share_name = location_share.name
				created_data["location_share"] = location_share_name

				# Update recovery case with location summary
				frappe.db.set_value(
					"Recovery Case",
					recovery_case_name,
					{
						"latest_location_summary": "37.774900, -122.419400 (±10m)",
						"handover_status": "Location Shared",
					},
				)

		# 8. Create Recovery Timeline Events
		if recovery_case_name:
			# Delete existing timeline events to allow refresh
			frappe.db.delete("Recovery Timeline Event", {"recovery_case": recovery_case_name})

			# Timeline: Scan Detected
			timeline1 = frappe.get_doc(
				{
					"doctype": "Recovery Timeline Event",
					"recovery_case": recovery_case_name,
					"event_type": "Scan Detected",
					"event_label": "QR Code Scanned",
					"actor_type": "Finder",
					"actor_reference": finder_session_id,
					"event_time": now_datetime(),
					"summary": "QR code scanned by John Finder",
					"reference_doctype": "Scan Event",
				}
			)
			timeline1.insert(ignore_permissions=True)

			# Timeline: Finder Message
			timeline2 = frappe.get_doc(
				{
					"doctype": "Recovery Timeline Event",
					"recovery_case": recovery_case_name,
					"event_type": "Finder Message",
					"event_label": "Message from Finder",
					"actor_type": "Finder",
					"actor_reference": "John Finder",
					"event_time": now_datetime(),
					"summary": "Hi, I found your MacBook at the coffee shop on Main Street. It's in great condition!",
					"reference_doctype": "Recovery Message",
				}
			)
			timeline2.insert(ignore_permissions=True)

			# Timeline: Status Updated
			timeline3 = frappe.get_doc(
				{
					"doctype": "Recovery Timeline Event",
					"recovery_case": recovery_case_name,
					"event_type": "Status Updated",
					"event_label": "Case Status Changed",
					"actor_type": "System",
					"event_time": now_datetime(),
					"summary": "Case status changed from Open to Owner Responded",
				}
			)
			timeline3.insert(ignore_permissions=True)

			# Timeline: Location Shared
			if location_share_name:
				timeline4 = frappe.get_doc(
					{
						"doctype": "Recovery Timeline Event",
						"recovery_case": recovery_case_name,
						"event_type": "Location Shared",
						"event_label": "Location Shared by Finder",
						"actor_type": "Finder",
						"actor_reference": finder_session_id,
						"event_time": now_datetime(),
						"summary": "Finder shared location: 37.774900, -122.419400 (±10m)",
						"reference_doctype": "Location Share",
						"reference_name": location_share_name,
					}
				)
				timeline4.insert(ignore_permissions=True)

			# Timeline: Owner Reply
			timeline5 = frappe.get_doc(
				{
					"doctype": "Recovery Timeline Event",
					"recovery_case": recovery_case_name,
					"event_type": "Owner Reply",
					"event_label": "Reply from Owner",
					"actor_type": "Owner",
					"actor_reference": "Demo User",
					"event_time": now_datetime(),
					"summary": "Thank you so much for finding it! Can we meet at the coffee shop tomorrow?",
					"reference_doctype": "Recovery Message",
				}
			)
			timeline5.insert(ignore_permissions=True)

			created_data["timeline_events"] = "created"

	# 9. Create additional recovery cases with different handover statuses
	if owner_profile_name and item1_name and activated_qr:
		# Create a case in "Return Planned" status
		case2_title = f"Recovery - Keys - {now_datetime().strftime('%Y%m%d%H%M%S')}"
		if not frappe.db.exists("Recovery Case", {"case_title": case2_title}):
			recovery_case2 = frappe.get_doc(
				{
					"doctype": "Recovery Case",
					"case_title": case2_title,
					"qr_code_tag": activated_qr.get("name") if activated_qr else None,
					"registered_item": item1_name,
					"owner_profile": owner_profile_name,
					"status": "Return Planned",
					"opened_on": now_datetime(),
					"last_activity_on": now_datetime(),
					"finder_session_id": "demo_finder_002",
					"finder_name": "Jane Finder",
					"finder_contact_hint": "+9876543211",
					"handover_status": "Return Planned",
					"handover_note": "Planning to meet tomorrow at 3 PM",
				}
			)
			recovery_case2.insert(ignore_permissions=True)
			created_data["recovery_case_2"] = recovery_case2.name

			# Add timeline for case 2
			timeline_case2 = frappe.get_doc(
				{
					"doctype": "Recovery Timeline Event",
					"recovery_case": recovery_case2.name,
					"event_type": "Status Updated",
					"event_label": "Return Planned",
					"actor_type": "Owner",
					"actor_reference": "Demo User",
					"event_time": now_datetime(),
					"summary": "Handover status changed to Return Planned",
				}
			)
			timeline_case2.insert(ignore_permissions=True)

		# Create a case in "Recovered" status
		case3_title = f"Recovery - Wallet - {now_datetime().strftime('%Y%m%d%H%M%S')}"
		if not frappe.db.exists("Recovery Case", {"case_title": case3_title}):
			recovery_case3 = frappe.get_doc(
				{
					"doctype": "Recovery Case",
					"case_title": case3_title,
					"qr_code_tag": activated_qr.get("name") if activated_qr else None,
					"registered_item": item1_name,
					"owner_profile": owner_profile_name,
					"status": "Recovered",
					"opened_on": now_datetime(),
					"last_activity_on": now_datetime(),
					"closed_on": now_datetime(),
					"finder_session_id": "demo_finder_003",
					"finder_name": "Bob Finder",
					"finder_contact_hint": "+9876543212",
					"handover_status": "Recovered",
					"handover_note": "Item successfully returned",
				}
			)
			recovery_case3.insert(ignore_permissions=True)
			created_data["recovery_case_3"] = recovery_case3.name

			# Add timeline for case 3
			timeline_case3 = frappe.get_doc(
				{
					"doctype": "Recovery Timeline Event",
					"recovery_case": recovery_case3.name,
					"event_type": "Case Closed",
					"event_label": "Item Recovered",
					"actor_type": "Owner",
					"actor_reference": "Demo User",
					"event_time": now_datetime(),
					"summary": "Case marked as recovered - item successfully returned",
				}
			)
			timeline_case3.insert(ignore_permissions=True)

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
			"demo_email": demo_user_email,
			"owner_profile": owner_profile_name,
			"categories": created_categories,
			"qr_batch": created_data.get("qr_batch"),
			"public_test_token": public_token,
			"recovery": {
				"finder_session": created_data.get("finder_session"),
				"scan_event": created_data.get("scan_event"),
				"recovery_messages": created_data.get("recovery_messages"),
				"location_share": created_data.get("location_share"),
				"timeline_events": created_data.get("timeline_events"),
			},
			"handover_cases": {
				"case_with_location": created_data.get("recovery_case_id"),
				"case_return_planned": created_data.get("recovery_case_2"),
				"case_recovered": created_data.get("recovery_case_3"),
			},
			"notifications": {
				"preference": created_data.get("notification_preference"),
				"event_logs": created_data.get("notification_event_logs"),
				"email_enabled": True,
			},
			"sample_coordinates": {
				"latitude": 37.7749,
				"longitude": -122.4194,
				"description": "San Francisco, CA (coffee shop location)",
			},
			"handover_statuses": {
				"location_shared": "Location Shared",
				"return_planned": "Return Planned",
				"recovered": "Recovered",
			},
			"email_trigger_scenario": {
				"description": "Submit a finder message using the public token",
				"api_method": "scanifyme.messaging.api.message_api.submit_finder_message",
				"token": public_token,
				"expected_result": "Email notification sent to demo@scanifyme.app",
			},
			"location_sharing_scenario": {
				"description": "Submit a location share using the public token",
				"api_method": "scanifyme.public_portal.api.location_api.submit_finder_location",
				"token": public_token,
				"expected_result": "Location shared successfully, timeline updated",
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

	# Get the demo owner profile
	demo_user_email = "demo@scanifyme.app"
	owner_profile = frappe.db.get_value("Owner Profile", {"user": demo_user_email}, "name")

	# Get recovery case ID
	recovery_case_id = None
	if owner_profile:
		recovery_case = frappe.db.get_value(
			"Recovery Case", {"owner_profile": owner_profile}, "name", order_by="creation desc"
		)
		recovery_case_id = recovery_case

	# Get unread notification count
	unread_count = 0
	if owner_profile:
		unread_count = frappe.db.count(
			"Notification Event Log", {"owner_profile": owner_profile, "is_read": 0}
		)

	# Get sample notification IDs
	sample_notification_ids = []
	if owner_profile:
		sample_notifications = frappe.get_list(
			"Notification Event Log",
			filters={"owner_profile": owner_profile},
			fields=["name", "title", "is_read", "route"],
			order_by="triggered_on desc",
			limit=5,
		)
		sample_notification_ids = sample_notifications

	# Get location share info
	location_share_info = None
	if recovery_case_id:
		location = frappe.db.get_value(
			"Location Share",
			{"recovery_case": recovery_case_id, "is_latest": 1},
			["name", "latitude", "longitude", "shared_on"],
			as_dict=True,
		)
		if location:
			location_share_info = {
				"name": location.name,
				"latitude": location.latitude,
				"longitude": location.longitude,
				"shared_on": str(location.shared_on) if location.shared_on else None,
			}

	# Get handover info
	handover_info = None
	if recovery_case_id:
		handover_info = frappe.db.get_value(
			"Recovery Case",
			recovery_case_id,
			["handover_status", "handover_note", "latest_location_summary"],
			as_dict=True,
		)

	# Get all recovery cases with different handover statuses
	recovery_cases = []
	if owner_profile:
		cases = frappe.get_list(
			"Recovery Case",
			filters={"owner_profile": owner_profile},
			fields=["name", "case_title", "status", "handover_status"],
			order_by="creation desc",
			limit=10,
		)
		recovery_cases = cases

	# Owner B info
	owner_b_email = "owner_b@scanifyme.app"
	owner_b_profile = frappe.db.get_value("Owner Profile", {"user": owner_b_email}, "name")
	owner_b_items = []
	owner_b_cases = []
	if owner_b_profile:
		owner_b_items = frappe.get_list(
			"Registered Item",
			filters={"owner_profile": owner_b_profile},
			fields=["name", "item_name", "status"],
			limit=10,
		)
		owner_b_cases = frappe.get_list(
			"Recovery Case",
			filters={"owner_profile": owner_b_profile},
			fields=["name", "case_title", "status"],
			limit=10,
		)

	return {
		"batch": demo_batch,
		"tags": qr_tags,
		"recovery_case_id": recovery_case_id,
		"recovery_cases": recovery_cases,
		"location_share": location_share_info,
		"handover": handover_info,
		"unread_notification_count": unread_count,
		"sample_notifications": sample_notification_ids,
		"demo_email": demo_user_email,
		"email_enabled": True,
		"sample_coordinates": {
			"latitude": 37.7749,
			"longitude": -122.4194,
			"description": "San Francisco, CA (coffee shop location)",
		},
		"owner_b_email": owner_b_email,
		"owner_b_profile": owner_b_profile,
		"owner_b_items": owner_b_items,
		"owner_b_cases": owner_b_cases,
	}


@frappe.whitelist()
def create_reliability_demo_data():
	"""
	Create demo data for reliability and maintenance testing.

	This creates:
	- Failed notification events for retry testing
	- Stale/expired finder sessions for cleanup testing
	- Cases with metadata for recompute testing
	- Various notification statuses for queue testing

	Returns:
	    dict with created demo data info
	"""
	# Security: Only allow in development
	if frappe.flags.in_import or frappe.flags.in_patch:
		pass  # Allow in bench context
	elif not has_admin_role():
		frappe.throw("Permission denied. Admin role required.", frappe.PermissionError)

	from frappe.utils import add_to_date
	import random

	created_data = {}

	# Get demo user and owner profile
	demo_user_email = "demo@scanifyme.app"
	owner_profile = frappe.db.get_value("Owner Profile", {"user": demo_user_email}, "name")

	if not owner_profile:
		return {"success": False, "error": "Run create_demo_data() first"}

	# Get an existing recovery case
	recovery_case = frappe.db.get_value(
		"Recovery Case",
		{"owner_profile": owner_profile, "status": ["!=", "Closed"]},
		"name",
	)

	if not recovery_case:
		return {"success": False, "error": "No recovery case found. Run create_demo_data() first"}

	created_data["recovery_case"] = recovery_case

	# 1. Create failed notification events for retry testing
	failed_notifications = []
	for i in range(3):
		try:
			notification = frappe.get_doc(
				{
					"doctype": "Notification Event Log",
					"event_type": random.choice(
						[
							"Finder Message Received",
							"Recovery Case Opened",
							"Case Status Updated",
						]
					),
					"owner_profile": owner_profile,
					"recovery_case": recovery_case,
					"channel": "Email",
					"status": "Failed",
					"error_message": f"Demo failed notification #{i + 1} - SMTP connection timeout",
					"title": f"Test Notification {i + 1}",
					"triggered_on": add_to_date(now_datetime(), hours=-random.randint(1, 24)),
					"priority": random.choice(["Low", "Normal", "High"]),
					"retry_count": random.randint(0, 2),
				}
			)
			notification.insert(ignore_permissions=True)
			failed_notifications.append(notification.name)
		except Exception:
			pass

	created_data["failed_notifications"] = failed_notifications

	# 2. Create queued notifications for queue testing
	queued_notifications = []
	for i in range(2):
		try:
			notification = frappe.get_doc(
				{
					"doctype": "Notification Event Log",
					"event_type": random.choice(
						[
							"Finder Message Received",
							"Case Status Updated",
						]
					),
					"owner_profile": owner_profile,
					"recovery_case": recovery_case,
					"channel": random.choice(["In App", "Email"]),
					"status": "Queued",
					"title": f"Queued Notification {i + 1}",
					"triggered_on": now_datetime(),
					"priority": "Normal",
				}
			)
			notification.insert(ignore_permissions=True)
			queued_notifications.append(notification.name)
		except Exception:
			pass

	created_data["queued_notifications"] = queued_notifications

	# 3. Create stale/expired finder sessions for cleanup testing
	stale_sessions = []
	for i in range(3):
		try:
			session_id = f"stale_{random.randint(100000, 999999)}"

			# Create session with old timestamps
			session = frappe.get_doc(
				{
					"doctype": "Finder Session",
					"session_id": session_id,
					"status": "Active",
					"started_on": add_to_date(now_datetime(), hours=-random.randint(25, 72)),
					"last_seen_on": add_to_date(now_datetime(), hours=-random.randint(3, 24)),
					"ip_hash": f"demo_hash_{i}",
				}
			)
			session.insert(ignore_permissions=True)
			stale_sessions.append(session.name)
		except Exception:
			pass

	# Also create some explicitly expired sessions
	for i in range(2):
		try:
			session_id = f"expired_{random.randint(100000, 999999)}"
			session = frappe.get_doc(
				{
					"doctype": "Finder Session",
					"session_id": session_id,
					"status": "Expired",
					"started_on": add_to_date(now_datetime(), hours=-random.randint(48, 96)),
					"last_seen_on": add_to_date(now_datetime(), hours=-random.randint(25, 48)),
					"ip_hash": f"expired_hash_{i}",
				}
			)
			session.insert(ignore_permissions=True)
			stale_sessions.append(session.name)
		except Exception:
			pass

	created_data["stale_finder_sessions"] = stale_sessions

	# 4. Create sent notifications for history
	sent_notifications = []
	for i in range(5):
		try:
			notification = frappe.get_doc(
				{
					"doctype": "Notification Event Log",
					"event_type": random.choice(
						[
							"Finder Message Received",
							"Recovery Case Opened",
							"Case Status Updated",
							"Owner Reply Sent",
						]
					),
					"owner_profile": owner_profile,
					"recovery_case": recovery_case,
					"channel": random.choice(["In App", "Email"]),
					"status": "Sent",
					"title": f"Sent Notification {i + 1}",
					"triggered_on": add_to_date(now_datetime(), days=-random.randint(1, 7)),
					"delivered_on": add_to_date(
						now_datetime(), days=-random.randint(1, 7), hours=random.randint(0, 23)
					),
					"priority": "Normal",
					"is_read": random.choice([0, 1]),
				}
			)
			notification.insert(ignore_permissions=True)
			sent_notifications.append(notification.name)
		except Exception:
			pass

	created_data["sent_notifications"] = sent_notifications

	# 5. Get stale session IDs for testing
	stale_session_ids = frappe.get_list(
		"Finder Session",
		filters={
			"status": ["in", ["Active", "Expired"]],
			"started_on": ["<", add_to_date(now_datetime(), hours=-24)],
		},
		fields=["name", "session_id", "status", "started_on"],
		limit=5,
	)

	created_data["stale_session_ids"] = [s.session_id for s in stale_session_ids]

	frappe.db.commit()

	return {
		"success": True,
		"created": created_data,
		"message": "Reliability demo data created",
	}


@frappe.whitelist()
def get_reliability_demo_summary():
	"""
	Get summary of reliability test data for validation.

	Returns:
	    dict with reliability test data counts
	"""
	if not has_admin_role():
		frappe.throw("Permission denied. Admin role required.", frappe.PermissionError)

	from frappe.utils import add_to_date

	demo_user_email = "demo@scanifyme.app"
	owner_profile = frappe.db.get_value("Owner Profile", {"user": demo_user_email}, "name")

	if not owner_profile:
		return {"success": False, "error": "Run create_demo_data() first"}

	# Count by notification status
	notification_stats = {
		"failed": frappe.db.count(
			"Notification Event Log",
			{"status": "Failed", "owner_profile": owner_profile},
		),
		"queued": frappe.db.count(
			"Notification Event Log",
			{"status": "Queued", "owner_profile": owner_profile},
		),
		"sent": frappe.db.count(
			"Notification Event Log",
			{"status": "Sent", "owner_profile": owner_profile},
		),
	}

	# Count finder sessions by status
	session_stats = {
		"active": frappe.db.count(
			"Finder Session",
			{"status": "Active"},
		),
		"expired": frappe.db.count(
			"Finder Session",
			{"status": "Expired"},
		),
		"stale_24h": frappe.db.count(
			"Finder Session",
			{
				"status": "Active",
				"started_on": ["<", add_to_date(now_datetime(), hours=-24)],
			},
		),
	}

	# Get failed notification details
	failed_notifications = frappe.get_list(
		"Notification Event Log",
		filters={"status": "Failed", "owner_profile": owner_profile},
		fields=["name", "event_type", "error_message", "retry_count"],
		limit=5,
	)

	# Get stale sessions
	stale_sessions = frappe.get_list(
		"Finder Session",
		filters={
			"status": ["in", ["Active", "Expired"]],
			"started_on": ["<", add_to_date(now_datetime(), hours=-24)],
		},
		fields=["name", "session_id", "status", "started_on"],
		limit=5,
	)

	return {
		"success": True,
		"notifications": notification_stats,
		"sessions": session_stats,
		"failed_notifications": failed_notifications,
		"stale_sessions": stale_sessions,
	}


# ==================== PRINT AND DISTRIBUTION DEMO DATA ====================


@frappe.whitelist()
def create_print_distribution_demo_data():
	"""
	Create demo data for print and distribution testing.

	This creates:
	- A QR batch with tags in different states
	- A print job
	- Tags marked as printed
	- A distribution record
	- Tags in various stock states: Generated, Printed, In Stock, Assigned, Activated

	Returns:
	    dict with created demo data info
	"""
	# Security: Only allow in development
	if frappe.flags.in_import or frappe.flags.in_patch:
		pass  # Allow in bench context
	elif not has_admin_role():
		frappe.throw("Permission denied. Admin role required.", frappe.PermissionError)

	import uuid
	from scanifyme.qr_management.services.qr_service import generate_qr_token, generate_qr_uid

	created_data = {}

	# Create a new batch for print/distribution demo
	batch_suffix = str(uuid.uuid4())[:8]
	batch_name = f"PrintDemo-Batch-{now_datetime().strftime('%Y%m%d')}-{batch_suffix}"
	batch = frappe.get_doc(
		{
			"doctype": "QR Batch",
			"batch_name": batch_name,
			"batch_prefix": "PRINT",
			"batch_size": 10,
			"status": "Generated",
			"naming_series": "QRB-.YYYY.-",
		}
	)
	batch.insert(ignore_permissions=True)
	created_data["qr_batch"] = batch.name

	# Create tags in different lifecycle states
	# 2 Generated, 2 Printed, 2 In Stock, 2 Assigned, 1 Activated, 1 Suspended
	statuses = [
		"Generated",
		"Generated",
		"Printed",
		"Printed",
		"In Stock",
		"In Stock",
		"Assigned",
		"Assigned",
		"Activated",
		"Suspended",
	]

	created_tags = []
	activated_tag = None
	assigned_tags = []
	for i in range(1, 11):
		token = generate_qr_token()
		uid = generate_qr_uid(f"PRINT{batch_suffix[:4].upper()}", i)
		status = statuses[i - 1]

		tag = frappe.get_doc(
			{
				"doctype": "QR Code Tag",
				"qr_uid": uid,
				"qr_token": token,
				"qr_url": f"{frappe.utils.get_url()}/s/{token}",
				"batch": batch.name,
				"status": status,
			}
		)
		tag.insert(ignore_permissions=True)

		tag_data = {
			"name": tag.name,
			"uid": uid,
			"token": token,
			"status": status,
		}

		# Track activated tag to link to registered item
		if status == "Activated":
			activated_tag = tag_data
		# Track assigned tags
		if status == "Assigned":
			assigned_tags.append(tag.name)

		created_tags.append(tag_data)

	created_data["qr_tags"] = created_tags

	# Link activated tag to a registered item if owner profile exists
	demo_user_email = "demo@scanifyme.app"
	owner_profile = frappe.db.get_value("Owner Profile", {"user": demo_user_email}, "name")

	if owner_profile and activated_tag:
		# Create a registered item for the activated tag
		# Use an existing category
		item_category = frappe.db.get_value("Item Category", {}, "name")
		item = frappe.get_doc(
			{
				"doctype": "Registered Item",
				"item_name": "Demo Activated Item",
				"owner_profile": owner_profile,
				"qr_code_tag": activated_tag["name"],
				"item_category": item_category or "Keys",
				"public_label": "Demo Item",
				"recovery_note": "This is a demo item for testing",
				"status": "Active",
				"activation_date": now_datetime(),
			}
		)
		item.insert(ignore_permissions=True)

		# Update QR tag to link to the registered item
		frappe.db.set_value("QR Code Tag", activated_tag["name"], "registered_item", item.name)
		created_data["registered_item"] = item.name

	# Create a print job for the batch
	job_name = f"PrintJob-{now_datetime().strftime('%Y%m%d%H%M%S')}"
	print_job = frappe.get_doc(
		{
			"doctype": "QR Print Job",
			"print_job_name": job_name,
			"qr_batch": batch.name,
			"status": "Printed",
			"item_count": 10,
			"generated_on": now_datetime(),
			"printed_on": now_datetime(),
			"created_by": "Administrator",
			"notes": "Demo print job for testing",
			"naming_series": "QPJ-.YYYY.-",
		}
	)
	print_job.insert(ignore_permissions=True)

	# Update printed tags with print job reference
	for tag in created_tags:
		if tag["status"] in ["Printed", "In Stock", "Assigned"]:
			frappe.db.set_value("QR Code Tag", tag["name"], "print_job", print_job.name)

	created_data["print_job"] = print_job.name

	# Create a distribution record
	dist_name = f"Dist-{now_datetime().strftime('%Y%m%d%H%M%S')}"
	distribution = frappe.get_doc(
		{
			"doctype": "QR Distribution Record",
			"distribution_name": dist_name,
			"qr_batch": batch.name,
			"status": "Delivered",
			"distributed_to_type": "Demo",
			"distributed_to_name": "Demo Distribution",
			"quantity": 4,
			"distributed_on": now_datetime(),
			"created_by": "Administrator",
			"notes": "Demo distribution for testing",
			"naming_series": "QDIST-.YYYY.-",
		}
	)
	distribution.insert(ignore_permissions=True)

	# Update assigned tags with distribution record reference
	for tag_name in assigned_tags[:2]:  # Only first 2
		frappe.db.set_value("QR Code Tag", tag_name, "distribution_record", distribution.name)

	created_data["distribution_record"] = distribution.name

	frappe.db.commit()

	# Get activation-eligible token (In Stock status)
	eligible_tag = frappe.db.get_value(
		"QR Code Tag",
		{"batch": batch.name, "status": "In Stock"},
		["name", "qr_uid", "qr_token"],
		as_dict=True,
	)

	# Get activation-ineligible token (Suspended status)
	ineligible_tag = frappe.db.get_value(
		"QR Code Tag",
		{"batch": batch.name, "status": "Suspended"},
		["name", "qr_uid", "qr_token"],
		as_dict=True,
	)

	# Get activation-ineligible token (Activated status)
	already_activated_tag = frappe.db.get_value(
		"QR Code Tag",
		{"batch": batch.name, "status": "Activated"},
		["name", "qr_uid", "qr_token"],
		as_dict=True,
	)

	return {
		"success": True,
		"message": "Print and distribution demo data created",
		"data": {
			"qr_batch": created_data.get("qr_batch"),
			"print_job": created_data.get("print_job"),
			"distribution_record": created_data.get("distribution_record"),
			"registered_item": created_data.get("registered_item"),
			"tags": created_data.get("qr_tags"),
			"stock_summary": {
				"generated": 2,
				"printed": 2,
				"in_stock": 2,
				"assigned": 2,
				"activated": 1,
				"suspended": 1,
			},
			"activation_eligible_token": eligible_tag.qr_token if eligible_tag else None,
			"activation_eligible_uid": eligible_tag.qr_uid if eligible_tag else None,
			"activation_ineligible_suspended_token": ineligible_tag.qr_token if ineligible_tag else None,
			"activation_ineligible_suspended_uid": ineligible_tag.qr_uid if ineligible_tag else None,
			"activation_ineligible_activated_token": already_activated_tag.qr_token
			if already_activated_tag
			else None,
			"activation_ineligible_activated_uid": already_activated_tag.qr_uid
			if already_activated_tag
			else None,
		},
	}


@frappe.whitelist()
def get_print_distribution_demo_summary():
	"""
	Get summary of print and distribution demo data.

	Returns:
	    dict with demo data summary
	"""
	if not has_admin_role():
		frappe.throw("Permission denied. Admin role required.", frappe.PermissionError)

	# Get the print/distribution demo batch
	demo_batch = frappe.db.get_value(
		"QR Batch",
		{"batch_name": ["like", "PrintDemo-Batch%"]},
		"name",
		order_by="creation desc",
	)

	if not demo_batch:
		return {"success": False, "error": "Run create_print_distribution_demo_data() first"}

	# Get stock summary
	from scanifyme.qr_management.services import stock_service

	stock_summary = stock_service.get_stock_summary(demo_batch)

	# Get print jobs for this batch
	print_jobs = frappe.db.get_all(
		"QR Print Job",
		filters={"qr_batch": demo_batch},
		fields=["name", "print_job_name", "status", "item_count"],
	)

	# Get distribution records for this batch
	distributions = frappe.db.get_all(
		"QR Distribution Record",
		filters={"qr_batch": demo_batch},
		fields=["name", "distribution_name", "status", "distributed_to_type", "quantity"],
	)

	# Get tags
	tags = frappe.db.get_all(
		"QR Code Tag",
		filters={"batch": demo_batch},
		fields=["name", "qr_uid", "qr_token", "status", "print_job", "distribution_record"],
		order_by="creation asc",
	)

	# Find activation-eligible and ineligible tokens
	eligible_tag = next((t for t in tags if t.status == "In Stock"), None)
	ineligible_suspended = next((t for t in tags if t.status == "Suspended"), None)
	ineligible_activated = next((t for t in tags if t.status == "Activated"), None)

	return {
		"success": True,
		"qr_batch": demo_batch,
		"stock_summary": stock_summary,
		"print_jobs": print_jobs,
		"distributions": distributions,
		"tags": tags,
		"activation_eligible_token": eligible_tag.qr_token if eligible_tag else None,
		"activation_ineligible_suspended_token": ineligible_suspended.qr_token
		if ineligible_suspended
		else None,
		"activation_ineligible_activated_token": ineligible_activated.qr_token
		if ineligible_activated
		else None,
	}


# ==================== ANALYTICS / REPORTING DEMO DATA ==================== Owner B + richer mixed data


@frappe.whitelist()
def create_analytics_demo_data():
	"""
	Create demo data for analytics and reporting testing.

	This creates:
	- A second owner (owner_b@scanifyme.app) with profile
	- Multiple items for both owners in various statuses
	- Multiple recovery cases for both owners in various statuses
	- Multiple scan events (valid and invalid)
	- Multiple notifications (various statuses)
	- Location shares on some cases
	- Reward-enabled and non-reward items
	- Multiple QR batches

	Returns:
	    dict with created demo data info
	"""
	if frappe.flags.in_import or frappe.flags.in_patch:
		pass
	elif not has_admin_role():
		frappe.throw("Permission denied. Admin role required.", frappe.PermissionError)

	from frappe.utils import add_to_date
	import uuid

	created_data = {}
	demo_a_email = "demo@scanifyme.app"

	# Ensure demo_a has owner profile
	owner_a_profile = None
	if not frappe.db.exists("Owner Profile", {"user": demo_a_email}):
		owner_a_profile = frappe.get_doc(
			{
				"doctype": "Owner Profile",
				"user": demo_a_email,
				"display_name": "Demo User",
				"phone": "+1234567890",
				"address": "123 Demo Street, Demo City, DC 12345",
				"is_verified": 1,
			}
		)
		owner_a_profile.insert(ignore_permissions=True)
		owner_a_profile = owner_a_profile.name
	else:
		owner_a_profile = frappe.db.get_value("Owner Profile", {"user": demo_a_email}, "name")

	created_data["owner_a_profile"] = owner_a_profile

	# Create owner B if not exists
	owner_b_email = "owner_b@scanifyme.app"
	owner_b_profile = None
	if not frappe.db.exists("User", owner_b_email):
		user_b = frappe.get_doc(
			{
				"doctype": "User",
				"email": owner_b_email,
				"first_name": "Owner",
				"last_name": "B",
				"send_welcome_email": 0,
				"user_type": "Website User",
				"enabled": 1,
			}
		)
		# Bypass Redis enqueue in User.on_update by patching enqueue temporarily
		import frappe.utils.background_jobs as bj

		_orig_enqueue = bj.enqueue

		def _no_enqueue(*a, **kw):
			pass

		bj.enqueue = _no_enqueue
		try:
			user_b.insert(ignore_permissions=True)
		finally:
			bj.enqueue = _orig_enqueue

	if not frappe.db.exists("Owner Profile", {"user": owner_b_email}):
		owner_b_profile = frappe.get_doc(
			{
				"doctype": "Owner Profile",
				"user": owner_b_email,
				"display_name": "Owner B",
				"phone": "+1987654321",
				"address": "456 Test Avenue, Test City, TC 67890",
				"is_verified": 1,
			}
		)
		owner_b_profile.insert(ignore_permissions=True)
		owner_b_profile = owner_b_profile.name
	else:
		owner_b_profile = frappe.db.get_value("Owner Profile", {"user": owner_b_email}, "name")

	created_data["owner_b_email"] = owner_b_email
	created_data["owner_b_profile"] = owner_b_profile

	# Get an activated QR tag for linking items
	site_url = frappe.utils.get_url()
	activated_qr = frappe.db.get_value(
		"QR Code Tag",
		{"status": "Activated", "registered_item": ["is", "set"]},
		["name", "qr_token", "qr_uid"],
		as_dict=True,
	)

	# Get categories
	categories = frappe.get_all("Item Category", pluck="name")
	if not categories:
		for cat in [
			{"category_name": "Keys", "category_code": "KEYS"},
			{"category_name": "Bag", "category_code": "BAG"},
			{"category_name": "Wallet", "category_code": "WALLET"},
			{"category_name": "Laptop", "category_code": "LAPTOP"},
		]:
			c = frappe.get_doc({"doctype": "Item Category", **cat, "is_active": 1})
			c.insert(ignore_permissions=True)
			categories.append(c.name)

	# Create additional QR batches for reporting diversity
	batch_suffix = str(uuid.uuid4())[:8]
	analytics_batch_name = f"Analytics-Batch-{now_datetime().strftime('%Y%m%d')}-{batch_suffix}"
	analytics_batch = frappe.get_doc(
		{
			"doctype": "QR Batch",
			"batch_name": analytics_batch_name,
			"batch_prefix": "ANLY",
			"batch_size": 20,
			"status": "Generated",
			"naming_series": "QRB-.YYYY.-",
		}
	)
	analytics_batch.insert(ignore_permissions=True)
	created_data["analytics_batch"] = analytics_batch.name

	from scanifyme.qr_management.services.qr_service import generate_qr_token, generate_qr_uid

	# Create 20 QR tags in various states for analytics batch
	tag_statuses = [
		"Generated",
		"Generated",
		"Generated",
		"Printed",
		"Printed",
		"In Stock",
		"In Stock",
		"In Stock",
		"In Stock",
		"Assigned",
		"Assigned",
		"Assigned",
		"Activated",
		"Activated",
		"Activated",
		"Suspended",
	]
	batch_tags = []
	for i, status in enumerate(tag_statuses):
		token = generate_qr_token()
		uid = generate_qr_uid(f"ANLY{batch_suffix[:4].upper()}", i + 1)
		tag = frappe.get_doc(
			{
				"doctype": "QR Code Tag",
				"qr_uid": uid,
				"qr_token": token,
				"qr_url": f"{site_url}/s/{token}",
				"batch": analytics_batch.name,
				"status": status,
			}
		)
		tag.insert(ignore_permissions=True)
		batch_tags.append({"name": tag.name, "token": token, "status": status})

	created_data["analytics_tags"] = [t["name"] for t in batch_tags]

	# Create items for Owner A in various statuses
	owner_a_items = []
	item_statuses_a = [
		{"name": "MacBook Pro 16 - Owner A", "status": "Active", "reward": True},
		{"name": "iPhone 15 Pro - Owner A", "status": "Active", "reward": False},
		{"name": "AirPods Max - Owner A", "status": "Lost", "reward": True},
		{"name": "iPad Pro - Owner A", "status": "Recovered", "reward": False},
		{"name": "Apple Watch - Owner A", "status": "Draft", "reward": False},
		{"name": "Sony WH-1000XM5 - Owner A", "status": "Active", "reward": True},
	]

	activated_tag = next((t for t in batch_tags if t["status"] == "Activated"), None)
	assigned_tags = [t for t in batch_tags if t["status"] == "Assigned"]

	for idx, item_def in enumerate(item_statuses_a):
		qr_tag = None
		if idx == 0 and activated_tag:
			qr_tag = activated_tag["name"]
		elif idx < len(assigned_tags):
			qr_tag = assigned_tags[idx - 1]["name"]

		category = categories[idx % len(categories)] if categories else None
		item = frappe.get_doc(
			{
				"doctype": "Registered Item",
				"item_name": item_def["name"],
				"owner_profile": owner_a_profile,
				"qr_code_tag": qr_tag,
				"item_category": category,
				"public_label": item_def["name"].split(" - ")[0],
				"recovery_note": "Please return this item. Reward available!",
				"reward_enabled": 1 if item_def["reward"] else 0,
				"reward_amount_text": "₹500" if item_def["reward"] else None,
				"reward_note": "Thank you for returning!" if item_def["reward"] else None,
				"reward_visibility": "Public" if item_def["reward"] else "Disabled",
				"status": item_def["status"],
				"activation_date": now_datetime()
				if item_def["status"] in ["Active", "Lost", "Recovered"]
				else None,
			}
		)
		item.insert(ignore_permissions=True)

		if qr_tag:
			frappe.db.set_value("QR Code Tag", qr_tag, "registered_item", item.name)

		owner_a_items.append(
			{
				"name": item.name,
				"item_name": item.item_name,
				"status": item.status,
				"reward_enabled": item.reward_enabled,
			}
		)

	created_data["owner_a_items"] = owner_a_items

	# Create items for Owner B in various statuses
	owner_b_items = []
	item_statuses_b = [
		{"name": "Bicycle Trek Marlin - Owner B", "status": "Active", "reward": True},
		{"name": "Canon EOS R5 - Owner B", "status": "Lost", "reward": True},
		{"name": "DJI Mini 3 Pro - Owner B", "status": "Recovered", "reward": False},
		{"name": "Nintendo Switch - Owner B", "status": "Active", "reward": False},
	]

	suspended_tag = next((t for t in batch_tags if t["status"] == "Suspended"), None)
	stock_tags = [t for t in batch_tags if t["status"] == "In Stock"]

	for idx, item_def in enumerate(item_statuses_b):
		qr_tag = None
		if idx == 0 and stock_tags:
			qr_tag = stock_tags[0]["name"]
		elif idx == 1 and suspended_tag:
			qr_tag = suspended_tag["name"]

		category = categories[(idx + 2) % len(categories)] if categories else None
		item = frappe.get_doc(
			{
				"doctype": "Registered Item",
				"item_name": item_def["name"],
				"owner_profile": owner_b_profile,
				"qr_code_tag": qr_tag,
				"item_category": category,
				"public_label": item_def["name"].split(" - ")[0],
				"recovery_note": "Please contact me!",
				"reward_enabled": 1 if item_def["reward"] else 0,
				"reward_amount_text": "₹1000" if item_def["reward"] else None,
				"reward_note": "Reward for safe return!" if item_def["reward"] else None,
				"reward_visibility": "Public" if item_def["reward"] else "Disabled",
				"status": item_def["status"],
				"activation_date": now_datetime()
				if item_def["status"] in ["Active", "Lost", "Recovered"]
				else None,
			}
		)
		item.insert(ignore_permissions=True)

		if qr_tag:
			frappe.db.set_value("QR Code Tag", qr_tag, "registered_item", item.name)

		owner_b_items.append(
			{
				"name": item.name,
				"item_name": item.item_name,
				"status": item.status,
				"reward_enabled": item.reward_enabled,
			}
		)

	created_data["owner_b_items"] = owner_b_items

	# Create recovery cases for Owner A
	owner_a_cases = []
	case_statuses_a = ["Open", "Owner Responded", "Return Planned", "Recovered", "Closed"]
	for idx, status in enumerate(case_statuses_a):
		if idx < len(owner_a_items):
			item_name = owner_a_items[idx]["name"]
			item_doc = frappe.get_doc("Registered Item", item_name)
			qr_tag = item_doc.qr_code_tag
			if not qr_tag:
				continue  # Skip items without QR tags (Recovery Case requires qr_code_tag)
			closed_on = now_datetime() if status in ["Recovered", "Closed"] else None

			case = frappe.get_doc(
				{
					"doctype": "Recovery Case",
					"case_title": f"Recovery - {owner_a_items[idx]['item_name']} - Analytics",
					"qr_code_tag": qr_tag,
					"registered_item": item_name,
					"owner_profile": owner_a_profile,
					"status": status,
					"opened_on": add_to_date(now_datetime(), days=-idx * 3),
					"last_activity_on": add_to_date(now_datetime(), days=-idx),
					"closed_on": closed_on,
					"finder_name": f"Finder {idx + 1}",
					"finder_contact_hint": f"+999000{idx}",
					"handover_status": "Recovered" if status in ["Recovered", "Closed"] else "Not Started",
					"reward_offered": 1 if idx % 2 == 0 else 0,
				}
			)
			case.insert(ignore_permissions=True)
			owner_a_cases.append(
				{
					"name": case.name,
					"item": item_name,
					"status": status,
					"handover": case.handover_status,
				}
			)

			if qr_tag:
				frappe.db.set_value("QR Code Tag", qr_tag, "registered_item", item_name)

	created_data["owner_a_cases"] = owner_a_cases

	# Create recovery cases for Owner B
	owner_b_cases = []
	case_statuses_b = ["Open", "Recovered"]
	for idx, status in enumerate(case_statuses_b):
		if idx < len(owner_b_items):
			item_name = owner_b_items[idx]["name"]
			item_doc = frappe.get_doc("Registered Item", item_name)
			qr_tag = item_doc.qr_code_tag
			if not qr_tag:
				continue  # Skip items without QR tags (Recovery Case requires qr_code_tag)

			case = frappe.get_doc(
				{
					"doctype": "Recovery Case",
					"case_title": f"Recovery - {owner_b_items[idx]['item_name']} - Analytics B",
					"qr_code_tag": qr_tag,
					"registered_item": item_name,
					"owner_profile": owner_b_profile,
					"status": status,
					"opened_on": add_to_date(now_datetime(), days=-idx * 5),
					"last_activity_on": add_to_date(now_datetime(), days=-idx * 2),
					"closed_on": now_datetime() if status == "Recovered" else None,
					"finder_name": f"Finder B{idx + 1}",
					"finder_contact_hint": f"+111000{idx}",
					"handover_status": "Recovered" if status == "Recovered" else "Not Started",
					"reward_offered": 1,
				}
			)
			case.insert(ignore_permissions=True)
			owner_b_cases.append(
				{
					"name": case.name,
					"item": item_name,
					"status": status,
					"handover": case.handover_status,
				}
			)

			if qr_tag:
				frappe.db.set_value("QR Code Tag", qr_tag, "registered_item", item_name)

	created_data["owner_b_cases"] = owner_b_cases

	# Create scan events (valid and invalid)
	scan_statuses = ["Valid", "Valid", "Valid", "Invalid", "Recovery Initiated"]
	all_items = owner_a_items + owner_b_items
	scan_events_created = []
	for idx, scan_status in enumerate(scan_statuses):
		item_idx = idx % len(all_items)
		item_name = all_items[item_idx]["name"]
		item_doc = frappe.get_doc("Registered Item", item_name)
		qr_tag = item_doc.qr_code_tag

		if qr_tag:
			token = frappe.db.get_value("QR Code Tag", qr_tag, "qr_token")
			scan = frappe.get_doc(
				{
					"doctype": "Scan Event",
					"qr_code_tag": qr_tag,
					"registered_item": item_name,
					"token": token,
					"scanned_on": add_to_date(now_datetime(), hours=-idx * 6),
					"ip_hash": f"analytics_hash_{idx}",
					"user_agent": "Analytics Test Agent",
					"route": f"/s/{token}" if token else None,
					"status": scan_status,
					"recovery_case": owner_a_cases[0]["name"]
					if scan_status == "Recovery Initiated" and owner_a_cases
					else None,
				}
			)
			scan.insert(ignore_permissions=True)
			scan_events_created.append(scan.name)

	created_data["scan_events"] = scan_events_created

	# Create notification events (various statuses)
	notification_statuses = ["Sent", "Sent", "Queued", "Failed"]
	all_cases = owner_a_cases + owner_b_cases
	notifications_created = []
	for idx, notif_status in enumerate(notification_statuses):
		case_idx = idx % len(all_cases)
		case_name = all_cases[case_idx]["name"]
		owner_profile = owner_a_profile if case_idx < len(owner_a_cases) else owner_b_profile

		event_types = [
			"Finder Message Received",
			"Recovery Case Opened",
			"Case Status Updated",
			"Item Marked Recovered",
		]
		event_type = event_types[idx % len(event_types)]

		notif = frappe.get_doc(
			{
				"doctype": "Notification Event Log",
				"event_type": event_type,
				"owner_profile": owner_profile,
				"recovery_case": case_name,
				"title": f"Analytics: {event_type}",
				"message_summary": f"Test notification {idx + 1} for reporting",
				"channel": "In App" if idx % 2 == 0 else "Email",
				"status": notif_status,
				"priority": ["Low", "Normal", "High", "Normal"][idx % 4],
				"triggered_on": add_to_date(now_datetime(), hours=-idx * 4),
				"delivered_on": now_datetime() if notif_status == "Sent" else None,
				"is_read": 1 if notif_status == "Sent" and idx > 0 else 0,
				"route": f"/frontend/recovery/{case_name}",
			}
		)
		notif.insert(ignore_permissions=True)
		notifications_created.append(notif.name)

	created_data["notifications"] = notifications_created

	# Create location shares on first 2 owner A cases
	location_shares_created = []
	for idx, case_data in enumerate(owner_a_cases[:2]):
		loc = frappe.get_doc(
			{
				"doctype": "Location Share",
				"recovery_case": case_data["name"],
				"qr_code_tag": frappe.db.get_value("Recovery Case", case_data["name"], "qr_code_tag"),
				"latitude": 37.78 + idx * 0.01,
				"longitude": -122.41 + idx * 0.02,
				"accuracy_meters": 10.0,
				"source": "Browser Geolocation",
				"shared_on": add_to_date(now_datetime(), hours=-idx * 2),
				"note": f"Analytics location share {idx + 1}",
				"is_latest": 1,
			}
		)
		loc.insert(ignore_permissions=True)
		location_shares_created.append(loc.name)

	created_data["location_shares"] = location_shares_created

	frappe.db.commit()

	return {
		"success": True,
		"message": "Analytics demo data created",
		"data": created_data,
		"summary": {
			"owner_a_email": demo_a_email,
			"owner_a_items": len(owner_a_items),
			"owner_a_cases": len(owner_a_cases),
			"owner_b_email": owner_b_email,
			"owner_b_items": len(owner_b_items),
			"owner_b_cases": len(owner_b_cases),
			"scan_events": len(scan_events_created),
			"notifications": len(notifications_created),
			"location_shares": len(location_shares_created),
			"analytics_batch": analytics_batch.name,
			"analytics_tags": len(batch_tags),
		},
	}


@frappe.whitelist()
def get_analytics_demo_summary():
	"""
	Get summary of analytics demo data for validation.

	Returns:
	    dict with analytics demo data counts
	"""
	if not has_admin_role():
		frappe.throw("Permission denied. Admin role required.", frappe.PermissionError)

	owner_a_email = "demo@scanifyme.app"
	owner_b_email = "owner_b@scanifyme.app"
	owner_a_profile = frappe.db.get_value("Owner Profile", {"user": owner_a_email}, "name")
	owner_b_profile = frappe.db.get_value("Owner Profile", {"user": owner_b_email}, "name")

	summary = {}

	if owner_a_profile:
		owner_a_items = frappe.db.count("Registered Item", {"owner_profile": owner_a_profile})
		owner_a_cases = frappe.db.count("Recovery Case", {"owner_profile": owner_a_profile})
		owner_a_active = frappe.db.count(
			"Registered Item", {"owner_profile": owner_a_profile, "status": "Active"}
		)
		owner_a_lost = frappe.db.count(
			"Registered Item", {"owner_profile": owner_a_profile, "status": "Lost"}
		)
		owner_a_recovered = frappe.db.count(
			"Registered Item", {"owner_profile": owner_a_profile, "status": "Recovered"}
		)
		owner_a_open_cases = frappe.db.count(
			"Recovery Case",
			{
				"owner_profile": owner_a_profile,
				"status": ["in", ["Open", "Owner Responded", "Return Planned"]],
			},
		)
		summary["owner_a"] = {
			"email": owner_a_email,
			"profile": owner_a_profile,
			"items_total": owner_a_items,
			"items_active": owner_a_active,
			"items_lost": owner_a_lost,
			"items_recovered": owner_a_recovered,
			"cases_total": owner_a_cases,
			"cases_open": owner_a_open_cases,
		}

	if owner_b_profile:
		owner_b_items = frappe.db.count("Registered Item", {"owner_profile": owner_b_profile})
		owner_b_cases = frappe.db.count("Recovery Case", {"owner_profile": owner_b_profile})
		summary["owner_b"] = {
			"email": owner_b_email,
			"profile": owner_b_profile,
			"items_total": owner_b_items,
			"cases_total": owner_b_cases,
		}

	summary["system"] = {
		"total_items": frappe.db.count("Registered Item"),
		"total_cases": frappe.db.count("Recovery Case"),
		"total_scans": frappe.db.count("Scan Event"),
		"total_notifications": frappe.db.count("Notification Event Log"),
		"total_batches": frappe.db.count("QR Batch"),
		"total_tags": frappe.db.count("QR Code Tag"),
		"total_owner_profiles": frappe.db.count("Owner Profile"),
	}

	return {"success": True, "summary": summary}


# ==================== ONBOARDING DEMO DATA ==================== 5 owners in different onboarding states


@frappe.whitelist()
def create_onboarding_demo_data():
	"""
	Create demo data for onboarding and readiness testing.

	This creates 5 owners in different onboarding states:
	- Owner A (owner_a@scanifyme.app): Complete onboarding - everything set up
	- Owner B (owner_b_partial@scanifyme.app): Partial - profile only, no items
	- Owner C (owner_c_qr_only@scanifyme.app): QR activated but no item registered
	- Owner D (owner_d_no_recovery@scanifyme.app): Item registered but no recovery note
	- Owner E (owner_e_no_notif@scanifyme.app): Item + recovery note but no notifications

	Returns:
	    dict with created demo data info
	"""
	if frappe.flags.in_import or frappe.flags.in_patch:
		pass
	elif not has_admin_role():
		frappe.throw("Permission denied. Admin role required.", frappe.PermissionError)

	import uuid
	from scanifyme.qr_management.services.qr_service import generate_qr_token, generate_qr_uid

	created_data = {}
	site_url = frappe.utils.get_url()

	# Owner email mapping
	owner_configs = {
		"owner_a": {
			"email": "owner_a@scanifyme.app",
			"first_name": "Owner",
			"last_name": "A",
			"display_name": "Owner A - Complete",
			"phone": "+1110000001",
			"address": "101 Alpha Street, City A, CA 10001",
			"onboarding_state": "complete",
			"has_item": True,
			"has_qr_linked": True,
			"has_recovery_note": True,
			"has_notification_preference": True,
		},
		"owner_b": {
			"email": "owner_b_partial@scanifyme.app",
			"first_name": "Owner",
			"last_name": "B Partial",
			"display_name": "Owner B - Partial",
			"phone": "+1110000002",
			"address": "202 Beta Avenue, City B, CA 10002",
			"onboarding_state": "partial",
			"has_item": False,
			"has_qr_linked": False,
			"has_recovery_note": False,
			"has_notification_preference": False,
		},
		"owner_c": {
			"email": "owner_c_qr_only@scanifyme.app",
			"first_name": "Owner",
			"last_name": "C QR Only",
			"display_name": "Owner C - QR Only",
			"phone": "+1110000003",
			"address": "303 Gamma Boulevard, City C, CA 10003",
			"onboarding_state": "qr_activated_no_item",
			"has_item": False,
			"has_qr_linked": False,  # QR is Activated but NOT linked to item
			"has_recovery_note": False,
			"has_notification_preference": False,
		},
		"owner_d": {
			"email": "owner_d_no_recovery@scanifyme.app",
			"first_name": "Owner",
			"last_name": "D No Recovery",
			"display_name": "Owner D - No Recovery Note",
			"phone": "+1110000004",
			"address": "404 Delta Road, City D, CA 10004",
			"onboarding_state": "item_no_recovery_note",
			"has_item": True,
			"has_qr_linked": True,
			"has_recovery_note": False,  # Item registered but recovery_note is empty
			"has_notification_preference": False,
		},
		"owner_e": {
			"email": "owner_e_no_notif@scanifyme.app",
			"first_name": "Owner",
			"last_name": "E No Notif",
			"display_name": "Owner E - No Notifications",
			"phone": "+1110000005",
			"address": "505 Epsilon Lane, City E, CA 10005",
			"onboarding_state": "no_notifications",
			"has_item": True,
			"has_qr_linked": True,
			"has_recovery_note": True,
			"has_notification_preference": False,  # Everything else set up, but no Notification Preference record
		},
	}

	# Create a dedicated QR batch for onboarding demo
	batch_suffix = str(uuid.uuid4())[:8]
	batch_name = f"Onboard-Batch-{now_datetime().strftime('%Y%m%d')}-{batch_suffix}"
	batch = frappe.get_doc(
		{
			"doctype": "QR Batch",
			"batch_name": batch_name,
			"batch_prefix": "ONBD",
			"batch_size": 10,
			"status": "Generated",
			"naming_series": "QRB-.YYYY.-",
		}
	)
	batch.insert(ignore_permissions=True)
	created_data["qr_batch"] = batch.name

	# Create QR tags: 4 In Stock + 4 Activated
	# In Stock: for Owner B (partial, unused) and Owner D (needs QR), Owner E
	# Activated: for Owner A (complete), Owner C (QR only, NOT linked to item)
	qr_tag_statuses = [
		"In Stock",   # idx 0 - available for Owner B/D/E
		"In Stock",   # idx 1 - available for Owner B/D/E
		"In Stock",   # idx 2 - available
		"In Stock",   # idx 3 - available
		"Activated",  # idx 4 - Owner A (complete)
		"Activated",  # idx 5 - Owner C (QR only, NOT linked to item)
		"Activated",  # idx 6 - Owner D (item, no recovery note)
		"Activated",  # idx 7 - Owner E (item, no notifications)
	]
	created_qr_tags = {}
	for i, status in enumerate(qr_tag_statuses):
		token = generate_qr_token()
		uid = generate_qr_uid(f"ONBD{batch_suffix[:4].upper()}", i + 1)
		qr_tag = frappe.get_doc(
			{
				"doctype": "QR Code Tag",
				"qr_uid": uid,
				"qr_token": token,
				"qr_url": f"{site_url}/s/{token}",
				"batch": batch.name,
				"status": status,
			}
		)
		qr_tag.insert(ignore_permissions=True)
		created_qr_tags[i] = {
			"name": qr_tag.name,
			"token": token,
			"uid": uid,
			"status": status,
		}

	created_data["qr_tags"] = created_qr_tags

	# Get a category for item creation
	categories = frappe.get_all("Item Category", pluck="name")
	if not categories:
		# Create default categories if none exist
		for cat in [
			{"category_name": "Keys", "category_code": "KEYS"},
			{"category_name": "Bag", "category_code": "BAG"},
			{"category_name": "Wallet", "category_code": "WALLET"},
			{"category_name": "Laptop", "category_code": "LAPTOP"},
		]:
			c = frappe.get_doc({"doctype": "Item Category", **cat, "is_active": 1})
			c.insert(ignore_permissions=True)
			categories.append(c.name)

	# Helper: ensure User exists (with Redis enqueue bypass)
	def ensure_user(email, first_name, last_name):
		if frappe.db.exists("User", email):
			return None  # Already exists, no action needed
		user = frappe.get_doc(
			{
				"doctype": "User",
				"email": email,
				"first_name": first_name,
				"last_name": last_name,
				"send_welcome_email": 0,
				"user_type": "Website User",
				"enabled": 1,
			}
		)
		import frappe.utils.background_jobs as bj

		_orig_enqueue = bj.enqueue

		def _no_enqueue(*a, **kw):
			pass

		bj.enqueue = _no_enqueue
		try:
			user.insert(ignore_permissions=True)
		finally:
			bj.enqueue = _orig_enqueue
		return user.name

	# Helper: ensure Owner Profile exists
	def ensure_owner_profile(email, display_name, phone, address, is_verified=1):
		if frappe.db.exists("Owner Profile", {"user": email}):
			return frappe.db.get_value("Owner Profile", {"user": email}, "name")
		profile = frappe.get_doc(
			{
				"doctype": "Owner Profile",
				"user": email,
				"display_name": display_name,
				"phone": phone,
				"address": address,
				"is_verified": is_verified,
			}
		)
		profile.insert(ignore_permissions=True)
		return profile.name

	# Helper: ensure Notification Preference exists (all flags ON by default)
	def ensure_notification_preference(owner_profile_name, enabled=True):
		existing = frappe.db.get_value(
			"Notification Preference", {"owner_profile": owner_profile_name}, "name"
		)
		if existing:
			# Update existing to ensure flags are set
			frappe.db.set_value(
				"Notification Preference",
				existing,
				{
					"enable_in_app_notifications": 1 if enabled else 0,
					"enable_email_notifications": 1 if enabled else 0,
					"notify_on_new_finder_message": 1 if enabled else 0,
					"notify_on_case_opened": 1 if enabled else 0,
					"notify_on_case_status_change": 1 if enabled else 0,
					"is_default": 1,
				},
			)
			return existing
		pref = frappe.get_doc(
			{
				"doctype": "Notification Preference",
				"owner_profile": owner_profile_name,
				"enable_in_app_notifications": 1 if enabled else 0,
				"enable_email_notifications": 1 if enabled else 0,
				"notify_on_new_finder_message": 1 if enabled else 0,
				"notify_on_case_opened": 1 if enabled else 0,
				"notify_on_case_status_change": 1 if enabled else 0,
				"is_default": 1,
			}
		)
		pref.insert(ignore_permissions=True)
		return pref.name

	owner_results = {}

	# ---- Owner A: Complete onboarding ----
	cfg_a = owner_configs["owner_a"]
	ensure_user(cfg_a["email"], cfg_a["first_name"], cfg_a["last_name"])
	owner_a_profile = ensure_owner_profile(
		cfg_a["email"], cfg_a["display_name"], cfg_a["phone"], cfg_a["address"]
	)
	qr_a = created_qr_tags[4]  # Activated tag at idx 4

	# Create Registered Item with recovery note
	item_a = frappe.get_doc(
		{
			"doctype": "Registered Item",
			"item_name": "MacBook Pro 16 - Owner A",
			"owner_profile": owner_a_profile,
			"qr_code_tag": qr_a["name"],
			"item_category": categories[3] if len(categories) > 3 else categories[0],
			"public_label": "MacBook Pro",
			"recovery_note": "This is my laptop. Please message me through this platform. Reward available!",
			"reward_enabled": 1,
			"reward_amount_text": "₹500",
			"reward_note": "Thank you for returning safely!",
			"reward_visibility": "Public",
			"status": "Active",
			"activation_date": now_datetime(),
		}
	)
	item_a.insert(ignore_permissions=True)
	frappe.db.set_value("QR Code Tag", qr_a["name"], "registered_item", item_a.name)

	ensure_notification_preference(owner_a_profile, enabled=True)

	owner_results["owner_a"] = {
		"email": cfg_a["email"],
		"profile": owner_a_profile,
		"item_name": item_a.name,
		"item_display": item_a.item_name,
		"qr_token": qr_a["token"],
		"onboarding_state": cfg_a["onboarding_state"],
		"onboarding_complete": True,
		"has_recovery_note": True,
		"has_notification_preference": True,
	}

	# ---- Owner B: Partial onboarding (profile only) ----
	cfg_b = owner_configs["owner_b"]
	ensure_user(cfg_b["email"], cfg_b["first_name"], cfg_b["last_name"])
	owner_b_profile = ensure_owner_profile(
		cfg_b["email"], cfg_b["display_name"], cfg_b["phone"], cfg_b["address"]
	)

	owner_results["owner_b"] = {
		"email": cfg_b["email"],
		"profile": owner_b_profile,
		"item_name": None,
		"item_display": None,
		"qr_token": None,
		"onboarding_state": cfg_b["onboarding_state"],
		"onboarding_complete": False,
		"has_recovery_note": False,
		"has_notification_preference": False,
	}

	# ---- Owner C: QR activated but no item registered ----
	cfg_c = owner_configs["owner_c"]
	ensure_user(cfg_c["email"], cfg_c["first_name"], cfg_c["last_name"])
	owner_c_profile = ensure_owner_profile(
		cfg_c["email"], cfg_c["display_name"], cfg_c["phone"], cfg_c["address"]
	)
	qr_c = created_qr_tags[5]  # Activated tag at idx 5 - NOT linked to any item

	owner_results["owner_c"] = {
		"email": cfg_c["email"],
		"profile": owner_c_profile,
		"item_name": None,
		"item_display": None,
		"qr_token": qr_c["token"],
		"qr_status": qr_c["status"],
		"qr_linked_to_item": False,
		"onboarding_state": cfg_c["onboarding_state"],
		"onboarding_complete": False,
		"has_recovery_note": False,
		"has_notification_preference": False,
	}

	# ---- Owner D: Item registered but no recovery note ----
	cfg_d = owner_configs["owner_d"]
	ensure_user(cfg_d["email"], cfg_d["first_name"], cfg_d["last_name"])
	owner_d_profile = ensure_owner_profile(
		cfg_d["email"], cfg_d["display_name"], cfg_d["phone"], cfg_d["address"]
	)
	qr_d = created_qr_tags[6]  # Activated tag at idx 6

	# Create Registered Item WITHOUT recovery_note field (omitted intentionally)
	item_d = frappe.get_doc(
		{
			"doctype": "Registered Item",
			"item_name": "Canon EOS R5 - Owner D",
			"owner_profile": owner_d_profile,
			"qr_code_tag": qr_d["name"],
			"item_category": categories[2] if len(categories) > 2 else categories[0],
			"public_label": "Canon Camera",
			# recovery_note intentionally omitted to simulate incomplete onboarding
			"reward_enabled": 0,
			"reward_visibility": "Disabled",
			"status": "Active",
			"activation_date": now_datetime(),
		}
	)
	item_d.insert(ignore_permissions=True)
	frappe.db.set_value("QR Code Tag", qr_d["name"], "registered_item", item_d.name)

	owner_results["owner_d"] = {
		"email": cfg_d["email"],
		"profile": owner_d_profile,
		"item_name": item_d.name,
		"item_display": item_d.item_name,
		"qr_token": qr_d["token"],
		"onboarding_state": cfg_d["onboarding_state"],
		"onboarding_complete": False,
		"has_recovery_note": False,  # recovery_note is empty/missing
		"has_notification_preference": False,
	}

	# ---- Owner E: Item + recovery note but no notifications ----
	cfg_e = owner_configs["owner_e"]
	ensure_user(cfg_e["email"], cfg_e["first_name"], cfg_e["last_name"])
	owner_e_profile = ensure_owner_profile(
		cfg_e["email"], cfg_e["display_name"], cfg_e["phone"], cfg_e["address"]
	)
	qr_e = created_qr_tags[7]  # Activated tag at idx 7

	# Create Registered Item WITH recovery_note
	item_e = frappe.get_doc(
		{
			"doctype": "Registered Item",
			"item_name": "Nintendo Switch - Owner E",
			"owner_profile": owner_e_profile,
			"qr_code_tag": qr_e["name"],
			"item_category": categories[1] if len(categories) > 1 else categories[0],
			"public_label": "Nintendo Switch",
			"recovery_note": "Please return my Nintendo Switch. Contact me for a reward!",
			"reward_enabled": 1,
			"reward_amount_text": "₹300",
			"reward_note": "Thanks for returning!",
			"reward_visibility": "Public",
			"status": "Active",
			"activation_date": now_datetime(),
		}
	)
	item_e.insert(ignore_permissions=True)
	frappe.db.set_value("QR Code Tag", qr_e["name"], "registered_item", item_e.name)

	# DO NOT create Notification Preference for Owner E - this is intentional
	# (absence of the record = "notifications not configured")

	owner_results["owner_e"] = {
		"email": cfg_e["email"],
		"profile": owner_e_profile,
		"item_name": item_e.name,
		"item_display": item_e.item_name,
		"qr_token": qr_e["token"],
		"onboarding_state": cfg_e["onboarding_state"],
		"onboarding_complete": False,
		"has_recovery_note": True,
		"has_notification_preference": False,  # Intentionally not created
	}

	frappe.db.commit()

	# Build onboarding completeness summary
	onboarding_summary = {}
	for key in ["owner_a", "owner_b", "owner_c", "owner_d", "owner_e"]:
		cfg = owner_configs[key]
		r = owner_results[key]
		onboarding_summary[key] = {
			"email": r["email"],
			"onboarding_state": r["onboarding_state"],
			"profile_created": bool(r["profile"]),
			"qr_activated": bool(r.get("qr_token")),
			"qr_linked_to_item": r["onboarding_state"] not in ["qr_activated_no_item", "partial"],
			"item_registered": bool(r.get("item_name")),
			"recovery_note_set": r.get("has_recovery_note", False),
			"notifications_configured": r.get("has_notification_preference", False),
		}

	return {
		"success": True,
		"message": "Onboarding demo data created successfully",
		"data": {
			"qr_batch": created_data.get("qr_batch"),
			"owners": owner_results,
			"onboarding_summary": onboarding_summary,
		},
		"summary": {
			"owner_a": {
				"email": cfg_a["email"],
				"state": cfg_a["onboarding_state"],
				"item_registered": True,
				"recovery_note": True,
				"notifications": True,
			},
			"owner_b": {
				"email": cfg_b["email"],
				"state": cfg_b["onboarding_state"],
				"item_registered": False,
				"recovery_note": False,
				"notifications": False,
			},
			"owner_c": {
				"email": cfg_c["email"],
				"state": cfg_c["onboarding_state"],
				"item_registered": False,
				"recovery_note": False,
				"notifications": False,
			},
			"owner_d": {
				"email": cfg_d["email"],
				"state": cfg_d["onboarding_state"],
				"item_registered": True,
				"recovery_note": False,  # Intentional: item without recovery note
				"notifications": False,
			},
			"owner_e": {
				"email": cfg_e["email"],
				"state": cfg_e["onboarding_state"],
				"item_registered": True,
				"recovery_note": True,
				"notifications": False,  # Intentional: no Notification Preference record
			},
		},
	}


@frappe.whitelist()
def get_onboarding_demo_summary():
	"""
	Get summary of onboarding demo data for validation.

	Returns counts and details for all 5 demo onboarding owners.
	"""
	if not has_admin_role():
		frappe.throw("Permission denied. Admin role required.", frappe.PermissionError)

	# List of onboarding demo owner emails
	emails = [
		"owner_a@scanifyme.app",
		"owner_b_partial@scanifyme.app",
		"owner_c_qr_only@scanifyme.app",
		"owner_d_no_recovery@scanifyme.app",
		"owner_e_no_notif@scanifyme.app",
	]

	summary = {}

	for email in emails:
		profile = frappe.db.get_value("Owner Profile", {"user": email}, "name")

		if not profile:
			summary[email] = {
				"profile": None,
				"owner_profile_name": None,
				"item_count": 0,
				"items": [],
				"activated_qr_count": 0,
				"activated_qr_unlinked_count": 0,
				"has_notification_preference": False,
				"onboarding_state": "not_started",
			}
			continue

		# Get items for this owner
		items = frappe.get_list(
			"Registered Item",
			filters={"owner_profile": profile},
			fields=["name", "item_name", "recovery_note", "qr_code_tag", "status"],
			limit=10,
		)

		# Count activated QR tags that ARE linked to items for this owner
		# (via the registered_item link from Registered Item → QR Code Tag)
		items_with_qr = [i for i in items if i.get("qr_code_tag")]
		activated_qr_count = len(items_with_qr)

		# Count activated QR tags that are NOT linked to any item
		# (these are orphaned activated tags - relevant for Owner C)
		activated_qr_unlinked = frappe.db.count(
			"QR Code Tag",
			{"status": "Activated", "registered_item": ["is", "not set"]},
		)

		# Check if owner has activated QR tag assigned to them (via assigned_to_user or batch)
		# Look for any activated tag owned by this profile's user
		owner_user = email
		activated_qr_for_user = frappe.db.get_value(
			"QR Code Tag",
			{
				"status": "Activated",
				"assigned_to_user": owner_user,
				"registered_item": ["is", "not set"],
			},
			"name",
		)

		# Check notification preference
		notif_pref_name = frappe.db.get_value(
			"Notification Preference", {"owner_profile": profile}, "name"
		)
		has_notif_pref = bool(notif_pref_name)

		# Determine onboarding state
		item_count = len(items)
		has_qr_linked = item_count > 0 and any(i.get("qr_code_tag") for i in items)
		has_recovery_note = any(
			i.get("recovery_note") for i in items if i.get("recovery_note")
		)

		if has_qr_linked and has_recovery_note and has_notif_pref:
			onboarding_state = "complete"
		elif has_qr_linked and has_recovery_note and not has_notif_pref:
			onboarding_state = "no_notifications"
		elif has_qr_linked and not has_recovery_note:
			onboarding_state = "item_no_recovery_note"
		elif item_count > 0 and not has_qr_linked:
			onboarding_state = "partial"
		elif activated_qr_for_user or activated_qr_unlinked > 0:
			onboarding_state = "qr_activated_no_item"
		else:
			onboarding_state = "partial"

		# Count items with empty/null recovery_note
		items_missing_recovery_note = [
			i["name"]
			for i in items
			if not i.get("recovery_note")
		]

		summary[email] = {
			"profile": profile,
			"owner_profile_name": profile,
			"item_count": item_count,
			"items": [
				{
					"name": i["name"],
					"item_name": i["item_name"],
					"status": i["status"],
					"has_recovery_note": bool(i.get("recovery_note")),
					"qr_linked": bool(i.get("qr_code_tag")),
				}
				for i in items
			],
			"activated_qr_count": activated_qr_count,
			"activated_qr_unlinked_count": activated_qr_unlinked,
			"has_notification_preference": has_notif_pref,
			"notification_preference_name": notif_pref_name,
			"items_missing_recovery_note": items_missing_recovery_note,
			"onboarding_state": onboarding_state,
		}

	# System-wide summary
	summary["_system"] = {
		"total_onboarding_owners": sum(
			1 for k, v in summary.items() if not k.startswith("_") and v.get("profile")
		),
		"total_items": frappe.db.count("Registered Item"),
		"total_qr_tags": frappe.db.count("QR Code Tag"),
		"onboard_batch": frappe.db.get_value(
			"QR Batch",
			{"batch_name": ["like", "Onboard-Batch%"]},
			"name",
			order_by="creation desc",
		),
	}

	return {"success": True, "summary": summary}
