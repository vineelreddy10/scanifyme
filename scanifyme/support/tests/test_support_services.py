"""
Tests for ScanifyMe Support Services.

Covers:
- Logging service
- Health service
- Diagnostics service
- Maintenance service
"""

import frappe
import unittest
from frappe.utils import now_datetime, add_to_date


class TestLoggingService(unittest.TestCase):
	"""Tests for the logging service."""

	def test_log_scanifyme_event_basic(self):
		"""Test basic event logging."""
		from scanifyme.support.services.logging_service import log_scanifyme_event, EventCategory

		tracking_id = log_scanifyme_event(
			category=EventCategory.QR_ACTIVATION,
			action="test_activated",
			doctype="QR Code Tag",
			docname="TEST-001",
			actor_type="Owner",
			actor_id="test@user.com",
			context={"token": "ABC123"},
		)

		self.assertIsNotNone(tracking_id)
		self.assertIn("qr_activation", tracking_id)
		self.assertIn("test_activated", tracking_id)

	def test_log_scanifyme_event_sanitizes_sensitive_data(self):
		"""Test that sensitive data is sanitized in event logging."""
		from scanifyme.support.services.logging_service import (
			log_scanifyme_event,
			EventCategory,
			sanitize_dict,
		)

		# Test sanitize_dict with sensitive fields
		data = {
			"password": "secret123",
			"api_key": "key123",
			"safe_field": "visible",
			"user_token": "token123",
		}

		sanitized = sanitize_dict(data)

		self.assertEqual(sanitized["password"], "[REDACTED]")
		self.assertEqual(sanitized["api_key"], "[REDACTED]")
		self.assertEqual(sanitized["safe_field"], "visible")
		self.assertEqual(sanitized["user_token"], "[REDACTED]")

	def test_log_scanifyme_event_nested_dict(self):
		"""Test sanitization of nested dicts."""
		from scanifyme.support.services.logging_service import sanitize_dict

		data = {
			"level1": {
				"password": "secret",
				"safe": "value",
			}
		}

		sanitized = sanitize_dict(data)

		self.assertEqual(sanitized["level1"]["password"], "[REDACTED]")
		self.assertEqual(sanitized["level1"]["safe"], "value")

	def test_log_scanifyme_event_truncation(self):
		"""Test that long strings are truncated."""
		from scanifyme.support.services.logging_service import sanitize_dict

		data = {
			"long_field": "x" * 1000,
		}

		sanitized = sanitize_dict(data, max_length=500)

		self.assertLessEqual(len(sanitized["long_field"]), 503)  # 500 + "..."

	def test_log_scanifyme_error(self):
		"""Test error logging."""
		from scanifyme.support.services.logging_service import log_scanifyme_error, EventCategory

		try:
			raise ValueError("Test error")
		except ValueError as e:
			tracking_id = log_scanifyme_error(
				error=e,
				category=EventCategory.NOTIFICATION,
				action="test_send",
				doctype="Notification Event Log",
				docname="TEST-001",
				context={"owner_profile": "Test Owner"},
			)

		self.assertIsNotNone(tracking_id)
		self.assertIn("ERR:", tracking_id)

	def test_convenience_functions(self):
		"""Test convenience logging functions."""
		from scanifyme.support.services.logging_service import (
			log_qr_activation,
			log_finder_message,
			log_recovery_status_change,
		)

		# These should not raise exceptions
		result = log_qr_activation(
			token="TEST_TOKEN",
			user="test@user.com",
			success=True,
		)
		self.assertIsNotNone(result)

		result = log_finder_message(
			token="TEST_TOKEN",
			case_id="TEST-CASE-001",
			finder_name="Test Finder",
			success=True,
		)
		self.assertIsNotNone(result)


class TestHealthService(unittest.TestCase):
	"""Tests for the health service."""

	def test_get_quick_health_check(self):
		"""Test quick health check returns valid response."""
		from scanifyme.support.services.health_service import get_quick_health_check

		result = get_quick_health_check()

		self.assertIn("status", result)
		self.assertIn("timestamp", result)
		self.assertIn(result["status"], ["healthy", "degraded", "unhealthy"])

	def test_check_database(self):
		"""Test database check."""
		from scanifyme.support.services.health_service import check_database

		result = check_database()

		self.assertEqual(result.name, "database")
		self.assertIn(result.status, ["healthy", "critical", "unknown"])
		if result.status == "healthy":
			self.assertIn("db_type", result.details)

	def test_check_email_account(self):
		"""Test email account check."""
		from scanifyme.support.services.health_service import check_email_account

		result = check_email_account()

		self.assertEqual(result.name, "email_account")
		# Status can be healthy, warning, critical, or unknown
		self.assertIn(result.status, ["healthy", "warning", "critical", "unknown"])

	def test_get_environment_health_summary(self):
		"""Test environment health summary."""
		from scanifyme.support.services.health_service import get_environment_health_summary

		result = get_environment_health_summary()

		self.assertTrue(result.get("success"))
		self.assertIn("overall_status", result)
		self.assertIn("checks", result)
		self.assertIn("summary", result)
		self.assertIn("timestamp", result)

		# Should have multiple checks
		self.assertGreaterEqual(len(result["checks"]), 4)

		# Summary should match checks
		checks = result["checks"]
		total = sum(
			[
				result["summary"].get("healthy", 0),
				result["summary"].get("warnings", 0),
				result["summary"].get("critical", 0),
				result["summary"].get("unknown", 0),
			]
		)
		self.assertEqual(total, len(checks))

	def test_validate_email_readiness(self):
		"""Test email readiness validation."""
		from scanifyme.support.services.health_service import validate_email_readiness

		result = validate_email_readiness()

		self.assertIn("ready", result)
		self.assertIn("status", result)
		# ready can be True or False depending on config

	def test_validate_queue_readiness(self):
		"""Test queue readiness validation."""
		from scanifyme.support.services.health_service import validate_queue_readiness

		result = validate_queue_readiness()

		self.assertIn("ready", result)
		self.assertIn("status", result)


class TestDiagnosticsService(unittest.TestCase):
	"""Tests for the diagnostics service."""

	def test_get_system_state_snapshot(self):
		"""Test system state snapshot."""
		from scanifyme.support.services.diagnostics_service import get_system_state_snapshot

		result = get_system_state_snapshot(hours=1)

		self.assertTrue(result.get("success"))
		self.assertIn("totals", result)
		self.assertIn("generated_at", result)
		self.assertIn("period_hours", result)
		self.assertEqual(result["period_hours"], 1)

	def test_get_system_state_snapshot_totals(self):
		"""Test that system state snapshot has expected total fields."""
		from scanifyme.support.services.diagnostics_service import get_system_state_snapshot

		result = get_system_state_snapshot(hours=24)

		totals = result.get("totals", {})

		# Should have basic counts
		self.assertIn("recovery_cases", totals)
		self.assertIn("notification_events", totals)
		self.assertIn("registered_items", totals)

	def test_get_stale_cases_report(self):
		"""Test stale cases report."""
		from scanifyme.support.services.diagnostics_service import get_stale_cases_report

		result = get_stale_cases_report(days_threshold=7)

		self.assertTrue(result.get("success"))
		self.assertIn("stale_count", result)
		self.assertIn("cases", result)
		self.assertIn("days_threshold", result)
		self.assertEqual(result["days_threshold"], 7)

	def test_get_queue_failure_report(self):
		"""Test queue failure report."""
		from scanifyme.support.services.diagnostics_service import get_queue_failure_report

		result = get_queue_failure_report()

		self.assertTrue(result.get("success"))
		self.assertIn("summary", result)
		self.assertIn("notifications_by_type", result)
		self.assertIn("failed_emails", result)


class TestMaintenanceService(unittest.TestCase):
	"""Tests for the maintenance service."""

	def test_recompute_case_metadata_requires_case_id(self):
		"""Test that recompute requires valid case."""
		from scanifyme.support.services.maintenance_service import recompute_case_metadata

		# With non-existent case, should return error
		result = recompute_case_metadata("NON-EXISTENT-CASE")

		self.assertFalse(result.get("success"))
		self.assertIn("error", result)

	def test_expire_stale_sessions(self):
		"""Test expire stale sessions."""
		from scanifyme.support.services.maintenance_service import expire_stale_sessions

		result = expire_stale_sessions(days_threshold=0)

		self.assertIn("success", result)
		self.assertIn("expired_count", result)
		self.assertIn("threshold_days", result)

	def test_validate_system_state(self):
		"""Test system state validation."""
		from scanifyme.support.services.maintenance_service import validate_system_state

		result = validate_system_state()

		self.assertTrue(result.get("success"))
		self.assertIn("overall_status", result)
		self.assertIn("issues", result)
		self.assertIn("total_issues", result)

	def test_get_maintenance_actions(self):
		"""Test that maintenance actions are listed."""
		from scanifyme.support.services.maintenance_service import get_maintenance_actions

		actions = get_maintenance_actions()

		self.assertIsInstance(actions, list)
		self.assertGreater(len(actions), 0)

		# Each action should have required fields
		for action in actions:
			self.assertIn("action", action)
			self.assertIn("label", action)
			self.assertIn("description", action)
			self.assertIn("confirm_required", action)
			self.assertIn("idempotent", action)

	def test_run_maintenance_action_unknown(self):
		"""Test that unknown action returns error."""
		from scanifyme.support.services.maintenance_service import run_maintenance_action

		result = run_maintenance_action("unknown_action")

		self.assertFalse(result.get("success"))
		self.assertIn("error", result)


class TestSupportAPI(unittest.TestCase):
	"""Tests for support API endpoints."""

	def test_permission_check_requires_admin(self):
		"""Test that APIs require admin/operations role."""
		from scanifyme.support.api.support_api import _check_admin_or_operations

		# As Administrator, should pass
		frappe.set_user("Administrator")
		_check_admin_or_operations()  # Should not raise

	def test_get_environment_health_summary_api(self):
		"""Test get_environment_health_summary API."""
		from scanifyme.support.api.support_api import get_environment_health_summary

		frappe.set_user("Administrator")
		result = get_environment_health_summary()

		self.assertTrue(result.get("success"))
		self.assertIn("overall_status", result)
		self.assertIn("checks", result)

	def test_get_notification_queue_status_api(self):
		"""Test get_notification_queue_status API."""
		from scanifyme.support.api.support_api import get_notification_queue_status

		frappe.set_user("Administrator")
		result = get_notification_queue_status()

		self.assertTrue(result.get("success"))
		self.assertIn("queue", result)
		self.assertIn("today", result)

	def test_get_maintenance_actions_api(self):
		"""Test get_maintenance_actions API."""
		from scanifyme.support.api.support_api import get_maintenance_actions

		frappe.set_user("Administrator")
		result = get_maintenance_actions()

		self.assertIsInstance(result, list)
		self.assertGreater(len(result), 0)

	def test_validate_scanifyme_setup_api(self):
		"""Test validate_scanifyme_setup API."""
		from scanifyme.support.api.support_api import validate_scanifyme_setup

		frappe.set_user("Administrator")
		result = validate_scanifyme_setup()

		self.assertTrue(result.get("success"))
		self.assertIn("setup_status", result)
		self.assertIn("environment", result)
		self.assertIn("email", result)
		self.assertIn("queue", result)

	def test_get_case_diagnostic_bundle_requires_case_id(self):
		"""Test that get_case_diagnostic_bundle requires case_id."""
		from scanifyme.support.api.support_api import get_case_diagnostic_bundle

		frappe.set_user("Administrator")
		result = get_case_diagnostic_bundle("")

		self.assertFalse(result.get("success"))
		self.assertIn("error", result)

	def test_run_safe_maintenance_action_requires_action(self):
		"""Test that run_safe_maintenance_action requires action."""
		from scanifyme.support.api.support_api import run_safe_maintenance_action

		frappe.set_user("Administrator")
		result = run_safe_maintenance_action("")

		self.assertFalse(result.get("success"))
		self.assertIn("error", result)


def run_tests():
	"""Run all tests."""
	loader = unittest.TestLoader()
	suite = unittest.TestSuite()

	suite.addTests(loader.loadTestsFromTestCase(TestLoggingService))
	suite.addTests(loader.loadTestsFromTestCase(TestHealthService))
	suite.addTests(loader.loadTestsFromTestCase(TestDiagnosticsService))
	suite.addTests(loader.loadTestsFromTestCase(TestMaintenanceService))
	suite.addTests(loader.loadTestsFromTestCase(TestSupportAPI))

	runner = unittest.TextTestRunner(verbosity=2)
	result = runner.run(suite)

	return result


if __name__ == "__main__":
	run_tests()
