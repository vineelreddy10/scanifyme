import frappe
from frappe.model.document import Document


class ItemCategory(Document):
	"""Item Category DocType controller"""

	def validate(self):
		"""Validate the item category"""
		if not self.category_code:
			# Generate category code from name
			import re

			self.category_code = re.sub(r"[^a-zA-Z0-9]", "_", self.category_name.upper())

	def update_item_count(self):
		"""Update the item count based on registered items"""
		if self.name:
			count = frappe.db.count("Registered Item", {"item_category": self.name})
			self.item_count = count or 0
