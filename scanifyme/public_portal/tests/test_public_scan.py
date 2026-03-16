# SPDX-License-Identifier: MIT
"""
Tests for Public Scan Service and API.
"""

import unittest
from unittest.mock import patch, MagicMock
import frappe
from scanifyme.public_portal.services.public_scan_service import (
	resolve_public_token,
	get_public_item_context,
	hash_ip,
	create_scan_event,
	get_public_item_context_api,
)


class TestPublicScanService(unittest.TestCase):
	"""Unit tests for the public scan service module"""

	def setUp(self):
		"""Set up test fixtures"""
		pass

	def tearDown(self):
		"""Clean up after tests"""
		pass

	@patch("scanifyme.public_portal.services.public_scan_service.frappe.db.get_value")
	def test_resolve_public_token_invalid(self, mock_get_value):
		"""Test resolving an invalid token"""
		mock_get_value.return_value = None

		result = resolve_public_token("INVALID_TOKEN")

		self.assertIsNotNone(result.get("error"))
		self.assertIsNone(result.get("qr_tag"))

	@patch("scanifyme.public_portal.services.public_scan_service.frappe.db.get_value")
	def test_resolve_public_token_not_activated(self, mock_get_value):
		"""Test resolving a token that's not activated"""
		mock_get_value.return_value = {
			"name": "qr-tag-001",
			"qr_uid": "QR001",
			"qr_token": "VALID_TOKEN",
			"status": "In Stock",  # Not activated
			"registered_item": None,
		}

		result = resolve_public_token("VALID_TOKEN")

		self.assertIsNotNone(result.get("error"))
		self.assertIn("is", result.get("error", "").lower())

	@patch("scanifyme.public_portal.services.public_scan_service.frappe.db.get_value")
	def test_resolve_public_token_valid(self, mock_get_value):
		"""Test resolving a valid token"""
		# First call returns QR tag, second returns item
		mock_get_value.side_effect = [
			{
				"name": "qr-tag-001",
				"qr_uid": "QR001",
				"qr_token": "VALID_TOKEN",
				"status": "Activated",
				"registered_item": "item-001",
			},
			{
				"name": "item-001",
				"item_name": "Test Item",
				"owner_profile": "owner-001",
				"item_category": "Laptop",
				"public_label": "Test",
				"recovery_note": "Call me",
				"reward_note": "$50",
				"status": "Active",
			},
		]

		result = resolve_public_token("VALID_TOKEN")

		self.assertIsNone(result.get("error"))
		self.assertIsNotNone(result.get("qr_tag"))
		self.assertIsNotNone(result.get("registered_item"))

	@patch("scanifyme.public_portal.services.public_scan_service.frappe.db.get_value")
	def test_resolve_public_token_item_not_active(self, mock_get_value):
		"""Test resolving a token where item is not active"""
		mock_get_value.side_effect = [
			{
				"name": "qr-tag-001",
				"qr_uid": "QR001",
				"qr_token": "VALID_TOKEN",
				"status": "Activated",
				"registered_item": "item-001",
			},
			{
				"name": "item-001",
				"item_name": "Test Item",
				"owner_profile": "owner-001",
				"item_category": "Laptop",
				"public_label": "Test",
				"recovery_note": "Call me",
				"reward_note": "$50",
				"status": "Lost",  # Not active
			},
		]

		result = resolve_public_token("VALID_TOKEN")

		self.assertIsNotNone(result.get("error"))

	def test_get_public_item_context(self):
		"""Test that public context filters sensitive data"""
		item = {
			"name": "item-001",
			"item_name": "MacBook Pro",
			"owner_profile": "owner-internal-name",
			"owner_email": "owner@email.com",  # Should not be exposed
			"owner_phone": "+1234567890",  # Should not be exposed
			"public_label": "MacBook",
			"recovery_note": "Please contact me",
			"reward_note": "$50 reward",
			"status": "Active",
			"item_category": "Laptop",
		}

		result = get_public_item_context(item)

		# These should NOT be in the result
		self.assertNotIn("owner_profile", result)
		self.assertNotIn("owner_email", result)
		self.assertNotIn("owner_phone", result)

		# These SHOULD be in the result
		self.assertIn("item_name", result)
		self.assertIn("public_label", result)
		self.assertIn("recovery_note", result)
		self.assertIn("reward_note", result)

	def test_hash_ip(self):
		"""Test IP hashing for privacy"""
		ip1 = "192.168.1.1"
		ip2 = "192.168.1.1"
		different_ip = "10.0.0.1"

		hash1 = hash_ip(ip1)
		hash2 = hash_ip(ip2)
		hash3 = hash_ip(different_ip)

		# Same IP should produce same hash
		self.assertEqual(hash1, hash2)

		# Different IP should produce different hash
		self.assertNotEqual(hash1, hash3)

		# Hash should be 16 characters (SHA256 first 16 hex chars)
		self.assertEqual(len(hash1), 16)

	def test_hash_ip_empty(self):
		"""Test hashing empty IP"""
		result = hash_ip(None)
		self.assertIsNone(result)

		result = hash_ip("")
		self.assertIsNone(result)

	@patch("scanifyme.public_portal.services.public_scan_service.frappe.db.get_value")
	@patch("scanifyme.public_portal.services.public_scan_service.create_scan_event")
	def test_get_public_item_context_api_valid(self, mock_scan_event, mock_get_value):
		"""Test the API for valid token"""
		mock_get_value.side_effect = [
			{
				"name": "qr-tag-001",
				"qr_uid": "QR001",
				"qr_token": "VALID_TOKEN",
				"status": "Activated",
				"registered_item": "item-001",
			},
			{
				"name": "item-001",
				"item_name": "MacBook Pro",
				"owner_profile": "owner-001",
				"item_category": "Laptop",
				"public_label": "MacBook",
				"recovery_note": "Please contact me",
				"reward_note": "$50",
				"status": "Active",
			},
		]

		result = get_public_item_context_api("VALID_TOKEN")

		self.assertTrue(result.get("success"))
		self.assertIsNotNone(result.get("item"))
		self.assertEqual(result["item"]["item_name"], "MacBook Pro")

	@patch("scanifyme.public_portal.services.public_scan_service.frappe.db.get_value")
	@patch("scanifyme.public_portal.services.public_scan_service.create_scan_event")
	def test_get_public_item_context_api_invalid_token(self, mock_scan_event, mock_get_value):
		"""Test the API for invalid token"""
		mock_get_value.return_value = None

		result = get_public_item_context_api("INVALID_TOKEN")

		self.assertFalse(result.get("success"))
		self.assertIsNotNone(result.get("error"))

	@patch("scanifyme.public_portal.services.public_scan_service.frappe.db.get_value")
	@patch("scanifyme.public_portal.services.public_scan_service.create_scan_event")
	def test_get_public_item_context_api_no_item(self, mock_scan_event, mock_get_value):
		"""Test the API when no item is linked"""
		mock_get_value.return_value = {
			"name": "qr-tag-001",
			"qr_uid": "QR001",
			"qr_token": "VALID_TOKEN",
			"status": "Activated",
			"registered_item": None,
		}

		result = get_public_item_context_api("VALID_TOKEN")

		self.assertFalse(result.get("success"))


def run_tests():
	"""Run all tests"""
	loader = unittest.TestLoader()
	suite = loader.loadTestsFromTestCase(TestPublicScanService)
	runner = unittest.TextTestRunner(verbosity=2)
	runner.run(suite)


if __name__ == "__main__":
	run_tests()
