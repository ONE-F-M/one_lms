def get_course_lesson_custom_fields():
    return {
        "Course Lesson": [
            {
                "fieldname": "lms_assignment",
                "fieldtype": "Link",
                "label": "LMS Assignment",
                "options": "LMS Assignment",
                "insert_after": "section_break_16"
            }
        ]
    }
