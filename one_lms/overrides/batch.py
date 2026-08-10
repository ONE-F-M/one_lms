import frappe
from frappe.utils import flt, format_datetime

from lms.lms.utils import has_submitted_assessment


@frappe.whitelist()
def get_batch_students(batch):
	"""Return the students of a batch along with their true learning progress.

	This overrides ``lms.lms.utils.get_batch_students``. The upstream version
	reports ``progress`` as the ratio of *fully completed* courses/assessments,
	so a trainee who is 99% through the only course of a batch shows 0% on the
	Instructor Dashboard "Students" list — even though the individual profile
	shows the correct 99%. Here ``progress`` is the average of each course's
	actual ``LMS Enrollment.progress`` plus the passed-assessment fraction, so
	partial progress is reflected on the list.
	"""
	students = []
	students_list = frappe.get_all(
		"LMS Batch Enrollment", filters={"batch": batch}, fields=["member", "name"]
	)

	batch_courses = frappe.get_all("Batch Course", {"parent": batch}, ["course", "title"])
	assessments = frappe.get_all(
		"LMS Assessment",
		filters={"parent": batch},
		fields=["name", "assessment_type", "assessment_name"],
	)

	for student in students_list:
		courses_completed = 0
		assessments_completed = 0
		# Running sum of actual progress (in percentage points) across all items,
		# so the dashboard reflects partial learning progress, not just 100% items.
		progress_sum = 0.0
		detail = frappe.db.get_value(
			"User",
			student.member,
			["full_name", "email", "username", "last_active", "user_image"],
			as_dict=True,
		)
		detail.last_active = format_datetime(detail.last_active, "dd MMM YY")
		detail.name = student.name
		detail.courses = frappe._dict()
		detail.assessments = frappe._dict()

		""" Iterate through courses and track their progress """
		for course in batch_courses:
			progress = frappe.db.get_value(
				"LMS Enrollment", {"course": course.course, "member": student.member}, "progress"
			)
			detail.courses[course.title] = progress
			progress_sum += flt(progress)
			if progress == 100:
				courses_completed += 1

		""" Iterate through assessments and track their progress """
		for assessment in assessments:
			title = frappe.db.get_value(assessment.assessment_type, assessment.assessment_name, "title")
			assessment_info = has_submitted_assessment(
				assessment.assessment_name, assessment.assessment_type, student.member
			)
			detail.assessments[title] = assessment_info

			if assessment_info.result == "Pass":
				assessments_completed += 1
				progress_sum += 100

		detail.courses_completed = courses_completed
		detail.assessments_completed = assessments_completed
		total_items = len(batch_courses) + len(assessments)
		if total_items:
			detail.progress = flt(progress_sum / total_items, 2)
		else:
			detail.progress = 0

		students.append(detail)
		students = sorted(students, key=lambda x: x.progress, reverse=True)
	return students
