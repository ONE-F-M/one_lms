def get_lms_quiz_submission_custom_fields():
    return {
        "LMS Quiz Submission": [
            {
                "fieldname": "instructor_notified_submission",
                "fieldtype": "Check",
                "label": "Instructor Notified Submission",
                "read_only": 1,
                "insert_after": "result",
                "default": "0"
            },
            {
                "fieldname": "custom_employee_id",
                "fieldtype": "Data",
                "fetch_from": "member.username",
                "label": "Employee ID",
                "insert_after": "member_name"
            },
            {
                "fieldname": "custom_date",
                "fieldtype": "Datetime",
                "label": "Submission Date",
                "read_only": 1,
                "insert_after": "owner"
            }
        ]
    }
