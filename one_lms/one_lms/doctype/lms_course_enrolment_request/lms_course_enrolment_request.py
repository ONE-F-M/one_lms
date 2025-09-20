# Copyright (c) 2025, ONE-F-M and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

class LMSCourseEnrolmentRequest(Document):
    def after_insert(self):
        self.notify_instructors_on_request()

    def notify_instructors_on_request(self):
        try:
            instructors = self.get_instructors()
            if instructors:
                content = self.get_email_content_for_instructor()
                context = dict(
                    header="Dear Instructor,<br/> Good day.",
                    document_name=self.name,
                    document_type=self.doctype,
                    document_link=frappe.utils.get_url(self.get_url()),
                    description="A new course enrollment request has been submitted. Please review this request in the system and take the necessary action.",
                    content=content,
                    link_name="Link to the Course Enrolment Request",
                )
                subject = f"Course Enrollment Request: {self.course_title or self.course}"
                
                msg = frappe.render_template('one_lms/templates/emails/default_email.html', context=context)
                frappe.sendmail(
                    recipients=instructors,
                    subject=subject,
                    message=msg
                )
                # Create Notification Log for each instructor
                self.create_notification_log(instructors, subject, msg)
        except Exception as e:
            frappe.log_error(message=f"Error sending instructor notification: {e}", title="LMS Enrolment Request Notification")

    def get_instructors(self):
        course_doc = frappe.get_doc("LMS Course", self.course)
        instructors = []
        if course_doc.instructors:
            for instructor in course_doc.instructors:
                if instructor.instructor:
                    instructors.append(instructor.instructor)
        return instructors

    def get_email_content_for_instructor(self):
        return f"""The details of the enrolment request are shown below:
            <br/><br/>
            Employee ID: {self.username}
            <br/>
            Employee Name: {self.member_name or self.member}
            <br/>
            Email: {self.member}
            <br/>
            Course Name: {self.course_title or self.course}
            <br/>
            Request Date: {frappe.utils.format_datetime(self.creation, "medium")}
        """

    def create_notification_log(self, emails, subject, msg):
        for user in emails:
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

    @frappe.whitelist()
    def enrolment_request_approve_reject(self, action):
        if action == "Approve":
            self.db_set("status", "Approved")
        elif action == "Reject":
            self.db_set("status", "Rejected")
        self.on_update()
        return "success"

    def on_update(self):
        if self.status == "Approved":
            self.create_enrollment()
        self.notify_member_on_instructor_action()

    def create_enrollment(self):
        if self.status != "Approved":
            return
        existing_enrollment = frappe.db.exists(
            "LMS Enrollment",
            {"course": self.course, "member": self.member, "member_type": "Student"},
        )
        if existing_enrollment:
            return
        frappe.get_doc({
            "doctype": "LMS Enrollment",
            "course": self.course,
            "role": "Member",
            "member_type": "Student",
            "member": self.member,
        }).insert(ignore_permissions=True)

    def notify_member_on_instructor_action(self):
        if self.status not in ["Approved", "Rejected"]:
            return
        content = self.get_email_content_for_member()
        context = dict(
            header="Dear {0},<br/> Good day.".format(self.member_name or self.member),
            document_name=self.name,
            document_type=self.doctype,
            document_link=frappe.utils.get_url(f"lms/courses/{self.course}"),
            description=f"Your course enrollment request has been {self.status.lower()}.",
            content=content,
            link_name="Link to the Course Page",
        )
        subject = f"Course Enrollment Request for {self.course_title} has been {self.status.lower()}"

        msg = frappe.render_template('one_lms/templates/emails/default_email.html', context=context)
        frappe.sendmail(
            recipients=[self.member],
            subject=subject,
            message=msg
        )
        # Create Notification Log for each instructor
        self.create_notification_log([self.member], subject, msg)

    def get_email_content_for_member(self):
        return f"""
            Course Name: {self.course_title or self.course}
            <br/>
            Approver: {frappe.db.get_value("User", frappe.session.user, "full_name") or frappe.session.user}
            <br/>
            Decision Date: {frappe.utils.format_datetime(self.modified, "medium")}
        """

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