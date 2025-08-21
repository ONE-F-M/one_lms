import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import add_years, nowdate
from lms.lms.utils import is_certified
from frappe.email.doctype.email_template.email_template import get_email_template
from lms.lms.doctype.lms_certificate.lms_certificate import LMSCertificate as BaseLMSCertificate

class LMSCertificate(BaseLMSCertificate):
    def send_mail(self):
        subject = _("Congratulations on getting certified!")
        template = "certification"
        custom_template = frappe.db.get_single_value("LMS Settings", "certification_template")
        course_name, course_title = frappe.db.get_value("LMS Course", self.course, ["name", "title"])

        args = {
            "student_name": self.member_name,
            "course": course_title,
            "certificate_name": self.name,
            "certificate_link":f"{frappe.utils.get_url()}/courses/{course_name}/{self.name}"
        }

        if custom_template:
            email_template = get_email_template(custom_template, args)
            subject = email_template.get("subject")
            content = email_template.get("message")
        frappe.sendmail(
            recipients=self.member,
            subject=subject,
            template=template if not custom_template else None,
            content=content if custom_template else None,
            args=args,
            header=[subject, "green"],
        )

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