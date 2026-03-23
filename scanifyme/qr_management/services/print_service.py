"""
Print Service - Business logic for QR code print operations.

This module provides functions for:
- Creating print jobs from QR batches
- Generating printable output (HTML/PDF)
- Marking tags as printed
- Managing print job lifecycle
"""

import frappe
from frappe import _
from frappe.utils import now_datetime, cint
from typing import Optional, List, Dict, Any


def create_print_job(
	print_job_name: str,
	qr_batch: Optional[str] = None,
	template_name: Optional[str] = None,
	notes: Optional[str] = None,
) -> str:
	"""Create a new QR print job.

	Args:
	    print_job_name: Name for the print job
	    qr_batch: Optional QR Batch to print
	    template_name: Optional template name
	    notes: Optional notes

	Returns:
	    QR Print Job name

	Raises:
	    frappe.PermissionError: If user doesn't have permission
	    frappe.ValidationError: If validation fails
	"""
	frappe.has_permission("QR Print Job", "create", throw=True)

	if not print_job_name:
		frappe.throw(_("Print job name is required"))

	# Count tags in batch if batch provided
	item_count = 0
	if qr_batch:
		if not frappe.db.exists("QR Batch", qr_batch):
			frappe.throw(_("QR Batch {0} not found").format(qr_batch))
		item_count = frappe.db.count("QR Code Tag", {"batch": qr_batch})

	# Create the print job
	print_job = frappe.get_doc(
		{
			"doctype": "QR Print Job",
			"print_job_name": print_job_name,
			"qr_batch": qr_batch,
			"template_name": template_name,
			"status": "Draft",
			"item_count": item_count,
			"notes": notes,
			"created_by": frappe.session.user,
		}
	)
	print_job.insert()

	frappe.db.commit()
	return print_job.name


def get_batch_printable_tags(batch_name: str, status_filter: Optional[str] = None) -> List[Dict[str, Any]]:
	"""Get printable tags from a QR batch.

	Args:
	    batch_name: QR Batch name
	    status_filter: Optional status filter (default: Generated)

	Returns:
	    List of QR tag dictionaries with print data
	"""
	filters = {"batch": batch_name}
	if status_filter:
		filters["status"] = status_filter
	else:
		# Default to tags that haven't been printed yet
		filters["status"] = ["in", ["Generated", "In Stock"]]

	tags = frappe.db.get_all(
		"QR Code Tag",
		filters=filters,
		fields=[
			"name",
			"qr_uid",
			"qr_token",
			"qr_url",
			"qr_image",
			"status",
			"batch",
			"stock_location",
		],
		order_by="creation asc",
	)

	return tags


def generate_print_output(
	print_job_name: str,
	output_format: str = "html",
) -> Dict[str, Any]:
	"""Generate print output for a QR print job.

	This creates an HTML representation of the QR codes that can be printed.
	For this phase, we generate HTML output that can be printed directly.

	Args:
	    print_job_name: QR Print Job name
	    output_format: Output format (html or pdf)

	Returns:
	    Dict with output file URL and metadata
	"""
	if not frappe.db.exists("QR Print Job", print_job_name):
		frappe.throw(_("Print job {0} not found").format(print_job_name))

	print_job = frappe.get_doc("QR Print Job", print_job_name)

	# Get tags to print
	if print_job.qr_batch:
		tags = get_batch_printable_tags(print_job.qr_batch)
	else:
		# If no batch specified, get tags linked to this print job
		tags = frappe.db.get_all(
			"QR Code Tag",
			filters={"print_job": print_job_name},
			fields=[
				"name",
				"qr_uid",
				"qr_token",
				"qr_url",
				"status",
				"batch",
				"stock_location",
			],
		)

	if not tags:
		frappe.throw(_("No tags found for printing"))

	# Generate HTML output
	html_content = _generate_printable_html(tags, print_job)

	# Save HTML to a file
	file_name = f"PrintJob_{print_job_name.replace(' ', '_')}_{now_datetime().strftime('%Y%m%d%H%M%S')}.html"

	file_doc = frappe.get_doc(
		{
			"doctype": "File",
			"file_name": file_name,
			"content": html_content,
			"is_private": 1,
			"folder": "Home/Attachments",
		}
	)
	file_doc.insert()

	# Update print job
	print_job.output_file = file_doc.file_url
	print_job.status = "Generated"
	print_job.generated_on = now_datetime()
	print_job.item_count = len(tags)
	print_job.save()

	frappe.db.commit()

	return {
		"print_job": print_job_name,
		"output_file": file_doc.file_url,
		"item_count": len(tags),
		"generated_on": str(print_job.generated_on),
	}


def _generate_printable_html(tags: List[Dict[str, Any]], print_job: Any) -> str:
	"""Generate HTML content for printing QR codes.

	Args:
	    tags: List of QR tag dictionaries
	    print_job: QR Print Job document

	Returns:
	    HTML string
	"""
	# Build tag rows
	tag_rows = ""
	for tag in tags:
		qr_url = tag.get("qr_url", "")
		qr_image = tag.get("qr_image", "")
		# Use stored QR image if available, otherwise generate inline QR
		if qr_image:
			img_src = frappe.utils.get_url() + qr_image
		else:
			# Fallback: use a QR generation service or placeholder
			img_src = f"https://api.qrserver.com/v1/create-qr-code/?size=150x150&data={qr_url}"
		tag_rows += f"""
        <div class="qr-label">
            <div class="qr-code">
                <img src="{img_src}" alt="QR Code" />
            </div>
            <div class="qr-info">
                <div class="qr-uid">{tag.get("qr_uid", "")}</div>
                <div class="qr-url">{qr_url}</div>
            </div>
        </div>
        """

	# Full HTML document
	html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>QR Print Job: {print_job.print_job_name}</title>
    <style>
        @page {{
            size: A4;
            margin: 0.5cm;
        }}
        body {{
            font-family: Arial, sans-serif;
            margin: 0;
            padding: 20px;
        }}
        .header {{
            text-align: center;
            margin-bottom: 20px;
            border-bottom: 2px solid #333;
            padding-bottom: 10px;
        }}
        .qr-label {{
            display: inline-block;
            width: 180px;
            height: 100px;
            border: 1px solid #ddd;
            margin: 5px;
            padding: 10px;
            text-align: center;
            vertical-align: top;
            page-break-inside: avoid;
        }}
        .qr-code img {{
            width: 80px;
            height: 80px;
        }}
        .qr-info {{
            font-size: 10px;
            margin-top: 5px;
        }}
        .qr-uid {{
            font-weight: bold;
            font-size: 11px;
        }}
        .qr-url {{
            font-size: 8px;
            word-break: break-all;
            color: #666;
        }}
        .footer {{
            margin-top: 20px;
            text-align: center;
            font-size: 10px;
            color: #666;
        }}
        @media print {{
            .qr-label {{
                border: 1px solid #ccc;
            }}
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>ScanifyMe QR Labels</h1>
        <p>Job: {print_job.print_job_name} | Date: {now_datetime().strftime("%Y-%m-%d %H:%M")}</p>
    </div>
    <div class="labels-container">
        {tag_rows}
    </div>
    <div class="footer">
        <p>Total Labels: {len(tags)} | Generated by ScanifyMe</p>
    </div>
</body>
</html>"""

	return html


def mark_tags_printed(print_job_name: str) -> Dict[str, Any]:
	"""Mark QR tags as printed and update their status.

	After printing, tags move from Generated to Printed status.
	They can then be moved to In Stock for distribution.

	Args:
	    print_job_name: QR Print Job name

	Returns:
	    Dict with update summary
	"""
	if not frappe.db.exists("QR Print Job", print_job_name):
		frappe.throw(_("Print job {0} not found").format(print_job_name))

	print_job = frappe.get_doc("QR Print Job", print_job_name)

	# Get tags linked to this print job
	tags = frappe.db.get_all(
		"QR Code Tag",
		filters={"print_job": print_job_name},
		fields=["name", "status"],
	)

	# Also get tags from batch if print job has batch
	if print_job.qr_batch and not tags:
		tags = frappe.db.get_all(
			"QR Code Tag",
			filters={"batch": print_job.qr_batch, "status": ["in", ["Generated", "In Stock"]]},
			fields=["name", "status"],
		)

	if not tags:
		frappe.throw(_("No tags found to mark as printed"))

	updated_count = 0
	for tag in tags:
		# Update tag status to Printed
		frappe.db.set_value(
			"QR Code Tag",
			tag.name,
			{
				"status": "Printed",
				"print_job": print_job_name,
			},
		)
		updated_count += 1

	# Update print job status
	print_job.status = "Printed"
	print_job.printed_on = now_datetime()
	print_job.save()

	# Update batch status if exists
	if print_job.qr_batch:
		frappe.db.set_value("QR Batch", print_job.qr_batch, "status", "Printed")

	frappe.db.commit()

	return {
		"print_job": print_job_name,
		"tags_updated": updated_count,
		"status": "Printed",
	}


def cancel_print_job(print_job_name: str) -> Dict[str, Any]:
	"""Cancel a QR print job.

	Args:
	    print_job_name: QR Print Job name

	Returns:
	    Dict with cancellation summary
	"""
	if not frappe.db.exists("QR Print Job", print_job_name):
		frappe.throw(_("Print job {0} not found").format(print_job_name))

	print_job = frappe.get_doc("QR Print Job", print_job_name)

	if print_job.status == "Printed":
		frappe.throw(_("Cannot cancel a printed job"))

	print_job.status = "Cancelled"
	print_job.save()

	frappe.db.commit()

	return {
		"print_job": print_job_name,
		"status": "Cancelled",
	}


def get_print_job_detail(print_job_name: str) -> Dict[str, Any]:
	"""Get detailed information about a print job.

	Args:
	    print_job_name: QR Print Job name

	Returns:
	    Dict with print job details and tags
	"""
	if not frappe.db.exists("QR Print Job", print_job_name):
		frappe.throw(_("Print job {0} not found").format(print_job_name))

	print_job = frappe.get_doc("QR Print Job", print_job_name)

	# Get tags
	tags = frappe.db.get_all(
		"QR Code Tag",
		filters={"print_job": print_job_name},
		fields=["name", "qr_uid", "qr_token", "qr_url", "qr_image", "status", "stock_location"],
	)

	# If no tags linked directly, get from batch
	if not tags and print_job.qr_batch:
		tags = frappe.db.get_all(
			"QR Code Tag",
			filters={"batch": print_job.qr_batch},
			fields=["name", "qr_uid", "qr_token", "qr_url", "qr_image", "status", "stock_location"],
		)

	return {
		"name": print_job.name,
		"print_job_name": print_job.print_job_name,
		"qr_batch": print_job.qr_batch,
		"status": print_job.status,
		"template_name": print_job.template_name,
		"output_file": print_job.output_file,
		"item_count": print_job.item_count,
		"generated_on": str(print_job.generated_on) if print_job.generated_on else None,
		"printed_on": str(print_job.printed_on) if print_job.printed_on else None,
		"created_by": print_job.created_by,
		"notes": print_job.notes,
		"tags": tags,
	}
