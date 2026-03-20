import random
import string
import frappe
from frappe import _
from frappe.utils import now_datetime
from urllib.parse import urljoin


def generate_qr_token(length: int = 10) -> str:
	"""Generate a random token for QR code.

	Args:
	    length: Token length (8-12 characters)

	Returns:
	    Random alphanumeric token
	"""
	if length < 8 or length > 12:
		length = 10

	chars = string.ascii_uppercase + string.digits
	chars = chars.replace("O", "").replace("0", "").replace("I", "").replace("1", "")

	return "".join(random.choices(chars, k=length))


def generate_qr_uid(prefix: str = None, sequence: int = None) -> str:
	"""Generate a human-readable QR UID.

	Args:
	    prefix: Optional prefix for the UID
	    sequence: Optional sequence number

	Returns:
	    Human-readable QR UID
	"""
	if sequence is not None:
		seq_str = str(sequence).zfill(6)
	else:
		seq_str = frappe.generate_hash(length=6).upper()

	if prefix:
		return f"{prefix}{seq_str}"

	return seq_str


def generate_qr_url(token: str) -> str:
	"""Generate the public URL for a QR token.

	Args:
	    token: QR token

	Returns:
	    Full public URL
	"""
	base_url = frappe.utils.get_url()
	return urljoin(base_url, f"/s/{token}")


def generate_qr_image(token: str) -> str:
	"""Generate QR code image and save using Frappe File API.

	Args:
	    token: QR token

	Returns:
	    File URL of saved QR image
	"""
	try:
		import qrcode
		from io import BytesIO
		import base64
	except ImportError:
		frappe.throw(_("qrcode library is required. Install it with: pip install qrcode[pil]"))

	qr = qrcode.QRCode(
		version=1,
		error_correction=qrcode.constants.ERROR_CORRECT_L,
		box_size=10,
		border=4,
	)

	qr_url = generate_qr_url(token)
	qr.add_data(qr_url)
	qr.make(fit=True)

	img = qr.make_image(fill_color="black", back_color="white")

	buffer = BytesIO()
	img.save(buffer, format="PNG")
	buffer.seek(0)

	img_base64 = base64.b64encode(buffer.getvalue()).decode()

	file_name = f"QR_{token}.png"

	file_doc = frappe.get_doc(
		{
			"doctype": "File",
			"file_name": file_name,
			"content": img_base64,
			"is_private": 1,
			"folder": "Home/Attachments",
		}
	)
	file_doc.insert()

	return file_doc.file_url


def get_public_qr(token: str) -> dict:
	"""Get public QR information by token.

	Args:
	    token: QR token

	Returns:
	    Dict with QR information
	"""
	qr_tag = frappe.db.get_value(
		"QR Code Tag",
		{"qr_token": token},
		["name", "qr_uid", "qr_url", "status", "registered_item"],
		as_dict=True,
	)

	if not qr_tag:
		frappe.throw(_("QR code not found"), frappe.DoesNotExistError)

	return {
		"qr_uid": qr_tag.qr_uid,
		"qr_url": qr_tag.qr_url,
		"status": qr_tag.status,
		"registered_item": qr_tag.registered_item,
	}


def generate_qr_batch(batch_name: str, batch_size: int, batch_prefix: str = None) -> str:
	"""Generate a batch of QR codes.

	Args:
	    batch_name: Name for the batch
	    batch_size: Number of QR codes to generate
	    batch_prefix: Optional prefix for QR UIDs

	Returns:
	    QR Batch name
	"""
	if batch_size <= 0 or batch_size > 10000:
		frappe.throw(_("Batch size must be between 1 and 10,000"))

	frappe.has_permission("QR Batch", "create", throw=True)

	batch = frappe.get_doc(
		{
			"doctype": "QR Batch",
			"batch_name": batch_name,
			"batch_prefix": batch_prefix,
			"batch_size": batch_size,
			"status": "Draft",
			"naming_series": "QRB-.YYYY.-",
		}
	)
	batch.insert()

	site_url = frappe.utils.get_url()

	for i in range(1, batch_size + 1):
		token = generate_qr_token()
		uid = generate_qr_uid(batch_prefix, i)
		qr_url = urljoin(site_url, f"/s/{token}")

		qr_tag = frappe.get_doc(
			{
				"doctype": "QR Code Tag",
				"qr_uid": uid,
				"qr_token": token,
				"qr_url": qr_url,
				"batch": batch.name,
				"status": "Generated",
			}
		)
		qr_tag.insert()

	batch.status = "Generated"
	batch.save()

	frappe.db.commit()

	return batch.name
