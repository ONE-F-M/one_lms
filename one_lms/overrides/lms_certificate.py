import frappe
from lms.lms.utils import is_certified
from frappe.utils import add_years, nowdate

@frappe.whitelist()
def create_certificate(course):
	certificate = is_certified(course)

	if certificate:
		return certificate

	else:
		expires_after_yrs = int(frappe.db.get_value("LMS Course", course, "expiry"))
		expiry_date = None
		if expires_after_yrs:
			expiry_date = add_years(nowdate(), expires_after_yrs)

		course_certificate_template = frappe.db.get_value("LMS Course", course, "template")
		if course_certificate_template:
			default_certificate_template = course_certificate_template
		else:
			default_certificate_template = frappe.db.get_value(
				"Property Setter",
				{
					"doc_type": "LMS Certificate",
					"property": "default_print_format",
				},
				"value",
			)

		certificate = frappe.get_doc(
			{
				"doctype": "LMS Certificate",
				"member": frappe.session.user,
				"course": course,
				"issue_date": nowdate(),
				"expiry_date": expiry_date,
				"template": default_certificate_template,
			}
		)
		certificate.save(ignore_permissions=True)
		return certificate