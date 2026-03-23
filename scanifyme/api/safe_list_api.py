"""
Safe List/Doc APIs - Server-driven dynamic list and detail rendering.

This module provides safe, normalized APIs for the frontend to render
DocType lists and details without raw metadata interpretation.

The backend normalizes all values into safe renderable primitives.
"""

import frappe
from frappe.utils import now_datetime, get_datetime, get_date_str, cstr
from typing import Any


# Supported fieldtypes for list view rendering
SUPPORTED_LIST_FIELDTYPES = {
	"Data",
	"Link",
	"Select",
	"Check",
	"Int",
	"Float",
	"Currency",
	"Date",
	"Datetime",
	"Time",
	"Small Text",
	"Long Text",
	"Text",
}

# Supported fieldtypes for detail view
SUPPORTED_DETAIL_FIELDTYPES = SUPPORTED_LIST_FIELDTYPES | {
	"Text Editor",
	"Code",
	"Password",
	"Email",
	"Phone",
	"URL",
	"Read Only",
}


def normalize_value(value: Any, fieldtype: str) -> str:
	"""
	Normalize a field value into a safe string for rendering.

	Rules:
	- null/undefined -> "-"
	- objects -> safe fallback string
	- booleans -> "Yes"/"No"
	- numbers -> safe numeric string
	- dates -> formatted string
	- links/select/data -> strings
	- unsupported types -> fallback string
	"""
	if value is None:
		return "-"

	if isinstance(value, (list, dict)):
		return "-"

	if fieldtype == "Check":
		return "Yes" if value else "No"

	if fieldtype in ("Int", "Currency", "Float"):
		if isinstance(value, (int, float)):
			return str(value)
		return cstr(value) if value else "-"

	if fieldtype in ("Date", "Datetime"):
		if isinstance(value, str):
			try:
				dt = get_datetime(value)
				if fieldtype == "Date":
					return get_date_str(dt)
				return dt.strftime("%Y-%m-%d %H:%M")
			except (ValueError, TypeError):
				return value[:16] if len(value) > 16 else value
		elif hasattr(value, "strftime"):
			if fieldtype == "Date":
				return get_date_str(value)
			return value.strftime("%Y-%m-%d %H:%M")
		return cstr(value) or "-"

	if fieldtype == "Link":
		if isinstance(value, str) and "." in value:
			return value.split(".")[-1]
		return cstr(value) or "-"

	if isinstance(value, bool):
		return "Yes" if value else "No"

	if isinstance(value, (int, float)):
		return str(value)

	return cstr(value) or "-"


@frappe.whitelist()
def get_safe_list_schema(doctype: str) -> dict:
	"""
	Get a safe, normalized list schema for a DocType.

	This API:
	- Validates doctype existence
	- Enforces permissions
	- Uses Frappe metadata
	- Returns only supported/safe fields
	- Never leaks raw objects or tracebacks

	Returns:
	    {
	        "doctype": str,
	        "title": str,
	        "columns": [
	            {
	                "fieldname": str,
	                "label": str,
	                "fieldtype": str,
	                "in_list_view": 1,
	                "width": str | None
	            }
	        ],
	        "permissions": {
	            "can_read": bool,
	            "can_write": bool,
	            "can_create": bool,
	            "can_delete": bool
	        },
	        "sort_field": str,
	        "sort_order": str
	    }
	"""
	if not doctype:
		frappe.throw("DocType name is required")

	try:
		meta = frappe.get_meta(doctype)
	except frappe.DoesNotExistError:
		frappe.throw(f"DocType '{doctype}' does not exist")

	if not frappe.has_permission(doctype, "read"):
		frappe.throw(f"Permission denied for DocType '{doctype}'", frappe.PermissionError)

	columns = []

	# Always include 'name' first
	columns.append(
		{"fieldname": "name", "label": "ID", "fieldtype": "Data", "in_list_view": 1, "width": None}
	)

	# Add list view fields
	seen_fields = {"name"}
	for field in meta.get("fields"):
		if field.fieldname in seen_fields:
			continue

		# Skip unsupported fieldtypes
		if field.fieldtype not in SUPPORTED_LIST_FIELDTYPES:
			continue

		# Skip Section/Column/Tab breaks
		if field.fieldtype in ("Section Break", "Column Break", "Tab Break"):
			continue

		# Include if in_list_view
		if field.in_list_view:
			columns.append(
				{
					"fieldname": field.fieldname,
					"label": field.label or field.fieldname,
					"fieldtype": field.fieldtype,
					"in_list_view": 1,
					"width": None,
				}
			)
			seen_fields.add(field.fieldname)

	# If no list view fields, add fallback fields (first few Data/Link fields)
	if len(columns) == 1:
		for field in meta.get("fields"):
			if field.fieldname in seen_fields:
				continue
			if field.fieldtype in ("Data", "Link", "Select"):
				columns.append(
					{
						"fieldname": field.fieldname,
						"label": field.label or field.fieldname,
						"fieldtype": field.fieldtype,
						"in_list_view": 1,
						"width": None,
					}
				)
				seen_fields.add(field.fieldname)
				if len(columns) >= 4:  # Limit to 4 fallback columns
					break

	return {
		"doctype": meta.name,
		"title": meta.label if hasattr(meta, "label") and meta.label else meta.name,
		"columns": columns,
		"permissions": {
			"can_read": frappe.has_permission(doctype, "read"),
			"can_write": frappe.has_permission(doctype, "write"),
			"can_create": frappe.has_permission(doctype, "create"),
			"can_delete": frappe.has_permission(doctype, "delete"),
		},
		"sort_field": meta.sort_field if hasattr(meta, "sort_field") and meta.sort_field else "modified",
		"sort_order": meta.sort_order if hasattr(meta, "sort_order") and meta.sort_order else "DESC",
	}


@frappe.whitelist()
def get_safe_list_rows(
	doctype: str,
	filters: str | dict | None = None,
	order_by: str = None,
	page_length: int = 20,
	start: int = 0,
	search: str = None,
) -> dict:
	"""
	Get safe, normalized list rows for a DocType.

	This API:
	- Validates doctype existence
	- Enforces permissions
	- Uses Frappe list APIs
	- Normalizes all values into safe strings
	- Returns only required fields

	Returns:
	    {
	        "rows": [
	            {
	                "name": str,
	                "values": {fieldname: value},
	                "display_values": {fieldname: safe_string}
	            }
	        ],
	        "total_count": int,
	        "page": int,
	        "page_length": int
	    }
	"""
	if not doctype:
		frappe.throw("DocType name is required")

	try:
		meta = frappe.get_meta(doctype)
	except frappe.DoesNotExistError:
		frappe.throw(f"DocType '{doctype}' does not exist")

	if not frappe.has_permission(doctype, "read"):
		frappe.throw(f"Permission denied for DocType '{doctype}'", frappe.PermissionError)

	# Get list schema to know which fields to fetch
	try:
		schema = get_safe_list_schema(doctype)
		columns = schema.get("columns", [])
		fieldnames = [col["fieldname"] for col in columns]
	except Exception:
		# Fallback to just name
		fieldnames = ["name"]

	# Parse filters
	filters_list = []
	if filters:
		try:
			# Handle both string and dict formats
			if isinstance(filters, str):
				filters_list = frappe.parse_json(filters)
			elif isinstance(filters, dict):
				filters_list = filters
			else:
				filters_list = []
		except Exception:
			pass

	# Default order_by
	if not order_by:
		sort_field = meta.sort_field if hasattr(meta, "sort_field") and meta.sort_field else "modified"
		sort_order = meta.sort_order if hasattr(meta, "sort_order") and meta.sort_order else "DESC"
		order_by = f"{sort_field} {sort_order}"

	# Get total count
	try:
		total_count = (
			frappe.db.count(doctype, filters=filters_list) if filters_list else frappe.db.count(doctype)
		)
	except Exception:
		total_count = 0

	# Build field list for query (always include name)
	query_fields = ["name"]
	for fn in fieldnames:
		if fn != "name" and fn not in query_fields:
			query_fields.append(fn)

	# Get documents
	try:
		docs = frappe.get_list(
			doctype,
			filters=filters_list if filters_list else None,
			order_by=order_by,
			start=start,
			page_length=page_length,
			fields=query_fields,
		)
	except Exception as e:
		frappe.log_error(f"Error fetching list for {doctype}: {str(e)}")
		frappe.throw(f"Error fetching data: {str(e)}")

	# Normalize rows
	rows = []
	fieldtype_map = {col["fieldname"]: col["fieldtype"] for col in columns}

	for doc in docs:
		values = {}
		display_values = {}

		for fieldname in query_fields:
			value = doc.get(fieldname)
			values[fieldname] = value

			fieldtype = fieldtype_map.get(fieldname, "Data")
			display_values[fieldname] = normalize_value(value, fieldtype)

		rows.append({"name": doc.get("name"), "values": values, "display_values": display_values})

	return {
		"rows": rows,
		"total_count": total_count,
		"page": (start // page_length) + 1 if page_length > 0 else 1,
		"page_length": page_length,
	}


@frappe.whitelist()
def get_safe_detail_schema(doctype: str) -> dict:
	"""
	Get a safe, normalized detail schema for a DocType.

	Returns:
	    {
	        "doctype": str,
	        "title": str,
	        "fields": [
	            {
	                "fieldname": str,
	                "label": str,
	                "fieldtype": str,
	                "options": str | None,
	                "read_only": bool,
	                "reqd": bool
	            }
	        ],
	        "permissions": {
	            "can_read": bool,
	            "can_write": bool,
	            "can_create": bool,
	            "can_delete": bool
	        }
	    }
	"""
	if not doctype:
		frappe.throw("DocType name is required")

	try:
		meta = frappe.get_meta(doctype)
	except frappe.DoesNotExistError:
		frappe.throw(f"DocType '{doctype}' does not exist")

	if not frappe.has_permission(doctype, "read"):
		frappe.throw(f"Permission denied for DocType '{doctype}'", frappe.PermissionError)

	fields = []

	for field in meta.get("fields"):
		# Skip unsupported fieldtypes
		if field.fieldtype not in SUPPORTED_DETAIL_FIELDTYPES:
			continue

		# Skip Section/Column/Tab breaks (frontend handles these)
		if field.fieldtype in ("Section Break", "Column Break", "Tab Break"):
			continue

		field_info = {
			"fieldname": field.fieldname,
			"label": field.label or field.fieldname,
			"fieldtype": field.fieldtype,
			"options": field.options if hasattr(field, "options") else None,
			"read_only": bool(field.read_only) if hasattr(field, "read_only") else False,
			"reqd": bool(field.reqd) if hasattr(field, "reqd") else False,
		}

		# Get options for Select fields
		if field.fieldtype == "Select" and field.options:
			field_info["options_list"] = [opt.strip() for opt in field.options.split("\n") if opt.strip()]

		fields.append(field_info)

	return {
		"doctype": meta.name,
		"title": meta.label if hasattr(meta, "label") and meta.label else meta.name,
		"fields": fields,
		"permissions": {
			"can_read": frappe.has_permission(doctype, "read"),
			"can_write": frappe.has_permission(doctype, "write"),
			"can_create": frappe.has_permission(doctype, "create"),
			"can_delete": frappe.has_permission(doctype, "delete"),
		},
	}


@frappe.whitelist()
def get_safe_detail_doc(doctype: str, name: str) -> dict:
	"""
	Get a safe, normalized document for detail view.

	Returns:
	    {
	        "doctype": str,
	        "name": str,
	        "values": {fieldname: value},
	        "display_values": {fieldname: safe_string},
	        "permissions": {
	            "can_read": bool,
	            "can_write": bool
	        }
	    }
	"""
	if not doctype:
		frappe.throw("DocType name is required")

	if not name:
		frappe.throw("Document name is required")

	try:
		meta = frappe.get_meta(doctype)
	except frappe.DoesNotExistError:
		frappe.throw(f"DocType '{doctype}' does not exist")

	if not frappe.has_permission(doctype, "read", doc=name):
		frappe.throw(f"Permission denied for document '{name}'", frappe.PermissionError)

	try:
		doc = frappe.get_doc(doctype, name)
	except frappe.DoesNotExistError:
		frappe.throw(f"Document '{name}' does not exist in {doctype}")

	# Get schema for fieldtypes
	try:
		schema = get_safe_detail_schema(doctype)
		fields = schema.get("fields", [])
	except Exception:
		fields = []

	fieldtype_map = {f["fieldname"]: f["fieldtype"] for f in fields}

	values = {}
	display_values = {}

	# Get all field values
	for field in meta.get("fields"):
		fieldname = field.fieldname
		value = doc.get(fieldname)
		values[fieldname] = value

		fieldtype = fieldtype_map.get(fieldname, field.fieldtype)
		display_values[fieldname] = normalize_value(value, fieldtype)

	return {
		"doctype": doctype,
		"name": name,
		"values": values,
		"display_values": display_values,
		"permissions": {
			"can_read": frappe.has_permission(doctype, "read", doc=name),
			"can_write": frappe.has_permission(doctype, "write", doc=name),
		},
	}


@frappe.whitelist()
def create_safe_doc(doctype: str, values: str = None) -> dict:
	"""
	Create a new document with safe validation.

	Args:
	    doctype: The DocType name
	    values: JSON string of field values to set

	Returns:
	    {
	        "success": bool,
	        "data": {
	            "name": str,
	            "doctype": str
	        },
	        "error": str | None
	    }
	"""
	if not doctype:
		return {"success": False, "error": "DocType name is required"}

	try:
		meta = frappe.get_meta(doctype)
	except frappe.DoesNotExistError:
		return {"success": False, "error": f"DocType '{doctype}' does not exist"}

	if not frappe.has_permission(doctype, "create"):
		return {"success": False, "error": "Permission denied: You cannot create this document"}

	# Parse values from JSON
	doc_values = {}
	if values:
		try:
			doc_values = frappe.parse_json(values)
		except Exception:
			return {"success": False, "error": "Invalid values format"}

	# Validate required fields
	for field in meta.get("fields"):
		if field.reqd and field.fieldname not in doc_values:
			if not doc_values.get(field.fieldname):
				return {"success": False, "error": f"Required field '{field.label}' is missing"}

		try:
			doc = frappe.get_doc({"doctype": doctype})
			for key, value in doc_values.items():
				doc.set(key, value)
			doc.insert(ignore_permissions=True)
			return {"success": True, "data": {"name": doc.name, "doctype": doctype}}
		except frappe.ValidationError as e:
			return {"success": False, "error": str(e)}
		except Exception as e:
			frappe.log_error(f"Error creating {doctype}: {str(e)}")
			return {"success": False, "error": "Failed to create document"}


@frappe.whitelist()
def update_safe_doc(doctype: str, name: str, values: str = None) -> dict:
	"""
	Update an existing document with safe validation.

	Args:
	    doctype: The DocType name
	    name: The document name
	    values: JSON string of field values to update

	Returns:
	    {
	        "success": bool,
	        "data": {
	            "name": str,
	            "doctype": str
	        },
	        "error": str | None
	    }
	"""
	if not doctype:
		return {"success": False, "error": "DocType name is required"}

	if not name:
		return {"success": False, "error": "Document name is required"}

	try:
		meta = frappe.get_meta(doctype)
	except frappe.DoesNotExistError:
		return {"success": False, "error": f"DocType '{doctype}' does not exist"}

	if not frappe.has_permission(doctype, "write", doc=name):
		return {"success": False, "error": "Permission denied: You cannot edit this document"}

	try:
		doc = frappe.get_doc(doctype, name)
	except frappe.DoesNotExistError:
		return {"success": False, "error": f"Document '{name}' not found in {doctype}"}

	# Parse values from JSON
	doc_values = {}
	if values:
		try:
			doc_values = frappe.parse_json(values)
		except Exception:
			return {"success": False, "error": "Invalid values format"}

	# Update fields (only allowed ones)
	for key, value in doc_values.items():
		if key not in ("doctype", "name", "owner", "creation", "modified", "modified_by"):
			doc.set(key, value)

	try:
		doc.save(ignore_permissions=True)
		return {"success": True, "data": {"name": doc.name, "doctype": doctype}}
	except frappe.ValidationError as e:
		return {"success": False, "error": str(e)}
	except Exception as e:
		frappe.log_error(f"Error updating {doctype}/{name}: {str(e)}")
		return {"success": False, "error": "Failed to update document"}


@frappe.whitelist()
def delete_safe_doc(doctype: str, name: str) -> dict:
	"""
	Delete an existing document with permission check.

	Args:
	    doctype: The DocType name
	    name: The document name

	Returns:
	    {
	        "success": bool,
	        "error": str | None
	    }
	"""
	if not doctype:
		return {"success": False, "error": "DocType name is required"}

	if not name:
		return {"success": False, "error": "Document name is required"}

	try:
		meta = frappe.get_meta(doctype)
	except frappe.DoesNotExistError:
		return {"success": False, "error": f"DocType '{doctype}' does not exist"}

	if not frappe.has_permission(doctype, "delete", doc=name):
		return {"success": False, "error": "Permission denied: You cannot delete this document"}

	try:
		doc = frappe.get_doc(doctype, name)
		frappe.delete_doc(doctype, name, ignore_permissions=True)
		return {"success": True}
	except frappe.DoesNotExistError:
		return {"success": False, "error": f"Document '{name}' not found in {doctype}"}
	except Exception as e:
		frappe.log_error(f"Error deleting {doctype}/{name}: {str(e)}")
		return {"success": False, "error": "Failed to delete document"}
