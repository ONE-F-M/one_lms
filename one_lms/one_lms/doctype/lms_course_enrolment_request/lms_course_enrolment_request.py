# Copyright (c) 2025, ONE-F-M and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

class LMSCourseEnrolmentRequest(Document):
    def after_insert(self):
        self.notify_instructors_on_request()

    def notify_instructors_on_request(self):
        try:
            course_doc = frappe.get_doc("LMS Course", self.course)
            instructor_emails = []
            if course_doc.instructors:
                for instructor in course_doc.instructors:
                    if instructor.instructor:
                        instructor_emails.append(instructor.instructor)
            if instructor_emails:
                member_doc = frappe.get_doc("User", self.member)
                member_name = member_doc.full_name or self.member
                subject = f"New Course Enrollment Request - {course_doc.title}"
                message = f"""
                <p>Dear Instructor,</p>
                <p>A new course enrollment request has been submitted:</p>
                <ul>
                <li><strong>Course:</strong> {course_doc.title}</li>
                <li><strong>Student:</strong> {member_name} ({self.member})</li>
                <li><strong>Request Date:</strong> {frappe.format(self.creation, 'datetime')}</li>
                </ul>
                <p>Please review and approve/reject the request from the LMS Course Enrolment Request list.</p>
                <p>Thank you.</p>
                """
                for email in instructor_emails:
                    notification_doc = frappe.get_doc({
                        "doctype": "Notification Log",
                        "subject": subject,
                        "email_content": message,
                        "document_type": self.doctype,
                        "document_name": self.name,
                        "from_user": frappe.session.user,
                        "type": "Alert",
                        "for_user": email
                    })
                    notification_doc.insert(ignore_permissions=True)
        except Exception as e:
            frappe.log_error(f"Error sending instructor notification", "LMS Enrolment Request Notification")

    def notify_member_on_status_change(self, status):
        try:
            member_doc = frappe.get_doc("User", self.member)
            member_name = member_doc.full_name or self.member
            course_doc = frappe.get_doc("LMS Course", self.course)
            if status == "Approved":
                subject = f"Course Enrolment Request Approved - {course_doc.title}"
                message = f"""
                <p>Dear {member_name},</p>
                <p>Great news! Your course enrolment request has been <strong>approved</strong>.</p>
                <ul>
                <li><strong>Course:</strong> {course_doc.title}</li>
                <li><strong>Status:</strong> Approved</li>
                <li><strong>Date:</strong> {frappe.format(frappe.utils.now(), 'datetime')}</li>
                </ul>
                <p>You can now access the course content and begin your learning journey.</p>
                <p>Happy Learning!</p>
                """
            else:
                subject = f"Course Enrolment Request Rejected - {course_doc.title}"
                message = f"""
                <p>Dear {member_name},</p>
                <p>We regret to inform you that your course enrolment request has been <strong>rejected</strong>.</p>
                <ul>
                <li><strong>Course:</strong> {course_doc.title}</li>
                <li><strong>Status:</strong> Rejected</li>
                <li><strong>Date:</strong> {frappe.format(frappe.utils.now(), 'datetime')}</li>
                </ul>
                <p>Please contact the course instructors for more information.</p>
                <p>Thank you.</p>
                """
            notification_doc = frappe.get_doc({
                "doctype": "Notification Log",
                "subject": subject,
                "email_content": message,
                "document_type": self.doctype,
                "document_name": self.name,
                "from_user": frappe.session.user,
                "type": "Alert",
                "for_user": self.member
            })
            notification_doc.insert(ignore_permissions=True)
        except Exception as e:
            frappe.log_error(f"Error sending member notification", "LMS Enrolment Request Status Notification")

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
    enrolment_request.notify_member_on_status_change(enrolment_request.status)
    frappe.db.commit()
    return "success"
