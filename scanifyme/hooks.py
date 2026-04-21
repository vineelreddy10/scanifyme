app_name = "scanifyme"
app_title = "ScanifyMe"
app_publisher = "ScanifyMe"
app_description = "QR-based item recovery platform"
app_email = "support@scanifyme.app"
app_license = "mit"

# Fixtures to load on app installation
fixtures = [
	{
		"dt": "Role",
		"filters": [
			["name", "in", ["ScanifyMe User", "ScanifyMe Operations", "ScanifyMe Support", "ScanifyMe Admin"]]
		],
	},
	"Workspace",
]

# Apps
# ------------------

# required_apps = []

# Each item in the list will be shown as an app in the apps page
add_to_apps_screen = [
	{
		"name": "scanifyme",
		"logo": "/assets/scanifyme/images/logo.svg",
		"title": "ScanifyMe",
		"route": "/app/scanifyme",
		"has_permission": "scanifyme.api.permission.has_app_permission",
	}
]

# Includes in <head>
# ------------------

# include js, css files in header of desk.html
# app_include_css = "/assets/scanifyme/css/scanifyme.css"
# app_include_js = "/assets/scanifyme/js/scanifyme.js"

# include js, css files in header of web template
# web_include_css = "/assets/scanifyme/css/scanifyme.css"
# web_include_js = "/assets/scanifyme/js/scanifyme.js"

# include custom scss in every website theme (without file extension ".scss")
# website_theme_scss = "scanifyme/public/scss/website"

# include js, css files in header of web form
# webform_include_js = {"doctype": "public/js/doctype.js"}
# webform_include_css = {"doctype": "public/css/doctype.css"}

# include js in page
# page_js = {"page" : "public/js/file.js"}

# include js in doctype views
# doctype_js = {"doctype" : "public/js/doctype.js"}
# doctype_list_js = {"doctype" : "public/js/doctype_list.js"}
# doctype_tree_js = {"doctype" : "public/js/doctype_tree.js"}
# doctype_calendar_js = {"doctype" : "public/js/doctype_calendar.js"}

# Svg Icons
# ------------------
# include app icons in desk
# app_include_icons = "scanifyme/public/icons.svg"

# Home Pages
# ----------

# application home page (will override Website Settings)
# home_page = "login"

# website user home page (by Role)
# role_home_page = {
# 	"Role": "home_page"
# }

# Generators
# ----------

# automatically create page for each record of this doctype
# website_generators = ["Web Page"]

# automatically load and sync documents of this doctype from downstream apps
# importable_doctypes = [doctype_1]

# Jinja
# ----------

# add methods and filters to jinja environment
# jinja = {
# 	"methods": "scanifyme.utils.jinja_methods",
# 	"filters": "scanifyme.utils.jinja_filters"
# }

# Installation
# ------------

# before_install = "scanifyme.install.before_install"
# after_install = "scanifyme.install.after_install"

# Uninstallation
# ------------

# before_uninstall = "scanifyme.uninstall.before_uninstall"
# after_uninstall = "scanifyme.uninstall.after_uninstall"

# Integration Setup
# ------------------
# To set up dependencies/integrations with other apps
# Name of the app being installed is passed as an argument

# before_app_install = "scanifyme.utils.before_app_install"
# after_app_install = "scanifyme.utils.after_app_install"

# Integration Cleanup
# -------------------
# To clean up dependencies/integrations with other apps
# Name of the app being uninstalled is passed as an argument

# before_app_uninstall = "scanifyme.utils.before_app_uninstall"
# after_app_uninstall = "scanifyme.utils.after_app_uninstall"

# Desk Notifications
# ------------------
# See frappe.core.notifications.get_notification_config

# notification_config = "scanifyme.notifications.get_notification_config"

# Permissions
# -----------
# Permissions evaluated in scripted ways

# permission_query_conditions = {
# 	"Event": "frappe.desk.doctype.event.event.get_permission_query_conditions",
# }
#
# has_permission = {
# 	"Event": "frappe.desk.doctype.event.event.has_permission",
# }

# Document Events
# ---------------
# Hook on document methods and events

# doc_events = {
# 	"*": {
# 		"on_update": "method",
# 		"on_cancel": "method",
# 		"on_trash": "method"
# 	}
# }

# Scheduled Tasks
# ---------------

scheduler_events = {
	"hourly": [
		"scanifyme.recovery.services.cleanup_service.expire_stale_finder_sessions",
	],
	"daily": [
		"scanifyme.recovery.services.cleanup_service.recompute_case_latest_metadata",
		"scanifyme.recovery.services.cleanup_service.health_check_notification_backlog",
	],
	"weekly": [
		"scanifyme.recovery.services.cleanup_service.cleanup_old_scan_events",
	],
}

# Testing
# -------

# before_tests = "scanifyme.install.before_tests"

# Extend DocType Class
# ------------------------------
#
# Specify custom mixins to extend the standard doctype controller.
# extend_doctype_class = {
# 	"Task": "scanifyme.custom.task.CustomTaskMixin"
# }

# Overriding Methods
# ------------------------------
#
# override_whitelisted_methods = {
# 	"frappe.desk.doctype.event.event.get_events": "scanifyme.event.get_events"
# }
#
# each overriding function accepts a `data` argument;
# generated from the base implementation of the doctype dashboard,
# along with any modifications made in other Frappe apps
# override_doctype_dashboards = {
# 	"Task": "scanifyme.task.get_dashboard_data"
# }

# exempt linked doctypes from being automatically cancelled
#
# auto_cancel_exempted_doctypes = ["Auto Repeat"]

# Ignore links to specified DocTypes when deleting documents
# -----------------------------------------------------------

# ignore_links_on_delete = ["Communication", "ToDo"]

# Request Events
# ----------------
# before_request = ["scanifyme.utils.before_request"]
# after_request = ["scanifyme.utils.after_request"]

# Job Events
# ----------
# before_job = ["scanifyme.utils.before_job"]
# after_job = ["scanifyme.utils.after_job"]

# User Data Protection
# --------------------

# user_data_fields = [
# 	{
# 		"doctype": "{doctype_1}",
# 		"filter_by": "{filter_by}",
# 		"redact_fields": ["{field_1}", "{field_2}"],
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_2}",
# 		"filter_by": "{filter_by}",
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_3}",
# 		"strict": False,
# 	},
# 	{
# 		"doctype": "{doctype_4}"
# 	}
# ]

# Authentication and authorization
# --------------------------------

# auth_hooks = [
# 	"scanifyme.auth.validate"
# ]

# Automatically update python controller files with type annotations for this app.
# export_python_type_annotations = True

# default_log_clearing_doctypes = {
# 	"Logging DocType Name": 30  # days to retain logs
# }

# Translation
# ------------
# List of apps whose translatable strings should be excluded from this app's translations.
# ignore_translatable_strings_from = []


website_route_rules = [
	{"from_route": "/frontend/<path:app_path>", "to_route": "frontend"},
	{"from_route": "/s/<path:token>", "to_route": "scan_page"},
]
