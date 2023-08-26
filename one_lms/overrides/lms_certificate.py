import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import add_years, nowdate
from lms.lms.utils import is_certified
from lms.lms.doctype.lms_certificate.lms_certificate import LMSCertificate


class CustomLMSCertificate(LMSCertificate):
    def validate(self):
        self.validate_duplicate_certificate()

    def validate_duplicate_certificate(self):
        table = frappe.qb.DocType("LMS Certificate")
        certificates = (
            frappe.qb.from_("LMS Certificate")
                .select(
                    "name", "issue_date", "expiry_date", "course", "member"
                )
                .where(
                    (table.name != (self.name or "No Name"))
                    & (table.member == self.member)
                    & (table.course == self.course)
                    & (
                        ((self.issue_date > table.issue_date) & (self.issue_date < table.expiry_date))
                        | ((self.expiry_date > table.issue_date) & (self.expiry_date < table.expiry_date))
                        | ((self.issue_date <= table.issue_date) & (self.expiry_date >= table.expiry_date))
                        | ((table.expiry_date.isnull()) & (self.issue_date >= table.issue_date))
                    )
                )
        ).run(as_dict=True)

        if len(certificates):
            full_name = frappe.db.get_value("User", self.member, "full_name")
            course_name = frappe.db.get_value("LMS Course", self.course, "title")
            frappe.throw(
                _("{0} is already certified for the course {1}").format(full_name, course_name)
            )

    def on_update(self):
        super().on_update()
