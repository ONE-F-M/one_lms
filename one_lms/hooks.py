app_name = "one_lms"
app_title = "ONE FM LMS"
app_publisher = "ONE FM"
app_description = "Extend Frappe LMS"
app_email = "develop@one-fm.com"
app_license = "mit"

fixtures = ["Translation"]

# Apps
# ------------------

# required_apps = []

# Each item in the list will be shown as an app in the apps page
# add_to_apps_screen = [
# 	{
# 		"name": "one_lms",
# 		"logo": "/assets/one_lms/logo.png",
# 		"title": "ONE FM LMS",
# 		"route": "/one_lms",
# 		"has_permission": "one_lms.api.permission.has_app_permission"
# 	}
# ]

# Includes in <head>
# ------------------

# include js, css files in header of desk.html
app_include_css = "/assets/one_lms/css/frappe_tinymce.css"
app_include_js = [
	"https://cdnjs.cloudflare.com/ajax/libs/tinymce/6.2.0/tinymce.min.js",
	"/assets/one_lms/js/frappe_tinymce.js"
]

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
# Jinja methods
jinja = {
	"methods": [
		"one_lms.utils.get_course_lessons_progress",
	]
}
doctype_js = {
	"LMS Course" : "public/js/doctype_js/lms_course.js"
}
# doctype_list_js = {"doctype" : "public/js/doctype_list.js"}
# doctype_tree_js = {"doctype" : "public/js/doctype_tree.js"}
# doctype_calendar_js = {"doctype" : "public/js/doctype_calendar.js"}

# Svg Icons
# ------------------
# include app icons in desk
# app_include_icons = "one_lms/public/icons.svg"

# Home Pages
# ----------

# application home page (will override Website Settings)
# home_page = "login"

# website user home page (by Role)
# role_home_page = {
# 	"Role": "home_page"
# }

# Scheduler Events for Notifications (from PR)
scheduler_events = {
	"cron": {
		"50 23 * * *": [
			'one_lms.notification.notifications.notify_course_completion',
			'one_lms.notification.notifications.notify_assignment_submission',
			'one_lms.notification.notifications.notify_quiz_submission'
		]
	}
}

# Template Overrides
override_template = {
	"courses/course.html": "one_lms/www/courses/custom_course.html"
}

# Generators
# ----------

# automatically create page for each record of this doctype
# website_generators = ["Web Page"]

# Jinja
# ----------

# add methods and filters to jinja environment
# jinja = {
# 	"methods": "one_lms.utils.jinja_methods",
# 	"filters": "one_lms.utils.jinja_filters"
# }

# Installation
# ------------

# before_install = "one_lms.install.before_install"
after_install = "one_lms.setup.setup.after_install"

# Uninstallation
# ------------

# before_uninstall = "one_lms.uninstall.before_uninstall"
# after_uninstall = "one_lms.uninstall.after_uninstall"

# Integration Setup
# ------------------
# To set up dependencies/integrations with other apps
# Name of the app being installed is passed as an argument

# before_app_install = "one_lms.utils.before_app_install"
# after_app_install = "one_lms.utils.after_app_install"

# Integration Cleanup
# -------------------
# To clean up dependencies/integrations with other apps
# Name of the app being uninstalled is passed as an argument

# before_app_uninstall = "one_lms.utils.before_app_uninstall"
# after_app_uninstall = "one_lms.utils.after_app_uninstall"

# Desk Notifications
# ------------------
# See frappe.core.notifications.get_notification_config

# notification_config = "one_lms.notifications.get_notification_config"

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

# DocType Class
# ---------------
# Override standard doctype classes

# override_doctype_class = {
# 	"ToDo": "custom_app.overrides.CustomToDo"
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

# scheduler_events = {
# 	"all": [
# 		"one_lms.tasks.all"
# 	],
# 	"daily": [
# 		"one_lms.tasks.daily"
# 	],
# 	"hourly": [
# 		"one_lms.tasks.hourly"
# 	],
# 	"weekly": [
# 		"one_lms.tasks.weekly"
# 	],
# 	"monthly": [
# 		"one_lms.tasks.monthly"
# 	],
# }

# Testing
# -------

# before_tests = "one_lms.install.before_tests"

# Overriding Methods
# ------------------------------
#

after_migrate = [
	"one_lms.after_migrate.execute.update_lesson"
]


override_whitelisted_methods = {
	"lms.lms.doctype.lms_assignment_submission.lms_assignment_submission.upload_assignment": "one_lms.overrides.lms_assignment_submission.upload_assignment",
	"lms.lms.doctype.course_lesson.course_lesson.save_progress": "one_lms.overrides.course_lesson.save_progress",
	"lms.lms.doctype.lms_certificate.lms_certificate.create_certificate": "one_lms.overrides.lms_certificate.create_certificate"
}


override_doctype_class = {
	"LMS Batch": "one_lms.overrides.lms_batch.LMSBatch",
	"User": "one_lms.overrides.user.User",
	"LMS Enrollment": "one_lms.overrides.lms_enrollment.LMSEnrollment",
	"LMS Quiz Submission": "one_lms.overrides.lms_quiz_submission.LMSQuizSubmission",
	"LMS Certificate": "one_lms.overrides.lms_certificate.LMSCertificate"
}
#
# each overriding function accepts a `data` argument;
# generated from the base implementation of the doctype dashboard,
# along with any modifications made in other Frappe apps
# override_doctype_dashboards = {
# 	"Task": "one_lms.task.get_dashboard_data"
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
# 	"one_lms.auth.validate"
# ]

# Automatically update python controller files with type annotations for this app.
# export_python_type_annotations = True

# default_log_clearing_doctypes = {
# 	"Logging DocType Name": 30  # days to retain logs
# }
