# SPDX-License-Identifier: MIT

import unittest
from unittest.mock import patch, MagicMock
import frappe
from frappe import _
from scanifyme.items.services.item_service import (
	activate_qr,
	create_item,
	link_item_to_qr,
	get_user_items,
	get_item_details,
	get_or_create_owner_profile,
	update_item_status,
)


class TestItemService(unittest.TestCase):
	"""Unit tests for the item service module"""

	def setUp(self):
		"""Set up test fixtures"""
		self.mock_user = "test@example.com"
		self.mock_qr_token = "TEST123456"
		self.mock_qr_tag_name = "test-qr-tag"
		self.mock_item_name = "test-item"

	def tearDown(self):
		"""Clean up after tests"""
		pass

	@patch("scanifyme.items.services.item_service.frappe.db.get_value")
	def test_activate_qr_invalid_token(self, mock_get_value):
		"""Test activating with invalid QR token"""
		mock_get_value.return_value = None

		with self.assertRaises(frappe.ValidationError) as context:
			activate_qr("INVALID_TOKEN")

		self.assertIn("Invalid QR token", str(context.exception))

	@patch("scanifyme.items.services.item_service.frappe.db.get_value")
	def test_activate_qr_already_activated(self, mock_get_value):
		"""Test activating an already activated QR code"""
		mock_get_value.return_value = {
			"name": self.mock_qr_tag_name,
			"qr_uid": "QR001",
			"qr_token": self.mock_qr_token,
			"status": "Activated",
			"registered_item": "test-item",
		}

		result = activate_qr(self.mock_qr_token)

		self.assertTrue(result["success"])
		self.assertFalse(result["needs_item_creation"])

	@patch("scanifyme.items.services.item_service.frappe.db.get_value")
	def test_activate_qr_valid_token(self, mock_get_value):
		"""Test activating a valid QR token"""
		mock_get_value.return_value = {
			"name": self.mock_qr_tag_name,
			"qr_uid": "QR001",
			"qr_token": self.mock_qr_token,
			"status": "In Stock",
			"registered_item": None,
		}

		result = activate_qr(self.mock_qr_token)

		self.assertTrue(result["success"])
		self.assertTrue(result["needs_item_creation"])
		self.assertEqual(result["qr_tag"]["status"], "In Stock")

	@patch("scanifyme.items.services.item_service.frappe.db.get_value")
	def test_activate_qr_invalid_status(self, mock_get_value):
		"""Test activating QR with invalid status"""
		mock_get_value.return_value = {
			"name": self.mock_qr_tag_name,
			"qr_uid": "QR001",
			"qr_token": self.mock_qr_token,
			"status": "Retired",
			"registered_item": None,
		}

		with self.assertRaises(frappe.ValidationError) as context:
			activate_qr(self.mock_qr_token)

		self.assertIn("cannot be activated", str(context.exception))

	@patch("scanifyme.items.services.item_service.get_or_create_owner_profile")
	@patch("scanifyme.items.services.item_service.frappe.db.get_value")
	@patch("scanifyme.items.services.item_service.frappe.get_doc")
	def test_create_item_success(self, mock_get_doc, mock_db_value, mock_get_profile):
		"""Test successful item creation"""
		mock_get_profile.return_value = "owner-profile-001"
		mock_db_value.return_value = None
		mock_item_doc = MagicMock()
		mock_item_doc.name = "new-item-001"
		mock_get_doc.return_value = mock_item_doc

		result = create_item({"item_name": "Test Item", "qr_code_tag": "qr-tag-001"}, self.mock_user)

		self.assertEqual(result, "new-item-001")
		mock_item_doc.insert.assert_called_once()

	def test_create_item_missing_name(self):
		"""Test creating item without name"""
		with self.assertRaises(frappe.ValidationError) as context:
			create_item({"qr_code_tag": "qr-tag-001"})

		self.assertIn("Item name is required", str(context.exception))

	def test_create_item_missing_qr_tag(self):
		"""Test creating item without QR tag"""
		with self.assertRaises(frappe.ValidationError) as context:
			create_item({"item_name": "Test Item"})

		self.assertIn("QR Code Tag is required", str(context.exception))

	@patch("scanifyme.items.services.item_service.frappe.db.get_value")
	def test_create_item_duplicate_qr(self, mock_db_value):
		"""Test creating item with already linked QR"""
		mock_db_value.return_value = "existing-item"

		with self.assertRaises(frappe.ValidationError) as context:
			create_item({"item_name": "Test Item", "qr_code_tag": "qr-tag-001"})

		self.assertIn("already linked", str(context.exception))

	@patch("scanifyme.items.services.item_service.frappe.get_doc")
	@patch("scanifyme.items.services.item_service.frappe.db.get_value")
	def test_link_item_to_qr_success(self, mock_db_value, mock_get_doc):
		"""Test successful QR to item linking"""
		mock_db_value.return_value = None
		mock_item_doc = MagicMock()
		mock_item_doc.qr_code_tag = None
		mock_item_doc.status = "Draft"
		mock_item_doc.activation_date = None
		mock_get_doc.side_effect = [mock_item_doc, MagicMock()]

		result = link_item_to_qr("item-001", "qr-tag-001")

		self.assertTrue(result["success"])

	@patch("scanifyme.items.services.item_service.frappe.get_list")
	def test_get_user_items_empty(self, mock_get_list):
		"""Test getting items for user with no items"""
		mock_get_list.return_value = []

		result = get_user_items(self.mock_user)

		self.assertEqual(result, [])

	@patch("scanifyme.items.services.item_service.frappe.db.get_value")
	@patch("scanifyme.items.services.item_service.frappe.get_list")
	def test_get_user_items_with_data(self, mock_get_list, mock_db_value):
		"""Test getting items for user with items"""
		mock_db_value.return_value = "owner-profile-001"
		mock_get_list.return_value = [{"name": "item-001", "item_name": "Test Item", "status": "Active"}]

		result = get_user_items(self.mock_user)

		self.assertEqual(len(result), 1)
		self.assertEqual(result[0]["item_name"], "Test Item")


def run_tests():
	"""Run all tests"""
	loader = unittest.TestLoader()
	suite = loader.loadTestsFromTestCase(TestItemService)
	runner = unittest.TextTestRunner(verbosity=2)
	runner.run(suite)


if __name__ == "__main__":
	run_tests()
