import frappe
from frappe import _
from frappe.utils import escape_html, formatdate, get_time, get_url
from frappe.email.doctype.email_template.email_template import get_email_template
from lms.lms.doctype.lms_batch.lms_batch import LMSBatch as BaseLMSBatch


def format_time_value(value):
    """Return a human friendly HH:MM AM/PM string, or empty string if not set."""
    if not value:
        return ""
    return get_time(value).strftime("%I:%M %p")


class LMSBatch(BaseLMSBatch):
    def send_mail(self, student):
        subject = _("Enrollment Confirmation for the Next Training Batch")
        template = "batch_confirmation"
        custom_template = frappe.db.get_single_value(
            "LMS Settings", "batch_confirmation_template"
        )

        # Every placeholder used by the template must be present here. Frappe's
        # Jinja env uses DebugUndefined, so any missing variable is rendered as a
        # literal "{{ placeholder }}" in the email instead of a blank — which is
        # exactly how end_date/end_time/courses were leaking into notifications.
        args = {
            "student_name": student.student_name,
            "title": self.title,
            "start_date": formatdate(self.start_date) if self.start_date else "",
            "end_date": formatdate(self.end_date) if self.end_date else "",
            "start_time": format_time_value(self.start_time),
            "end_time": format_time_value(self.end_time),
            "medium": self.medium or "",
            "name": self.name,
            "courses": ", ".join([course.title for course in self.courses])
            if self.courses
            else "",
            "course_link": get_url(f"/lms/batches/{self.name}"),
            "timetable": self.get_timetable_html(),
        }

        # Make any remaining doc fields available too, without overriding the
        # friendly values built above.
        for key, value in self.as_dict().items():
            args.setdefault(key, value)

        content = None
        if custom_template:
            email_template = get_email_template(custom_template, args)
            subject = email_template.get("subject")
            content = email_template.get("message")

        frappe.sendmail(
            recipients=student.student,
            subject=subject,
            template=template if not custom_template else None,
            # `content` is already fully rendered by get_email_template, so we do
            # not pass `args` again on that path to avoid a fragile second render.
            content=content,
            args=args if not custom_template else None,
            header=[subject, "green"],
            retry=3,
        )

    def get_timetable_html(self):
        """Build a simple, email-safe HTML table of the batch schedule.

        Uses plain HTML attributes (not inline styles / CSS classes) so the
        table survives email clients that strip <style> and class-based CSS.
        """
        if not self.timetable:
            return ""

        header = (
            "<tr>"
            f"<th align='left'>{_('Date')}</th>"
            f"<th align='left'>{_('Session')}</th>"
            f"<th align='left'>{_('Time')}</th>"
            "</tr>"
        )
        rows = []
        for entry in self.timetable:
            day = formatdate(entry.date) if entry.date else ""
            session = escape_html(entry.reference_docname or "")
            start = format_time_value(entry.start_time)
            end = format_time_value(entry.end_time)
            timing = f"{start} - {end}".strip(" -")
            rows.append(f"<tr><td>{day}</td><td>{session}</td><td>{timing}</td></tr>")

        return (
            "<table border='1' cellpadding='6' cellspacing='0'>"
            + header
            + "".join(rows)
            + "</table>"
        )
