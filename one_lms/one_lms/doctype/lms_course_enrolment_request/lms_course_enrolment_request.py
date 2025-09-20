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
            instructor_emails = self.get_instructors()
            if instructor_emails:
                member_doc = frappe.get_doc("User", self.member)
                content = self.get_email_content(member_doc)
                context = dict(
                    header="Dear Instructor,<br/> Good day.",
                    document_name=self.name,
                    document_type=self.doctype,
                    document_link=frappe.utils.get_url(self.get_url()),
                    description="A new course enrollment request has been submitted. Please review this request in the system and take the necessary action.",
                    content=content,
                    link_name="Link to the Course Enrolment Request",
                )
                subject = f"Course Enrollment Request: {self.course}"
                
                msg = frappe.render_template('one_lms/templates/emails/default_email.html', context=context)
                frappe.sendmail(
                    recipients=instructor_emails,
                    subject=subject,
                    message=msg
                )
                # Create Notification Log for each instructor
                self.create_notification_log(instructor_emails, subject, msg)
        except Exception as e:
            frappe.log_error(message=f"Error sending instructor notification: {e}", title="LMS Enrolment Request Notification")

    def get_instructors(self):
        course_doc = frappe.get_doc("LMS Course", self.course)
        instructor_emails = []
        if course_doc.instructors:
            for instructor in course_doc.instructors:
                if instructor.instructor:
                    instructor_emails.append(instructor.instructor)
        return instructor_emails

    def get_email_content(self, member_doc):
        return f"""The details of the enrolment request are shown below:
            <br/><br/>
            Employee ID: {member_doc.username}
            <br/>
            Employee Name: {member_doc.full_name or self.member}
            <br/>
            Email: {self.member}
            <br/>
            Course Name: {self.course}
            <br/>
            Request Date: {frappe.utils.format_datetime(self.creation, "medium")}
        """

    def create_notification_log(self, instructor_emails, subject, msg):
        for user in instructor_emails:
            notification_doc = frappe.get_doc({
                "doctype": "Notification Log",
                "subject": subject,
                "email_content": msg,
                "document_type": self.doctype,
                "document_name": self.name,
                "from_user": frappe.session.user,
                "type": "Alert",
                "for_user": user
            })
            notification_doc.insert(ignore_permissions=True)

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
