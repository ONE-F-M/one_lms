import frappe
from frappe import _
from frappe.utils import ceil
from lms.lms.doctype.lms_enrollment.lms_enrollment import LMSEnrollment as BaseLMSEnrollment
from one_lms.overrides.lms_course import clear_course_learning_records, is_re_enrollment_allowed


class LMSEnrollment(BaseLMSEnrollment):
    def validate(self):
        # On a re-enrollment course a second enrollment row for the same
        # member+course is expected - after_insert prunes the older one - so the
        # base duplicate guard would block the very flow it is meant to protect.
        if is_re_enrollment_allowed(self.course):
            return

        super().validate()

    def on_update(self):
        update_program_progress(self.member)

    def after_insert(self):
        self.reset_course_progress()
        self.notify_user()

    def notify_user(self):
        """Queue the "you have been enrolled" mail.

        Enqueued rather than sent inline: this used to run inside validate(), one
        blocking sendmail per row, which made bulk enrollment O(n) slow enough to
        hit the request timeout - and mailed people whose enrollment was later
        rolled back.
        """
        frappe.enqueue(
            "one_lms.overrides.lms_enrollment.send_enrollment_email",
            queue="long",
            enqueue_after_commit=True,
            enrollment=self.name,
        )

    def reset_course_progress(self):
        """When a member is re-enrolled in a course, wipe their previous learning
        records so they start fresh, and drop the now-stale earlier enrollment so
        we don't accumulate duplicate enrollments for the same member + course.

        Runs in after_insert (not before_insert) so the new enrollment already
        exists and can be excluded when removing the older duplicates.
        """
        if not is_re_enrollment_allowed(self.course):
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


def send_enrollment_email(enrollment: str):
    """Notify the member that they have been enrolled in a course."""
    if not frappe.db.exists("LMS Enrollment", enrollment):
        # Rolled back or superseded by a re-enrollment before the job ran.
        return

    doc = frappe.get_doc("LMS Enrollment", enrollment)
    template = "one_lms/templates/emails/lms_course_enrollment.html"
    try:
        args = {
            "course_name": frappe.db.get_value("LMS Course", doc.course, "title"),
            "student_name": doc.member_name,
            "enrollment_date": doc.get("date") or frappe.utils.nowdate(),
            "course_url": f"{frappe.utils.get_url()}/courses/{doc.course}/",
        }
        frappe.sendmail(
            recipients=[doc.member],
            subject=_("You have been Enrolled!"),
            message=frappe.render_template(template, context=args),
            header=[_("Course Enrollment on LMS"), "green"],
        )
    except Exception:
        frappe.log_error(
            title=f"Error notifying {doc.member} of enrollment in {doc.course}",
            message=frappe.get_traceback(with_context=True),
        )


def update_program_progress(member: str):
    """Recompute program progress for every program the member belongs to.

    Reimplemented from lms so a program with no courses cannot raise
    ZeroDivisionError - in the enrollment tool that aborted the whole batch.
    """
    programs = frappe.get_all("LMS Program Member", {"member": member}, ["parent", "name"])

    for program in programs:
        courses = frappe.get_all("LMS Program Course", {"parent": program.parent}, pluck="course")
        if not courses:
            continue

        total_progress = 0
        for course in courses:
            total_progress += (
                frappe.db.get_value("LMS Enrollment", {"course": course, "member": member}, "progress") or 0
            )

        frappe.db.set_value("LMS Program Member", program.name, "progress", ceil(total_progress / len(courses)))
