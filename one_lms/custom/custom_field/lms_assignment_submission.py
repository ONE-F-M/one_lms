def get_lms_assignment_submission_custom_fields():
	return {
		"LMS Assignment Submission": [
			{
				"fieldname": "instructor_notified_submission",
				"fieldtype": "Check",
				"label": "Instructor Notified Submission",
				"read_only": 1,
				"insert_after": "column_break_ygdu",
				"default": "0",
			},
			{
				"fieldname": "custom_employee_id",
				"fieldtype": "Data",
				"fetch_from": "member.username",
				"label": "Employee ID",
				"insert_after": "member_name",
			},
		]
	}
