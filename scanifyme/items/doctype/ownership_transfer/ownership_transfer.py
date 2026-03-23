import frappe
from frappe.model.document import Document
from frappe.utils import now_datetime
import secrets


class OwnershipTransfer(Document):
	"""Ownership Transfer DocType controller"""

	def validate(self):
		"""Validate the ownership transfer"""
		if not self.transfer_token:
			self.transfer_token = self.generate_transfer_token()

		if not self.created_on:
			self.created_on = now_datetime()

		# Validate item ownership
		if self.item and self.from_owner:
			item = frappe.get_doc("Registered Item", self.item)
			if item.owner_profile != self.from_owner:
				frappe.throw("The item does not belong to the specified owner.")

	def generate_transfer_token(self) -> str:
		"""Generate a unique transfer token"""
		return secrets.token_urlsafe(16)

	def approve(self):
		"""Approve the transfer"""
		if self.status != "Pending":
			frappe.throw("Can only approve pending transfers.")

		self.status = "Approved"
		self.completed_on = now_datetime()
		self.save(ignore_permissions=True)

		# Update item ownership
		item = frappe.get_doc("Registered Item", self.item)
		item.owner_profile = self.to_owner
		item.save(ignore_permissions=True)

	def reject(self, reason: str = None):
		"""Reject the transfer"""
		if self.status != "Pending":
			frappe.throw("Can only reject pending transfers.")

		self.status = "Rejected"
		if reason:
			self.notes = reason
		self.save(ignore_permissions=True)

	def complete(self):
		"""Mark the transfer as completed"""
		if self.status != "Approved":
			frappe.throw("Can only complete approved transfers.")

		self.status = "Completed"
		self.completed_on = now_datetime()
		self.save(ignore_permissions=True)


def create_transfer_request(item: str, to_owner: str) -> str:
	"""
	Create a transfer request for an item.

	Args:
	    item: Registered Item name
	    to_owner: Target Owner Profile name

	Returns:
	    Transfer request name
	"""
	# Get current owner
	item_doc = frappe.get_doc("Registered Item", item)

	# Create transfer request
	transfer = frappe.get_doc(
		{
			"doctype": "Ownership Transfer",
			"item": item,
			"from_owner": item_doc.owner_profile,
			"to_owner": to_owner,
			"status": "Pending",
		}
	)
	transfer.insert()

	return transfer.name
