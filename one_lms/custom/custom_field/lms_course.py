def get_lms_course_custom_fields():
    return {
        "LMS Course": [
            {
                "fieldname": "allow_reenrollments",
                "fieldtype": "Check",
                "label": "Allow Re-Enrollments",
                "default": "0",
                "insert_after": "category",
            },
            {
                "fieldname": "template",
                "fieldtype": "Link",
                "label": "Template",
                "options": "Print Format",
                "depends_on": "enable_certification",
            },
            {
                "fieldname": "default_instructor",
                "fieldtype": "Select",
                "label": "Default Instructor",
                "description": "The selected instructor will be displayed on the course certificates.",
                "insert_after": "grant_certificate_after",
            }
        ]
    }
