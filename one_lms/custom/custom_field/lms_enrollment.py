def get_lms_enrollment_custom_fields():
    return {
        "LMS Enrollment": [
            {
                "fieldname": "instructor_notified_completion",
                "fieldtype": "Check",
                "label": "Instructor Notified Completion",
                "read_only": 1,
                "insert_after": "role",
                "default": "0",
                "depends_on": "eval:doc.progress==100"
            }
        ]
    }
