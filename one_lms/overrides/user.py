import frappe
from frappe.core.doctype.user.user import User as BaseUser
from frappe.desk.doctype.notification_settings.notification_settings import create_notification_settings


class User(BaseUser):
	def after_insert(self):
		create_notification_settings(self.name)
		frappe.cache.delete_key("users_for_mentions")
		frappe.cache.delete_key("enabled_users")
		# Add LMS Student role on user creation if not already added
		# On new user signup using SSO, LMS student role is not added by default
		roles = frappe.get_roles(self.name)
		if "LMS Student" not in roles:
			self.add_roles("LMS Student")
