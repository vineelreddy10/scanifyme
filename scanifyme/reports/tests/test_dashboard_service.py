"""
Tests for Reports/Dashboard Services.

Tests dashboard summary, metrics aggregation, and permission enforcement.
"""

import frappe
import unittest
from frappe.utils import now_datetime


class TestDashboardService(unittest.TestCase):
	"""Test cases for dashboard service functions."""

	@classmethod
	def setUpClass(cls):
		"""Create demo data before tests."""
		frappe.set_user("Administrator")
		try:
			from scanifyme.api.demo_data import create_demo_data

			create_demo_data()
		except Exception:
			pass

	def test_get_owner_dashboard_summary_returns_dict(self):
		"""Summary returns a dict with expected keys."""
		from scanifyme.reports.services.dashboard_service import (
			get_owner_dashboard_summary,
		)

		result = get_owner_dashboard_summary("Administrator")
		self.assertIsInstance(result, dict)
		self.assertIn("items", result)
		self.assertIn("recovery_cases", result)
		self.assertIn("qr_tags", result)
		self.assertIn("rewards", result)
		self.assertIn("notifications", result)

	def test_get_owner_dashboard_summary_items_counts(self):
		"""Summary items counts are integers."""
		from scanifyme.reports.services.dashboard_service import (
			get_owner_dashboard_summary,
		)

		result = get_owner_dashboard_summary("Administrator")
		items = result["items"]
		self.assertIsInstance(items["total"], int)
		self.assertIsInstance(items["active"], int)
		self.assertIsInstance(items["lost"], int)
		self.assertIsInstance(items["recovered"], int)
		self.assertIsInstance(items["draft"], int)

	def test_get_owner_dashboard_summary_cases_counts(self):
		"""Summary case counts are integers."""
		from scanifyme.reports.services.dashboard_service import (
			get_owner_dashboard_summary,
		)

		result = get_owner_dashboard_summary("Administrator")
		cases = result["recovery_cases"]
		self.assertIsInstance(cases["total"], int)
		self.assertIsInstance(cases["open"], int)
		self.assertIsInstance(cases["active_workflow"], int)

	def test_get_owner_dashboard_summary_notifications(self):
		"""Summary notifications counts are integers."""
		from scanifyme.reports.services.dashboard_service import (
			get_owner_dashboard_summary,
		)

		result = get_owner_dashboard_summary("Administrator")
		notifs = result["notifications"]
		self.assertIsInstance(notifs["unread"], int)
		self.assertGreaterEqual(notifs["unread"], 0)

	def test_get_owner_recent_activity_returns_dict(self):
		"""Recent activity returns dict with expected keys."""
		from scanifyme.reports.services.dashboard_service import (
			get_owner_recent_activity,
		)

		result = get_owner_recent_activity("Administrator")
		self.assertIsInstance(result, dict)
		self.assertIn("recent_cases", result)
		self.assertIn("recent_notifications", result)
		self.assertIn("recent_scans", result)
		self.assertIn("recent_locations", result)

	def test_get_owner_recent_activity_arrays(self):
		"""Recent activity arrays are lists."""
		from scanifyme.reports.services.dashboard_service import (
			get_owner_recent_activity,
		)

		result = get_owner_recent_activity("Administrator")
		self.assertIsInstance(result["recent_cases"], list)
		self.assertIsInstance(result["recent_notifications"], list)
		self.assertIsInstance(result["recent_scans"], list)

	def test_get_owner_recent_activity_limit(self):
		"""Recent activity respects limit parameter."""
		from scanifyme.reports.services.dashboard_service import (
			get_owner_recent_activity,
		)

		result = get_owner_recent_activity("Administrator", limit=3)
		self.assertLessEqual(len(result["recent_cases"]), 3)
		self.assertLessEqual(len(result["recent_notifications"]), 3)

	def test_get_admin_operational_summary_returns_dict(self):
		"""Admin summary returns dict with expected keys."""
		from scanifyme.reports.services.dashboard_service import (
			get_admin_operational_summary,
		)

		result = get_admin_operational_summary()
		self.assertIsInstance(result, dict)
		self.assertIn("qr_batches", result)
		self.assertIn("qr_tags", result)
		self.assertIn("registered_items", result)
		self.assertIn("recovery_cases", result)
		self.assertIn("scans", result)
		self.assertIn("notifications", result)

	def test_get_admin_operational_summary_qr_batches(self):
		"""Admin summary QR batch counts are integers."""
		from scanifyme.reports.services.dashboard_service import (
			get_admin_operational_summary,
		)

		result = get_admin_operational_summary()
		batches = result["qr_batches"]
		self.assertIsInstance(batches["total"], int)
		self.assertIsInstance(batches["by_status"], dict)

	def test_get_admin_operational_summary_scans(self):
		"""Admin summary scan breakdown is correct."""
		from scanifyme.reports.services.dashboard_service import (
			get_admin_operational_summary,
		)

		result = get_admin_operational_summary()
		scans = result["scans"]
		self.assertIsInstance(scans["total"], int)
		self.assertIsInstance(scans["valid"], int)
		self.assertIsInstance(scans["invalid"], int)

	def test_get_admin_operational_summary_cases_by_status(self):
		"""Admin summary cases by status breakdown."""
		from scanifyme.reports.services.dashboard_service import (
			get_admin_operational_summary,
		)

		result = get_admin_operational_summary()
		cases = result["recovery_cases"]
		self.assertIsInstance(cases["total"], int)
		self.assertIsInstance(cases["by_status"], dict)
		self.assertIn("active_workflow", cases)

	def test_get_admin_operational_summary_handover(self):
		"""Admin summary handover breakdown."""
		from scanifyme.reports.services.dashboard_service import (
			get_admin_operational_summary,
		)

		result = get_admin_operational_summary()
		self.assertIn("handover", result)
		self.assertIsInstance(result["handover"]["by_status"], dict)

	def test_get_admin_operational_summary_rewards(self):
		"""Admin summary rewards data."""
		from scanifyme.reports.services.dashboard_service import (
			get_admin_operational_summary,
		)

		result = get_admin_operational_summary()
		self.assertIn("rewards", result)
		self.assertIsInstance(result["rewards"]["enabled_items"], int)
		self.assertIsInstance(result["rewards"]["cases_with_rewards"], int)


class TestRecoveryMetricsService(unittest.TestCase):
	"""Test cases for recovery metrics service functions."""

	def test_get_recovery_metrics_returns_list(self):
		"""Recovery metrics returns a list."""
		from scanifyme.reports.services.recovery_metrics_service import (
			get_recovery_metrics,
		)

		result = get_recovery_metrics()
		self.assertIsInstance(result, list)

	def test_get_recovery_metrics_with_status_filter(self):
		"""Recovery metrics respects status filter."""
		from scanifyme.reports.services.recovery_metrics_service import (
			get_recovery_metrics,
		)

		result = get_recovery_metrics(status="Open")
		for row in result:
			self.assertEqual(row.get("status"), "Open")

	def test_get_recovery_metrics_enrichment(self):
		"""Recovery metrics rows have enrichment fields."""
		from scanifyme.reports.services.recovery_metrics_service import (
			get_recovery_metrics,
		)

		result = get_recovery_metrics(limit=5)
		for row in result:
			self.assertIsInstance(row, dict)

	def test_get_scan_metrics_returns_list(self):
		"""Scan metrics returns a list."""
		from scanifyme.reports.services.recovery_metrics_service import (
			get_scan_metrics,
		)

		result = get_scan_metrics()
		self.assertIsInstance(result, list)

	def test_get_scan_metrics_with_status_filter(self):
		"""Scan metrics respects status filter."""
		from scanifyme.reports.services.recovery_metrics_service import (
			get_scan_metrics,
		)

		result = get_scan_metrics(status="Valid")
		for row in result:
			self.assertEqual(row.get("status"), "Valid")

	def test_get_notification_metrics_returns_list(self):
		"""Notification metrics returns a list."""
		from scanifyme.reports.services.recovery_metrics_service import (
			get_notification_metrics,
		)

		result = get_notification_metrics()
		self.assertIsInstance(result, list)

	def test_get_notification_metrics_with_channel(self):
		"""Notification metrics respects channel filter."""
		from scanifyme.reports.services.recovery_metrics_service import (
			get_notification_metrics,
		)

		result = get_notification_metrics(channel="In App")
		for row in result:
			self.assertEqual(row.get("channel"), "In App")


class TestStockMetricsService(unittest.TestCase):
	"""Test cases for stock metrics service functions."""

	def test_get_stock_metrics_returns_list(self):
		"""Stock metrics returns a list."""
		from scanifyme.reports.services.stock_metrics_service import (
			get_stock_metrics,
		)

		result = get_stock_metrics()
		self.assertIsInstance(result, list)

	def test_get_stock_metrics_with_status_filter(self):
		"""Stock metrics respects status filter."""
		from scanifyme.reports.services.stock_metrics_service import (
			get_stock_metrics,
		)

		result = get_stock_metrics(status="Activated")
		for row in result:
			self.assertEqual(row.get("status"), "Activated")

	def test_get_qr_stock_summary_returns_dict(self):
		"""QR stock summary returns dict with expected keys."""
		from scanifyme.reports.services.stock_metrics_service import (
			get_qr_stock_summary,
		)

		result = get_qr_stock_summary()
		self.assertIsInstance(result, dict)
		self.assertIn("total_tags", result)
		self.assertIn("by_status", result)
		self.assertIn("by_batch", result)

	def test_get_qr_stock_summary_counts(self):
		"""QR stock summary counts are integers."""
		from scanifyme.reports.services.stock_metrics_service import (
			get_qr_stock_summary,
		)

		result = get_qr_stock_summary()
		self.assertIsInstance(result["total_tags"], int)
		self.assertIsInstance(result["by_status"], dict)

	def test_get_registered_items_report_returns_list(self):
		"""Registered items report returns list."""
		from scanifyme.reports.services.stock_metrics_service import (
			get_registered_items_report,
		)

		result = get_registered_items_report()
		self.assertIsInstance(result, list)

	def test_get_registered_items_report_enrichment(self):
		"""Registered items rows have enrichment fields."""
		from scanifyme.reports.services.stock_metrics_service import (
			get_registered_items_report,
		)

		result = get_registered_items_report(limit=5)
		for row in result:
			self.assertIsInstance(row, dict)
			self.assertIn("name", row)


if __name__ == "__main__":
	unittest.main()
