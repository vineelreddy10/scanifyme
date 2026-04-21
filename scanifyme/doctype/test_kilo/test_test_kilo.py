# Copyright (c) 2025, Scanifyme and contributors
# For license information, please see license.txt

import frappe
from frappe.tests import IntegrationTestCase


class TestTestKilo(IntegrationTestCase):
	def test_create_test_kilo(self):
		doc = frappe.get_doc({
			"doctype": "Test Kilo",
			"title": "Test Entry",
			"description": "This is a test description."
		})
		doc.insert()
		self.assertEqual(doc.title, "Test Entry")
		self.assertEqual(doc.description, "This is a test description.")
