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
                # Read by one_lms.overrides.lms_certificate.get_expiry_date. The
                # field never existed on this site, so certificate expiry was
                # silently never applied (and an unguarded read raised "Unknown
                # column" for every certificate the portal tried to generate).
                "fieldname": "expiry",
                "fieldtype": "Int",
                "label": "Certificate Expires After (Years)",
                "description": "Leave at 0 for a certificate that never expires.",
                "default": "0",
                "non_negative": 1,
                "depends_on": "enable_certification",
                "insert_after": "template",
            },
            {
                "fieldname": "default_instructor",
                "fieldtype": "Select",
                "label": "Default Instructor",
                "description": "The selected instructor will be displayed on the course certificates.",
                "insert_after": "image",
            }
        ]
    }
