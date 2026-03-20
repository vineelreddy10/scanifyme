from frappe import _


def get_data():
	return [
		{
			"module_name": "ScanifyMe Operations",
			"color": "blue",
			"icon": "octicon octicon-qr_code",
			"type": "module",
			"label": _("ScanifyMe Operations"),
			"shortcut": "QR Batch",
			"links": [
				{"type": "doctype", "doctype": "QR Batch", "label": _("QR Batches")},
				{"type": "doctype", "doctype": "QR Code Tag", "label": _("QR Code Tags")},
			],
		}
	]
