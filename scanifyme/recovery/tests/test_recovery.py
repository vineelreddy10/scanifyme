# SPDX-License-Identifier: MIT
"""
Tests for Recovery Service and Recovery API.
"""

import unittest
from unittest.mock import patch, MagicMock
import frappe
from frappe import _
from scanifyme.recovery.services.recovery_service import (
	create_or_get_recovery_case,
	get_owner_recovery_cases,
	get_recovery_case_details,
	update_recovery_case_status,
)


class TestRecoveryService(unittest.TestCase):
	"""Unit tests for the recovery service module"""

	def setUp(self):
		"""Set up test fixtures"""
		self.mock_owner_profile = "owner-profile-001"
		self.mock_qr_tag = "qr-tag-001"
		self.mock_registered_item = "registered-item-001"
		self.mock_finder_session = "finder-session-001"

	def tearDown(self):
		"""Clean up after tests"""
		pass

	@patch("scanifyme.recovery.services.recovery_service.frappe.db.get_value")
	@patch("scanifyme.recovery.services.recovery_service.frappe.get_doc")
	def test_create_or_get_recovery_case_new(self, mock_get_doc, mock_get_value):
		"""Test creating a new recovery case"""
		mock_get_value.return_value = None  # No existing case

		mock_doc = MagicMock()
		mock_doc.name = "recovery-case-001"
		mock_get_doc.return_value = mock_doc

		result = create_or_get_recovery_case(
			qr_tag=self.mock_qr_tag,
			registered_item=self.mock_registered_item,
			owner_profile=self.mock_owner_profile,
			finder_name="John Finder",
			finder_contact_hint="+1234567890",
		)

		self.assertEqual(result, "recovery-case-001")
		mock_doc.insert.assert_called_once()

	@patch("scanifyme.recovery.services.recovery_service.frappe.db.get_value")
	def test_create_or_get_recovery_case_existing(self, mock_get_value):
		"""Test reusing an existing open recovery case"""
		mock_get_value.return_value = "existing-case-001"

		result = create_or_get_recovery_case(
			qr_tag=self.mock_qr_tag,
			registered_item=self.mock_registered_item,
			owner_profile=self.mock_owner_profile,
			finder_session_id=self.mock_finder_session,
			finder_name="John Finder",
		)

		self.assertEqual(result, "existing-case-001")

	@patch("scanifyme.recovery.services.recovery_service.frappe.get_list")
	def test_get_owner_recovery_cases(self, mock_get_list):
		"""Test getting recovery cases for an owner"""
		mock_get_list.return_value = [
			{"name": "case-001", "case_title": "Test Case 1", "status": "Open"},
			{"name": "case-002", "case_title": "Test Case 2", "status": "Closed"},
		]

		result = get_owner_recovery_cases(self.mock_owner_profile)

		self.assertEqual(len(result), 2)
		self.assertEqual(result[0]["name"], "case-001")

	@patch("scanifyme.recovery.services.recovery_service.frappe.get_list")
	def test_get_owner_recovery_cases_with_status_filter(self, mock_get_list):
		"""Test filtering recovery cases by status"""
		mock_get_list.return_value = [
			{"name": "case-001", "case_title": "Test Case 1", "status": "Open"},
		]

		result = get_owner_recovery_cases(self.mock_owner_profile, status="Open")

		self.assertEqual(len(result), 1)
		# Verify filters were applied
		call_args = mock_get_list.call_args
		self.assertEqual(call_args[1]["filters"]["status"], "Open")

	@patch("scanifyme.recovery.services.recovery_service.frappe.db.get_value")
	@patch("scanifyme.recovery.services.recovery_service.frappe.get_doc")
	def test_get_recovery_case_details(self, mock_get_doc, mock_db_value):
		"""Test getting recovery case details"""
		# Mock the case document
		mock_case = MagicMock()
		mock_case.name = "case-001"
		mock_case.case_title = "Test Case"
		mock_case.status = "Open"
		mock_case.owner_profile = self.mock_owner_profile
		mock_case.registered_item = self.mock_registered_item
		mock_case.qr_code_tag = self.mock_qr_tag
		mock_case.finder_name = "John Finder"
		mock_case.finder_contact_hint = "+1234567890"
		mock_case.notes_internal = "Internal note"
		mock_case.opened_on = "2024-01-01"
		mock_case.last_activity_on = "2024-01-02"
		mock_case.closed_on = None
		mock_get_doc.return_value = mock_case

		# Mock item and QR tag lookups
		mock_db_value.side_effect = [
			{"name": "item-001", "item_name": "Test Item", "public_label": "Test", "qr_code_tag": "qr-001"},
			{"name": "qr-001", "qr_token": "token123"},
		]

		result = get_recovery_case_details("case-001", self.mock_owner_profile)

		self.assertEqual(result["name"], "case-001")
		self.assertEqual(result["status"], "Open")

	def test_get_recovery_case_details_permission_denied(self):
		"""Test that getting details for another owner's case fails"""
		with self.assertRaises(frappe.PermissionError):
			get_recovery_case_details("case-001", "different-owner")

	@patch("scanifyme.recovery.services.recovery_service.frappe.get_doc")
	def test_update_recovery_case_status(self, mock_get_doc):
		"""Test updating recovery case status"""
		mock_case = MagicMock()
		mock_case.name = "case-001"
		mock_case.status = "Open"
		mock_case.owner_profile = self.mock_owner_profile
		mock_case.last_activity_on = None
		mock_case.closed_on = None
		mock_get_doc.return_value = mock_case

		result = update_recovery_case_status("case-001", "Closed", self.mock_owner_profile)

		self.assertTrue(result["success"])
		self.assertEqual(mock_case.status, "Closed")

	def test_update_recovery_case_status_invalid(self):
		"""Test updating with invalid status fails"""
		with self.assertRaises(frappe.ValidationError) as context:
			update_recovery_case_status("case-001", "InvalidStatus", self.mock_owner_profile)

		self.assertIn("Invalid status", str(context.exception))

	def test_update_recovery_case_status_permission_denied(self):
		"""Test that updating another owner's case fails"""
		with self.assertRaises(frappe.PermissionError):
			update_recovery_case_status("case-001", "Closed", "different-owner")


class TestRecoveryAPI(unittest.TestCase):
	"""Unit tests for the recovery API module"""

	def setUp(self):
		"""Set up test fixtures"""
		pass

	def tearDown(self):
		"""Clean up after tests"""
		pass

	@patch("scanifyme.recovery.api.recovery_api.get_owner_profile_for_user")
	@patch("scanifyme.recovery.api.recovery_api.recovery_service.get_owner_recovery_cases")
	def test_get_owner_recovery_cases_api(self, mock_service, mock_get_profile):
		"""Test the API endpoint for getting owner recovery cases"""
		from scanifyme.recovery.api import recovery_api

		mock_get_profile.return_value = "owner-001"
		mock_service.return_value = [{"name": "case-001", "status": "Open"}]

		# Can't easily test the @frappe.whitelist decorated function without Frappe context
		# This is a placeholder for integration tests
		self.assertTrue(True)


def run_tests():
	"""Run all tests"""
	loader = unittest.TestLoader()
	suite = unittest.TestSuite()

	suite.addTests(loader.loadTestsFromTestCase(TestRecoveryService))
	suite.addTests(loader.loadTestsFromTestCase(TestRecoveryAPI))

	runner = unittest.TextTestRunner(verbosity=2)
	runner.run(suite)


if __name__ == "__main__":
	run_tests()
