# Copyright (c) 2024, ScanifyMe and contributors
# For license information, please see license.txt

import frappe
import unittest
from frappe.utils import now_datetime


class TestPrintService(unittest.TestCase):
	"""Tests for print_service module."""

	def setUp(self):
		"""Set up test data."""
		# Create a test batch with tags using the service function
		self.batch_name = f"TestBatch-{now_datetime().strftime('%Y%m%d%H%M%S')}"
		from scanifyme.qr_management.services.qr_service import generate_qr_batch

		frappe.set_user("Administrator")
		batch_name = generate_qr_batch(
			batch_name=self.batch_name,
			batch_size=5,
			batch_prefix="TEST",
		)
		self.batch = frappe.get_doc("QR Batch", batch_name)

		# Get created tags
		self.tags = frappe.get_all(
			"QR Code Tag",
			filters={"batch": self.batch.name},
			fields=["name", "qr_uid", "qr_token", "status"],
		)

	def tearDown(self):
		"""Clean up test data."""
		# Delete test data
		for tag in self.tags:
			frappe.db.delete("QR Code Tag", tag.name)
		frappe.db.delete("QR Batch", self.batch.name)
		frappe.db.commit()

	def test_create_print_job(self):
		"""Test print job creation."""
		from scanifyme.qr_management.services.print_service import create_print_job

		job_name = f"TestPrintJob-{now_datetime().strftime('%Y%m%d%H%M%S')}"
		job_name_result = create_print_job(
			print_job_name=job_name,
			qr_batch=self.batch.name,
			notes="Test print job",
		)

		self.assertIsNotNone(job_name_result)

		# Verify job was created
		job = frappe.get_doc("QR Print Job", job_name_result)
		self.assertEqual(job.print_job_name, job_name)
		self.assertEqual(job.qr_batch, self.batch.name)
		self.assertEqual(job.status, "Draft")
		self.assertEqual(job.item_count, len(self.tags))

		# Clean up
		frappe.db.delete("QR Print Job", job_name_result)

	def test_get_batch_printable_tags(self):
		"""Test getting printable tags from a batch."""
		from scanifyme.qr_management.services.print_service import get_batch_printable_tags

		tags = get_batch_printable_tags(self.batch.name)

		self.assertEqual(len(tags), 5)
		self.assertTrue(all(t["batch"] == self.batch.name for t in tags))

	def test_validate_tag_can_be_activated(self):
		"""Test tag activation eligibility validation."""
		from scanifyme.qr_management.services.stock_service import validate_tag_can_be_activated

		# Test In Stock tag - should be eligible
		in_stock_tag = frappe.db.get_value(
			"QR Code Tag",
			{"batch": self.batch.name, "status": "Generated"},
			"name",
		)

		# Set to In Stock for testing
		frappe.db.set_value("QR Code Tag", in_stock_tag, "status", "In Stock")
		frappe.db.commit()

		result = validate_tag_can_be_activated(in_stock_tag)
		self.assertTrue(result["can_activate"])
		self.assertEqual(result["current_status"], "In Stock")

		# Test Suspended tag - should not be eligible
		frappe.db.set_value("QR Code Tag", in_stock_tag, "status", "Suspended")
		frappe.db.commit()

		result = validate_tag_can_be_activated(in_stock_tag)
		self.assertFalse(result["can_activate"])
		self.assertEqual(result["current_status"], "Suspended")


class TestDistributionService(unittest.TestCase):
	"""Tests for distribution_service module."""

	def setUp(self):
		"""Set up test data."""
		# Create a test batch with tags using the service function
		self.batch_name = f"TestBatch-{now_datetime().strftime('%Y%m%d%H%M%S')}"
		from scanifyme.qr_management.services.qr_service import generate_qr_batch

		frappe.set_user("Administrator")
		batch_name = generate_qr_batch(
			batch_name=self.batch_name,
			batch_size=5,
			batch_prefix="TEST",
		)
		self.batch = frappe.get_doc("QR Batch", batch_name)

		# Get created tags
		self.tags = frappe.get_all(
			"QR Code Tag",
			filters={"batch": self.batch.name},
			fields=["name", "qr_uid", "qr_token", "status"],
		)

	def tearDown(self):
		"""Clean up test data."""
		# Delete test data
		for tag in self.tags:
			frappe.db.delete("QR Code Tag", tag.name)
		frappe.db.delete("QR Batch", self.batch.name)
		frappe.db.commit()

	def test_create_distribution_record(self):
		"""Test distribution record creation."""
		from scanifyme.qr_management.services.distribution_service import create_distribution_record

		dist_name = f"TestDist-{now_datetime().strftime('%Y%m%d%H%M%S')}"
		dist_result = create_distribution_record(
			distribution_name=dist_name,
			distributed_to_type="Demo",
			distributed_to_name="Test Demo",
			qr_batch=self.batch.name,
			notes="Test distribution",
		)

		self.assertIsNotNone(dist_result)

		# Verify record was created
		dist = frappe.get_doc("QR Distribution Record", dist_result)
		self.assertEqual(dist.distribution_name, dist_name)
		self.assertEqual(dist.distributed_to_type, "Demo")
		self.assertEqual(dist.distributed_to_name, "Test Demo")
		self.assertEqual(dist.status, "Draft")

		# Clean up
		frappe.db.delete("QR Distribution Record", dist_result)

	def test_valid_status_transitions(self):
		"""Test valid distribution status transitions."""
		from scanifyme.qr_management.services.distribution_service import (
			create_distribution_record,
			update_distribution_status,
		)

		# Create distribution
		dist_name = f"TestDist-{now_datetime().strftime('%Y%m%d%H%M%S')}"
		dist_result = create_distribution_record(
			distribution_name=dist_name,
			distributed_to_type="Demo",
			distributed_to_name="Test",
			qr_batch=self.batch.name,
		)

		# Test: Draft -> Packed (valid)
		result = update_distribution_status(dist_result, "Packed")
		self.assertEqual(result["new_status"], "Packed")

		# Test: Packed -> Dispatched (valid)
		result = update_distribution_status(dist_result, "Dispatched")
		self.assertEqual(result["new_status"], "Dispatched")

		# Test: Dispatched -> Delivered (valid)
		result = update_distribution_status(dist_result, "Delivered")
		self.assertEqual(result["new_status"], "Delivered")

		# Clean up
		frappe.db.delete("QR Distribution Record", dist_result)

	def test_invalid_status_transition(self):
		"""Test invalid distribution status transitions."""
		from scanifyme.qr_management.services.distribution_service import (
			create_distribution_record,
			update_distribution_status,
		)

		# Create distribution
		dist_name = f"TestDist-{now_datetime().strftime('%Y%m%d%H%M%S')}"
		dist_result = create_distribution_record(
			distribution_name=dist_name,
			distributed_to_type="Demo",
			distributed_to_name="Test",
			qr_batch=self.batch.name,
		)

		# Test: Draft -> Delivered (invalid - should fail)
		with self.assertRaises(frappe.ValidationError):
			update_distribution_status(dist_result, "Delivered")

		# Clean up
		frappe.db.delete("QR Distribution Record", dist_result)

	def test_can_tag_be_distributed(self):
		"""Test tag distribution eligibility."""
		from scanifyme.qr_management.services.distribution_service import can_tag_be_distributed

		# Test In Stock tag - should be eligible
		tag_name = self.tags[0].name
		result = can_tag_be_distributed(tag_name)
		self.assertTrue(result["eligible"])

		# Set to Activated - should not be eligible
		frappe.db.set_value("QR Code Tag", tag_name, "status", "Activated")
		frappe.db.commit()

		result = can_tag_be_distributed(tag_name)
		self.assertFalse(result["eligible"])
		self.assertIn("activated", result["reason"].lower())

		# Set to Suspended - should not be eligible
		frappe.db.set_value("QR Code Tag", tag_name, "status", "Suspended")
		frappe.db.commit()

		result = can_tag_be_distributed(tag_name)
		self.assertFalse(result["eligible"])


class TestStockService(unittest.TestCase):
	"""Tests for stock_service module."""

	def setUp(self):
		"""Set up test data."""
		# Create a test batch with tags in different statuses using service
		self.batch_name = f"TestBatch-{now_datetime().strftime('%Y%m%d%H%M%S')}"
		from scanifyme.qr_management.services.qr_service import generate_qr_batch

		frappe.set_user("Administrator")
		batch_name = generate_qr_batch(
			batch_name=self.batch_name,
			batch_size=6,
			batch_prefix="TEST",
		)
		self.batch = frappe.get_doc("QR Batch", batch_name)

		# Get created tags and set different statuses
		self.tags = frappe.get_all(
			"QR Code Tag",
			filters={"batch": self.batch.name},
			fields=["name", "qr_uid", "status"],
		)

		# Set statuses and re-fetch to get updated data
		statuses = ["Generated", "Printed", "In Stock", "Assigned", "Activated", "Suspended"]
		for i, tag in enumerate(self.tags):
			frappe.db.set_value("QR Code Tag", tag["name"], "status", statuses[i])
		frappe.db.commit()

		# Re-fetch tags with updated statuses
		self.tags = frappe.get_all(
			"QR Code Tag",
			filters={"batch": self.batch.name},
			fields=["name", "qr_uid", "status"],
		)

	def tearDown(self):
		"""Clean up test data."""
		# Delete test data
		for tag in self.tags:
			frappe.db.delete("QR Code Tag", tag["name"])
		frappe.db.delete("QR Batch", self.batch.name)
		frappe.db.commit()

	def test_get_stock_summary(self):
		"""Test getting stock summary."""
		from scanifyme.qr_management.services.stock_service import get_stock_summary

		summary = get_stock_summary(self.batch.name)

		self.assertEqual(summary["total_tags"], 6)
		self.assertEqual(summary["generated"], 1)
		self.assertEqual(summary["printed"], 1)
		self.assertEqual(summary["in_stock"], 1)
		self.assertEqual(summary["assigned"], 1)
		self.assertEqual(summary["activated"], 1)
		self.assertEqual(summary["suspended"], 1)

	def test_get_stock_summary_all_batches(self):
		"""Test getting stock summary for all batches."""
		from scanifyme.qr_management.services.stock_service import get_stock_summary

		summary = get_stock_summary()

		self.assertIn("total_tags", summary)
		self.assertIn("status_counts", summary)
		self.assertGreaterEqual(summary["total_tags"], 6)

	def test_get_tags_by_status(self):
		"""Test getting tags by status."""
		from scanifyme.qr_management.services.stock_service import get_tags_by_status

		# Get In Stock tags
		in_stock_tags = get_tags_by_status("In Stock", limit=10)
		self.assertTrue(len(in_stock_tags) >= 1)

		# Get Activated tags
		activated_tags = get_tags_by_status("Activated", limit=10)
		self.assertTrue(len(activated_tags) >= 1)

	def test_validate_tag_can_be_activated(self):
		"""Test tag activation eligibility."""
		from scanifyme.qr_management.services.stock_service import validate_tag_can_be_activated

		# In Stock tag should be eligible
		in_stock_tag = next(t for t in self.tags if t["status"] == "In Stock")
		result = validate_tag_can_be_activated(in_stock_tag["name"])
		self.assertTrue(result["can_activate"])

		# Activated tag should not be eligible
		activated_tag = next(t for t in self.tags if t["status"] == "Activated")
		result = validate_tag_can_be_activated(activated_tag["name"])
		self.assertFalse(result["can_activate"])

		# Suspended tag should not be eligible
		suspended_tag = next(t for t in self.tags if t["status"] == "Suspended")
		result = validate_tag_can_be_activated(suspended_tag["name"])
		self.assertFalse(result["can_activate"])

		# Generated tag should not be eligible (needs to be printed first)
		generated_tag = next(t for t in self.tags if t["status"] == "Generated")
		result = validate_tag_can_be_activated(generated_tag["name"])
		self.assertFalse(result["can_activate"])

	def test_get_print_ready_batches(self):
		"""Test getting print-ready batches."""
		from scanifyme.qr_management.services.stock_service import get_print_ready_batches

		batches = get_print_ready_batches()

		# Our test batch should be in the list
		batch_names = [b["name"] for b in batches]
		self.assertIn(self.batch.name, batch_names)

	def test_get_distribution_ready_tags(self):
		"""Test getting distribution-ready tags."""
		from scanifyme.qr_management.services.stock_service import get_distribution_ready_tags

		# Get tags that are Printed or In Stock
		tags = get_distribution_ready_tags(self.batch.name)

		statuses = [t["status"] for t in tags]
		self.assertIn("Printed", statuses)
		self.assertIn("In Stock", statuses)


class TestQRAPIPermissions(unittest.TestCase):
	"""Tests for QR API permissions."""

	def test_admin_can_access_print_apis(self):
		"""Test that admin can access print APIs."""
		from scanifyme.qr_management.api.qr_api import has_qr_role

		# Mock admin user
		frappe.set_user("Administrator")

		self.assertTrue(has_qr_role())

	def test_regular_user_cannot_access_print_apis(self):
		"""Test that regular users cannot access print APIs without role."""
		from scanifyme.qr_management.api.qr_api import has_qr_role

		# Create a regular user without QR roles (use unique email each time)
		test_email = f"test_regular_{now_datetime().strftime('%Y%m%d%H%M%S')}@example.com"
		if not frappe.db.exists("User", test_email):
			user = frappe.get_doc(
				{
					"doctype": "User",
					"email": test_email,
					"first_name": "Test",
					"last_name": "Regular",
					"send_welcome_email": 0,
					"user_type": "Website User",
					"enabled": 1,
				}
			)
			user.insert(ignore_permissions=True)
			frappe.db.commit()

		frappe.set_user(test_email)

		# Regular users should not have QR role by default
		self.assertFalse(has_qr_role())

		# Cleanup
		frappe.set_user("Administrator")
		if frappe.db.exists("User", test_email):
			frappe.db.delete("User", test_email)
			frappe.db.commit()
