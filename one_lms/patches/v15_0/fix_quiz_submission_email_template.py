import frappe

TEMPLATE_NAME = "Daily Quiz Submission"

# Body for the daily quiz submission digest sent by
# one_lms.notification.notifications.notify_quiz_submission. This mirrors
# one_lms/templates/emails/lms_quiz_submission_group_template.html — the record
# below wins whenever LMS Settings.quiz_submission_template is set, so the two
# must be kept in sync.
#
# The previous body resolved the course with a bare `course` variable that the
# notification never passed. An undefined name is falsy in Jinja, so
# frappe.db.get_value("LMS Course", course, ...) ran without a filter and
# returned the first tabLMS Course row by `modified desc` — every digest showed
# that one course no matter which quiz was submitted. The body now reads the
# course and quiz from each LMS Quiz Submission row instead.
RESPONSE_HTML = """<!--
	Available data format -> 
	{
		'course': 'avsec-awareness-awareness-course', 
		'quiz' 'Security Awareness Course Evaluation',
		'members': [{'member': 'John Doe', 'member_id': 'johndoe@gmail.com', 'quiz_submission': '4645asa23', 'score': 87, 'result': 'PASS'}], 
		'names': ['4645asa23']  (IDs of LMS Quiz submission)
	}
-->
{% set date = frappe.format_date(frappe.utils.today()) %}
<p>
	{{ _("The following trainees have submitted their quiz.") }}
</p>
<br>
<table class="table table-bordered table-condensed">
	<thead>
	<tr>
	    <th class="text-center">SI No.</th>
	    <th class="text-center">ID Number</th>
	    <th class="text-center">Trainee Name</th>
	    <th class="text-center">Course Name</th>
	    <th class="text-center">Quiz Submission</th>
	    <th class="text-center">Evaluation Score</th>
	    <th class="text-center">Result</th>
	    <th class="text-center">Date of Submission</th>
	</tr>
    </thead>
    <tbody>
	{% for member in members %}
		{# Read course/quiz from the submission itself so every row shows its own course #}
		{% set submission = frappe.db.get_value("LMS Quiz Submission", member.quiz_submission, ["creation", "quiz", "course"], as_dict=True) or {} %}
		{% set course_name = submission.get("course") or member.get("course") %}
		{% set course_title = frappe.db.get_value("LMS Course", course_name, "title") if course_name else "" %}
		{% set quiz_title = frappe.db.get_value("LMS Quiz", submission.get("quiz"), "title") if submission.get("quiz") else "" %}
		{% set user = frappe.db.get_value("User", member.member_id, ["username"], as_dict=True) or {} %}
		<tr>
		    <td class="text-center">{{ loop.index }}</td>
		    <td class="text-center">{{ user.get("username") or "" }}</td>
		    <td class="text-center">{{ member.member }}</td>
		    <td class="text-center">{{ course_title }}</td>
		    <td class="text-center">
			<a href="app/lms-quiz-submission/{{ member['quiz_submission'] }}">
			    {{ quiz_title }}
			</a>
		    </td>
		    <td class="text-center">{{ member.score }}</td>
		    <td class="text-center">{{ member.result }}</td>
		    <td class="text-center">{{ frappe.format(submission.get("creation"), {'fieldtype': 'Date'}) }}</td>
		</tr>
	{% endfor %}
    </tbody>
</table>"""

SUBJECT = "Daily Quiz Submission Information"


def execute():
    """Fix the course name shown in the Daily Quiz Submission email template."""

    if not frappe.db.exists("Email Template", TEMPLATE_NAME):
        # Nothing to update on sites that don't use this template.
        return

    doc = frappe.get_doc("Email Template", TEMPLATE_NAME)
    doc.use_html = 1
    doc.subject = SUBJECT
    doc.response_html = RESPONSE_HTML
    doc.save(ignore_permissions=True)
