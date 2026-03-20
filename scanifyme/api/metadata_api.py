"""
Metadata API - Whitelisted API methods for DocType metadata.

This module provides API endpoints for fetching DocType metadata
(field definitions, labels, types, options) for the generic list page.
"""

import frappe


@frappe.whitelist()
def get_doctype_meta(doctype: str) -> dict:
	"""
	Get metadata for a DocType including field definitions.

	Args:
	    doctype: Name of the DocType (e.g., "Item Category", "QR Batch")

	Returns:
	    Dict containing:
	    - name: DocType name
	    - label: DocType label
	    - fields: List of field definitions with fieldname, label, fieldtype, options, in_list_view, in_standard_filter
	    - title_field: Title field for the doctype
	    - sort_field: Default sort field
	    - sort_order: Default sort order
	"""
	if not doctype:
		frappe.throw("DocType name is required")

	# Validate doctype exists and user has permission
	try:
		meta = frappe.get_meta(doctype)
	except frappe.DoesNotExistError:
		frappe.throw(f"DocType '{doctype}' does not exist")

	# Check if user has read permission (at least)
	if not frappe.has_permission(doctype, "read"):
		frappe.throw(f"Permission denied for DocType '{doctype}'", frappe.PermissionError)

	# Extract field information
	fields = []
	for field in meta.get("fields"):
		# Skip Section Breaks, Column Breaks, and Table fields for list view
		if field.fieldtype in ("Section Break", "Column Break", "Tab Break"):
			continue

		field_info = {
			"fieldname": field.fieldname,
			"label": field.label,
			"fieldtype": field.fieldtype,
			"options": field.options if hasattr(field, "options") else None,
			"in_list_view": bool(field.in_list_view) if hasattr(field, "in_list_view") else False,
			"in_standard_filter": bool(field.in_standard_filter)
			if hasattr(field, "in_standard_filter")
			else False,
			"read_only": bool(field.read_only) if hasattr(field, "read_only") else False,
			"reqd": bool(field.reqd) if hasattr(field, "reqd") else False,
		}

		# Get options for Select fields
		if field.fieldtype == "Select" and field.options:
			field_info["options_list"] = [opt.strip() for opt in field.options.split("\n") if opt.strip()]

		fields.append(field_info)

	# Build response
	return {
		"name": meta.name,
		"label": meta.label if hasattr(meta, "label") else meta.name,
		"fields": fields,
		"title_field": meta.title_field if hasattr(meta, "title_field") and meta.title_field else None,
		"sort_field": meta.sort_field if hasattr(meta, "sort_field") else "modified",
		"sort_order": meta.sort_order if hasattr(meta, "sort_order") else "DESC",
		"editable_grid": bool(meta.editable_grid) if hasattr(meta, "editable_grid") else False,
	}


@frappe.whitelist()
def get_doctype_list(
	doctype: str,
	fields: str = None,
	filters: str = None,
	or_filters: str = None,
	order_by: str = None,
	limit_start: int = 0,
	limit_page_length: int = 20,
) -> dict:
	"""
	Get a list of documents for a DocType with pagination.

	Args:
	    doctype: Name of the DocType
	    fields: JSON string of fields to fetch (default: ["name"])
	    filters: JSON string of AND filters (default: [])
	    or_filters: JSON string of OR filters (default: [])
	    order_by: Order by clause (default: "modified DESC")
	    limit_start: Starting offset for pagination (default: 0)
	    limit_page_length: Number of records per page (default: 20)

	Returns:
	    Dict containing:
	    - data: List of documents
	    - total_count: Total number of matching documents
	"""
	if not doctype:
		frappe.throw("DocType name is required")

	# Validate doctype exists
	try:
		meta = frappe.get_meta(doctype)
	except frappe.DoesNotExistError:
		frappe.throw(f"DocType '{doctype}' does not exist")

	# Check if user has read permission
	if not frappe.has_permission(doctype, "read"):
		frappe.throw(f"Permission denied for DocType '{doctype}'", frappe.PermissionError)

	# Parse fields
	fields_list = ["name"]  # Always include name
	if fields:
		try:
			parsed_fields = frappe.parse_json(fields)
			if isinstance(parsed_fields, list):
				fields_list = parsed_fields
		except Exception:
			frappe.throw("Invalid fields format")

	# Parse filters
	filters_list = []
	if filters:
		try:
			filters_list = frappe.parse_json(filters)
		except Exception:
			frappe.throw("Invalid filters format")

	# Parse or_filters
	or_filters_list = []
	if or_filters:
		try:
			or_filters_list = frappe.parse_json(or_filters)
		except Exception:
			frappe.throw("Invalid or_filters format")

	# Default order_by
	if not order_by:
		order_by = f"{meta.sort_field or 'modified'} {meta.sort_order or 'DESC'}"

	# Get total count
	try:
		total_count = (
			frappe.db.count(doctype, filters=filters_list) if filters_list else frappe.db.count(doctype)
		)
	except Exception:
		total_count = 0

	# Get documents
	try:
		# Build kwargs for get_list
		list_kwargs = {
			"doctype": doctype,
			"filters": filters_list if filters_list else None,
			"or_filters": or_filters_list if or_filters_list else None,
			"order_by": order_by,
			"start": limit_start,
			"page_length": limit_page_length,
		}

		# Only include fields if explicitly requested (empty list = all fields)
		if fields_list and fields_list != ["*"]:
			list_kwargs["fields"] = fields_list

		docs = frappe.get_list(**list_kwargs)

	except Exception as e:
		frappe.log_error(f"Error fetching list for {doctype}: {str(e)}")
		frappe.throw(f"Error fetching data: {str(e)}")

	return {
		"data": docs,
		"total_count": total_count,
	}


@frappe.whitelist()
def get_list_view_fields(doctype: str) -> list:
	"""
	Get the default list view fields for a DocType.

	Args:
	    doctype: Name of the DocType

	Returns:
	    List of fieldnames that should be shown in list view by default
	"""
	if not doctype:
		frappe.throw("DocType name is required")

	try:
		meta = frappe.get_meta(doctype)
	except frappe.DoesNotExistError:
		frappe.throw(f"DocType '{doctype}' does not exist")

	# Get fields that are marked for list view
	list_view_fields = []
	for field in meta.get("fields"):
		if field.in_list_view and field.fieldtype not in ("Section Break", "Column Break", "Tab Break"):
			list_view_fields.append(field.fieldname)

	return list_view_fields
