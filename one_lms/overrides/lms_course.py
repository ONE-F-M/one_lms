import frappe
from frappe.model.document import Document


def is_re_enrollment_allowed(course):
	return frappe.db.get_value("LMS Course", course, "allow_reenrollments")


def re_enroll_member(course, member):
	frappe.db.delete("LMS Course Progress", {"course": course, "member": member})
	enrollment = frappe.get_doc("LMS Enrollment", {"course": course, "member": member})
	enrollment.progress = 0
	enrollment.current_lesson = ""
	enrollment.save(ignore_permissions=True)


@frappe.whitelist()
def re_enroll_single_member(course, member):
	if not is_re_enrollment_allowed(course):
		frappe.throw("Re-Enrollments are not allowed in this course")
	if not frappe.db.exists("LMS Enrollment", {"course": course, "member": member}):
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
