"""
Notification Delivery Service - Handles email notification delivery.

This module provides:
- Email sending using Frappe's sendmail system
- Email template generation using Jinja templates
- Integration with Frappe Email Queue
"""

import frappe
from frappe.utils import get_url
from frappe.utils.jinja import render_template
from typing import Optional


def get_owner_email(owner_profile: str) -> Optional[str]:
	"""
	Get the email address for an owner profile.

	Args:
	    owner_profile: Owner Profile name

	Returns:
	    Owner's email address or None
	"""
	# Get the user linked to the owner profile
	user = frappe.db.get_value("Owner Profile", owner_profile, "user")

	if not user:
		return None

	# Get the user's email
	user_email = frappe.db.get_value("User", user, "email")
	if user_email:
		return user_email

	return None


def get_default_outgoing_email_account() -> Optional[str]:
	"""
	Get the default outgoing email account.

	Returns:
	    Email account email address or None
	"""
	email_account = frappe.db.get_value(
		"Email Account",
		{"default_outgoing": 1, "enabled": 1},
		"email_account_name",
	)

	if not email_account:
		# Try to get any enabled email account
		email_account = frappe.db.get_value(
			"Email Account",
			{"enabled": 1},
			"email_account_name",
			order_by="creation asc",
		)

	return email_account


def get_site_url() -> str:
	"""
	Get the site URL for generating action links.

	Returns:
	    Site URL string
	"""
	return get_url()


def build_action_link(case_id: str) -> str:
	"""
	Build the action link for a recovery case.

	Args:
		case_id: Recovery Case name

	Returns:
	    Full URL to the recovery case
	"""
	site_url = get_site_url().rstrip("/")
	return f"{site_url}/frontend/recovery/{case_id}"


def generate_finder_message_email_content(
	owner_name: str,
	item_name: str,
	public_label: str,
	recovery_case_id: str,
	message_preview: str,
) -> dict:
	"""
	Generate email content for finder message notification.

	Args:
	    owner_name: Owner's display name
	    item_name: Item name
	    public_label: Public label for the item
	    recovery_case_id: Recovery Case name
	    message_preview: Preview of the message

	Returns:
	    Dict with subject and message (HTML)
	"""
	action_link = build_action_link(recovery_case_id)

	subject = f"New message for your {public_label or item_name}"

	# Build HTML content using Jinja template
	template_vars = {
		"owner_name": owner_name,
		"item_name": item_name,
		"public_label": public_label,
		"recovery_case_id": recovery_case_id,
		"message_preview": message_preview,
		"action_link": action_link,
	}

	message = """
	<div style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
		<div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 30px; border-radius: 10px 10px 0 0;">
			<h1 style="color: white; margin: 0; font-size: 24px;">New Message Received</h1>
		</div>
		
		<div style="background: #ffffff; padding: 30px; border: 1px solid #e0e0e0; border-top: none; border-radius: 0 0 10px 10px;">
			<p style="color: #333; font-size: 16px; margin-bottom: 20px;">
				Hello {{ owner_name }},
			</p>
			
			<p style="color: #333; font-size: 16px;">
				You received a new message regarding your <strong>{{ item_name }}</strong>.
			</p>
			
			<div style="background: #f5f5f5; padding: 15px; border-radius: 8px; margin: 20px 0;">
				<p style="color: #666; font-size: 14px; margin: 0; font-style: italic;">
					"{{ message_preview }}"
				</p>
			</div>
			
			<div style="text-align: center; margin: 30px 0;">
				<a href="{{ action_link }}" style="display: inline-block; background: #667eea; color: white; padding: 14px 28px; text-decoration: none; border-radius: 8px; font-weight: 600;">
					View Recovery Case
				</a>
			</div>
			
			<p style="color: #999; font-size: 12px; margin-top: 30px; text-align: center;">
				This email was sent by ScanifyMe. You can manage your notification preferences in your account settings.
			</p>
		</div>
	</div>
	"""

	return {
		"subject": subject,
		"message": frappe.render_template(message, template_vars),
	}


def generate_case_opened_email_content(
	owner_name: str,
	item_name: str,
	public_label: str,
	recovery_case_id: str,
) -> dict:
	"""
	Generate email content for recovery case opened notification.

	Args:
	    owner_name: Owner's display name
	    item_name: Item name
	    public_label: Public label for the item
	    recovery_case_id: Recovery Case name

	Returns:
	    Dict with subject and message (HTML)
	"""
	action_link = build_action_link(recovery_case_id)

	subject = f"New recovery case opened for your {public_label or item_name}"

	template_vars = {
		"owner_name": owner_name,
		"item_name": item_name,
		"public_label": public_label,
		"recovery_case_id": recovery_case_id,
		"action_link": action_link,
	}

	message = """
	<div style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
		<div style="background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%); padding: 30px; border-radius: 10px 10px 0 0;">
			<h1 style="color: white; margin: 0; font-size: 24px;">Recovery Case Opened</h1>
		</div>
		
		<div style="background: #ffffff; padding: 30px; border: 1px solid #e0e0e0; border-top: none; border-radius: 0 0 10px 10px;">
			<p style="color: #333; font-size: 16px; margin-bottom: 20px;">
				Hello {{ owner_name }},
			</p>
			
			<p style="color: #333; font-size: 16px;">
				A new recovery case has been opened for your <strong>{{ item_name }}</strong>.
			</p>
			
			<p style="color: #666; font-size: 14px;">
				Someone has found your item and wants to help return it to you!
			</p>
			
			<div style="text-align: center; margin: 30px 0;">
				<a href="{{ action_link }}" style="display: inline-block; background: #f5576c; color: white; padding: 14px 28px; text-decoration: none; border-radius: 8px; font-weight: 600;">
					View Recovery Case
				</a>
			</div>
			
			<p style="color: #999; font-size: 12px; margin-top: 30px; text-align: center;">
				This email was sent by ScanifyMe. You can manage your notification preferences in your account settings.
			</p>
		</div>
	</div>
	"""

	return {
		"subject": subject,
		"message": frappe.render_template(message, template_vars),
	}


def generate_case_status_updated_email_content(
	owner_name: str,
	item_name: str,
	public_label: str,
	recovery_case_id: str,
	old_status: str,
	new_status: str,
) -> dict:
	"""
	Generate email content for case status update notification.

	Args:
	    owner_name: Owner's display name
	    item_name: Item name
	    public_label: Public label for the item
	    recovery_case_id: Recovery Case name
	    old_status: Previous status
	    new_status: New status

	Returns:
	    Dict with subject and message (HTML)
	"""
	action_link = build_action_link(recovery_case_id)

	subject = f"Case status updated for your {public_label or item_name}"

	template_vars = {
		"owner_name": owner_name,
		"item_name": item_name,
		"public_label": public_label,
		"recovery_case_id": recovery_case_id,
		"old_status": old_status,
		"new_status": new_status,
		"action_link": action_link,
	}

	message = """
	<div style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
		<div style="background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%); padding: 30px; border-radius: 10px 10px 0 0;">
			<h1 style="color: white; margin: 0; font-size: 24px;">Case Status Updated</h1>
		</div>
		
		<div style="background: #ffffff; padding: 30px; border: 1px solid #e0e0e0; border-top: none; border-radius: 0 0 10px 10px;">
			<p style="color: #333; font-size: 16px; margin-bottom: 20px;">
				Hello {{ owner_name }},
			</p>
			
			<p style="color: #333; font-size: 16px;">
				The status of your recovery case for <strong>{{ item_name }}</strong> has been updated.
			</p>
			
			<div style="background: #f5f5f5; padding: 15px; border-radius: 8px; margin: 20px 0; text-align: center;">
				<p style="color: #666; font-size: 14px; margin: 0;">
					<strong>Status Change:</strong> {{ old_status }} → <strong>{{ new_status }}</strong>
				</p>
			</div>
			
			<div style="text-align: center; margin: 30px 0;">
				<a href="{{ action_link }}" style="display: inline-block; background: #4facfe; color: white; padding: 14px 28px; text-decoration: none; border-radius: 8px; font-weight: 600;">
					View Recovery Case
				</a>
			</div>
			
			<p style="color: #999; font-size: 12px; margin-top: 30px; text-align: center;">
				This email was sent by ScanifyMe. You can manage your notification preferences in your account settings.
			</p>
		</div>
	</div>
	"""

	return {
		"subject": subject,
		"message": frappe.render_template(message, template_vars),
	}


def send_email_notification(
	event_type: str,
	owner_profile: str,
	recovery_case: Optional[str] = None,
	registered_item: Optional[str] = None,
	message_summary: Optional[str] = None,
	old_status: Optional[str] = None,
	new_status: Optional[str] = None,
) -> dict:
	"""
	Send email notification to owner based on event type.

	This function:
	1. Checks if owner has email notifications enabled
	2. Gets owner's email address
	3. Generates appropriate email content
	4. Sends email via Frappe's sendmail system

	Args:
	    event_type: Type of event (Finder Message Received, Recovery Case Opened, Case Status Updated)
	    owner_profile: Owner Profile name
	    recovery_case: Recovery Case name (optional)
	    registered_item: Registered Item name (optional)
	    message_summary: Summary of the message (optional)
	    old_status: Previous status (for status updates)
	    new_status: New status (for status updates)

	Returns:
	    Dict with success status and details
	"""
	# Check if email notifications are enabled for this owner
	from scanifyme.notifications.services.notification_service import (
		get_owner_notification_preferences,
	)

	preferences = get_owner_notification_preferences(owner_profile)

	if not preferences:
		return {"success": False, "reason": "No preferences found"}

	if not preferences.get("enable_email_notifications"):
		return {"success": False, "reason": "Email notifications disabled"}

	# Get owner's email
	owner_email = get_owner_email(owner_profile)

	if not owner_email:
		return {"success": False, "reason": "No email address found for owner"}

	# Get owner name
	owner_name = frappe.db.get_value("Owner Profile", owner_profile, "display_name") or "User"

	# Get item details
	item_name = None
	public_label = None

	if registered_item:
		item_data = frappe.db.get_value(
			"Registered Item",
			registered_item,
			["item_name", "public_label"],
			as_dict=True,
		)
		if item_data:
			item_name = item_data.item_name
			public_label = item_data.public_label or item_name
	elif recovery_case:
		# Try to get from recovery case
		item_name = frappe.db.get_value("Recovery Case", recovery_case, "registered_item")
		if item_name:
			item_data = frappe.db.get_value(
				"Registered Item",
				item_name,
				["item_name", "public_label"],
				as_dict=True,
			)
			if item_data:
				item_name = item_data.item_name
				public_label = item_data.public_label or item_name

	# Generate email content based on event type
	recovery_case_id = recovery_case or "unknown"

	if event_type == "Finder Message Received":
		content = generate_finder_message_email_content(
			owner_name=owner_name,
			item_name=item_name or "your item",
			public_label=public_label or "item",
			recovery_case_id=recovery_case_id,
			message_preview=message_summary or "You have a new message",
		)
	elif event_type == "Recovery Case Opened":
		content = generate_case_opened_email_content(
			owner_name=owner_name,
			item_name=item_name or "your item",
			public_label=public_label or "item",
			recovery_case_id=recovery_case_id,
		)
	elif event_type == "Case Status Updated":
		content = generate_case_status_updated_email_content(
			owner_name=owner_name,
			item_name=item_name or "your item",
			public_label=public_label or "item",
			recovery_case_id=recovery_case_id,
			old_status=old_status or "Unknown",
			new_status=new_status or "Unknown",
		)
	else:
		# Generic email for other event types
		content = {
			"subject": f"ScanifyMe Notification: {event_type}",
			"message": f"<p>Hello {owner_name},</p><p>{message_summary or 'You have a new notification.'}</p>",
		}

	# Send email using Frappe's sendmail
	try:
		frappe.sendmail(
			recipients=[owner_email],
			subject=content["subject"],
			message=content["message"],
			reference_doctype="Recovery Case" if recovery_case else None,
			reference_name=recovery_case,
			expose_recipients="header",
		)

		frappe.db.commit()

		return {
			"success": True,
			"event_type": event_type,
			"recipient": owner_email,
			"recovery_case": recovery_case,
		}

	except Exception as e:
		frappe.db.rollback()

		return {
			"success": False,
			"reason": "Email sending failed",
			"error": str(e),
		}


def should_send_email(event_type: str, preferences: dict) -> bool:
	"""
	Determine if email should be sent based on event type and preferences.

	Args:
	    event_type: Type of event
	    preferences: Owner's notification preferences

	Returns:
	    True if email should be sent, False otherwise
	"""
	# Check if email notifications are enabled
	if not preferences.get("enable_email_notifications"):
		return False

	# Map event types to preference fields
	event_preference_map = {
		"Finder Message Received": "notify_on_new_finder_message",
		"Recovery Case Opened": "notify_on_case_opened",
		"Case Status Updated": "notify_on_case_status_change",
	}

	pref_field = event_preference_map.get(event_type)
	if pref_field and not preferences.get(pref_field):
		return False

	return True


def get_email_queue_entries(recipient: str = None, limit: int = 10) -> list:
	"""
	Get email queue entries.

	Args:
	    recipient: Filter by recipient email (optional)
	    limit: Maximum number of entries to return

	Returns:
	    List of email queue entries
	"""
	filters = {}
	if recipient:
		filters["recipient"] = ["like", f"%{recipient}%"]

	entries = frappe.get_list(
		"Email Queue",
		filters=filters,
		fields=["name", "subject", "recipient", "status", "creation", "executed"],
		order_by="creation desc",
		limit=limit,
	)

	return entries
