import frappe
from frappe.core.doctype.user.user import User as BaseUser

class User(BaseUser):
    def after_insert(self):
        # Add LMS Student role on user creation if not already added
		# On new user signup using SSO, LMS student role is not added by default
        roles = frappe.get_roles(self.name)
		if "LMS Student" not in roles:
			self.add_roles("LMS Student")
