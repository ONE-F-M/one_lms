import frappe

TEMPLATE_NAME = "Batch Confirmation Template"

# Body for the batch enrollment confirmation email. Every placeholder here is
# supplied by one_lms.overrides.lms_batch.LMSBatch.send_mail. Keep the two in
# sync — a placeholder without a matching arg renders as a literal "{{ ... }}"
# because Frappe's Jinja env uses DebugUndefined.
RESPONSE = """<div class="ql-editor read-mode">
<p>Dear {{ student_name }},</p>
<p>This email is to confirm your enrollment in our upcoming training: <b>{{ courses }}</b>. Your participation is crucial in maintaining a strong security posture for our organization.</p>
<p><b>Training Date:</b> {{ start_date }} to {{ end_date }}</p>
<p><b>Training Time:</b> {{ start_time }} to {{ end_time }}</p>
<p><b>Course Timetable:</b></p>
{{ timetable }}
<p><b>Course Access Link:</b> <a href="{{ course_link }}">{{ course_link }}</a></p>
<p>Please use the link above to access your course.</p>
</div>"""

SUBJECT = "Training Schedule"


def execute():
    """Update the Batch Confirmation Template email to include the training
    date, time, course timetable and course access link."""

    if not frappe.db.exists("Email Template", TEMPLATE_NAME):
        # Nothing to update on sites that don't use this template.
        return

    doc = frappe.get_doc("Email Template", TEMPLATE_NAME)
    doc.use_html = 0
    doc.subject = SUBJECT
    doc.response = RESPONSE
    doc.save(ignore_permissions=True)
