import frappe
from frappe import _
from frappe.model.document import Document
from lms.lms.doctype.lms_enrollment.lms_enrollment import LMSEnrollment as BaseLMSEnrollment
from one_lms.overrides.lms_course import clear_course_learning_records

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

    
    def after_insert(self):
        self.reset_course_progress()

    def reset_course_progress(self):
        """When a member is re-enrolled in a course, wipe their previous learning
        records so they start fresh, and drop the now-stale earlier enrollment so
        we don't accumulate duplicate enrollments for the same member + course.

        Runs in after_insert (not before_insert) so the new enrollment already
        exists and can be excluded when removing the older duplicates.
        """
        if not frappe.db.get_value("LMS Course", self.course, "allow_reenrollments"):
            return

        previous_enrollments = frappe.get_all(
            "LMS Enrollment",
            filters={
                "course": self.course,
                "member": self.member,
                "name": ["!=", self.name],
            },
            pluck="name",
        )
        if not previous_enrollments:
            return

        # Delete progress, quiz and assignment submissions. The new enrollment has
        # none yet, so this effectively resets the member to a clean slate.
        clear_course_learning_records(self.course, self.member)

        for enrollment in previous_enrollments:
            frappe.db.delete("LMS Enrollment", enrollment)

    
