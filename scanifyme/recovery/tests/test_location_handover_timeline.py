# SPDX-License-Identifier: MIT
"""
Tests for Location, Timeline, and Handover Services.
"""

import unittest
from unittest.mock import patch, MagicMock
from datetime import datetime
import frappe
from frappe import _
from scanifyme.recovery.services.location_service import (
	validate_coordinates,
	submit_location_share,
	get_latest_case_location,
	get_case_location_history,
	summarize_latest_location,
)
from scanifyme.recovery.services.timeline_service import (
	create_timeline_event,
	get_case_timeline,
	get_case_timeline_count,
)
from scanifyme.recovery.services.handover_service import (
	update_handover_status,
	get_handover_status_options,
	auto_update_handover_on_finder_message,
	get_case_handover_details,
)


class TestLocationService(unittest.TestCase):
	"""Unit tests for the location service module"""

	def test_validate_coordinates_valid(self):
		"""Test that valid coordinates are accepted"""
		self.assertTrue(validate_coordinates(37.7749, -122.4194))
		self.assertTrue(validate_coordinates(0, 0))
		self.assertTrue(validate_coordinates(-90, -180))
		self.assertTrue(validate_coordinates(90, 180))

	def test_validate_coordinates_invalid_lat(self):
		"""Test that invalid latitudes are rejected"""
		self.assertFalse(validate_coordinates(91, 0))
		self.assertFalse(validate_coordinates(-91, 0))
		self.assertFalse(validate_coordinates(180, 0))

	def test_validate_coordinates_invalid_lng(self):
		"""Test that invalid longitudes are rejected"""
		self.assertFalse(validate_coordinates(0, 181))
		self.assertFalse(validate_coordinates(0, -181))
		self.assertFalse(validate_coordinates(0, 200))

	def test_validate_coordinates_none(self):
		"""Test that None coordinates are rejected"""
		self.assertFalse(validate_coordinates(None, 0))
		self.assertFalse(validate_coordinates(0, None))
		self.assertFalse(validate_coordinates(None, None))


class TestTimelineService(unittest.TestCase):
	"""Unit tests for the timeline service module"""

	def test_get_handover_status_options(self):
		"""Test that valid handover status options are returned"""
		options = get_handover_status_options()
		self.assertIn("Not Started", options)
		self.assertIn("Finder Contacted", options)
		self.assertIn("Location Shared", options)
		self.assertIn("Return Planned", options)
		self.assertIn("Handover Scheduled", options)
		self.assertIn("Recovered", options)
		self.assertIn("Closed", options)
		self.assertIn("Failed", options)

	@patch("scanifyme.recovery.services.timeline_service.frappe.get_doc")
	@patch("scanifyme.recovery.services.timeline_service.now_datetime")
	@patch("scanifyme.recovery.services.timeline_service.frappe.db.commit")
	def test_create_timeline_event(self, mock_commit, mock_now_datetime, mock_get_doc):
		"""Test creating a timeline event"""
		mock_now_datetime.return_value = datetime(2026, 3, 17, 12, 0, 0)
		mock_doc = MagicMock()
		mock_doc.name = "timeline-event-001"
		mock_get_doc.return_value = mock_doc

		result = create_timeline_event(
			recovery_case="recovery-case-001",
			event_type="Finder Message",
			event_label="New Message",
			actor_type="Finder",
			actor_reference="John Finder",
			summary="Test message",
		)

		self.assertEqual(result, "timeline-event-001")
		mock_doc.insert.assert_called_once()

	@patch("scanifyme.recovery.services.timeline_service.frappe.get_doc")
	def test_create_timeline_event_invalid_type(self, mock_get_doc):
		"""Test that invalid event type raises error"""
		with self.assertRaises(frappe.ValidationError):
			create_timeline_event(
				recovery_case="recovery-case-001",
				event_type="Invalid Type",
				actor_type="Finder",
			)

	@patch("scanifyme.recovery.services.timeline_service.frappe.get_doc")
	def test_create_timeline_event_invalid_actor(self, mock_get_doc):
		"""Test that invalid actor type raises error"""
		with self.assertRaises(frappe.ValidationError):
			create_timeline_event(
				recovery_case="recovery-case-001",
				event_type="Finder Message",
				actor_type="Invalid Actor",
			)


class TestHandoverService(unittest.TestCase):
	"""Unit tests for the handover service module"""

	def test_get_handover_status_options(self):
		"""Test that valid handover status options are returned"""
		options = get_handover_status_options()
		self.assertIn("Not Started", options)
		self.assertIn("Finder Contacted", options)
		self.assertIn("Location Shared", options)
		self.assertIn("Return Planned", options)
		self.assertIn("Handover Scheduled", options)
		self.assertIn("Recovered", options)
		self.assertIn("Closed", options)
		self.assertIn("Failed", options)

	@patch("scanifyme.recovery.services.handover_service.frappe.get_doc")
	@patch("scanifyme.recovery.services.handover_service.frappe.db.get_value")
	def test_update_handover_status_invalid(self, mock_get_value, mock_get_doc):
		"""Test that invalid handover status raises error"""
		mock_case = MagicMock()
		mock_case.name = "recovery-case-001"
		mock_case.handover_status = "Not Started"
		mock_case.owner_profile = "owner-profile-001"
		mock_get_doc.return_value = mock_case
		mock_get_value.return_value = "owner-profile-001"

		with self.assertRaises(frappe.ValidationError):
			update_handover_status(
				case_id="recovery-case-001",
				handover_status="Invalid Status",
				owner_profile="owner-profile-001",
			)

	@patch("scanifyme.recovery.services.handover_service.frappe.get_doc")
	@patch("scanifyme.recovery.services.handover_service.frappe.db.get_value")
	def test_update_handover_status_permission_denied(self, mock_get_value, mock_get_doc):
		"""Test that permission is denied for wrong owner"""
		mock_case = MagicMock()
		mock_case.name = "recovery-case-001"
		mock_case.handover_status = "Not Started"
		mock_case.owner_profile = "owner-profile-001"
		mock_get_doc.return_value = mock_case
		# Return DIFFERENT owner from what function receives, to trigger permission error
		mock_get_value.return_value = "owner-profile-001"  # Case is owned by this

		# Pass a different owner_profile - should trigger PermissionError
		with self.assertRaises(frappe.PermissionError):
			update_handover_status(
				case_id="recovery-case-001",
				handover_status="Location Shared",
				owner_profile="owner-profile-002",  # Different from case owner
			)


if __name__ == "__main__":
	unittest.main()
