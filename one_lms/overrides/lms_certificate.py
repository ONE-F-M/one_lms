import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import add_years, cint, flt, nowdate
from lms.lms.utils import get_course_progress, has_course_moderator_role, is_certified
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
def create_certificate(course: str):
	certificate = is_certified(course)

	if certificate:
		return certificate

	validate_course_completed(course)

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
			"expiry_date": get_expiry_date(course),
			"template": default_certificate_template,
		}
	)
	certificate.save(ignore_permissions=True)
	return certificate


def validate_course_completed(course: str):
	"""Only a member who has finished the whole course may generate its certificate.

	The 100% rule used to be enforced in the portal alone - the Get Certificate
	button is hidden below 100% - so calling this method directly issued a
	certificate for an unfinished course. Progress is recomputed rather than read
	off the enrollment row, which can be stale.
	"""
	if frappe.session.user == "Administrator" or has_course_moderator_role():
		return

	if not frappe.db.exists("LMS Enrollment", {"course": course, "member": frappe.session.user}):
		frappe.throw(_("You are not enrolled in this course."), title=_("Not Enrolled"))

	progress = flt(get_course_progress(course))
	if progress < 100:
		frappe.throw(
			_("Your certificate becomes available once the course is 100% complete. You are at {0}%.").format(
				flt(progress, 2)
			),
			title=_("Course Not Completed"),
		)


def get_expiry_date(course: str):
	"""Certificate expiry, when the course defines one.

	Guarded with a meta check: `LMS Course.expiry` is read here but has never been
	defined as a field on this site, so the unguarded read raised "Unknown column"
	for every certificate the portal tried to generate.
	"""
	if not frappe.get_meta("LMS Course").has_field("expiry"):
		return None

	expires_after_yrs = cint(frappe.db.get_value("LMS Course", course, "expiry"))
	return add_years(nowdate(), expires_after_yrs) if expires_after_yrs else None
