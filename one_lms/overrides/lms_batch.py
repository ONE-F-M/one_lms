import frappe
from frappe import _
from frappe.utils import escape_html, formatdate, get_time, get_url
from lms.lms.doctype.lms_batch.lms_batch import LMSBatch as BaseLMSBatch


def format_time_value(value):
    """Return a human friendly HH:MM AM/PM string, or empty string if not set."""
    if not value:
        return ""
    return get_time(value).strftime("%I:%M %p")


class LMSBatch(BaseLMSBatch):
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
