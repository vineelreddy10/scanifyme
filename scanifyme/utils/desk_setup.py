"""
ScanifyMe Desk Setup - Python-based Workspace and Sidebar creation

This module creates Workspaces and Workspace Sidebars programmatically instead of using fixtures.
This approach is more reliable as it bypasses fixture validation issues.

Usage:
    from scanifyme.utils.desk_setup import setup_desk
    
    # After app installation
    setup_desk()
"""

import frappe
from frappe import _
from frappe.utils import nowdate


def get_or_create_doc(doctype, name, **kwargs):
    """Get existing doc or create new one if it doesn't exist."""
    # For Workspace, check by label (since that's the autoname field)
    # For Workspace Sidebar, check by title (since that's the autoname field)
    if doctype == "Workspace":
        exists = frappe.db.exists("Workspace", {"label": kwargs.get("label", name)})
    elif doctype == "Workspace Sidebar":
        exists = frappe.db.exists("Workspace Sidebar", {"title": kwargs.get("title", name)})
    else:
        exists = frappe.db.exists(doctype, name)
    
    if exists:
        if doctype == "Workspace":
            doc = frappe.get_doc("Workspace", kwargs.get("label", name))
        elif doctype == "Workspace Sidebar":
            doc = frappe.get_doc("Workspace Sidebar", kwargs.get("title", name))
        else:
            doc = frappe.get_doc(doctype, name)
        return doc, False  # exists
    else:
        # Create new doc with proper structure based on doctype
        if doctype == "Workspace":
            doc = frappe.new_doc("Workspace")
            doc.label = kwargs.get("label", name)
        elif doctype == "Workspace Sidebar":
            doc = frappe.new_doc("Workspace Sidebar")
            doc.title = kwargs.get("title", name)
        else:
            doc = frappe.new_doc(doctype)
            doc.name = name
        
        return doc, True  # created


def setup_workspaces():
    """Create or update ScanifyMe Workspaces."""
    
    workspaces_config = [
        {
            "name": "ScanifyMe",
            "title": "ScanifyMe",
            "label": "ScanifyMe",
            "icon": "qrcode",
            "indicator_color": "green",
            "module": "ScanifyMe Core",
            "content": "[]",
            "links": [
                {"type": "Card Break", "label": "QR Management", "icon": "qrcode", "link_count": 2},
                {"type": "Link", "link_type": "DocType", "link_to": "QR Batch", "label": "QR Batch"},
                {"type": "Link", "link_type": "DocType", "link_to": "QR Code Tag", "label": "QR Code Tag"},
                {"type": "Card Break", "label": "Items", "icon": "package", "link_count": 3},
                {"type": "Link", "link_type": "DocType", "link_to": "Registered Item", "label": "Registered Item"},
                {"type": "Link", "link_type": "DocType", "link_to": "Item Category", "label": "Item Category"},
                {"type": "Link", "link_type": "DocType", "link_to": "Owner Profile", "label": "Owner Profile"},
                {"type": "Card Break", "label": "Recovery", "icon": "refresh", "link_count": 1},
                {"type": "Link", "link_type": "DocType", "link_to": "Recovery Case", "label": "Recovery Case"},
                {"type": "Card Break", "label": "Notifications", "icon": "notification", "link_count": 1},
                {"type": "Link", "link_type": "DocType", "link_to": "Notification Event Log", "label": "Event Log"},
            ],
            "shortcuts": [],
        },
        {
            "name": "QR Management",
            "title": "QR Management",
            "label": "QR Management",
            "icon": "qrcode",
            "indicator_color": "blue",
            "module": "QR Management",
            "content": "[]",
            "links": [
                {"type": "Card Break", "label": "QR Codes", "icon": "qrcode", "link_count": 2},
                {"type": "Link", "link_type": "DocType", "link_to": "QR Batch", "label": "QR Batch"},
                {"type": "Link", "link_type": "DocType", "link_to": "QR Code Tag", "label": "QR Code Tag"},
                {"type": "Card Break", "label": "Distribution", "icon": "share-alt", "link_count": 1},
                {"type": "Link", "link_type": "DocType", "link_to": "QR Distribution Record", "label": "Distribution Record"},
            ],
            "shortcuts": [
                {"type": "DocType", "link_to": "QR Batch", "label": "New QR Batch"},
                {"type": "DocType", "link_to": "QR Code Tag", "label": "QR Code Tags"},
            ],
        },
        {
            "name": "Items",
            "title": "Items",
            "label": "Items",
            "icon": "package",
            "indicator_color": "orange",
            "module": "Items",
            "content": "[]",
            "links": [
                {"type": "Card Break", "label": "Items", "icon": "package", "link_count": 2},
                {"type": "Link", "link_type": "DocType", "link_to": "Registered Item", "label": "Registered Item"},
                {"type": "Link", "link_type": "DocType", "link_to": "Item Category", "label": "Item Category"},
                {"type": "Card Break", "label": "Ownership", "icon": "user", "link_count": 2},
                {"type": "Link", "link_type": "DocType", "link_to": "Owner Profile", "label": "Owner Profile"},
                {"type": "Link", "link_type": "DocType", "link_to": "Ownership Transfer", "label": "Ownership Transfer"},
            ],
            "shortcuts": [
                {"type": "DocType", "link_to": "Registered Item", "label": "New Registered Item"},
                {"type": "DocType", "link_to": "Item Category", "label": "Item Categories"},
            ],
        },
        {
            "name": "Recovery",
            "title": "Recovery",
            "label": "Recovery",
            "icon": "refresh",
            "indicator_color": "cyan",
            "module": "Recovery",
            "content": "[]",
            "links": [
                {"type": "Card Break", "label": "Recovery Cases", "icon": "refresh", "link_count": 1},
                {"type": "Link", "link_type": "DocType", "link_to": "Recovery Case", "label": "Recovery Case"},
            ],
            "shortcuts": [
                {"type": "DocType", "link_to": "Recovery Case", "label": "New Recovery Case"},
            ],
        },
        {
            "name": "Notifications",
            "title": "Notifications",
            "label": "Notifications",
            "icon": "notification",
            "indicator_color": "purple",
            "module": "Notifications",
            "content": "[]",
            "links": [
                {"type": "Card Break", "label": "Notifications", "icon": "notification", "link_count": 2},
                {"type": "Link", "link_type": "DocType", "link_to": "Notification Event Log", "label": "Event Log"},
                {"type": "Link", "link_type": "DocType", "link_to": "Notification Preference", "label": "Preferences"},
            ],
            "shortcuts": [],
        },
        {
            "name": "Masters",
            "title": "Masters",
            "label": "Masters",
            "icon": "th",
            "indicator_color": "yellow",
            "module": "ScanifyMe Core",
            "content": "[]",
            "links": [
                {"type": "Card Break", "label": "Master Data", "icon": "th", "link_count": 4},
                {"type": "Link", "link_type": "DocType", "link_to": "Item Category", "label": "Item Category"},
                {"type": "Link", "link_type": "DocType", "link_to": "Owner Profile", "label": "Owner Profile"},
                {"type": "Link", "link_type": "DocType", "link_to": "QR Customer", "label": "QR Customer"},
                {"type": "Link", "link_type": "DocType", "link_to": "ScanifyMe Settings", "label": "Settings"},
            ],
            "shortcuts": [
                {"type": "DocType", "link_to": "Item Category", "label": "New Item Category"},
                {"type": "DocType", "link_to": "Owner Profile", "label": "New Owner Profile"},
            ],
        },
    ]
    
    created = []
    updated = []
    errors = []
    
    for config in workspaces_config:
        try:
            doc, is_new = get_or_create_doc("Workspace", config["name"])
            
            # Update fields
            doc.title = config["title"]
            doc.label = config["label"]
            doc.icon = config["icon"]
            doc.indicator_color = config.get("indicator_color", "blue")
            doc.module = config["module"]
            doc.public = 1
            doc.is_public = 1
            doc.sequence_id = 0
            doc.type = "Workspace"
            doc.app = "scanifyme"
            doc.for_user = ""
            
            # Set links - use the links table field
            doc.links = []  # Clear existing
            for link_data in config.get("links", []):
                link = frappe.get_doc({
                    "doctype": "Workspace Link",
                    "type": link_data.get("type"),
                    "label": link_data.get("label"),
                    "icon": link_data.get("icon", ""),
                    "link_type": link_data.get("link_type"),
                    "link_to": link_data.get("link_to"),
                    "link_count": link_data.get("link_count", 0),
                })
                doc.links.append(link)
            
            # Set shortcuts
            doc.shortcuts = []  # Clear existing
            for shortcut_data in config.get("shortcuts", []):
                shortcut = frappe.get_doc({
                    "doctype": "Workspace Shortcut",
                    "type": shortcut_data.get("type"),
                    "link_to": shortcut_data.get("link_to"),
                    "label": shortcut_data.get("label"),
                })
                doc.shortcuts.append(shortcut)
            
            doc.flags.ignore_permissions = True
            doc.flags.ignore_links = True
            doc.save()
            
            if is_new:
                created.append(config["name"])
            else:
                updated.append(config["name"])
                
        except Exception as e:
            errors.append((config["name"], str(e)))
            # Don't call frappe functions that might fail
    
    return {
        "workspaces": {
            "created": created,
            "updated": updated,
            "errors": errors,
        }
    }


def setup_workspace_sidebars():
    """Create or update Workspace Sidebars."""
    
    sidebars_config = [
        {
            "name": "ScanifyMe",
            "title": "ScanifyMe",
            "header_icon": "qrcode",
            "module": "ScanifyMe Core",
            "items": [
                {"label": "ScanifyMe Home", "type": "Link", "link_type": "Workspace", "link_to": "ScanifyMe", "icon": "home"},
                {"label": "QR Management", "type": "Link", "link_type": "Workspace", "link_to": "QR Management", "icon": "qrcode"},
                {"label": "Items", "type": "Link", "link_type": "Workspace", "link_to": "Items", "icon": "package"},
                {"label": "Recovery", "type": "Link", "link_type": "Workspace", "link_to": "Recovery", "icon": "refresh"},
                {"label": "Notifications", "type": "Link", "link_type": "Workspace", "link_to": "Notifications", "icon": "notification"},
                {"label": "Masters", "type": "Link", "link_type": "Workspace", "link_to": "Masters", "icon": "th"},
            ],
        },
        {
            "name": "QR Management",
            "title": "QR Management",
            "header_icon": "qrcode",
            "module": "QR Management",
            "items": [
                {"label": "QR Batch", "type": "Link", "link_type": "DocType", "link_to": "QR Batch", "icon": "layer"},
                {"label": "QR Code Tag", "type": "Link", "link_type": "DocType", "link_to": "QR Code Tag", "icon": "qrcode"},
                {"label": "Distribution Records", "type": "Link", "link_type": "DocType", "link_to": "QR Distribution Record", "icon": "share-alt"},
            ],
        },
        {
            "name": "Items",
            "title": "Items",
            "header_icon": "package",
            "module": "Items",
            "items": [
                {"label": "Registered Item", "type": "Link", "link_type": "DocType", "link_to": "Registered Item", "icon": "package"},
                {"label": "Item Category", "type": "Link", "link_type": "DocType", "link_to": "Item Category", "icon": "tag"},
                {"label": "Owner Profile", "type": "Link", "link_type": "DocType", "link_to": "Owner Profile", "icon": "user"},
                {"label": "Ownership Transfer", "type": "Link", "link_type": "DocType", "link_to": "Ownership Transfer", "icon": "exchange"},
            ],
        },
        {
            "name": "Recovery",
            "title": "Recovery",
            "header_icon": "refresh",
            "module": "Recovery",
            "items": [
                {"label": "Recovery Case", "type": "Link", "link_type": "DocType", "link_to": "Recovery Case", "icon": "refresh"},
                {"label": "Scan Event", "type": "Link", "link_type": "DocType", "link_to": "Scan Event", "icon": "barcode"},
                {"label": "Finder Session", "type": "Link", "link_type": "DocType", "link_to": "Finder Session", "icon": "search"},
            ],
        },
        {
            "name": "Notifications",
            "title": "Notifications",
            "header_icon": "notification",
            "module": "Notifications",
            "items": [
                {"label": "Event Log", "type": "Link", "link_type": "DocType", "link_to": "Notification Event Log", "icon": "list"},
                {"label": "Preferences", "type": "Link", "link_type": "DocType", "link_to": "Notification Preference", "icon": "settings"},
            ],
        },
        {
            "name": "Masters",
            "title": "Masters",
            "header_icon": "th",
            "module": "ScanifyMe Core",
            "items": [
                {"label": "Item Category", "type": "Link", "link_type": "DocType", "link_to": "Item Category", "icon": "tag"},
                {"label": "Owner Profile", "type": "Link", "link_type": "DocType", "link_to": "Owner Profile", "icon": "user"},
                {"label": "QR Customer", "type": "Link", "link_type": "DocType", "link_to": "QR Customer", "icon": "customer"},
                {"label": "Settings", "type": "Link", "link_type": "DocType", "link_to": "ScanifyMe Settings", "icon": "settings"},
            ],
        },
    ]
    
    created = []
    updated = []
    errors = []
    
    for config in sidebars_config:
        try:
            doc, is_new = get_or_create_doc("Workspace Sidebar", config["name"])
            
            # Update fields
            doc.title = config["title"]
            doc.header_icon = config.get("header_icon", "")
            doc.module = config["module"]
            doc.app = "scanifyme"
            doc.standard = 1
            
            # Set items - use the items table field
            doc.items = []  # Clear existing
            for item_data in config.get("items", []):
                item = frappe.get_doc({
                    "doctype": "Workspace Sidebar Item",
                    "label": item_data.get("label"),
                    "type": item_data.get("type"),
                    "link_type": item_data.get("link_type"),
                    "link_to": item_data.get("link_to"),
                    "icon": item_data.get("icon", ""),
                })
                doc.items.append(item)
            
            doc.flags.ignore_permissions = True
            doc.flags.ignore_links = True
            doc.save()
            
            if is_new:
                created.append(config["name"])
            else:
                updated.append(config["name"])
                
        except Exception as e:
            errors.append((config["name"], str(e)))
            frappe.clear_messages()
    
    return {
        "sidebars": {
            "created": created,
            "updated": updated,
            "errors": errors,
        }
    }


def setup_desk():
    """
    Main setup function - creates Workspaces and Workspace Sidebars.
    
    This is idempotent - running multiple times is safe.
    """
    if not frappe.flags.in_install:
        frappe.flags.in_setup_wizard = True
    
    result = {}
    
    # Setup Workspaces
    result.update(setup_workspaces())
    
    # Setup Sidebars  
    result.update(setup_workspace_sidebars())
    
    # Clear cache so changes take effect
    frappe.clear_cache()
    
    return result


def after_install():
    """Hook function to run after app installation."""
    setup_desk()