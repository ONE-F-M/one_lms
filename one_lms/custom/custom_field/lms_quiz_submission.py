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
            }
        ]
    }
