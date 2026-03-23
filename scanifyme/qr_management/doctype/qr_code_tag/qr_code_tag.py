import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import now_datetime


class QRCodeTag(Document):
	def validate(self):
		if self.qr_token:
			if len(self.qr_token) < 8 or len(self.qr_token) > 12:
				frappe.throw(_("QR token must be 8-12 characters long"))

	def before_insert(self):
		if not self.created_on:
			self.created_on = now_datetime()
