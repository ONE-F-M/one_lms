def get_lms_settings_custom_fields():
	return {
		"LMS Settings": [
			{
				"fieldname": "course_completion_notification_template",
				"fieldtype": "Link",
				"label": "Course Completion Notification Template",
				"options": "Email Template",
				"insert_after": "certification_template",
			},
			{
				"fieldname": "notification_settings_tab",
				"fieldtype": "Tab Break",
				"label": "Notification Settings",
				"insert_after": "course_completion_notification_template",
			},
			{
				"fieldname": "notify_instructor_course_completion_eod",
				"fieldtype": "Check",
				"label": "Notify Instructor on Course Completion by EOD",
				"default": "0",
				"description": "Check it true to send the course completion notification to the instructors assigned in the corse by end of the day(at 11:50 pm)\nYou can configure custom 'Course Completion Notification Template' from the Email Templates tab.",
				"insert_after": "notification_settings_tab",
			},
			{
				"fieldname": "notify_instructor_assignment_submission_eod",
				"fieldtype": "Check",
				"label": "Notify Instructor on Assignment Submission by EOD",
				"default": "0",
				"description": "Check it true to send the assignment submission notification to the instructors assigned in the corse by end of the day(at 11:50 pm)\nYou can configure custom 'Assignment Submission Template' from the Email Templates tab.\n\nCheck it false will send the assignment submission notification right after the creation",
				"insert_after": "notify_instructor_course_completion_eod",
			},
			{
				"fieldname": "column_break_6xas",
				"fieldtype": "Column Break",
				"insert_after": "notify_instructor_assignment_submission_eod",
			},
			{
				"fieldname": "notify_instructor_quiz_submission_eod",
				"fieldtype": "Check",
				"label": "Notify Instructor on Quiz Submission by EOD",
				"default": "0",
				"description": "Check it true to send the quiz submission notification to the instructors assigned in the corse by end of the day(at 11:50 pm)\nYou can configure custom 'Quiz Submission Notification Template' from the Email Templates tab.",
				"insert_after": "column_break_6xas",
			},
			{
				"fieldname": "quiz_submission_template",
				"fieldtype": "Link",
				"label": "Quiz Submission Notification Template",
				"options": "Email Template",
				"insert_after": "notify_instructor_quiz_submission_eod",
			},
			{
				"fieldname": "training_manager",
				"fieldtype": "Link",
				"label": "Training Manager",
				"options": "User",
				"insert_after": "search_placeholder",
			},
		]
	}
