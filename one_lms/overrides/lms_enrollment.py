import frappe
from frappe import _
from frappe.model.document import Document
from lms.lms.doctype.lms_enrollment.lms_enrollment import LMSEnrollment as BaseLMSEnrollment

class LMSEnrollment(BaseLMSEnrollment):
    def validate(self):
        
        if self.is_new():
            self.notify_user()
            

    def notify_user(self):
        """Notify the user that they have been Enrolled in a course. Add course details and include link as well"""
        template = "one_lms/templates/emails/lms_course_enrollment.html"
        try:
            recipient = [self.member]
            subject = "You have been Enrolled!"
            course_title = frappe.get_value("LMS Course", self.course, 'title')
            if not getattr(self, 'custom_date_', None):
                self.custom_date_ = frappe.utils.nowdate()
            args = {
                'course_name': course_title,
                'student_name': self.member_name,
                'enrollment_date': self.custom_date_,
                'course_url': f"{frappe.utils.get_url()}/courses/{self.course}/"
            }
            message = frappe.render_template(template, context=args)
            frappe.sendmail(
                recipients=recipient,
                subject=subject,
                message=message,
                header=["Course Enrollment on LMS", "green"],
            )
            frappe.msgprint("Employee Notified", alert=1)
        except Exception as e:
            frappe.msgprint("Error Notifying Employee", alert=1)
            frappe.log_error(title="Error Notifying Employee", message=e)

    
    def before_insert(self):
        self.reset_course_progress()

    def reset_course_progress(self):
        if not frappe.db.get_value("LMS Course", self.course, "allow_reenrollments"):
            return
        if not frappe.db.exists("LMS Enrollment", {"course": self.course, "member": self.member}):
            return
        frappe.db.sql(
            "UPDATE `tabLMS Course Progress` SET status = 'Incomplete' WHERE course = %s AND member = %s",
            (self.course, self.member)
        )

    
