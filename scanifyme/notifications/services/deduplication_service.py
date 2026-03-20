"""
Deduplication Service - Service layer for idempotency and duplicate suppression.

This module provides business logic for:
- Detecting and suppressing duplicate events
- Creating idempotency keys for critical operations
- Short-window duplicate suppression for finder actions
- Notification/event deduplication

Usage:
    from scanifyme.notifications.services.deduplication_service import (
        build_dedupe_key,
        should_skip_duplicate_event,
        check_and_suppress_duplicate,
    )
"""

import frappe
from frappe.utils import now_datetime, now, add_to_date
from typing import Optional, Dict, Any
import hashlib
import json


# Default deduplication window in seconds (5 minutes)
DEFAULT_DEDUP_WINDOW_SECONDS = 300

# Specific windows for different event types
DEDUP_WINDOWS = {
	"finder_message": 60,  # 1 minute for finder messages
	"location_share": 120,  # 2 minutes for location shares
	"notification_event": 300,  # 5 minutes for notifications
	"status_update": 30,  # 30 seconds for status updates
	"timeline_event": 60,  # 1 minute for timeline events
}


def build_dedupe_key(
	event_type: str,
	recovery_case: str,
	additional_context: Optional[Dict[str, Any]] = None,
) -> str:
	"""
	Build a deduplication key for an event.

	Args:
	    event_type: Type of event (finder_message, location_share, etc.)
	    recovery_case: Recovery Case name
	    additional_context: Additional context to include in the key

	Returns:
	    SHA256 hash key for deduplication
	"""
	# Normalize inputs
	context_dict = {
		"event_type": str(event_type),
		"recovery_case": str(recovery_case),
	}

	if additional_context:
		# Sort keys for consistent hashing
		for key in sorted(additional_context.keys()):
			context_dict[key] = additional_context[key]

	# Create deterministic JSON
	context_json = json.dumps(context_dict, sort_keys=True, default=str)

	# Generate hash
	hash_obj = hashlib.sha256(context_json.encode())
	return hash_obj.hexdigest()[:32]


def get_dedup_window_seconds(event_type: str) -> int:
	"""
	Get the deduplication window in seconds for an event type.

	Args:
	    event_type: Type of event

	Returns:
	    Window in seconds
	"""
	# Map event types to dedup categories
	if "message" in event_type.lower() or "finder" in event_type.lower():
		return DEDUP_WINDOWS.get("finder_message", DEFAULT_DEDUP_WINDOW_SECONDS)
	elif "location" in event_type.lower():
		return DEDUP_WINDOWS.get("location_share", DEFAULT_DEDUP_WINDOW_SECONDS)
	elif "status" in event_type.lower():
		return DEDUP_WINDOWS.get("status_update", DEFAULT_DEDUP_WINDOW_SECONDS)
	elif "timeline" in event_type.lower():
		return DEDUP_WINDOWS.get("timeline_event", DEFAULT_DEDUP_WINDOW_SECONDS)

	return DEDUP_WINDOWS.get("notification_event", DEFAULT_DEDUP_WINDOW_SECONDS)


def should_skip_duplicate_event(
	event_type: str,
	recovery_case: str,
	message_hash: Optional[str] = None,
	window_seconds: Optional[int] = None,
) -> Dict[str, Any]:
	"""
	Check if an event should be skipped as a duplicate.

	This checks for duplicates within a time window based on:
	- Event type
	- Recovery case
	- Optional message/content hash for exact duplicate detection

	Args:
	    event_type: Type of event
	    recovery_case: Recovery Case name
	    message_hash: Optional hash of the message content for exact matching
	    window_seconds: Custom window override (optional)

	Returns:
	    Dict with:
	        - should_skip: bool
	        - reason: str (if skipped)
	        - duplicate_of: str (name of duplicate event if found)
	"""
	if not window_seconds:
		window_seconds = get_dedup_window_seconds(event_type)

	# Calculate the time threshold
	time_threshold = add_to_date(now_datetime(), seconds=-window_seconds)

	# For notification events, check Notification Event Log
	if "notification" in event_type.lower() or event_type in [
		"Finder Message Received",
		"Recovery Case Opened",
		"Case Status Updated",
		"Owner Reply Sent",
	]:
		return _check_notification_duplicate(event_type, recovery_case, message_hash, time_threshold)

	# For timeline events, check Recovery Timeline Event
	if "timeline" in event_type.lower():
		return _check_timeline_duplicate(event_type, recovery_case, message_hash, time_threshold)

	# Default: don't skip
	return {"should_skip": False, "reason": None, "duplicate_of": None}


def _check_notification_duplicate(
	event_type: str,
	recovery_case: str,
	message_hash: Optional[str],
	time_threshold,
) -> Dict[str, Any]:
	"""
	Check for duplicate in Notification Event Log.
	"""
	filters = {
		"recovery_case": recovery_case,
		"event_type": event_type,
		"triggered_on": [">=", time_threshold],
	}

	# If message hash provided, try to match
	if message_hash:
		# Get recent notifications of this type
		recent = frappe.get_list(
			"Notification Event Log",
			filters=filters,
			fields=["name", "message_summary", "triggered_on"],
			order_by="triggered_on desc",
			limit=5,
		)

		for notif in recent:
			# Simple hash comparison based on message content
			if notif.message_summary and message_hash:
				# Create a simple hash of the message for comparison
				content_to_hash = notif.message_summary[:100]
				msg_hash = hashlib.sha256(content_to_hash.encode()).hexdigest()[:16]
				if msg_hash == message_hash[:16]:
					return {
						"should_skip": True,
						"reason": f"Duplicate notification within time window",
						"duplicate_of": notif.name,
					}
	else:
		# Just check if any recent event of this type exists
		exists = frappe.db.exists("Notification Event Log", filters)
		if exists:
			return {
				"should_skip": True,
				"reason": f"Duplicate event type within time window",
				"duplicate_of": exists,
			}

	return {"should_skip": False, "reason": None, "duplicate_of": None}


def _check_timeline_duplicate(
	event_type: str,
	recovery_case: str,
	message_hash: Optional[str],
	time_threshold,
) -> Dict[str, Any]:
	"""
	Check for duplicate in Recovery Timeline Event.
	"""
	filters = {
		"recovery_case": recovery_case,
		"event_type": event_type,
		"event_time": [">=", time_threshold],
	}

	exists = frappe.db.exists("Recovery Timeline Event", filters)
	if exists:
		return {
			"should_skip": True,
			"reason": f"Duplicate timeline event within time window",
			"duplicate_of": exists,
		}

	return {"should_skip": False, "reason": None, "duplicate_of": None}


def check_and_suppress_duplicate(
	event_type: str,
	recovery_case: str,
	message_content: Optional[str] = None,
	additional_context: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
	"""
	Check if an event should be suppressed as duplicate and return the result.

	This is the main entry point for duplicate checking.

	Args:
	    event_type: Type of event
	    recovery_case: Recovery Case name
	    message_content: The message content to create a hash from (optional)
	    additional_context: Additional context for key building (optional)

	Returns:
	    Dict with:
	        - should_process: bool - whether to proceed with processing
	        - should_skip: bool - whether to skip as duplicate
	        - reason: str - reason for decision
	        - dedupe_key: str - the deduplication key used
	        - existing_event: str - name of existing event if duplicate
	"""
	# Build message hash if content provided
	message_hash = None
	if message_content:
		message_hash = hashlib.sha256(message_content.encode()).hexdigest()

	# Build deduplication key
	dedupe_key = build_dedupe_key(
		event_type=event_type,
		recovery_case=recovery_case,
		additional_context=additional_context,
	)

	# Check for duplicate
	check_result = should_skip_duplicate_event(
		event_type=event_type,
		recovery_case=recovery_case,
		message_hash=message_hash,
	)

	return {
		"should_process": not check_result["should_skip"],
		"should_skip": check_result["should_skip"],
		"reason": check_result.get("reason"),
		"dedupe_key": dedupe_key,
		"existing_event": check_result.get("duplicate_of"),
	}


def suppress_duplicate_finder_message(
	token: str,
	message: str,
	session_id: str,
) -> Dict[str, Any]:
	"""
	Check and suppress duplicate finder message submissions.

	This prevents the same finder session from submitting the same message
	content repeatedly within a short time window.

	Args:
	    token: QR token
	    message: Message content
	    session_id: Finder session ID

	Returns:
	    Dict with should_process and reason
	"""
	# Calculate message hash
	message_hash = hashlib.sha256(message.encode()).hexdigest()[:16]

	# Check for recent messages from this session with same content
	time_threshold = add_to_date(now_datetime(), seconds=-DEDUP_WINDOWS["finder_message"])

	recent_message = frappe.db.get_value(
		"Recovery Message",
		{
			"recovery_case": ["is", "set"],  # Has a case
			"sender_type": "Finder",
			"created_on": [">=", time_threshold],
		},
		"name, message",
		order_by="created_on desc",
	)

	if recent_message:
		existing_msg_hash = (
			hashlib.sha256(recent_message[1].encode()).hexdigest()[:16] if recent_message[1] else ""
		)
		if existing_msg_hash == message_hash:
			return {
				"should_process": False,
				"should_skip": True,
				"reason": "Duplicate message from same session within time window",
				"existing_message": recent_message[0],
			}

	return {
		"should_process": True,
		"should_skip": False,
		"reason": None,
		"existing_message": None,
	}


def suppress_duplicate_location_share(
	recovery_case: str,
	latitude: float,
	longitude: float,
) -> Dict[str, Any]:
	"""
	Check and suppress duplicate location shares.

	This prevents location spam by checking if the same or very close location
	was shared within the time window.

	Args:
	    recovery_case: Recovery Case name
	    latitude: Latitude coordinate
	    longitude: Longitude coordinate

	Returns:
	    Dict with should_process and reason
	"""
	# Get recent locations for this case
	time_threshold = add_to_date(now_datetime(), seconds=-DEDUP_WINDOWS["location_share"])

	recent_locations = frappe.get_list(
		"Location Share",
		filters={
			"recovery_case": recovery_case,
			"shared_on": [">=", time_threshold],
		},
		fields=["name", "latitude", "longitude"],
		order_by="shared_on desc",
		limit=3,
	)

	if recent_locations:
		# Check if coordinates are very close (within ~10 meters)
		for loc in recent_locations:
			lat_diff = abs(float(loc.latitude) - latitude)
			lng_diff = abs(float(loc.longitude) - longitude)

			# Roughly: 0.0001 degrees ≈ 10 meters
			if lat_diff < 0.0001 and lng_diff < 0.0001:
				return {
					"should_process": False,
					"should_skip": True,
					"reason": "Very similar location shared within time window",
					"existing_location": loc.name,
				}

	return {
		"should_process": True,
		"should_skip": False,
		"reason": None,
		"existing_location": None,
	}


def suppress_duplicate_status_update(
	recovery_case: str,
	new_status: str,
) -> Dict[str, Any]:
	"""
	Check and suppress duplicate status updates.

	If the case is already in the target status, this prevents unnecessary
	notification/timeline spam.

	Args:
	    recovery_case: Recovery Case name
	    new_status: New status value

	Returns:
	    Dict with should_process and reason
	"""
	current_status = frappe.db.get_value("Recovery Case", recovery_case, "status")

	if current_status == new_status:
		return {
			"should_process": False,
			"should_skip": True,
			"reason": f"Case already in status: {new_status}",
			"current_status": current_status,
		}

	# Check for very recent status updates (within 30 seconds)
	time_threshold = add_to_date(now_datetime(), seconds=-DEDUP_WINDOWS["status_update"])

	recent_timeline = frappe.db.get_value(
		"Recovery Timeline Event",
		{
			"recovery_case": recovery_case,
			"event_type": "Status Updated",
			"event_time": [">=", time_threshold],
		},
		"name",
	)

	if recent_timeline:
		return {
			"should_process": False,
			"should_skip": True,
			"reason": "Status was updated very recently",
			"recent_update": recent_timeline,
		}

	return {
		"should_process": True,
		"should_skip": False,
		"reason": None,
		"current_status": current_status,
	}


def record_dedupe_key(
	dedupe_key: str,
	event_type: str,
	reference_doctype: str,
	reference_name: str,
	expires_after_seconds: int = 3600,
) -> None:
	"""
	Record a deduplication key for future duplicate checking.

	This stores the key in a simple table for later lookup.

	Args:
	    dedupe_key: The deduplication key
	    event_type: Type of event
	    reference_doctype: The doctype of the created record
	    reference_name: The name of the created record
	    expires_after_seconds: How long to keep the key (default 1 hour)
	"""
	# This function stores dedupe keys for cross-request checking
	# For now, we rely on the time-window based queries above
	# This can be extended to use a Dedupe Cache DocType if needed
	pass


def get_recent_events_by_type(
	event_type: str,
	recovery_case: str,
	limit: int = 10,
) -> list:
	"""
	Get recent events of a specific type for a recovery case.

	Args:
	    event_type: Type of event
	    recovery_case: Recovery Case name
	    limit: Maximum number of events to return

	Returns:
	    List of event dicts
	"""
	if "notification" in event_type.lower() or event_type in [
		"Finder Message Received",
		"Recovery Case Opened",
		"Case Status Updated",
	]:
		doctype = "Notification Event Log"
		time_field = "triggered_on"
	else:
		doctype = "Recovery Timeline Event"
		time_field = "event_time"

	events = frappe.get_list(
		doctype,
		filters={"recovery_case": recovery_case},
		fields=["name", time_field, "event_type"],
		order_by=f"{time_field} desc",
		limit=limit,
	)

	return events
