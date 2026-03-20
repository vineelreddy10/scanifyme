import frappe
from frappe.model.document import Document
from frappe.utils import now_datetime


class RegisteredItem(Document):
	"""Registered Item DocType controller"""

	def validate(self):
		"""Validate the registered item"""
		# Check that QR code tag is not already linked to another active item
		if self.qr_code_tag:
			existing = frappe.db.get_value(
				"Registered Item",
				{
					"qr_code_tag": self.qr_code_tag,
					"status": ["in", ["Active", "Lost"]],
					"name": ["!=", self.name],
				},
				"name",
			)
			if existing:
				frappe.throw(
					f"QR Code Tag is already linked to another active item. Unlink the existing item first."
				)

		# Set activation date if status changes to Active
		if self.status == "Active" and not self.activation_date:
			self.activation_date = now_datetime()

	def on_update(self):
		"""Update QR code tag status when item is activated"""
		if self.status == "Active" and self.qr_code_tag:
			# Update QR code tag status
			qr_tag = frappe.get_doc("QR Code Tag", self.qr_code_tag)
			if qr_tag.status != "Activated":
				qr_tag.status = "Activated"
				qr_tag.registered_item = self.name
				qr_tag.save(ignore_permissions=True)

	def update_last_scan(self):
		"""Update the last scan timestamp"""
		self.last_scan_at = now_datetime()
		self.save(ignore_permissions=True)


def get_item_for_qr(qr_token: str) -> dict:
	"""
	Get item details for a QR token.

	Args:
	    qr_token: The QR code token

	Returns:
	    Item details or None
	"""
	qr_tag = frappe.db.get_value("QR Code Tag", {"qr_token": qr_token}, "name", order_by="creation desc")

	if not qr_tag:
		return None

	item = frappe.db.get_value(
		"Registered Item",
		{"qr_code_tag": qr_tag, "status": ["in", ["Active", "Lost"]]},
		"name",
		order_by="creation desc",
	)

	if not item:
		return None

	return frappe.get_doc("Registered Item", item)
