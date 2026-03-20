# SPDX-License-Identifier: MIT

"""Unit tests for the onboarding service module."""

import unittest
import frappe
from scanifyme.onboarding.services.onboarding_service import (
	compute_onboarding_state,
	persist_onboarding_state,
	compute_owner_next_actions,
	get_incomplete_onboarding_summary,
	trigger_onboarding_recompute,
)


class TestOnboardingService(unittest.TestCase):
	"""Tests for onboarding service functions."""

	_test_user = "test_onboarding_owner@test.scanifyme"

	@classmethod
	def setUpClass(cls):
		"""Create test user and owner profile once for all tests."""
		frappe.set_user("Administrator")

		# Create test user if not exists
		if not frappe.db.exists("User", cls._test_user):
			user = frappe.get_doc(
				{
					"doctype": "User",
					"email": cls._test_user,
					"first_name": "Test",
					"last_name": "Owner",
					"send_welcome_email": 0,
					"user_type": "Website User",
				}
			)
			user.insert(ignore_permissions=True)
			frappe.db.commit()

		# Create test owner profile if not exists
		if not frappe.db.exists("Owner Profile", cls._test_user):
			profile = frappe.get_doc(
				{
					"doctype": "Owner Profile",
					"user": cls._test_user,
					"display_name": "Test Onboarding Owner",
				}
			)
			profile.insert(ignore_permissions=True)
			frappe.db.commit()

	def setUp(self):
		"""Set up test fixtures."""
		self.admin_user = "Administrator"
		frappe.set_user("Administrator")

	def tearDown(self):
		"""Clean up after tests."""
		frappe.set_user("Administrator")
		# Clean up test onboarding state if it exists
		if frappe.db.exists("Owner Onboarding State", self._test_user):
			frappe.delete_doc("Owner Onboarding State", self._test_user, force=True)
			frappe.db.commit()

	@classmethod
	def tearDownClass(cls):
		"""Clean up test data after all tests."""
		frappe.set_user("Administrator")
		if frappe.db.exists("Owner Onboarding State", cls._test_user):
			frappe.delete_doc("Owner Onboarding State", cls._test_user, force=True)
		if frappe.db.exists("Owner Profile", cls._test_user):
			frappe.delete_doc("Owner Profile", cls._test_user, force=True)
		if frappe.db.exists("User", cls._test_user):
			frappe.delete_doc("User", cls._test_user, force=True)
		frappe.db.commit()

	def test_get_onboarding_state_admin_returns_full(self):
		"""Admin user gets 100% completion state."""
		result = compute_onboarding_state("Administrator")

		self.assertTrue(result["account_created"])
		self.assertTrue(result["profile_completed"])
		self.assertTrue(result["qr_activated"])
		self.assertTrue(result["item_registered"])
		self.assertTrue(result["recovery_note_added"])
		self.assertTrue(result["notifications_configured"])
		self.assertTrue(result["reward_reviewed"])
		self.assertTrue(result["onboarding_completed"])
		self.assertEqual(result["completion_percent"], 100.0)

	def test_get_onboarding_state_empty_profile(self):
		"""Non-existent profile returns empty/zero state."""
		result = compute_onboarding_state("NonExistentOwner@nonexistent.app")

		self.assertFalse(result["account_created"])
		self.assertFalse(result["profile_completed"])
		self.assertFalse(result["qr_activated"])
		self.assertFalse(result["item_registered"])
		self.assertFalse(result["recovery_note_added"])
		self.assertFalse(result["notifications_configured"])
		self.assertFalse(result["reward_reviewed"])
		self.assertFalse(result["onboarding_completed"])
		self.assertEqual(result["completion_percent"], 0.0)

	def test_recompute_creates_doc(self):
		"""persist_onboarding_state creates Owner Onboarding State doc for real profile."""
		test_profile = self._test_user

		# Clean up if exists
		if frappe.db.exists("Owner Onboarding State", test_profile):
			frappe.delete_doc("Owner Onboarding State", test_profile, force=True)
			frappe.db.commit()

		result = persist_onboarding_state(test_profile)

		self.assertTrue(result["success"])
		self.assertEqual(result["message"], "Onboarding state created")
		self.assertIn("state", result)
		self.assertFalse(result["state"]["onboarding_completed"])

		# Verify doc was created
		self.assertTrue(frappe.db.exists("Owner Onboarding State", test_profile))

	def test_recompute_updates_existing(self):
		"""Second persist call updates the existing doc."""
		test_profile = self._test_user

		if frappe.db.exists("Owner Onboarding State", test_profile):
			frappe.delete_doc("Owner Onboarding State", test_profile, force=True)
			frappe.db.commit()

		# First call - creates
		result1 = persist_onboarding_state(test_profile)
		self.assertEqual(result1["message"], "Onboarding state created")

		# Second call - updates
		result2 = persist_onboarding_state(test_profile)
		self.assertTrue(result2["success"])
		self.assertEqual(result2["message"], "Onboarding state updated")

	def test_next_actions_empty_for_admin(self):
		"""Admin user gets empty next actions list."""
		result = compute_owner_next_actions("Administrator")

		self.assertIsInstance(result, list)
		self.assertEqual(len(result), 0)

	def test_next_actions_sorted_by_priority(self):
		"""Next actions are returned sorted by priority (ascending)."""
		test_profile = self._test_user

		# First create the onboarding state
		if not frappe.db.exists("Owner Onboarding State", test_profile):
			persist_onboarding_state(test_profile)

		result = compute_owner_next_actions(test_profile)

		if len(result) > 1:
			priorities = [a["priority"] for a in result]
			self.assertEqual(priorities, sorted(priorities), "Actions should be sorted by priority")

	def test_next_actions_structure(self):
		"""Each next action has required fields."""
		test_profile = self._test_user

		if not frappe.db.exists("Owner Onboarding State", test_profile):
			persist_onboarding_state(test_profile)

		result = compute_owner_next_actions(test_profile)

		required_fields = {"action_key", "title", "description", "route", "priority"}
		for action in result:
			self.assertEqual(required_fields, set(action.keys()), f"Action missing fields: {action}")

	def test_next_actions_missing_qr(self):
		"""Owner with no QR gets QR activation as first action."""
		test_profile = self._test_user

		if not frappe.db.exists("Owner Onboarding State", test_profile):
			persist_onboarding_state(test_profile)

		result = compute_owner_next_actions(test_profile)

		# Owner has no items/QR, so first action should be about QR
		if len(result) > 0:
			first_action = result[0]
			self.assertIn("qr", first_action["action_key"].lower())

	def test_trigger_onboarding_skips_admin(self):
		"""trigger_onboarding_recompute with admin does not error."""
		# Should not raise
		trigger_onboarding_recompute("Administrator")
		# If we get here without error, test passes

	def test_trigger_onboarding_works(self):
		"""trigger_onboarding_recompute creates state doc for real owner profile."""
		test_profile = self._test_user

		if frappe.db.exists("Owner Onboarding State", test_profile):
			frappe.delete_doc("Owner Onboarding State", test_profile, force=True)
			frappe.db.commit()

		trigger_onboarding_recompute(test_profile)

		self.assertTrue(frappe.db.exists("Owner Onboarding State", test_profile))

	def test_incomplete_summary_returns_list(self):
		"""get_incomplete_onboarding_summary returns a list."""
		result = get_incomplete_onboarding_summary()

		self.assertIsInstance(result, list)

	def test_incomplete_summary_filters_work(self):
		"""Filter parameters narrow down the results."""
		# Get all incomplete
		all_results = get_incomplete_onboarding_summary()

		# Filter by max_percent=10 (should get very few or none)
		filtered = get_incomplete_onboarding_summary(filters={"max_percent": 10})

		self.assertIsInstance(filtered, list)
		# Filtered should have same or fewer results
		self.assertLessEqual(len(filtered), len(all_results))

		# Each result should have required fields
		required_fields = {
			"owner_profile",
			"completion_percent",
			"onboarding_completed",
			"missing_steps",
		}
		for item in filtered:
			self.assertEqual(required_fields, set(item.keys()))


if __name__ == "__main__":
	unittest.main()
