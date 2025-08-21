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
            },
            {
                "fieldname": "date",
                "fieldtype": "Date",
                "label": "Date",
                "default": "Today",
                "in_filter": 1,
                "in_list_view": 1,
            },
            {
                "fieldname": "course_completion_date",
                "fieldtype": "Date",
                "label": "Course Completion Date",
                "depends_on": "eval:doc.progress==100",
                "read_only": 1,
                "in_filter": 1,
            }
        ]
    }
