import frappe
from frappe.model.document import Document
from frappe.utils import now_datetime


class OwnerProfile(Document):
	"""Owner Profile DocType controller"""

	def validate(self):
		"""Validate the owner profile"""
		if not self.display_name:
			self.display_name = frappe.utils.get_fullname(self.user)

		if not self.created_on:
			self.created_on = now_datetime()

		self.modified_on = now_datetime()

	def update_item_counts(self):
		"""Update the item count fields based on registered items"""
		if not self.user:
			return

		# Get counts from registered items
		total = frappe.db.count("Registered Item", {"owner_profile": self.name})
		active = frappe.db.count("Registered Item", {"owner_profile": self.name, "status": "Active"})
		recovered = frappe.db.count("Registered Item", {"owner_profile": self.name, "status": "Recovered"})

		self.total_items = total or 0
		self.active_items = active or 0
		self.recovered_items = recovered or 0


def get_owner_profile(user: str = None) -> str:
	"""
	Get or create owner profile for a user.

	Args:
	    user: User email. If None, uses current user.

	Returns:
	    Owner Profile name
	"""
	if not user:
		user = frappe.session.user

	# Check if profile exists
	existing = frappe.db.get_value("Owner Profile", {"user": user}, "name")

	if existing:
		return existing

	# Create new profile
	profile = frappe.get_doc(
		{
			"doctype": "Owner Profile",
			"user": user,
			"display_name": frappe.utils.get_fullname(user),
		}
	)
	profile.insert()

	return profile.name
