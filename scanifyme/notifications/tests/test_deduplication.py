"""
Tests for Deduplication Service.

These tests verify the idempotency and duplicate suppression functionality.
"""

import frappe
import unittest
from frappe.utils import now_datetime, add_to_date
from unittest.mock import patch, MagicMock


class TestDeduplicationService(unittest.TestCase):
	"""Test cases for deduplication service."""

	@classmethod
	def setUpClass(cls):
		"""Set up test fixtures."""
		frappe.set_user("Administrator")

	def test_build_dedupe_key(self):
		"""Test deduplication key generation."""
		from scanifyme.notifications.services.deduplication_service import (
			build_dedupe_key,
		)

		key1 = build_dedupe_key(
			event_type="finder_message",
			recovery_case="TEST-CASE-001",
		)

		# Same inputs should produce same key
		key2 = build_dedupe_key(
			event_type="finder_message",
			recovery_case="TEST-CASE-001",
		)

		self.assertEqual(key1, key2)

		# Different inputs should produce different keys
		key3 = build_dedupe_key(
			event_type="finder_message",
			recovery_case="TEST-CASE-002",
		)

		self.assertNotEqual(key1, key3)

	def test_build_dedupe_key_with_context(self):
		"""Test deduplication key with additional context."""
		from scanifyme.notifications.services.deduplication_service import (
			build_dedupe_key,
		)

		key1 = build_dedupe_key(
			event_type="notification",
			recovery_case="TEST-CASE-001",
			additional_context={"message": "Hello"},
		)

		key2 = build_dedupe_key(
			event_type="notification",
			recovery_case="TEST-CASE-001",
			additional_context={"message": "Hello"},
		)

		self.assertEqual(key1, key2)

	def test_get_dedup_window_seconds(self):
		"""Test deduplication window retrieval."""
		from scanifyme.notifications.services.deduplication_service import (
			get_dedup_window_seconds,
		)

		# Test event type mappings
		finder_msg_window = get_dedup_window_seconds("Finder Message Received")
		self.assertEqual(finder_msg_window, 60)  # 1 minute

		location_window = get_dedup_window_seconds("Location Shared")
		self.assertEqual(location_window, 120)  # 2 minutes

		status_window = get_dedup_window_seconds("Case Status Updated")
		self.assertEqual(status_window, 30)  # 30 seconds

	def test_should_skip_duplicate_event_no_existing(self):
		"""Test that duplicate check returns false when no existing events."""
		from scanifyme.notifications.services.deduplication_service import (
			should_skip_duplicate_event,
		)

		# Mock the database to return no existing events
		with patch("frappe.db.exists", return_value=False):
			result = should_skip_duplicate_event(
				event_type="Finder Message Received",
				recovery_case="NONEXISTENT-CASE",
			)

			self.assertFalse(result["should_skip"])
			self.assertIsNone(result["reason"])

	def test_suppress_duplicate_status_update_same_status(self):
		"""Test that status update to same value is suppressed."""
		from scanifyme.notifications.services.deduplication_service import (
			suppress_duplicate_status_update,
		)

		# Mock the database to return current status
		with patch.object(frappe.db, "get_value", return_value="Open"):
			result = suppress_duplicate_status_update(
				recovery_case="TEST-CASE-001",
				new_status="Open",
			)

			self.assertFalse(result["should_process"])
			self.assertTrue(result["should_skip"])
			self.assertIn("already in status", result["reason"])

	def test_suppress_duplicate_status_update_different_status(self):
		"""Test that status update to different value is allowed."""
		from scanifyme.notifications.services.deduplication_service import (
			suppress_duplicate_status_update,
		)

		# Mock the database to return different current status
		with patch.object(frappe.db, "get_value", return_value="Open"):
			result = suppress_duplicate_status_update(
				recovery_case="TEST-CASE-001",
				new_status="Recovered",
			)

			self.assertTrue(result["should_process"])
			self.assertFalse(result["should_skip"])
			self.assertEqual(result["current_status"], "Open")


class TestReliabilityService(unittest.TestCase):
	"""Test cases for reliability service."""

	@classmethod
	def setUpClass(cls):
		"""Set up test fixtures."""
		frappe.set_user("Administrator")

	def test_safe_create_notification_event_structure(self):
		"""Test that safe notification creation returns proper structure."""
		from scanifyme.notifications.services.reliability_service import (
			safe_create_notification_event,
		)

		# Mock the notification service
		with patch(
			"scanifyme.notifications.services.notification_service.log_notification_event"
		) as mock_log:
			mock_log.return_value = "TEST-NOTIF-001"

			result = safe_create_notification_event(
				event_type="Finder Message Received",
				owner_profile="TEST-OWNER",
				recovery_case="TEST-CASE",
			)

			self.assertTrue(result["success"])
			self.assertEqual(result["notification_id"], "TEST-NOTIF-001")
			self.assertEqual(result["status"], "Created")

	def test_safe_create_notification_event_error_handling(self):
		"""Test error handling in safe notification creation."""
		from scanifyme.notifications.services.reliability_service import (
			safe_create_notification_event,
		)

		# Mock to raise an exception
		with patch(
			"scanifyme.notifications.services.notification_service.log_notification_event",
			side_effect=Exception("Test error"),
		):
			result = safe_create_notification_event(
				event_type="Finder Message Received",
				owner_profile="TEST-OWNER",
			)

			self.assertFalse(result["success"])
			self.assertIn("error", result)
			self.assertEqual(result["status"], "Failed")

	def test_safe_queue_email_notification_disabled(self):
		"""Test email queue when notifications are disabled."""
		from scanifyme.notifications.services.reliability_service import (
			safe_queue_email_notification,
		)

		# Mock to return disabled preferences
		with patch(
			"scanifyme.notifications.services.notification_service.get_owner_notification_preferences",
			return_value={"enable_email_notifications": False},
		):
			result = safe_queue_email_notification(
				event_type="Finder Message Received",
				owner_profile="TEST-OWNER",
			)

			self.assertTrue(result["success"])
			self.assertEqual(result["status"], "Skipped")

	def test_safe_create_timeline_event_structure(self):
		"""Test that safe timeline creation returns proper structure."""
		from scanifyme.notifications.services.reliability_service import (
			safe_create_timeline_event,
		)

		# Mock the timeline service
		with patch("scanifyme.recovery.services.timeline_service.create_timeline_event") as mock_create:
			mock_create.return_value = "TEST-TIMELINE-001"

			result = safe_create_timeline_event(
				recovery_case="TEST-CASE-001",
				event_type="Finder Message",
				actor_type="Finder",
			)

			self.assertTrue(result["success"])
			self.assertEqual(result["event_id"], "TEST-TIMELINE-001")
			self.assertEqual(result["status"], "Created")


class TestCleanupService(unittest.TestCase):
	"""Test cases for cleanup service."""

	@classmethod
	def setUpClass(cls):
		"""Set up test fixtures."""
		frappe.set_user("Administrator")

	def test_get_operational_health_summary_structure(self):
		"""Test that operational health summary returns proper structure."""
		from scanifyme.recovery.services.cleanup_service import (
			get_operational_health_summary,
		)

		# Mock database counts
		with patch.object(frappe.db, "count", return_value=5):
			with patch(
				"scanifyme.recovery.services.cleanup_service.health_check_notification_backlog",
				return_value={"success": True, "health_status": "healthy", "backlog": {}},
			):
				result = get_operational_health_summary()

				self.assertTrue(result["success"])
				self.assertIn("overall_status", result)
				self.assertIn("finder_sessions", result)
				self.assertIn("recovery_cases", result)

	def test_cleanup_cache_no_op(self):
		"""Test that cache cleanup returns success (no-op)."""
		from scanifyme.recovery.services.cleanup_service import (
			cleanup_duplicate_suppression_cache,
		)

		result = cleanup_duplicate_suppression_cache()

		self.assertTrue(result["success"])
		self.assertEqual(result["cleaned"], 0)
		self.assertIn("time-window deduplication", result["message"])


class TestNotificationBacklog(unittest.TestCase):
	"""Test cases for notification backlog handling."""

	@classmethod
	def setUpClass(cls):
		"""Set up test fixtures."""
		frappe.set_user("Administrator")

	def test_get_notification_backlog(self):
		"""Test notification backlog retrieval."""
		from scanifyme.notifications.services.reliability_service import (
			get_notification_backlog,
		)

		# Mock database counts
		with patch.object(frappe.db, "count", return_value=3):
			result = get_notification_backlog()

			self.assertTrue(result["success"])
			self.assertIn("backlog", result)

	def test_health_check_notification_backlog_healthy(self):
		"""Test health check with healthy status."""
		from scanifyme.recovery.services.cleanup_service import (
			health_check_notification_backlog,
		)

		with patch.object(frappe.db, "count", return_value=2):
			with patch(
				"scanifyme.recovery.services.cleanup_service.get_notification_backlog",
				return_value={
					"success": True,
					"backlog": {"failed": 0, "queued": 5},
					"recent_failures": [],
				},
			):
				result = health_check_notification_backlog()

				self.assertTrue(result["success"])
				self.assertEqual(result["health_status"], "healthy")

	def test_health_check_notification_backlog_warning(self):
		"""Test health check with warning status."""
		from scanifyme.recovery.services.cleanup_service import (
			health_check_notification_backlog,
		)

		with patch(
			"scanifyme.recovery.services.cleanup_service.get_notification_backlog",
			return_value={
				"success": True,
				"backlog": {"failed": 7, "queued": 50},
				"recent_failures": [],
			},
		):
			result = health_check_notification_backlog()

			self.assertTrue(result["success"])
			self.assertEqual(result["health_status"], "warning")

	def test_health_check_notification_backlog_critical(self):
		"""Test health check with critical status."""
		from scanifyme.recovery.services.cleanup_service import (
			health_check_notification_backlog,
		)

		with patch(
			"scanifyme.recovery.services.cleanup_service.get_notification_backlog",
			return_value={
				"success": True,
				"backlog": {"failed": 15, "queued": 200},
				"recent_failures": [],
			},
		):
			result = health_check_notification_backlog()

			self.assertTrue(result["success"])
			self.assertEqual(result["health_status"], "critical")


if __name__ == "__main__":
	unittest.main()
