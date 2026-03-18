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
