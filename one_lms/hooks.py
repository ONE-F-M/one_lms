from . import __version__ as app_version

app_name = "one_lms"
app_title = "Learning Management by ONE FM"
app_publisher = "One Facilities Management"
app_description = "Extention to Frappe LMS"
app_email = "info@one-fm.com"
app_license = "MIT"




# Includes in <head>
# ------------------

# include js, css files in header of desk.html
# app_include_css = "/assets/one_lms/css/one_lms.css"
# app_include_js = "/assets/one_lms/js/one_lms.js"

# include js, css files in header of web template
# web_include_css = "/assets/one_lms/css/one_lms.css"
# web_include_js = "/assets/one_lms/js/one_lms.js"

# include custom scss in every website theme (without file extension ".scss")
# website_theme_scss = "one_lms/public/scss/website"

# include js, css files in header of web form
# webform_include_js = {"doctype": "public/js/doctype.js"}
# webform_include_css = {"doctype": "public/css/doctype.css"}

# include js in page
# page_js = {"page" : "public/js/file.js"}

# include js in doctype views
doctype_js = {
    "Course Lesson" : "public/js/doctype_js/course_lesson.js"
}
# doctype_list_js = {"doctype" : "public/js/doctype_list.js"}
# doctype_tree_js = {"doctype" : "public/js/doctype_tree.js"}
# doctype_calendar_js = {"doctype" : "public/js/doctype_calendar.js"}

# Home Pages
# ----------

# application home page (will override Website Settings)
# home_page = "login"

# website user home page (by Role)
# role_home_page = {
#	"Role": "home_page"
# }

# Generators
# ----------

# automatically create page for each record of this doctype
# website_generators = ["Web Page"]

# Jinja
# ----------

# add methods and filters to jinja environment
# jinja = {
#	"methods": "one_lms.utils.jinja_methods",
#	"filters": "one_lms.utils.jinja_filters"
# }

# Installation
# ------------

# before_install = "one_lms.install.before_install"
# after_install = "one_lms.install.after_install"

# Uninstallation
# ------------

# before_uninstall = "one_lms.uninstall.before_uninstall"
# after_uninstall = "one_lms.uninstall.after_uninstall"

# Desk Notifications
# ------------------
# See frappe.core.notifications.get_notification_config

# notification_config = "one_lms.notifications.get_notification_config"

# Permissions
# -----------
# Permissions evaluated in scripted ways

# permission_query_conditions = {
#	"Event": "frappe.desk.doctype.event.event.get_permission_query_conditions",
# }
#
# has_permission = {
#	"Event": "frappe.desk.doctype.event.event.has_permission",
# }

# DocType Class
# ---------------
# Override standard doctype classes

override_doctype_class = {
	"LMS Certificate": "one_lms.overrides.lms_certificate.CustomLMSCertificate"
}

# Document Events
# ---------------
# Hook on document methods and events

# doc_events = {
#	"*": {
#		"on_update": "method",
#		"on_cancel": "method",
#		"on_trash": "method"
#	}
# }
doc_events = {
  "LMS Batch Membership":{
    'validate':'one_lms.overrides.lms_batch_membership.validate_current_lesson'
  },
	"Course Lesson": {
		"validate": "one_lms.overrides.course_lesson.validate_course_lesson"
	}
}

# Scheduled Tasks
# ---------------

# scheduler_events = {
#	"all": [
#		"one_lms.tasks.all"
#	],
#	"daily": [
#		"one_lms.tasks.daily"
#	],
#	"hourly": [
#		"one_lms.tasks.hourly"
#	],
#	"weekly": [
#		"one_lms.tasks.weekly"
#	],
#	"monthly": [
#		"one_lms.tasks.monthly"
#	],
# }

# Testing
# -------



# before_tests = "one_lms.install.before_tests"

# Overriding Methods
# ------------------------------
#
# override_whitelisted_methods = {
#	"frappe.desk.doctype.event.event.get_events": "one_lms.event.get_events"
# }
#
# each overriding function accepts a `data` argument;
# generated from the base implementation of the doctype dashboard,
# along with any modifications made in other Frappe apps
# override_doctype_dashboards = {
#	"Task": "one_lms.task.get_dashboard_data"
# }

# exempt linked doctypes from being automatically cancelled
#
# auto_cancel_exempted_doctypes = ["Auto Repeat"]

# Ignore links to specified DocTypes when deleting documents
# -----------------------------------------------------------

# ignore_links_on_delete = ["Communication", "ToDo"]

# Request Events
# ----------------
# before_request = ["one_lms.utils.before_request"]
# after_request = ["one_lms.utils.after_request"]

# Job Events
# ----------
# before_job = ["one_lms.utils.before_job"]
# after_job = ["one_lms.utils.after_job"]

# User Data Protection
# --------------------

# user_data_fields = [
#	{
#		"doctype": "{doctype_1}",
#		"filter_by": "{filter_by}",
#		"redact_fields": ["{field_1}", "{field_2}"],
#		"partial": 1,
#	},
#	{
#		"doctype": "{doctype_2}",
#		"filter_by": "{filter_by}",
#		"partial": 1,
#	},
#	{
#		"doctype": "{doctype_3}",
#		"strict": False,
#	},
#	{
#		"doctype": "{doctype_4}"
#	}
# ]

# Authentication and authorization
# --------------------------------

# auth_hooks = [
#	"one_lms.auth.validate"
# ]



required_apps = ['frappe', "lms"]



website_route_rules = [
	{"from_route": "/batch/learn", "to_route": "one_lms/www/batch/learn"},

]

fixtures = [
    {
        "dt": "Custom DocPerm",
        "filters": {
            "parent": ("in",("LMS Course"))
        }
    }
]
