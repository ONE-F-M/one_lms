# Copyright (c) 2025, ONE-F-M and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

class LMSCourseEnrolmentRequest(Document):
    pass

@frappe.whitelist()
def create_lms_course_enrolment_request(course, member=None):
    frappe.get_doc(
        {
            "doctype": "LMS Course Enrolment Request",
            "course": course,
            "member": member or frappe.session.user,
        }
    ).save(ignore_permissions=True)
    return "OK"

@frappe.whitelist()
def has_pending_request(course, member):
    pending_request = frappe.db.exists(
        "LMS Course Enrolment Request",
        {"course": course, "member": member, "status": "Open"},
    )
    return bool(pending_request)

@frappe.whitelist()
def approve_lms_course_enrolment_request(docname, option):
    enrolment_request = frappe.get_doc("LMS Course Enrolment Request", docname)
    option = option.lower()
    if option == "approve":
        enrolment_request.status = "Approved"
    elif option == "reject":
        enrolment_request.status = "Rejected"
    enrolment_request.save(ignore_permissions=True)
    if option == "approve":
        frappe.get_doc({
            "doctype": "LMS Enrollment",
            "course": enrolment_request.course,
            "role": "Member",
            "member_type": "Student",
            "member": enrolment_request.member,
        }).insert(ignore_permissions=True)
    frappe.db.commit()
    return "success"
