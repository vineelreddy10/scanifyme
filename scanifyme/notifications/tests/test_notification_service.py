# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import frappe
import unittest
from frappe.utils import now_datetime


class TestNotificationService(unittest.TestCase):
	"""Test cases for notification service."""

	@classmethod
	def setUpClass(cls):
		"""Set up test fixtures."""
		# Create test owner profile
		if not frappe.db.exists("Owner Profile", {"user": "test_notification@example.com"}):
			cls.test_owner = frappe.get_doc(
				{
					"doctype": "Owner Profile",
					"user": "test_notification@example.com",
					"display_name": "Test Notification User",
					"phone": "+1234567890",
					"address": "Test Address",
					"is_verified": 1,
				}
			)
			cls.test_owner.insert(ignore_permissions=True)
		else:
			cls.test_owner = frappe.get_doc("Owner Profile", {"user": "test_notification@example.com"})

		# Create test notification preference
		if not frappe.db.exists("Notification Preference", {"owner_profile": cls.test_owner.name}):
			cls.test_pref = frappe.get_doc(
				{
					"doctype": "Notification Preference",
					"owner_profile": cls.test_owner.name,
					"enable_in_app_notifications": 1,
					"enable_email_notifications": 1,
					"notify_on_new_finder_message": 1,
					"notify_on_case_opened": 1,
					"notify_on_case_status_change": 1,
					"is_default": 1,
				}
			)
			cls.test_pref.insert(ignore_permissions=True)

		frappe.db.commit()

	def test_log_notification_event(self):
		"""Test logging a notification event."""
		from scanifyme.notifications.services.notification_service import log_notification_event

		notification_id = log_notification_event(
			event_type="Finder Message Received",
			owner_profile=self.test_owner.name,
			message_summary="Test message summary",
			channel="In App",
			status="Sent",
			title="Test Notification",
			route="/frontend/recovery/test-case",
			priority="Normal",
		)

		self.assertIsNotNone(notification_id)

		# Verify the notification was created
		notification = frappe.get_doc("Notification Event Log", notification_id)
		self.assertEqual(notification.event_type, "Finder Message Received")
		self.assertEqual(notification.owner_profile, self.test_owner.name)
		self.assertEqual(notification.title, "Test Notification")
		self.assertEqual(notification.route, "/frontend/recovery/test-case")
		self.assertEqual(notification.priority, "Normal")
		self.assertEqual(notification.is_read, 0)

	def test_get_owner_notifications(self):
		"""Test getting owner notifications."""
		from scanifyme.notifications.services.notification_service import (
			get_owner_notifications,
			log_notification_event,
		)

		# Create a test notification
		notification_id = log_notification_event(
			event_type="Recovery Case Opened",
			owner_profile=self.test_owner.name,
			message_summary="Test case opened",
			channel="In App",
			status="Sent",
			title="New Recovery Case",
			route="/frontend/recovery/test-case-2",
			priority="High",
		)

		# Get notifications
		notifications = get_owner_notifications(self.test_owner.name)

		self.assertIsInstance(notifications, list)
		self.assertGreater(len(notifications), 0)

		# Verify the notification we created is in the list
		found = any(n["name"] == notification_id for n in notifications)
		self.assertTrue(found)

	def test_get_unread_notification_count(self):
		"""Test getting unread notification count."""
		from scanifyme.notifications.services.notification_service import (
			get_unread_notification_count,
			log_notification_event,
		)

		# Create an unread notification
		notification_id = log_notification_event(
			event_type="Finder Message Received",
			owner_profile=self.test_owner.name,
			message_summary="Unread test message",
			channel="In App",
			status="Sent",
			title="Unread Notification",
			route="/frontend/recovery/test-case-3",
			priority="Normal",
		)

		# Get unread count
		count = get_unread_notification_count(self.test_owner.name)

		self.assertIsInstance(count, int)
		self.assertGreater(count, 0)

	def test_mark_notification_read(self):
		"""Test marking a notification as read."""
		from scanifyme.notifications.services.notification_service import (
			mark_notification_read,
			log_notification_event,
		)

		# Create an unread notification
		notification_id = log_notification_event(
			event_type="Case Status Updated",
			owner_profile=self.test_owner.name,
			message_summary="Status update test",
			channel="In App",
			status="Sent",
			title="Status Update",
			route="/frontend/recovery/test-case-4",
			priority="Normal",
		)

		# Mark as read
		result = mark_notification_read(notification_id, self.test_owner.name)

		self.assertTrue(result["success"])

		# Verify it's marked as read
		notification = frappe.get_doc("Notification Event Log", notification_id)
		self.assertEqual(notification.is_read, 1)
		self.assertIsNotNone(notification.read_on)

	def test_mark_all_notifications_read(self):
		"""Test marking all notifications as read."""
		from scanifyme.notifications.services.notification_service import (
			mark_all_notifications_read,
			get_unread_notification_count,
		)

		# Get initial count
		initial_count = get_unread_notification_count(self.test_owner.name)

		# Mark all as read
		result = mark_all_notifications_read(self.test_owner.name)

		self.assertTrue(result["success"])
		self.assertGreater(result["count"], 0)

		# Verify all are read
		final_count = get_unread_notification_count(self.test_owner.name)
		self.assertEqual(final_count, 0)

	def test_should_notify_owner(self):
		"""Test notification preference checking."""
		from scanifyme.notifications.services.notification_service import (
			should_notify_owner,
			get_owner_notification_preferences,
		)

		# Get preferences
		preferences = get_owner_notification_preferences(self.test_owner.name)

		# Should notify for enabled preferences
		self.assertTrue(should_notify_owner("Finder Message Received", preferences))
		self.assertTrue(should_notify_owner("Recovery Case Opened", preferences))
		self.assertTrue(should_notify_owner("Case Status Updated", preferences))

		# Test with disabled preferences
		disabled_prefs = {
			"enable_in_app_notifications": True,
			"notify_on_new_finder_message": False,
			"notify_on_case_opened": True,
			"notify_on_case_status_change": True,
		}
		self.assertFalse(should_notify_owner("Finder Message Received", disabled_prefs))

		# Test with no preferences (should allow)
		self.assertTrue(should_notify_owner("Finder Message Received", None))


def create_notification_tests():
	"""Create test cases for the test runner."""
	return [
		{
			"tests": [
				"test_log_notification_event",
				"test_get_owner_notifications",
				"test_get_unread_notification_count",
				"test_mark_notification_read",
				"test_mark_all_notifications_read",
				"test_should_notify_owner",
			]
		}
	]
