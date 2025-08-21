import random
import frappe
from urllib.parse import quote

def assignment_renderer(detail):
    supported_types = {
        "Document": ".doc,.docx,.xml,application/msword,application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "PDF": ".pdf",
        "Image": ".png, .jpg, .jpeg",
        "Video": "video/*",
    }
    question = detail.split("-")[0]
    file_type = frappe.db.get_value("Course Lesson", {'question': question}, 'file_type') or "PDF"
    accept = supported_types[file_type] if file_type else ""
    return frappe.render_template(
        "templates/assignment.html",
        {
            "question": question,
            "file_type": file_type,
            "accept": accept,
        },
    )

def quiz_renderer(quiz_name):
	if frappe.session.user == "Guest":
		return " <div class='alert alert-info'>" + _(
			"Quiz is not available to Guest users. Please login to continue."
		)
		+"</div>"

	quiz = frappe.db.get_value(
		"LMS Quiz",
		quiz_name,
		[
			"name",
			"title",
			"max_attempts",
			"show_answers",
			"show_submission_history",
			"passing_percentage",
		],
		as_dict=True,
	)
	quiz.questions = []
	fields = ["name", "question", "type", "multiple"]
	for num in range(1, 5):
		fields.append(f"option_{num}")
		fields.append(f"is_correct_{num}")
		fields.append(f"explanation_{num}")
		fields.append(f"possibility_{num}")

	questions = frappe.get_all(
		"LMS Quiz Question",
		filters={"parent": quiz.name},
		fields=["question", "marks"],
		order_by="idx",
	)

	question_list = []
	for question in questions:
		details = frappe.db.get_value("LMS Question", question.question, fields, as_dict=1)
		details["marks"] = question.marks
		question_list.append(details)

	random.shuffle(question_list)

	quiz.questions = question_list

	no_of_attempts = frappe.db.count(
		"LMS Quiz Submission", {"owner": frappe.session.user, "quiz": quiz_name}
	)

	if quiz.show_submission_history:
		all_submissions = frappe.get_all(
			"LMS Quiz Submission",
			{
				"quiz": quiz.name,
				"member": frappe.session.user,
			},
			["name", "score", "creation"],
			order_by="creation desc",
		)

	return frappe.render_template(
		"templates/quiz/quiz.html",
		{
			"quiz": quiz,
			"no_of_attempts": no_of_attempts,
			"all_submissions": all_submissions if quiz.show_submission_history else None,
			"hide_quiz": False,
		},
	)