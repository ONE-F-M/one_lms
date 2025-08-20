def get_lms_course_custom_fields():
    return {
        "LMS Course": [
            {
                "fieldname": "category",
                "fieldtype": "Link",
                "label": "Category",
                "options": "LMS Course Category",
                "insert_after": "status",
            }
        ]
    }
