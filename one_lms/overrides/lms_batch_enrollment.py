import json

import frappe
from frappe import _
from frappe.utils import formatdate, get_url
from frappe.email.doctype.email_template.email_template import get_email_template
from lms.lms.doctype.lms_batch_enrollment.lms_batch_enrollment import (
	LMSBatchEnrollment as BaseLMSBatchEnrollment,
)

from one_lms.overrides.lms_batch import format_time_value


class LMSBatchEnrollment(BaseLMSBatchEnrollment):
	def after_insert(self):
		# Route the confirmation mail through our corrected sender (full
		# placeholder set) instead of the base module-level send_mail, then keep
		# the rest of the base behaviour (adding the member to any live class).
		send_confirmation_email(self)
		self.add_member_to_live_class()


@frappe.whitelist()
def send_confirmation_email(doc):
	if isinstance(doc, str):
		doc = frappe._dict(json.loads(doc))

	if doc.confirmation_email_sent:
		return

	outgoing_email_account = frappe.get_cached_value(
		"Email Account", {"default_outgoing": 1, "enable_outgoing": 1}, "name"
	)
	if outgoing_email_account or frappe.conf.get("mail_login"):
		send_mail(doc)
		frappe.db.set_value(doc.doctype, doc.name, "confirmation_email_sent", 1)


def send_mail(doc):
	# Load the full batch doc (via the LMS Batch override) so we have the courses
	# child table and get_timetable_html() available.
	batch = frappe.get_doc("LMS Batch", doc.batch)

	subject = _("Enrollment Confirmation for {0}").format(batch.title)
	template = "batch_confirmation"
	custom_template = batch.confirmation_email_template or frappe.db.get_single_value(
		"LMS Settings", "batch_confirmation_template"
	)

	# Every placeholder the template can reference must be present here. Frappe's
	# Jinja env uses DebugUndefined, so any missing variable renders as a literal
	# "{{ placeholder }}" in the email — which is exactly how end_date, end_time,
	# courses, timetable and course_link were leaking into confirmation mails.
	args = {
		"title": batch.title,
		"student_name": doc.member_name,
		"start_date": formatdate(batch.start_date) if batch.start_date else "",
		"end_date": formatdate(batch.end_date) if batch.end_date else "",
		"start_time": format_time_value(batch.start_time),
		"end_time": format_time_value(batch.end_time),
		"medium": batch.medium or "",
		"name": batch.name,
		"courses": ", ".join([course.title for course in batch.courses])
		if batch.courses
		else "",
		"course_link": get_url(f"/lms/batches/{batch.name}"),
		"timetable": batch.get_timetable_html(),
	}

	content = None
	if custom_template:
		email_template = get_email_template(custom_template, args)
		subject = email_template.get("subject")
		content = email_template.get("message")

	frappe.sendmail(
		recipients=doc.member,
		subject=subject,
		template=template if not custom_template else None,
		# `content` is already fully rendered by get_email_template, so we do not
		# pass `args` again on that path to avoid a fragile second render.
		content=content,
		args=args if not custom_template else None,
		header=[_(batch.title), "green"],
		retry=3,
	)
