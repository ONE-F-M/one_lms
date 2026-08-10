import frappe
from frappe.model.document import Document

# Records that make a course "already taken" for a member. All of them must be
# cleared on re-enrollment, otherwise the member cannot restart the course:
#   - LMS Course Progress: base LMS treats a row's *existence* as "lesson done"
#     (see course_lesson.save_progress -> already_completed), so leftover rows
#     freeze progress and completion check marks.
#   - LMS Quiz / Assignment Submission: leftover submissions count as passed and
#     block a fresh first attempt.
LEARNING_RECORD_DOCTYPES = (
    "LMS Course Progress",
    "LMS Quiz Submission",
    "LMS Assignment Submission",
)


def is_re_enrollment_allowed(course):
    return frappe.db.get_value("LMS Course", course, "allow_reenrollments")


def clear_course_learning_records(course, member):
    """Delete progress, quiz and assignment submissions so the member can retake
    the course from a clean slate."""
    for doctype in LEARNING_RECORD_DOCTYPES:
        frappe.db.delete(doctype, {"course": course, "member": member})


def re_enroll_member(course, member):
    clear_course_learning_records(course, member)
    enrollment = frappe.get_doc("LMS Enrollment", { "course": course, "member": member })
    enrollment.progress = 0
    enrollment.current_lesson = ""
    enrollment.save(ignore_permissions=True)

@frappe.whitelist()
def re_enroll_single_member(course, member):
    if not is_re_enrollment_allowed(course):
        frappe.throw("Re-Enrollments are not allowed in this course")
    if not frappe.db.exists("LMS Enrollment", { "course": course, "member": member }):
        frappe.throw(f"{member} is currently not enrolled in {course}")
    re_enroll_member(course=course, member=member)
    return "OK"

@frappe.whitelist()
def re_enroll_all_members(course):
    if not is_re_enrollment_allowed(course):
        frappe.throw("Re-Enrollments are not allowed in this course")
    enrollments = frappe.get_all("LMS Enrollment", {"course": course}, ["member", "course"])
    for enrollment in enrollments:
        re_enroll_member(course=enrollment.course, member=enrollment.member)
    return "OK"
