# Copyright (c) 2024, Frappe and contributors
# For license information, please see license.txt

import json

import frappe
from frappe.model.document import Document


@frappe.whitelist()
def enrol_to_the_course(members, course):
	if isinstance(members, str):
		members = json.loads(members)
	for member in members:
		if not frappe.db.exists("LMS Enrollment", {"member": member["member"], "course": course}):
			lms_enrollment = frappe.get_doc(
				dict(doctype="LMS Enrollment", member=member["member"], course=course)
			)
			lms_enrollment.insert()


class LMSEnrollmentTool(Document):
	pass
