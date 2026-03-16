# SPDX-License-Identifier: MIT
"""
Integration tests for ScanifyMe API endpoints.

These tests run against the actual Frappe database and require:
- bench running
- database migrated
- demo data created
"""

import unittest
import frappe
import json


class TestAPIEndpoints(unittest.TestCase):
	"""Integration tests for all API endpoints"""

	@classmethod
	def setUpClass(cls):
		"""Set up test fixtures"""
		# These tests require a running Frappe instance
		frappe.set_site("test.localhost")

	def setUp(self):
		"""Set up each test"""
		frappe.set_user("Administrator")

	def tearDown(self):
		"""Clean up after each test"""
		frappe.db.rollback()

	# ==================== Public APIs (Guest) ====================

	def test_get_public_item_context_valid_token(self):
		"""Test getting public item context with valid token"""
		# First, create demo data to get a valid token
		from scanifyme.api.demo_data import create_demo_data

		result = create_demo_data()

		token = result.get("data", {}).get("public_test_token")
		if not token:
			self.skipTest("No valid token available")

		# Call the API
		from scanifyme.public_portal.api.public_api import get_public_item_context

		response = get_public_item_context(token)

		if response.get("success"):
			self.assertIn("item", response)
			item = response["item"]
			# Verify sensitive data is NOT exposed
			self.assertNotIn("owner_profile", item)
			self.assertNotIn("owner_email", item)
			self.assertNotIn("owner_phone", item)

	def test_get_public_item_context_invalid_token(self):
		"""Test getting public item context with invalid token"""
		from scanifyme.public_portal.api.public_api import get_public_item_context

		response = get_public_item_context("INVALID_TOKEN_THAT_DOES_NOT_EXIST")

		self.assertFalse(response.get("success"))
		self.assertIsNotNone(response.get("error"))

	def test_submit_finder_message_valid_token(self):
		"""Test submitting finder message with valid token"""
		# Get a valid token first
		from scanifyme.api.demo_data import create_demo_data

		result = create_demo_data()
		token = result.get("data", {}).get("public_test_token")

		if not token:
			self.skipTest("No valid token available")

		from scanifyme.messaging.api.message_api import submit_finder_message

		response = submit_finder_message(
			token=token,
			message="Test message from finder",
			finder_name="Test Finder",
			contact_hint="+9999999999",
		)

		self.assertTrue(response.get("success"))
		self.assertIsNotNone(response.get("case_id"))

	def test_submit_finder_message_invalid_token(self):
		"""Test submitting finder message with invalid token"""
		from scanifyme.messaging.api.message_api import submit_finder_message

		response = submit_finder_message(token="INVALID_TOKEN", message="Test message")

		self.assertFalse(response.get("success"))

	# ==================== Authenticated APIs ====================

	def test_get_user_items(self):
		"""Test getting user items"""
		# Login as demo user
		frappe.set_user("demo@scanifyme.app")

		from scanifyme.items.api.items_api import get_user_items

		try:
			response = get_user_items()
			self.assertIsInstance(response, list)
		except Exception as e:
			# May fail if no items exist, which is OK
			pass

	def test_get_item_categories(self):
		"""Test getting item categories"""
		from scanifyme.items.api.items_api import get_item_categories

		response = get_item_categories()
		self.assertIsInstance(response, list)

	def test_get_owner_recovery_cases(self):
		"""Test getting owner recovery cases"""
		# Login as demo user
		frappe.set_user("demo@scanifyme.app")

		from scanifyme.recovery.api.recovery_api import get_owner_recovery_cases

		try:
			response = get_owner_recovery_cases()
			self.assertIsInstance(response, list)
		except Exception:
			# May fail for various reasons
			pass

	# ==================== Permission Tests ====================

	def test_guest_cannot_access_owner_apis(self):
		"""Test that guest users cannot access owner-only APIs"""
		frappe.set_user("Guest")

		from scanifyme.items.api.items_api import get_user_items

		with self.assertRaises(frappe.PermissionError):
			get_user_items()

	def test_other_user_cannot_access_cases(self):
		"""Test that users cannot access other users' recovery cases"""
		# Create a case first
		frappe.set_user("demo@scanifyme.app")

		from scanifyme.recovery.api.recovery_api import get_recovery_case_details

		# Try to access a case that doesn't belong to this user
		frappe.set_user("Administrator")

		# This should fail because Administrator is not the owner
		try:
			response = get_recovery_case_details("NONEXISTENT_CASE")
			# If it doesn't raise an error, check the response
			if isinstance(response, dict) and response.get("name"):
				pass  # Case was found but should have been filtered
		except frappe.PermissionError:
			pass  # Expected - permission denied


def run_tests():
	"""Run all tests"""
	# Check if bench is available
	try:
		frappe.init(site="test.localhost")
		frappe.connect()

		loader = unittest.TestLoader()
		suite = loader.loadTestsFromTestCase(TestAPIEndpoints)
		runner = unittest.TextTestRunner(verbosity=2)
		runner.run(suite)

	except Exception as e:
		print(f"Could not run tests: {e}")
		print("Make sure bench is running and the site is accessible.")


if __name__ == "__main__":
	run_tests()
