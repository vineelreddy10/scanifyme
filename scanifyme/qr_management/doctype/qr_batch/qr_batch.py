import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import now_datetime


class QRBatch(Document):
	def validate(self):
		if self.batch_size and self.batch_size <= 0:
			frappe.throw(_("Batch size must be greater than 0"))

		if self.batch_size and self.batch_size > 10000:
			frappe.throw(_("Batch size cannot exceed 10,000 QR codes per batch"))

	def before_insert(self):
		if not self.created_by:
			self.created_by = frappe.session.user
		if not self.created_on:
			self.created_on = now_datetime()
