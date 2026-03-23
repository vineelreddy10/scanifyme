"""
Tests for Cleanup and Maintenance Service.

These tests verify the cleanup and maintenance functionality.
"""

import frappe
import unittest
from frappe.utils import now_datetime, add_to_date
from unittest.mock import patch, MagicMock


class TestCleanupService(unittest.TestCase):
	"""Test cases for cleanup service."""

	@classmethod
	def setUpClass(cls):
		"""Set up test fixtures."""
		frappe.set_user("Administrator")

	def test_expire_stale_finder_sessions_no_sessions(self):
		"""Test expiration with no stale sessions."""
		from scanifyme.recovery.services.cleanup_service import (
			expire_stale_finder_sessions,
		)

		# Mock to return empty lists
		with patch("frappe.get_list", return_value=[]):
			result = expire_stale_finder_sessions()

			self.assertTrue(result["success"])
			self.assertEqual(result["expired_count"], 0)

	def test_close_completed_sessions_structure(self):
		"""Test close completed sessions returns proper structure."""
		from scanifyme.recovery.services.cleanup_service import (
			close_completed_sessions,
		)

		# Mock sql to return empty results
		with patch("frappe.db.sql", return_value=[]):
			result = close_completed_sessions()

			self.assertTrue(result["success"])
			self.assertIn("closed_count", result)

	def test_recompute_case_latest_metadata_structure(self):
		"""Test recompute metadata returns proper structure."""
		from scanifyme.recovery.services.cleanup_service import (
			recompute_case_latest_metadata,
		)

		# Mock to return empty list
		with patch("frappe.get_list", return_value=[]):
			result = recompute_case_latest_metadata()

			self.assertTrue(result["success"])
			self.assertIn("updated", result)
			self.assertIn("failed", result)

	def test_cleanup_old_scan_events_structure(self):
		"""Test cleanup old scan events returns proper structure."""
		from scanifyme.recovery.services.cleanup_service import (
			cleanup_old_scan_events,
		)

		# Mock sql to return empty results
		with patch("frappe.db.sql", return_value=[]):
			result = cleanup_old_scan_events()

			self.assertTrue(result["success"])
			self.assertIn("deleted_count", result)

	def test_get_operational_health_summary_structure(self):
		"""Test operational health summary returns proper structure."""
		from scanifyme.recovery.services.cleanup_service import (
			get_operational_health_summary,
		)

		# Mock database counts
		with patch.object(frappe.db, "count", return_value=5):
			with patch(
				"scanifyme.recovery.services.cleanup_service.health_check_notification_backlog",
				return_value={
					"success": True,
					"health_status": "healthy",
					"issues": [],
					"backlog": {},
				},
			):
				result = get_operational_health_summary()

				self.assertTrue(result["success"])
				self.assertIn("overall_status", result)
				self.assertIn("issues", result)
				self.assertIn("finder_sessions", result)
				self.assertIn("recovery_cases", result)


class TestHealthChecks(unittest.TestCase):
	"""Test cases for health check functionality."""

	@classmethod
	def setUpClass(cls):
		"""Set up test fixtures."""
		frappe.set_user("Administrator")

	def test_health_check_notification_backlog_healthy(self):
		"""Test health check with no issues."""
		from scanifyme.recovery.services.cleanup_service import (
			health_check_notification_backlog,
		)

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
			self.assertEqual(len(result["issues"]), 0)

	def test_health_check_notification_backlog_warning(self):
		"""Test health check with warnings."""
		from scanifyme.recovery.services.cleanup_service import (
			health_check_notification_backlog,
		)

		with patch(
			"scanifyme.recovery.services.cleanup_service.get_notification_backlog",
			return_value={
				"success": True,
				"backlog": {"failed": 7, "queued": 150},
				"recent_failures": [],
			},
		):
			result = health_check_notification_backlog()

			self.assertTrue(result["success"])
			self.assertEqual(result["health_status"], "warning")
			self.assertTrue(len(result["issues"]) > 0)

	def test_health_check_notification_backlog_critical(self):
		"""Test health check with critical issues."""
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


class TestMaintenanceJobs(unittest.TestCase):
	"""Test cases for maintenance job execution."""

	@classmethod
	def setUpClass(cls):
		"""Set up test fixtures."""
		frappe.set_user("Administrator")

	def test_run_maintenance_job_unknown(self):
		"""Test running unknown maintenance job."""
		from scanifyme.admin_ops.api.operational_api import run_maintenance_job

		# Mock permission check
		with patch("frappe.has_permission", return_value=True):
			result = run_maintenance_job(job_name="nonexistent_job")

			self.assertFalse(result["success"])
			self.assertIn("Unknown", result["error"])

	def test_run_maintenance_job_expire_sessions(self):
		"""Test running expire stale finder sessions job."""
		from scanifyme.admin_ops.api.operational_api import run_maintenance_job

		# Mock permission check
		with patch("frappe.has_permission", return_value=True):
			# Mock the cleanup service
			with patch(
				"scanifyme.recovery.services.cleanup_service.expire_stale_finder_sessions",
				return_value={"success": True, "expired_count": 0},
			):
				result = run_maintenance_job(job_name="expire_stale_finder_sessions")

				self.assertTrue(result["success"])

	def test_run_maintenance_job_health_check(self):
		"""Test running health check job."""
		from scanifyme.admin_ops.api.operational_api import run_maintenance_job

		# Mock permission check
		with patch("frappe.has_permission", return_value=True):
			# Mock the cleanup service
			with patch(
				"scanifyme.recovery.services.cleanup_service.health_check_notification_backlog",
				return_value={"success": True, "health_status": "healthy"},
			):
				result = run_maintenance_job(job_name="health_check_notifications")

				self.assertTrue(result["success"])


if __name__ == "__main__":
	unittest.main()
